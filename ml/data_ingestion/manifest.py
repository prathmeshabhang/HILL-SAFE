"""
ml/data_ingestion/manifest.py
=============================
Cryptographic dataset manifest generation, immutability verification, and tracking.
Ensures raw inputs and processed outputs adhere to Phase 2 data versioning rules.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file efficiently."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Cannot compute hash: file does not exist: {file_path}")
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DatasetManifest:
    dataset_id: str
    dataset_version: str
    source_dataset_id: str
    source_files: List[Dict[str, str]]  # list of {"path": ..., "sha256": ...}
    output_files: List[Dict[str, str]]  # list of {"path": ..., "sha256": ...}
    schema_version: str
    observation_type: str  # OBSERVATION | DERIVED | MODELLED | PREDICTION | SYNTHETIC
    code_version: str = "3.1.0"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, manifests_dir: Optional[Path] = None) -> Path:
        target_dir = manifests_dir or Path("data/manifests")
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = target_dir / f"{self.dataset_id}_{self.dataset_version}.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return manifest_file

    @classmethod
    def load(cls, manifest_path: Path) -> DatasetManifest:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def verify_integrity(self, base_dir: Optional[Path] = None) -> Dict[str, bool]:
        """
        Verifies that all files declared in output_files match their recorded SHA-256 hashes.
        """
        root = base_dir or Path.cwd()
        results = {}
        for entry in self.output_files:
            rel_path = Path(entry["path"])
            full_path = root / rel_path if not rel_path.is_absolute() else rel_path
            if not full_path.exists():
                results[str(rel_path)] = False
                continue
            curr_hash = compute_sha256(full_path)
            results[str(rel_path)] = curr_hash == entry["sha256"]
        return results


def create_manifest_for_file(
    dataset_id: str,
    dataset_version: str,
    source_dataset_id: str,
    source_path: Path,
    output_path: Path,
    schema_version: str,
    observation_type: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> DatasetManifest:
    """Helper to generate and persist a DatasetManifest for a single source -> output pipeline step."""
    src_hash = compute_sha256(source_path) if source_path.exists() else "SOURCE_EXTERNAL"
    out_hash = compute_sha256(output_path) if output_path.exists() else "PENDING"

    manifest = DatasetManifest(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        source_dataset_id=source_dataset_id,
        source_files=[{"path": str(source_path).replace("\\", "/"), "sha256": src_hash}],
        output_files=[{"path": str(output_path).replace("\\", "/"), "sha256": out_hash}],
        schema_version=schema_version,
        observation_type=observation_type,
        metadata=metadata or {},
    )
    manifest.save()
    return manifest
