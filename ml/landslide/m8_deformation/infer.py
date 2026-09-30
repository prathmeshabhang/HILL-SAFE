"""
ml/landslide/m8_deformation/infer.py
====================================
Inference interface for Model M8 Ground Movement & Deformation Forecast.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from ml.landslide.m8_deformation.model import M8DeformationForecastModel

_default_model: Optional[M8DeformationForecastModel] = None


def get_model() -> M8DeformationForecastModel:
    global _default_model
    if _default_model is None:
        _default_model = M8DeformationForecastModel()
    return _default_model


def predict(
    features: Dict[str, Any],
    displacement_history: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Universal prediction endpoint for Model M8."""
    model = get_model()
    return model.predict(features, displacement_history)
