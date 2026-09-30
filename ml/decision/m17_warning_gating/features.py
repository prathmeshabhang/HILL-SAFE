"""
ml/decision/m17_warning_gating/features.py
==========================================
Feature extraction and multi-hazard fusion inputs for Model M17.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Tuple
import numpy as np

from ml.decision.m17_warning_gating.gating_rules import evaluate_evacuation_lead_time
from ml.decision.m17_warning_gating.schema import M17WarningInput


FEATURE_NAMES = [
    "normalized_water_stage",
    "warning_margin_m",
    "rainfall_intensity_mmh",
    "rainfall_3h_mm",
    "flood_probability",
    "flood_depth_m",
    "landslide_probability",
    "pore_water_pressure_ratio",
    "log_outburst_discharge",
    "log_at_risk_pop",
    "arterial_blocked",
    "bridge_submerged",
    "evacuation_urgency_index",
]


def extract_warning_features(inp: M17WarningInput) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Extracts 13-element feature vector and metadata.
    """
    norm_stage = inp.river_water_level_m / max(1.0, inp.danger_level_m)
    warn_margin = inp.river_water_level_m - inp.warning_level_m

    log_outburst = math.log10(max(1.0, inp.natural_dam_outburst_discharge_m3s + 1.0))
    log_pop = math.log10(max(1.0, float(inp.at_risk_population)))

    road_blk = 1.0 if inp.arterial_road_blocked else 0.0
    bridge_sub = 1.0 if inp.critical_bridge_submerged else 0.0

    ret_min, eui, strategy, urgency = evaluate_evacuation_lead_time(
        population=inp.at_risk_population,
        road_blocked=inp.arterial_road_blocked,
        bridge_down=inp.critical_bridge_submerged,
        lead_time_min=inp.flood_arrival_time_min,
    )

    feat_vec = np.array([
        norm_stage,
        warn_margin,
        inp.rainfall_intensity_mmh,
        inp.rainfall_3h_mm,
        inp.flood_probability,
        inp.flood_depth_m,
        inp.landslide_probability,
        inp.pore_water_pressure_ratio,
        log_outburst,
        log_pop,
        road_blk,
        bridge_sub,
        eui,
    ], dtype=np.float32)

    meta = {
        "required_evacuation_time_min": ret_min,
        "evacuation_urgency_index": eui,
        "strategy": strategy,
        "urgency": urgency,
        "lead_time_min": inp.flood_arrival_time_min,
    }

    return feat_vec, meta
