"""
ml/flood/m10_water_level
========================
Model M10: River Water-Level & Stage Forecast Engine.
"""

from ml.flood.m10_water_level.features import (
    compute_stage_rate_of_rise,
    extract_m10_features,
)
from ml.flood.m10_water_level.infer import get_model, predict
from ml.flood.m10_water_level.model import M10WaterLevelForecastModel
from ml.flood.m10_water_level.schema import (
    M10PredictionOutput,
    M10WaterLevelInput,
    StageAlertLevel,
    StageHorizonForecast,
    WaterLevelHorizon,
)

__all__ = [
    "compute_stage_rate_of_rise",
    "extract_m10_features",
    "get_model",
    "predict",
    "M10WaterLevelForecastModel",
    "M10PredictionOutput",
    "M10WaterLevelInput",
    "StageAlertLevel",
    "StageHorizonForecast",
    "WaterLevelHorizon",
]
