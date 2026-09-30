"""
backend/app/inference/registry.py
=================================
Centralized Model Registry Service for FLOODY SHIELD.
Validates SHA-256 hashes for frozen models and exposes metadata for all models.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.errors import ModelInferenceError
from backend.app.core.logging import get_logger

logger = get_logger("floody.inference.registry")

# Verified SHA-256 hashes for frozen model artifacts (M2, M4, M6, M7)
FROZEN_ARTIFACT_HASHES = {
    "M2": (
        "ml/flood/m2_upper_beas_flood_model.joblib",
        "a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b",
    ),
    "M4": (
        "data/satellite_output/flood_multimodal_unet.pt",
        "45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07",
    ),
    "M6": (
        "ml/landslide/m6_beas_susceptibility_rf.joblib",
        "e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c",
    ),
    "M7": (
        "ml/landslide/m7_beas_trigger_lgbm.joblib",
        "f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a",
    ),
}


class ModelRegistryService:
    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or settings.MODEL_REGISTRY_PATH
        self.registry_data: Dict[str, Any] = {}
        self.load_registry()
        self.verify_frozen_artifacts()

    def load_registry(self) -> None:
        """Loads the authoritative model registry from JSON."""
        if self.registry_file.exists():
            try:
                self.registry_data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                logger.info(f"Loaded {len(self.registry_data)} models from {self.registry_file}")
            except Exception as exc:
                logger.error(f"Failed loading model registry: {exc}")
                self.registry_data = {}
        else:
            logger.warning(f"Model registry file not found: {self.registry_file}")
            self.registry_data = {}

    def verify_frozen_artifacts(self) -> None:
        """
        Cryptographic verification: Computes SHA-256 for frozen model artifacts
        and asserts identity against immutable baseline.
        """
        repo_root = settings.REPO_ROOT
        for model_id, (rel_path, expected_hash) in FROZEN_ARTIFACT_HASHES.items():
            artifact_path = repo_root / rel_path
            if not artifact_path.exists():
                logger.warning(f"Frozen artifact for {model_id} not found on disk at {artifact_path}")
                continue

            content = artifact_path.read_bytes()
            actual_hash = hashlib.sha256(content).hexdigest()
            if actual_hash != expected_hash:
                err_msg = (
                    f"CRITICAL: Cryptographic integrity violation for frozen model {model_id}! "
                    f"Expected {expected_hash}, computed {actual_hash}."
                )
                logger.critical(err_msg)
                raise ModelInferenceError(message=err_msg, model_id=model_id)
            logger.info(f"Verified frozen artifact integrity: {model_id} ({actual_hash[:10]}...)")

    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Returns registered model metadata, metrics, and limitations."""
        return self.registry_data.get(model_id)

    def list_registered_models(self) -> Dict[str, Any]:
        """Returns all registered models with their current status and version."""
        return {
            mid: {
                "name": data.get("model_name"),
                "version": data.get("version"),
                "status": data.get("status"),
                "metrics": data.get("metrics"),
            }
            for mid, data in self.registry_data.items()
        }


model_registry_service = ModelRegistryService()
