"""
ml/decision/m14_infrastructure_loss/__init__.py
===============================================
Model M14: Infrastructure Damage & Loss Estimation Engine.
"""

from ml.decision.m14_infrastructure_loss.assets import (
    BEAS_INFRASTRUCTURE_ASSETS,
    InfrastructureAsset,
    get_asset_or_default,
)
from ml.decision.m14_infrastructure_loss.features import (
    extract_damage_features,
)
from ml.decision.m14_infrastructure_loss.infer import (
    assess_corridor_infrastructure,
    get_m14_model,
    predict_infrastructure_loss,
)
from ml.decision.m14_infrastructure_loss.model import M14InfrastructureLossModel
from ml.decision.m14_infrastructure_loss.schema import (
    AssetCategory,
    DamageState,
    LifelineStatus,
    M14DamageInput,
    M14PredictionOutput,
)
from ml.decision.m14_infrastructure_loss.validation import validate_m14_prediction
from ml.decision.m14_infrastructure_loss.vulnerability_curves import (
    compute_bridge_damage,
    compute_hospital_damage,
    compute_orchard_damage,
    compute_road_damage,
    compute_substation_damage,
    compute_water_intake_damage,
    evaluate_asset_damage,
)

__all__ = [
    "BEAS_INFRASTRUCTURE_ASSETS",
    "InfrastructureAsset",
    "get_asset_or_default",
    "extract_damage_features",
    "M14InfrastructureLossModel",
    "get_m14_model",
    "predict_infrastructure_loss",
    "assess_corridor_infrastructure",
    "AssetCategory",
    "DamageState",
    "LifelineStatus",
    "M14DamageInput",
    "M14PredictionOutput",
    "validate_m14_prediction",
    "compute_bridge_damage",
    "compute_road_damage",
    "compute_substation_damage",
    "compute_hospital_damage",
    "compute_water_intake_damage",
    "compute_orchard_damage",
    "evaluate_asset_damage",
]
