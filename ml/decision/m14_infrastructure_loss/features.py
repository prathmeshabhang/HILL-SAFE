"""
ml/decision/m14_infrastructure_loss/features.py
===============================================
Feature extraction and hydrodynamic indicators for Model M14.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Tuple
import numpy as np

from ml.decision.m14_infrastructure_loss.assets import get_asset_or_default
from ml.decision.m14_infrastructure_loss.schema import AssetCategory, InfrastructureAsset, M14DamageInput


FEATURE_NAMES = [
    "flood_depth_m",
    "flow_velocity_ms",
    "hydrodynamic_pressure_kpa",
    "debris_impact_flag",
    "inundation_duration_hours",
    "soffit_or_deck_height_m",
    "overtopping_depth_m",
    "log_replacement_value",
    "criticality_tier",
    "is_transportation",
    "is_lifeline_power_water",
    "is_hospital",
]


CATEGORY_MAP = {
    AssetCategory.TRANSPORTATION_ROAD: 1,
    AssetCategory.TRANSPORTATION_BRIDGE: 2,
    AssetCategory.POWER_SUBSTATION: 3,
    AssetCategory.HEALTHCARE_HOSPITAL: 4,
    AssetCategory.WATER_INTAKE: 5,
    AssetCategory.AGRICULTURE_ORCHARD: 6,
}


def extract_damage_features(
    input_data: M14DamageInput,
    asset: InfrastructureAsset | None = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Extracts 12-element feature vector and metadata.
    """
    if asset is None:
        if input_data.custom_asset is not None:
            asset = input_data.custom_asset
        else:
            asset = get_asset_or_default(input_data.asset_id)

    depth = max(0.0, input_data.flood_depth_m)
    v = max(0.0, input_data.flow_velocity_ms)
    debris = 1.0 if input_data.debris_impact_flag else 0.0
    duration = max(0.1, input_data.inundation_duration_hours)

    # Hydrodynamic stagnation pressure: P_dyn = 0.5 * rho * v^2 in kPa (rho = 1000 kg/m^3 for clear water, ~1200 with sediment)
    hydro_pressure = 0.5 * 1.15 * (v ** 2) / 10.0  # Approx kPa

    overtopping = max(0.0, depth - asset.soffit_or_deck_height_m)
    log_val = math.log10(max(1.0, asset.replacement_value_lakhs_inr))

    is_trans = 1.0 if asset.category in [AssetCategory.TRANSPORTATION_ROAD, AssetCategory.TRANSPORTATION_BRIDGE] else 0.0
    is_power_water = 1.0 if asset.category in [AssetCategory.POWER_SUBSTATION, AssetCategory.WATER_INTAKE] else 0.0
    is_hosp = 1.0 if asset.category == AssetCategory.HEALTHCARE_HOSPITAL else 0.0

    feat_vector = np.array([
        depth,
        v,
        hydro_pressure,
        debris,
        duration,
        asset.soffit_or_deck_height_m,
        overtopping,
        log_val,
        float(asset.criticality_tier),
        is_trans,
        is_power_water,
        is_hosp,
    ], dtype=np.float32)

    meta = {
        "asset_id": asset.asset_id,
        "name": asset.name,
        "category": asset.category,
        "replacement_value_lakhs_inr": asset.replacement_value_lakhs_inr,
        "criticality_tier": asset.criticality_tier,
        "overtopping_depth_m": overtopping,
    }

    return feat_vector, meta
