"""
ml/rainfall/m1_nowcast
======================
Model M1: Multi-Horizon Extreme Rainfall Nowcasting and Cloudburst Detection.
"""

from ml.rainfall.m1_nowcast.features import extract_features_from_history
from ml.rainfall.m1_nowcast.infer import get_model, predict
from ml.rainfall.m1_nowcast.model import M1RainfallNowcastModel
from ml.rainfall.m1_nowcast.schema import (
    CloudburstRiskLevel,
    HorizonForecast,
    M1InputFeatures,
    M1PredictionOutput,
    NowcastHorizon,
)

__all__ = [
    "extract_features_from_history",
    "get_model",
    "predict",
    "M1RainfallNowcastModel",
    "CloudburstRiskLevel",
    "HorizonForecast",
    "M1InputFeatures",
    "M1PredictionOutput",
    "NowcastHorizon",
]
