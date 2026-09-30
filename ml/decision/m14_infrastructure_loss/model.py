"""
ml/decision/m14_infrastructure_loss/model.py
============================================
Model M14: Infrastructure Damage & Loss Estimation Engine.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from ml.decision.m14_infrastructure_loss.assets import get_asset_or_default
from ml.decision.m14_infrastructure_loss.features import (
    FEATURE_NAMES,
    extract_damage_features,
)
from ml.decision.m14_infrastructure_loss.schema import (
    DamageState,
    InfrastructureAsset,
    LifelineStatus,
    M14DamageInput,
    M14PredictionOutput,
)
from ml.decision.m14_infrastructure_loss.vulnerability_curves import evaluate_asset_damage


MODEL_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "m14_infrastructure_gbdt.joblib")


class M14InfrastructureLossModel:
    """
    Predicts physical structural damage, direct economic losses (INR Lakhs),
    and functional lifeline disruption across Upper Beas infrastructure assets.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_ARTIFACT_PATH
        self.model: Optional[GradientBoostingRegressor] = None
        self.version = "1.0.0"
        self._load_or_initialize()

    def _load_or_initialize(self) -> None:
        if os.path.exists(self.model_path):
            try:
                loaded = joblib.load(self.model_path)
                if isinstance(loaded, dict) and "model" in loaded:
                    self.model = loaded["model"]
                    self.version = loaded.get("version", "1.0.0")
                else:
                    self.model = loaded
            except Exception:
                self.model = None

    def predict(self, input_data: M14DamageInput) -> M14PredictionOutput:
        """
        Executes damage and economic loss estimation satisfying the universal contract.
        """
        asset = input_data.custom_asset or get_asset_or_default(input_data.asset_id)
        feat_vec, meta = extract_damage_features(input_data, asset=asset)

        # Baseline analytical / curve-based damage evaluation
        (
            curve_d_ratio,
            curve_state,
            curve_status,
            curve_outage,
            curve_rationale,
        ) = evaluate_asset_damage(
            asset=asset,
            flood_depth_m=input_data.flood_depth_m,
            flow_velocity_ms=input_data.flow_velocity_ms,
            debris_flag=input_data.debris_impact_flag,
            duration_hours=input_data.inundation_duration_hours,
        )

        if self.model is not None:
            try:
                ml_d_ratio = float(self.model.predict(feat_vec.reshape(1, -1))[0])
                # Fuse 70% ML prediction + 30% deterministic hydrodynamic curve
                d_ratio = float(np.clip(0.70 * ml_d_ratio + 0.30 * curve_d_ratio, 0.0, 1.0))
            except Exception:
                d_ratio = curve_d_ratio
        else:
            d_ratio = curve_d_ratio

        # Determine refined damage state from final d_ratio
        if d_ratio < 0.05:
            state = DamageState.NEGLIGIBLE_INTACT
            status = LifelineStatus.OPERATIONAL
            outage_hours = 0.0
            rationale = "Superficial or zero water impact; infrastructure remains fully operational."
        elif d_ratio < 0.25:
            state = DamageState.SLIGHT_DAMAGE
            status = LifelineStatus.PARTIALLY_DEGRADED
            outage_hours = round(float(input_data.inundation_duration_hours + 4.0), 1)
            rationale = "Minor flooding / light debris; precautionary slowdown or short-term maintenance."
        elif d_ratio < 0.50:
            state = DamageState.MODERATE_DAMAGE
            status = LifelineStatus.IMPASSABLE_CUT_OFF
            outage_hours = round(float(24.0 + 48.0 * d_ratio), 1)
            rationale = "Substantial inundation; roadway/bridge approach compromised; closed for repairs."
        elif d_ratio < 0.80:
            state = DamageState.EXTENSIVE_DAMAGE
            status = LifelineStatus.STRUCTURALLY_FAILED
            outage_hours = round(float(72.0 + 120.0 * d_ratio), 1)
            rationale = "Severe structural damage; deck or sub-base sheared; requires major reconstruction."
        else:
            state = DamageState.COLLAPSED_DESTROYED
            status = LifelineStatus.STRUCTURALLY_FAILED
            outage_hours = 360.0
            rationale = "TOTAL LOSS / WASHOUT: Structural collapse; emergency replacement needed."

        direct_loss_lakhs = round(float(asset.replacement_value_lakhs_inr * d_ratio), 2)

        # Lifeline Criticality Score (0.0 to 1.0)
        # Higher for tier 1 assets (hospitals, arterial NH-3) under severe failure
        tier_weight = (4.0 - float(asset.criticality_tier)) / 3.0
        val_norm = min(1.0, np.log10(max(10.0, asset.replacement_value_lakhs_inr)) / 4.0)
        criticality_score = float(np.clip(d_ratio * (0.60 * tier_weight + 0.40 * val_norm), 0.0, 1.0))

        # Uncertainty intervals
        loss_lower = round(max(0.0, direct_loss_lakhs * 0.80), 2)
        loss_upper = round(min(asset.replacement_value_lakhs_inr, direct_loss_lakhs * 1.25), 2)
        d_lower = round(max(0.0, d_ratio - 0.05), 4)
        d_upper = round(min(1.0, d_ratio + 0.05), 4)

        uncertainty_dict = {
            "loss_lakhs_80ci": [loss_lower, loss_upper],
            "damage_ratio_80ci": [d_lower, d_upper],
            "loss_confidence_interval_pct": 22.0,
        }

        dq = 0.95 if input_data.custom_asset is not None else 0.93

        return M14PredictionOutput(
            asset_id=asset.asset_id,
            asset_name=asset.name,
            category=asset.category,
            damage_state=state,
            structural_damage_ratio=round(d_ratio, 4),
            estimated_direct_loss_lakhs_inr=direct_loss_lakhs,
            service_outage_hours=outage_hours,
            lifeline_status=status,
            lifeline_criticality_score=round(criticality_score, 3),
            damage_rationale=rationale,
            confidence=0.88,
            uncertainty=uncertainty_dict,
            data_quality=dq,
            model_version=self.version,
            applicability="UPPER_BEAS_KULLU_MANALI_CORRIDOR",
            provenance="NDMA_FLASH_FLOOD_GUIDELINES + USACE_DEPTH_DAMAGE_TABLES + BEAS_INFRA_INVENTORY",
        )

    def predict_batch(self, inputs: List[M14DamageInput]) -> List[M14PredictionOutput]:
        return [self.predict(inp) for inp in inputs]
