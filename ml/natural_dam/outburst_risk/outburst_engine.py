"""
outburst_engine.py — Natural Dam Outburst Risk & Failure Scenario Engine
========================================================================
Assesses geotechnical overtopping failure probability and flood outburst risk
based on impounded reservoir volume, dam structural geometry, and forecast rainfall.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ml.flood.m12_compound_cascade import CompoundCascadeEngine, LandslideDamBreachResult


@dataclass
class OutburstRiskAssessment:
    outburst_risk_level: str  # "VERY_HIGH", "HIGH", "MODERATE", "LOW", "INSUFFICIENT_DATA"
    risk_score: float         # 0.0 to 1.0
    failure_mode: str         # "OVERTOPPING_EROSION", "PIPING_SEEPAGE", "SLOPE_INSTABILITY", "UNKNOWN"
    peak_breach_discharge_m3s: Optional[float]
    first_reach_lead_time_min: Optional[float]
    surge_height_m: Optional[float]
    rationale: str


class NaturalDamOutburstEngine:
    def __init__(self):
        self._cascade_engine = CompoundCascadeEngine()

    def assess_outburst_risk(
        self,
        impounded_volume_m3: Optional[float],
        dam_height_m: Optional[float],
        forecast_rain_24h_mm: float = 65.0,
        normal_river_discharge_m3s: float = 350.0,
        dam_location_name: str = "Upper_Beas_Constriction",
    ) -> OutburstRiskAssessment:
        """
        Evaluates outburst potential. Returns INSUFFICIENT_DATA if primary
        geometric indicators are unavailable.
        """
        if impounded_volume_m3 is None or dam_height_m is None or impounded_volume_m3 <= 0 or dam_height_m <= 0:
            return OutburstRiskAssessment(
                outburst_risk_level="INSUFFICIENT_DATA",
                risk_score=0.0,
                failure_mode="UNKNOWN",
                peak_breach_discharge_m3s=None,
                first_reach_lead_time_min=None,
                surge_height_m=None,
                rationale="Physical dam height or impounded volume cannot be defensibly measured from available satellite passes.",
            )

        # 1. Run geotechnical breach physics (Model M12)
        sim_res = self._cascade_engine.simulate_dam_breach(
            dam_location=dam_location_name,
            dam_height_m=dam_height_m,
            impounded_volume_m3=impounded_volume_m3,
            normal_river_discharge_m3s=normal_river_discharge_m3s,
        )

        first_reach = sim_res.downstream_impacts[0] if sim_res.downstream_impacts else None
        lead_time = first_reach.flood_wave_lead_time_min if first_reach else 15.0
        surge = first_reach.surge_height_above_normal_m if first_reach else 4.5

        # 2. Risk Scoring Formula
        v_score = min(1.0, impounded_volume_m3 / 10_000_000.0)
        h_score = min(1.0, dam_height_m / 50.0)
        r_score = min(1.0, forecast_rain_24h_mm / 100.0)

        risk_score = round(float(0.40 * v_score + 0.35 * h_score + 0.25 * r_score), 3)

        if risk_score >= 0.70 or forecast_rain_24h_mm >= 80.0:
            level = "VERY_HIGH"
            failure_mode = "OVERTOPPING_EROSION"
        elif risk_score >= 0.45:
            level = "HIGH"
            failure_mode = "OVERTOPPING_EROSION"
        elif risk_score >= 0.25:
            level = "MODERATE"
            failure_mode = "PIPING_SEEPAGE"
        else:
            level = "LOW"
            failure_mode = "SLOPE_INSTABILITY"

        rationale = (
            f"Impounded volume of {impounded_volume_m3/1e6:.2f}M m3 with dam height {dam_height_m:.1f}m and "
            f"{forecast_rain_24h_mm:.0f}mm forecast rain yields {level} outburst potential (peak Q: {sim_res.peak_outflow_discharge_m3s:.0f} m3/s)."
        )

        return OutburstRiskAssessment(
            outburst_risk_level=level,
            risk_score=risk_score,
            failure_mode=failure_mode,
            peak_breach_discharge_m3s=sim_res.peak_outflow_discharge_m3s,
            first_reach_lead_time_min=lead_time,
            surge_height_m=surge,
            rationale=rationale,
        )
