"""
ml/decision/m14_infrastructure_loss/infer.py
============================================
Inference utilities and corridor-wide assessment for Model M14.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from ml.decision.m14_infrastructure_loss.assets import BEAS_INFRASTRUCTURE_ASSETS
from ml.decision.m14_infrastructure_loss.model import M14InfrastructureLossModel
from ml.decision.m14_infrastructure_loss.schema import M14DamageInput, M14PredictionOutput


_GLOBAL_MODEL: Optional[M14InfrastructureLossModel] = None


def get_m14_model() -> M14InfrastructureLossModel:
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is None:
        _GLOBAL_MODEL = M14InfrastructureLossModel()
    return _GLOBAL_MODEL


def predict_infrastructure_loss(input_data: M14DamageInput) -> M14PredictionOutput:
    """Predicts structural damage, economic loss, and downtime for a single asset."""
    return get_m14_model().predict(input_data)


def assess_corridor_infrastructure(
    hazard_map: Dict[str, Dict[str, Any]],
) -> List[M14PredictionOutput]:
    """
    Evaluates loss across all registered Upper Beas infrastructure assets.
    hazard_map format: {asset_id: {"flood_depth_m": float, "flow_velocity_ms": float, ...}}
    """
    model = get_m14_model()
    results: List[M14PredictionOutput] = []

    for asset_id in BEAS_INFRASTRUCTURE_ASSETS.keys():
        h = hazard_map.get(asset_id, {})
        inp = M14DamageInput(
            asset_id=asset_id,
            flood_depth_m=h.get("flood_depth_m", 0.0),
            flow_velocity_ms=h.get("flow_velocity_ms", 0.0),
            debris_impact_flag=h.get("debris_impact_flag", False),
            inundation_duration_hours=h.get("inundation_duration_hours", 2.0),
        )
        results.append(model.predict(inp))

    # Sort descending by economic loss (highest monetary impact first)
    results.sort(key=lambda r: -r.estimated_direct_loss_lakhs_inr)
    return results
