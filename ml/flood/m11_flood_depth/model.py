"""
ml/flood/m11_flood_depth/model.py
=================================
Model M11 Architecture: Flood Propagation & Inundation Depth Forecast Engine.
Combines Muskingum-Cunge Kinematic Wave Routing with Copernicus DEM HAND Hydraulics.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import joblib
import numpy as np

from ml.flood.m11_flood_depth.features import (
    BEAS_RIVER_REACHES,
    compute_wave_celerity_and_attenuation,
    extract_m11_features,
)
from ml.flood.m11_flood_depth.preprocessing import M11Preprocessor
from ml.flood.m11_flood_depth.schema import (
    InundationSeverity,
    M11PredictionOutput,
    ReachInundationForecast,
)
from ml.flood.m11_flood_depth.uncertainty import compute_depth_uncertainty_interval

MODEL_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = MODEL_DIR / "m11_depth_gbdt.joblib"


class M11FloodPropagationModel:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.preprocessor = M11Preprocessor()
        self.gbdt_model: Optional[Any] = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        if self.model_path.exists():
            try:
                bundle = joblib.load(self.model_path)
                self.gbdt_model = bundle.get("model")
            except Exception as e:
                print(f"[M11Model] Warning loading model: {e}")

    def route_flood_wave_along_basin(
        self,
        upstream_stage_m: float,
        upstream_discharge_m3s: float,
    ) -> List[ReachInundationForecast]:
        """
        Routes the flood hydrograph downstream from Palchan to Pandoh Dam.
        """
        forecasts: List[ReachInundationForecast] = []
        curr_q = max(20.0, upstream_discharge_m3s)
        cum_dist_km = 0.0
        cum_travel_time_sec = 0.0

        for reach_id, props in BEAS_RIVER_REACHES.items():
            length_km = props["length_km"]
            slope = props["slope"]
            manning = props["manning_n"]
            width = props["top_width_m"]
            bankfull = props["bankfull_stage_m"]
            fp_area = props["floodplain_area_sqkm"]

            # Compute wave celerity
            hyd = compute_wave_celerity_and_attenuation(curr_q, slope, manning, width)
            celerity = hyd["celerity_mps"]
            reach_travel_time_sec = (length_km * 1000.0) / celerity
            cum_travel_time_sec += reach_travel_time_sec
            cum_dist_km += length_km

            # Peak attenuation: channel storage diffuses peak by ~0.5% per km
            curr_q = curr_q * math.exp(-0.005 * length_km)

            # Reach stage from discharge & geometry: y ~ (q * n / (w * sqrt(s)))^0.6
            reach_stage = float(((curr_q * manning) / (width * math.sqrt(slope))) ** 0.6)
            max_depth = float(max(0.0, reach_stage - bankfull))

            # Severity
            if max_depth >= 2.5:
                sev = InundationSeverity.CATASTROPHIC_SUBMERGENCE
            elif max_depth >= 1.0:
                sev = InundationSeverity.SEVERE_DANGER
            elif max_depth >= 0.30:
                sev = InundationSeverity.MODERATE_FLOODING
            elif max_depth >= 0.05:
                sev = InundationSeverity.SHALLOW_NUISANCE
            else:
                sev = InundationSeverity.NO_INUNDATION

            inundated_sqkm = float(fp_area * (1.0 - math.exp(-max_depth / 1.5))) if max_depth > 0 else 0.0

            forecasts.append(ReachInundationForecast(
                reach_id=reach_id,
                reach_name=props["name"],
                distance_from_upstream_km=cum_dist_km,
                wave_arrival_time_min=cum_travel_time_sec / 60.0,
                peak_arrival_time_min=(cum_travel_time_sec / 60.0) + 25.0,
                routed_discharge_m3s=curr_q,
                peak_reach_stage_m=reach_stage,
                max_inundation_depth_m=max_depth,
                inundated_area_sqkm=inundated_sqkm,
                severity=sev,
            ))

        return forecasts

    def predict(
        self,
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Universal FLOODY SHIELD prediction interface for Model M11.
        """
        raw_feat = extract_m11_features(features)
        target_reach = str(features.get("target_reach_id", "REACH_03_PATLIKUHAL_KULLU"))
        clean_feat, dq_score, status_str, flags = self.preprocessor.process_and_audit(
            raw_feat,
            sample_id=target_reach,
        )

        stage = clean_feat.get("source_stage_m", 4.0)
        discharge = clean_feat.get("source_discharge_m3s", stage * 120.0)
        hand = clean_feat.get("hand_m", 1.5)

        # 1. Route across all basin reaches
        reach_forecasts = self.route_flood_wave_along_basin(stage, discharge)

        # 2. Extract target reach metrics
        target_rf = next((r for r in reach_forecasts if r.reach_id == target_reach), reach_forecasts[2])

        # 3. Localized inundation depth at user coordinates / HAND
        if self.gbdt_model is not None:
            vec = np.array([[
                clean_feat["source_stage_m"],
                clean_feat["source_discharge_m3s"],
                clean_feat["hand_m"],
                clean_feat["distance_to_river_m"],
                clean_feat["slope_deg"],
            ]])
            pred_depth = float(max(0.0, self.gbdt_model.predict(vec)[0]))
        else:
            # Physics HAND formula: depth = max(0, reach_stage - HAND)
            pred_depth = float(max(0.0, target_rf.peak_reach_stage_m - hand))

        # Filter out sub-5cm regression noise on dry terraces
        if pred_depth < 0.05:
            pred_depth = 0.0
            severity = InundationSeverity.NO_INUNDATION
        elif pred_depth >= 2.5:
            severity = InundationSeverity.CATASTROPHIC_SUBMERGENCE
        elif pred_depth >= 1.0:
            severity = InundationSeverity.SEVERE_DANGER
        elif pred_depth >= 0.30:
            severity = InundationSeverity.MODERATE_FLOODING
        else:
            severity = InundationSeverity.SHALLOW_NUISANCE

        unc_lower, unc_upper = compute_depth_uncertainty_interval(
            predicted_depth_m=pred_depth,
            hand_m=hand,
            data_quality=dq_score,
        )

        confidence = float(np.clip(dq_score * (1.0 - (0.05 * pred_depth)), 0.55, 0.98))

        out = M11PredictionOutput(
            target_reach_id=target_reach,
            forecasted_depth_m=pred_depth,
            inundation_severity=severity,
            flood_wave_arrival_time_min=target_rf.wave_arrival_time_min,
            peak_arrival_time_min=target_rf.peak_arrival_time_min,
            reach_forecasts=reach_forecasts,
            confidence=confidence,
            uncertainty={
                "interval_depth_m": [unc_lower, unc_upper],
                "confidence_level": 0.80,
                "method": "hand_hydraulic_conformal_quantiles",
            },
            data_quality=dq_score,
            model_version="M11-flooddepth-v1.0",
            applicability="UPPER_BEAS_AOI",
            provenance="COPERNICUS_DEM_HAND + MUSKINGUM_CUNGE_GBDT",
        )
        return out.to_dict()
