"""
tools/validation/registry.py
=============================
FLOODY SHIELD v3.8 - External Scientific Validation Dataset Governance & Registry.
Manages dataset metadata, cryptographic SHA-256 fingerprints, quality gating,
and strict lifecycle progression:
  DISCOVERED -> ACQUIRED -> QUALITY_CHECKED -> VALIDATION_READY -> USED_FOR_VALIDATION
  (or REJECTED, EXPIRED)
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET_DIR = PROJECT_ROOT / "data" / "validation_datasets"
DEFAULT_MANIFEST_PATH = DEFAULT_DATASET_DIR / "manifest.json"


class DatasetLifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    ACQUIRED = "ACQUIRED"
    QUALITY_CHECKED = "QUALITY_CHECKED"
    VALIDATION_READY = "VALIDATION_READY"
    USED_FOR_VALIDATION = "USED_FOR_VALIDATION"
    SYNTHETIC_BENCHMARK = "SYNTHETIC_BENCHMARK"
    PROVISIONAL = "PROVISIONAL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


ALLOWED_TRANSITIONS = {
    DatasetLifecycleState.DISCOVERED: {DatasetLifecycleState.ACQUIRED, DatasetLifecycleState.REJECTED},
    DatasetLifecycleState.ACQUIRED: {DatasetLifecycleState.QUALITY_CHECKED, DatasetLifecycleState.REJECTED},
    DatasetLifecycleState.QUALITY_CHECKED: {DatasetLifecycleState.VALIDATION_READY, DatasetLifecycleState.PROVISIONAL, DatasetLifecycleState.REJECTED},
    DatasetLifecycleState.VALIDATION_READY: {DatasetLifecycleState.USED_FOR_VALIDATION, DatasetLifecycleState.EXPIRED},
    DatasetLifecycleState.USED_FOR_VALIDATION: {DatasetLifecycleState.EXPIRED},
    DatasetLifecycleState.SYNTHETIC_BENCHMARK: {DatasetLifecycleState.EXPIRED},
    DatasetLifecycleState.PROVISIONAL: {DatasetLifecycleState.VALIDATION_READY, DatasetLifecycleState.EXPIRED},
    DatasetLifecycleState.REJECTED: set(),
    DatasetLifecycleState.EXPIRED: set(),
}


@dataclass
class ValidationDatasetMetadata:
    dataset_id: str
    name: str
    target_models: List[str]
    source_agency: str
    geographic_scope: str
    temporal_coverage: str
    sample_size: int
    provenance: str  # REAL, SIMULATED, REPLAY
    lifecycle_state: str  # DatasetLifecycleState
    sha256_hash: str
    file_path: str
    description: str
    created_at: str
    quality_notes: Optional[str] = None
    spatial_bounds: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationDatasetMetadata:
        return cls(**data)


class ValidationDatasetRegistry:
    """Central registry enforcing governance and cryptographic integrity for scientific validation."""

    def __init__(self, dataset_dir: Optional[Path] = None, manifest_path: Optional[Path] = None):
        self.dataset_dir = dataset_dir or DEFAULT_DATASET_DIR
        self.manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
        self.datasets: Dict[str, ValidationDatasetMetadata] = {}
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.load_manifest()

    def compute_sha256(self, file_path: Path) -> str:
        """Calculates exact SHA-256 digest of an on-disk dataset."""
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file does not exist: {file_path}")
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def load_manifest(self) -> None:
        """Loads registered datasets from manifest.json if present."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for ds_data in data.get("datasets", []):
                        meta = ValidationDatasetMetadata.from_dict(ds_data)
                        self.datasets[meta.dataset_id] = meta
            except Exception as e:
                print(f"Warning: Could not parse manifest {self.manifest_path}: {e}")

    def save_manifest(self) -> None:
        """Saves current registry state to manifest.json."""
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "version": "3.8.1",
            "last_updated": Path(__file__).stat().st_mtime if Path(__file__).exists() else 0,
            "total_datasets": len(self.datasets),
            "datasets": [ds.to_dict() for ds in self.datasets.values()],
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

    def register_dataset(
        self,
        dataset_id: str,
        name: str,
        target_models: List[str],
        source_agency: str,
        geographic_scope: str,
        temporal_coverage: str,
        sample_size: int,
        provenance: str,
        file_path: str,
        description: str,
        lifecycle_state: str = DatasetLifecycleState.ACQUIRED.value,
        spatial_bounds: Optional[Dict[str, float]] = None,
        quality_notes: Optional[str] = None,
    ) -> ValidationDatasetMetadata:
        """Registers a new dataset with verified SHA-256 fingerprint."""
        abs_path = Path(file_path)
        if not abs_path.is_absolute():
            abs_path = PROJECT_ROOT / file_path

        sha256 = self.compute_sha256(abs_path)

        try:
            stored_path = str(abs_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            stored_path = str(abs_path).replace("\\", "/")

        meta = ValidationDatasetMetadata(
            dataset_id=dataset_id,
            name=name,
            target_models=target_models,
            source_agency=source_agency,
            geographic_scope=geographic_scope,
            temporal_coverage=temporal_coverage,
            sample_size=sample_size,
            provenance=provenance.upper(),
            lifecycle_state=lifecycle_state,
            sha256_hash=sha256,
            file_path=stored_path,
            description=description,
            created_at=Path(abs_path).stat().st_ctime if abs_path.exists() else "",
            quality_notes=quality_notes,
            spatial_bounds=spatial_bounds,
        )
        self.datasets[dataset_id] = meta
        self.save_manifest()
        return meta

    def transition_state(self, dataset_id: str, new_state: DatasetLifecycleState) -> ValidationDatasetMetadata:
        """Transitions dataset lifecycle state following strict transition rules."""
        if dataset_id not in self.datasets:
            raise KeyError(f"Dataset {dataset_id} not registered.")
        current_meta = self.datasets[dataset_id]
        current_state = DatasetLifecycleState(current_meta.lifecycle_state)

        if new_state not in ALLOWED_TRANSITIONS.get(current_state, set()):
            raise ValueError(
                f"Illegal lifecycle transition for {dataset_id}: "
                f"{current_state.value} -> {new_state.value}. "
                f"Allowed: {[s.value for s in ALLOWED_TRANSITIONS.get(current_state, set())]}"
            )

        current_meta.lifecycle_state = new_state.value
        self.save_manifest()
        return current_meta

    def verify_integrity(self, dataset_id: str) -> bool:
        """Verifies if the on-disk file matches registered SHA-256 hash."""
        if dataset_id not in self.datasets:
            raise KeyError(f"Dataset {dataset_id} not registered.")
        meta = self.datasets[dataset_id]
        p = Path(meta.file_path)
        abs_path = p if p.is_absolute() else PROJECT_ROOT / p
        current_sha = self.compute_sha256(abs_path)
        return current_sha == meta.sha256_hash

    def get_dataset(self, dataset_id: str) -> Optional[ValidationDatasetMetadata]:
        if dataset_id in self.datasets:
            return self.datasets[dataset_id]
        aliases = {
            "EXT_VAL_M6_BEAS_STABLE_SLOPES": "BENCHMARK_SYNTH_M6_SLOPES",
            "EXT_VAL_M7_HIMALAYAN_STORM_LANDSLIDES": "BENCHMARK_SYNTH_M7_STORMS",
            "EXT_VAL_M10_CWC_THALOUT_STAGE": "BENCHMARK_SYNTH_M10_CWC_STAGE",
            "EXT_VAL_M11_SATELLITE_FLOOD_DELINEATION": "BENCHMARK_PROXY_M11_SAR_EXTENTS",
            "EXT_VAL_M19_FLASH_FLOOD_PROPAGATION": "BENCHMARK_SYNTH_M19_PROPAGATION",
            "EXT_VAL_M20_POST_EVENT_DAMAGE_SURVEY": "BENCHMARK_SYNTH_M20_DAMAGE",
        }
        mapped = aliases.get(dataset_id)
        if mapped and mapped in self.datasets:
            return self.datasets[mapped]
        return None

    def list_datasets(
        self,
        target_model: Optional[str] = None,
        lifecycle_state: Optional[str] = None,
        provenance: Optional[str] = None,
    ) -> List[ValidationDatasetMetadata]:
        res = list(self.datasets.values())
        if target_model:
            m_upper = target_model.upper()
            res = [d for d in res if m_upper in [m.upper() for m in d.target_models]]
        if lifecycle_state:
            res = [d for d in res if d.lifecycle_state == lifecycle_state.upper()]
        if provenance:
            res = [d for d in res if d.provenance == provenance.upper()]
        return res


validation_registry = ValidationDatasetRegistry()
