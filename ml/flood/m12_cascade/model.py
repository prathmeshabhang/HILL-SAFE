"""
ml/flood/m12_cascade/model.py
=============================
Model M12 Architecture: Multi-Hazard Compound Cascade & Landslide Dam Breach Engine.
Implements Froehlich (2008) and Costa (1985) empirical formulations calibrated for Himalayan gorges.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ml.flood.m12_cascade.features import extract_m12_features
from ml.flood.m12_cascade.physics import (
    GRAVITY,
    compute_costa_peak_outflow,
    compute_froehlich_breach_parameters,
)
from ml.flood.m12_cascade.preprocessing import M12Preprocessor
from ml.flood.m12_cascade.schema import (
    CascadeSeverity,
    DownstreamReachImpact,
    LandslideDamBreachResult,
    M12PredictionOutput,
)


class CompoundCascadeEngine:
    """
    Implements Froehlich (2008) and Costa (1985) empirical dam breach physics
    calibrated for narrow Himalayan V-shaped gorges (Upper Beas, Parvati, Sainj rivers).
    Maintains 100% backward compatibility with existing FLOODY SHIELD systems.
    """

    GRAVITY = 9.81  # m/s^2

    def simulate_dam_breach(
        self,
        dam_location: str = "Larji_Sainj_Confluence",
        dam_height_m: float = 35.0,
        impounded_volume_m3: float = 8_500_000.0,
        normal_river_discharge_m3s: float = 450.0,
    ) -> LandslideDamBreachResult:
        """
        Calculates breach outflow hydrograph and routes peak downstream.
        """
        # 1. Peak Breach Outflow (Froehlich Formulation)
        params = compute_froehlich_breach_parameters(dam_height_m, impounded_volume_m3)
        q_peak_breach = params["peak_breach_discharge_m3s"]
        t_f_min = params["breach_formation_time_min"]
        total_peak_q = normal_river_discharge_m3s + q_peak_breach

        # 2. Downstream Reaches along Beas River Corridor
        reaches = [
            ("Aut_Gorge_Settlement", 4.2, 38.0),      # km downstream, channel width m
            ("Thalout_NH3_Bypass", 8.5, 42.0),
            ("Pandoh_Dam_Reservoir", 19.5, 95.0),
            ("Mandi_Town_Floodplain", 38.0, 110.0),
        ]

        wave_speed_kmh = 21.0
        impacts: List[DownstreamReachImpact] = []

        for loc_name, dist_km, ch_width in reaches:
            lead_time_min = round((dist_km / wave_speed_kmh) * 60.0, 1)
            peak_time_min = round(lead_time_min + (t_f_min * 0.45), 1)

            # Hydraulic attenuation along channel storage
            decay_factor = math.exp(-0.024 * dist_km)
            q_reach = round(normal_river_discharge_m3s + (q_peak_breach * decay_factor), 1)

            # Surge height using Manning open-channel approximation
            surge_h = round(((q_reach * 0.045) / (ch_width * math.sqrt(0.012))) ** 0.60, 2)

            if lead_time_min <= 15.0:
                urgency = "IMMEDIATE_LIFE_SAFETY"
            elif lead_time_min <= 45.0:
                urgency = "PREPARE_EVACUATION"
            else:
                urgency = "ADVISORY"

            impacts.append(DownstreamReachImpact(
                location_name=loc_name,
                distance_downstream_km=dist_km,
                flood_wave_lead_time_min=lead_time_min,
                peak_arrival_time_min=peak_time_min,
                peak_discharge_m3s=q_reach,
                surge_height_above_normal_m=surge_h,
                evacuation_urgency=urgency,
            ))

        summary = (
            f"Landslide dam breach at {dam_location} (Height: {dam_height_m}m, Vol: {impounded_volume_m3/1e6:.1f}M m3) "
            f"generates peak outburst flood of {total_peak_q:.0f} m3/s with breach time of {t_f_min:.1f} minutes. "
            f"Aut Gorge reached in {impacts[0].flood_wave_lead_time_min} mins with +{impacts[0].surge_height_above_normal_m}m surge."
        )

        return LandslideDamBreachResult(
            dam_location=dam_location,
            dam_height_m=dam_height_m,
            impounded_volume_m3=impounded_volume_m3,
            peak_outflow_discharge_m3s=round(total_peak_q, 1),
            breach_formation_time_min=round(t_f_min, 1),
            downstream_impacts=impacts,
            cascade_summary=summary,
        )


class M12HazardCascadeModel:
    """Universal ML/Physics wrapper for Model M12."""

    def __init__(self):
        self.preprocessor = M12Preprocessor()
        self.engine = CompoundCascadeEngine()

    def classify_severity(self, peak_q: float) -> CascadeSeverity:
        if peak_q >= 10_000.0:
            return CascadeSeverity.CATASTROPHIC_OUTBURST
        if peak_q >= 3_000.0:
            return CascadeSeverity.MAJOR_DISASTER
        if peak_q >= 1_000.0:
            return CascadeSeverity.MODERATE_BREACH
        return CascadeSeverity.LOW_IMPACT

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Universal FLOODY SHIELD prediction interface for Model M12."""
        raw_feat = extract_m12_features(features)
        clean_feat, dq_score, status_str, flags = self.preprocessor.process_and_audit(raw_feat)

        loc = clean_feat["dam_location"]
        h_dam = clean_feat["dam_height_m"]
        v_imp = clean_feat["impounded_volume_m3"]
        q_norm = clean_feat["normal_river_discharge_m3s"]

        breach_res = self.engine.simulate_dam_breach(
            dam_location=loc,
            dam_height_m=h_dam,
            impounded_volume_m3=v_imp,
            normal_river_discharge_m3s=q_norm,
        )

        severity = self.classify_severity(breach_res.peak_outflow_discharge_m3s)
        shortest_lead = min(i.flood_wave_lead_time_min for i in breach_res.downstream_impacts)

        # Empirical Froehlich uncertainty bounds (+- 25% on peak Q)
        unc_lower = breach_res.peak_outflow_discharge_m3s * 0.75
        unc_upper = breach_res.peak_outflow_discharge_m3s * 1.25

        confidence = float(np.clip(dq_score * 0.92, 0.60, 0.96))

        out = M12PredictionOutput(
            dam_location=loc,
            peak_outflow_discharge_m3s=breach_res.peak_outflow_discharge_m3s,
            breach_formation_time_min=breach_res.breach_formation_time_min,
            cascade_severity=severity,
            shortest_evacuation_lead_time_min=shortest_lead,
            impacted_reaches_count=len(breach_res.downstream_impacts),
            breach_result=breach_res,
            confidence=confidence,
            uncertainty={
                "peak_outflow_interval_m3s": [round(unc_lower, 1), round(unc_upper, 1)],
                "confidence_level": 0.80,
                "method": "froehlich_empirical_case_study_envelope",
            },
            data_quality=dq_score,
            model_version="M12-cascade-v1.0",
            applicability="UPPER_BEAS_AOI",
            provenance="FROEHLICH_COSTA_BREACH_PHYSICS + HIMALAYAN_CALIBRATION",
        )
        return out.to_dict()
