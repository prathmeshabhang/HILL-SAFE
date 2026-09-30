"""
ml/landslide/m8_deformation
============================
Model M8: Ground Movement & Slope Deformation Forecast Engine.
"""

from ml.landslide.m8_deformation.features import (
    compute_kinematic_derivatives,
    extract_m8_features,
)
from ml.landslide.m8_deformation.infer import get_model, predict
from ml.landslide.m8_deformation.model import M8DeformationForecastModel
from ml.landslide.m8_deformation.schema import (
    DeformationHorizonForecast,
    ForecastHorizon,
    M8DeformationInput,
    M8PredictionOutput,
    MovementRegime,
)

__all__ = [
    "compute_kinematic_derivatives",
    "extract_m8_features",
    "get_model",
    "predict",
    "M8DeformationForecastModel",
    "DeformationHorizonForecast",
    "ForecastHorizon",
    "M8DeformationInput",
    "M8PredictionOutput",
    "MovementRegime",
]
