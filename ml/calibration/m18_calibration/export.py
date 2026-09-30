"""M18 — Export utilities."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Dict

from .model import M18CalibrationModel
from .train import ARTIFACT_PATH


def export_model(model: M18CalibrationModel) -> Dict[str, Any]:
    """Persist calibration model and return sha256 + artifact path."""
    with open(ARTIFACT_PATH, "wb") as f:
        pickle.dump(model, f)

    sha256 = hashlib.sha256(ARTIFACT_PATH.read_bytes()).hexdigest()
    return {
        "artifact_path": str(ARTIFACT_PATH),
        "sha256": sha256,
        "model_version": model.MODEL_VERSION,
        "best_method": model._best_method,
        "n_train": model._n_train,
    }


def load_model() -> M18CalibrationModel:
    """Load calibration model from artifact."""
    with open(ARTIFACT_PATH, "rb") as f:
        return pickle.load(f)
