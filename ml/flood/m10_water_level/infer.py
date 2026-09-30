"""
ml/flood/m10_water_level/infer.py
=================================
Inference interface for Model M10 River Water-Level Forecast.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from ml.flood.m10_water_level.model import M10WaterLevelForecastModel

_default_model: Optional[M10WaterLevelForecastModel] = None


def get_model() -> M10WaterLevelForecastModel:
    global _default_model
    if _default_model is None:
        _default_model = M10WaterLevelForecastModel()
    return _default_model


def predict(
    features: Dict[str, Any],
    stage_history_m: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Universal prediction endpoint for Model M10."""
    model = get_model()
    return model.predict(features, stage_history_m)
