"""
ml/flood/m10_water_level/model.py
=================================
Model M10 Architecture: Multi-Horizon River Water-Level & Stage Forecast Engine.
Combines Kinematic Rate-of-Rise Extrapolation with Catchment Rainfall-Runoff GBDT Regressors.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import joblib
import numpy as np

from ml.flood.m10_water_level.features import extract_m10_features
from ml.flood.m10_water_level.preprocessing import M10Preprocessor
from ml.flood.m10_water_level.schema import (
    M10PredictionOutput,
    StageAlertLevel,
    StageHorizonForecast,
    WaterLevelHorizon,
)
from ml.flood.m10_water_level.uncertainty import compute_stage_uncertainty_interval

MODEL_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = MODEL_DIR / "m10_water_level_gbdt.joblib"

HORIZON_HOURS = {
    "30m": 0.5,
    "1h": 1.0,
    "3h": 3.0,
    "6h": 6.0,
}


class M10WaterLevelForecastModel:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.preprocessor = M10Preprocessor()
        self.models_by_horizon: Dict[str, Any] = {}
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        if self.model_path.exists():
            try:
                bundle = joblib.load(self.model_path)
                self.models_by_horizon = bundle.get("models_by_horizon", {})
            except Exception as e:
                print(f"[M10Model] Warning loading model: {e}")

    def predict_kinematic_persistence(
        self,
        current_stage_m: float,
        rate_of_rise_m_hr: float,
        horizon_hours: float,
        effective_runoff_index: float,
    ) -> float:
        """
        Physical baseline combining current stage momentum with catchment runoff delay:
        h(t) = h0 + (rate * t * exp(-t / 4.0)) + runoff_boost
        """
        t = horizon_hours
        decay = math.exp(-t / 4.0)
        momentum_delta = rate_of_rise_m_hr * t * decay
        # Catchment runoff reaches peak stage after lag time (typically 1-3 hrs in Upper Beas)
        runoff_surge = 0.015 * effective_runoff_index * math.sqrt(t)
        return float(max(0.0, current_stage_m + momentum_delta + runoff_surge))

    def evaluate_alert_level(
        self,
        stage_m: float,
        warn_m: float,
        danger_m: float,
        hfl_m: float,
    ) -> StageAlertLevel:
        """Categorizes river stage into authoritative CWC alert tiers."""
        if stage_m >= hfl_m:
            return StageAlertLevel.HIGH_FLOOD_LEVEL
        if stage_m >= danger_m:
            return StageAlertLevel.DANGER_LEVEL
        if stage_m >= warn_m:
            return StageAlertLevel.WARNING_LEVEL
        return StageAlertLevel.NORMAL_FLOW

    def compute_danger_exceedance_probability(
        self,
        forecasted_stage_m: float,
        danger_level_m: float,
        uncertainty_upper_m: float,
    ) -> float:
        """Calculates probability of exceeding danger level under forecast uncertainty."""
        if forecasted_stage_m >= danger_level_m:
            margin = forecasted_stage_m - danger_level_m
            return float(np.clip(0.75 + (margin * 0.15), 0.75, 0.99))
        diff = danger_level_m - forecasted_stage_m
        sigma = max(0.1, (uncertainty_upper_m - forecasted_stage_m) / 1.28)
        z = -diff / sigma
        # Approx standard normal CDF
        prob = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        return float(np.clip(prob, 0.01, 0.70))

    def predict(
        self,
        features: Dict[str, Any],
        stage_history_m: Optional[Sequence[float]] = None,
    ) -> Dict[str, Any]:
        """
        Universal FLOODY SHIELD prediction interface for Model M10.
        """
        raw_feat = extract_m10_features(features, stage_history_m)
        clean_feat, dq_score, status_str, flags = self.preprocessor.process_and_audit(
            raw_feat,
            station_id=str(features.get("station_id", "STATION_01")),
        )

        h0 = clean_feat.get("current_stage_m", 3.0)
        rate = clean_feat.get("rate_of_rise_m_hr", 0.0)
        runoff = clean_feat.get("effective_runoff_index", 0.0)
        warn_lvl = clean_feat.get("warning_level_m", 5.0)
        danger_lvl = clean_feat.get("danger_level_m", 7.0)
        hfl = clean_feat.get("hfl_m", 9.5)

        forecasts: List[StageHorizonForecast] = []

        for h, hours in HORIZON_HOURS.items():
            if h in self.models_by_horizon and self.models_by_horizon[h] is not None:
                estimator = self.models_by_horizon[h]
                vec = np.array([[
                    clean_feat["current_stage_m"],
                    clean_feat["rate_of_rise_m_hr"],
                    clean_feat["rainfall_1h_mm"],
                    clean_feat["rainfall_3h_mm"],
                    clean_feat["rainfall_6h_mm"],
                    clean_feat["soil_moisture_pct"],
                    clean_feat["effective_runoff_index"],
                ]])
                pred_delta = float(estimator.predict(vec)[0])
                pred_stage = float(max(0.0, h0 + pred_delta))
            else:
                pred_stage = self.predict_kinematic_persistence(h0, rate, hours, runoff)
                pred_delta = pred_stage - h0

            unc_lower, unc_upper = compute_stage_uncertainty_interval(
                predicted_stage_m=pred_stage,
                horizon_hours=hours,
                data_quality=dq_score,
            )

            alert = self.evaluate_alert_level(pred_stage, warn_lvl, danger_lvl, hfl)
            p_danger = self.compute_danger_exceedance_probability(pred_stage, danger_lvl, unc_upper)

            forecasts.append(StageHorizonForecast(
                horizon=h,
                forecasted_stage_m=pred_stage,
                stage_delta_m=pred_delta,
                exceedance_prob_danger=p_danger,
                uncertainty_lower_m=unc_lower,
                uncertainty_upper_m=unc_upper,
                alert_level=alert,
            ))

        primary = forecasts[1]  # 1h primary operational horizon
        confidence = float(np.clip(dq_score * (1.0 - abs(primary.stage_delta_m) * 0.05), 0.5, 0.98))

        out = M10PredictionOutput(
            primary_horizon="1h",
            forecasted_stage_m=primary.forecasted_stage_m,
            stage_delta_m=primary.stage_delta_m,
            alert_level=primary.alert_level,
            exceedance_prob_danger=primary.exceedance_prob_danger,
            horizon_forecasts=forecasts,
            confidence=confidence,
            uncertainty={
                "interval_1h_m": [primary.uncertainty_lower_m, primary.uncertainty_upper_m],
                "confidence_level": 0.80,
                "method": "diffusive_flood_routing_bounds",
            },
            data_quality=dq_score,
            model_version="M10-waterlevel-v1.0",
            applicability="UPPER_BEAS_AOI",
            provenance="CWC_AWS_TELEMETRY + HYDROLOGICAL_GBDT",
        )
        return out.to_dict()
