"""
ml/landslide/m8_deformation/model.py
====================================
Model M8 Architecture: Ground Movement & Slope Deformation Forecast Engine.
Integrates Kinematic Creep Extrapolation, Saito Inverse Velocity, and Multi-Horizon GBDT Regressors.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import joblib
import numpy as np

from ml.landslide.m8_deformation.features import extract_m8_features
from ml.landslide.m8_deformation.preprocessing import M8Preprocessor
from ml.landslide.m8_deformation.schema import (
    DeformationHorizonForecast,
    ForecastHorizon,
    M8PredictionOutput,
    MovementRegime,
)
from ml.landslide.m8_deformation.uncertainty import compute_deformation_uncertainty_interval

MODEL_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = MODEL_DIR / "m8_deformation_gbdt.joblib"

HORIZON_DAYS = {
    "24h": 1.0,
    "72h": 3.0,
    "7d": 7.0,
}


class M8DeformationForecastModel:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.preprocessor = M8Preprocessor()
        self.models_by_horizon: Dict[str, Any] = {}
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        if self.model_path.exists():
            try:
                bundle = joblib.load(self.model_path)
                self.models_by_horizon = bundle.get("models_by_horizon", {})
            except Exception as e:
                print(f"[M8Model] Warning loading model: {e}")

    def compute_saito_time_to_failure(self, velocity_mm_day: float, acceleration_mm_day2: float) -> Optional[float]:
        """
        Saito (1969) / Fukuzono (1985) inverse velocity asymptotic failure estimation.
        When a creeping slope enters tertiary acceleration (v > 5 mm/day and a > 0.5 mm/day^2),
        the rate of change of inverse velocity d(1/v)/dt predicts the time to collapse (1/v -> 0).
        Returns estimated hours to failure, or None if in primary/secondary steady state.
        """
        if velocity_mm_day < 5.0 or acceleration_mm_day2 <= 0.2:
            return None

        # d(1/v)/dt = - (1 / v^2) * dv/dt = - a / (v^2)
        rate_inv_v = acceleration_mm_day2 / (velocity_mm_day ** 2)
        if rate_inv_v <= 1e-6:
            return None

        # Remaining time to failure in days: t_f = (1 / v) / (a / v^2) = v / a
        days_to_failure = velocity_mm_day / acceleration_mm_day2
        hours_to_failure = float(days_to_failure * 24.0)
        return float(min(720.0, max(1.0, hours_to_failure)))

    def classify_regime(
        self,
        velocity_mm_day: float,
        acceleration_mm_day2: float,
        ttf_hours: Optional[float],
    ) -> MovementRegime:
        """Categorizes current slope kinematic regime."""
        if ttf_hours is not None and ttf_hours <= 72.0:
            return MovementRegime.CRITICAL_FAILURE_IMMINENT
        if velocity_mm_day >= 15.0 and acceleration_mm_day2 >= 1.5:
            return MovementRegime.CRITICAL_FAILURE_IMMINENT
        if velocity_mm_day >= 5.0 or acceleration_mm_day2 >= 0.5:
            return MovementRegime.ACCELERATING
        if velocity_mm_day >= 1.0:
            return MovementRegime.LINEAR_CREEP
        return MovementRegime.STABLE

    def predict_kinematic_increment(
        self,
        v0: float,
        a0: float,
        horizon_days: float,
        hydro_driving: float,
    ) -> float:
        """
        Physics-informed kinematic baseline:
        d = v0 * t + 0.5 * a * t^2 + hydro_boost
        With realistic sub-linear deceleration damping unless rain continues to drive acceleration.
        """
        t = horizon_days
        # Rainfall driving adds transient acceleration
        effective_a = a0 + (hydro_driving * 0.005)
        # Damping prevents runaway explosion over 7 days
        damping = math.exp(-0.08 * t)
        disp = (v0 * t) + (0.5 * effective_a * (t ** 1.8) * damping)
        return float(max(0.0, disp))

    def predict(
        self,
        features: Dict[str, Any],
        displacement_history: Optional[Sequence[float]] = None,
    ) -> Dict[str, Any]:
        """
        Universal FLOODY SHIELD prediction interface for Model M8.
        """
        raw_feat = extract_m8_features(features, displacement_history)
        clean_feat, dq_score, status_str, flags = self.preprocessor.process_and_audit(
            raw_feat,
            pixel_id=str(features.get("sensor_or_pixel_id", "PX_01")),
        )

        v = clean_feat.get("velocity_mm_day", 0.0)
        a = clean_feat.get("acceleration_mm_day2", 0.0)
        cum_disp = clean_feat.get("cumulative_displacement_mm", 0.0)
        hydro = clean_feat.get("hydro_driving_index", 0.0)
        coherence = clean_feat.get("insar_coherence", 0.85)

        ttf_hours = self.compute_saito_time_to_failure(v, a)
        regime = self.classify_regime(v, a, ttf_hours)

        forecasts: List[DeformationHorizonForecast] = []

        for h, days in HORIZON_DAYS.items():
            if h in self.models_by_horizon and self.models_by_horizon[h] is not None:
                estimator = self.models_by_horizon[h]
                vec = np.array([[
                    clean_feat["velocity_mm_day"],
                    clean_feat["acceleration_mm_day2"],
                    clean_feat["cumulative_displacement_mm"],
                    clean_feat["rainfall_72h_mm"],
                    clean_feat["slope_deg"],
                    clean_feat["hydro_driving_index"],
                    clean_feat["insar_coherence"],
                ]])
                pred_inc = float(max(0.0, estimator.predict(vec)[0]))
            else:
                pred_inc = self.predict_kinematic_increment(v, a, days, hydro)

            unc_lower, unc_upper = compute_deformation_uncertainty_interval(
                predicted_increment_mm=pred_inc,
                horizon_days=days,
                insar_coherence=coherence,
            )

            # Regime projection over horizon
            if pred_inc / days >= 15.0:
                h_regime = MovementRegime.CRITICAL_FAILURE_IMMINENT
            elif pred_inc / days >= 5.0:
                h_regime = MovementRegime.ACCELERATING
            elif pred_inc / days >= 1.0:
                h_regime = MovementRegime.LINEAR_CREEP
            else:
                h_regime = MovementRegime.STABLE

            forecasts.append(DeformationHorizonForecast(
                horizon=h,
                predicted_displacement_increment_mm=pred_inc,
                cumulative_projected_displacement_mm=cum_disp + pred_inc,
                uncertainty_lower_mm=unc_lower,
                uncertainty_upper_mm=unc_upper,
                regime=h_regime,
            ))

        # Overall confidence reflects data quality, InSAR coherence, and regime stability
        conf = float(np.clip(dq_score * coherence * (0.95 if regime == MovementRegime.STABLE else 0.82), 0.4, 0.98))

        out = M8PredictionOutput(
            current_velocity_mm_day=v,
            acceleration_mm_day2=a,
            movement_regime=regime,
            time_to_failure_est_hours=ttf_hours,
            horizon_forecasts=forecasts,
            confidence=conf,
            uncertainty={
                "method": "insar_phase_conformal_quantiles",
                "coherence_weight": round(coherence, 3),
                "primary_24h_interval_mm": [forecasts[0].uncertainty_lower_mm, forecasts[0].uncertainty_upper_mm],
            },
            data_quality=dq_score,
            model_version="M8-deformation-v1.0",
            applicability="UPPER_BEAS_AOI",
            provenance="INSAR_GNSS_TELEMETRY + KINEMATIC_SAITO_GBDT",
        )
        return out.to_dict()
