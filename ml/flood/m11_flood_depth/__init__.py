"""
ml/flood/m11_flood_depth
========================
Model M11: Flood Propagation & Inundation Depth Forecast Engine.
"""

from ml.flood.m11_flood_depth.features import (
    BEAS_RIVER_REACHES,
    compute_wave_celerity_and_attenuation,
    extract_m11_features,
)
from ml.flood.m11_flood_depth.infer import get_model, predict
from ml.flood.m11_flood_depth.model import M11FloodPropagationModel
from ml.flood.m11_flood_depth.schema import (
    InundationSeverity,
    M11FloodDepthInput,
    M11PredictionOutput,
    ReachInundationForecast,
)

__all__ = [
    "BEAS_RIVER_REACHES",
    "compute_wave_celerity_and_attenuation",
    "extract_m11_features",
    "get_model",
    "predict",
    "M11FloodPropagationModel",
    "InundationSeverity",
    "M11FloodDepthInput",
    "M11PredictionOutput",
    "ReachInundationForecast",
]
