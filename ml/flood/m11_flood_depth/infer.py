"""
ml/flood/m11_flood_depth/infer.py
=================================
Inference interface for Model M11 Flood Propagation & Depth Forecast.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ml.flood.m11_flood_depth.model import M11FloodPropagationModel

_default_model: Optional[M11FloodPropagationModel] = None


def get_model() -> M11FloodPropagationModel:
    global _default_model
    if _default_model is None:
        _default_model = M11FloodPropagationModel()
    return _default_model


def predict(features: Dict[str, Any]) -> Dict[str, Any]:
    """Universal prediction endpoint for Model M11."""
    model = get_model()
    return model.predict(features)
