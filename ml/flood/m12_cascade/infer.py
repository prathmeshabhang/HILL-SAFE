"""
ml/flood/m12_cascade/infer.py
=============================
Inference interface for Model M12 Hazard Cascade Prediction.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ml.flood.m12_cascade.model import M12HazardCascadeModel

_default_model: Optional[M12HazardCascadeModel] = None


def get_model() -> M12HazardCascadeModel:
    global _default_model
    if _default_model is None:
        _default_model = M12HazardCascadeModel()
    return _default_model


def predict(features: Dict[str, Any]) -> Dict[str, Any]:
    """Universal prediction endpoint for Model M12."""
    model = get_model()
    return model.predict(features)
