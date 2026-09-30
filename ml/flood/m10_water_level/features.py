"""
ml/flood/m10_water_level/features.py
====================================
Feature engineering and catchment rainfall-runoff coupling for Model M10.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


def compute_stage_rate_of_rise(
    stage_history_m: Sequence[float],
    timestep_hours: float = 0.25,
) -> float:
    """Computes rate of rise (m/hr) from recent stage observations."""
    if not stage_history_m or len(stage_history_m) < 2:
        return 0.0
    arr = np.asarray(stage_history_m, dtype=float)
    delta = arr[-1] - arr[-2]
    return float(round(delta / max(1e-4, timestep_hours), 4))


def extract_m10_features(
    reading: Dict[str, Any],
    stage_history_m: Optional[Sequence[float]] = None,
) -> Dict[str, float]:
    """
    Constructs the 12-feature hydro-meteorological vector for Model M10.
    """
    stage = float(reading.get("current_stage_m", reading.get("water_level_m", reading.get("cwc_river_level_m", 3.0))))
    lat = float(reading.get("latitude", 31.88))  # Default Bhuntar
    lon = float(reading.get("longitude", 77.15))
    elev = float(reading.get("elevation_m", 1090.0))

    if stage_history_m and len(stage_history_m) >= 2:
        rate = compute_stage_rate_of_rise(stage_history_m)
    else:
        rate = float(reading.get("rate_of_rise_m_hr", reading.get("cwc_rate_of_rise_m_hr", 0.0)))

    r_15m = float(reading.get("rainfall_15m_mm", reading.get("r_15m", 0.0)))
    r_1h = float(reading.get("rainfall_1h_mm", reading.get("r_1h", 0.0)))
    r_3h = float(reading.get("rainfall_3h_mm", reading.get("r_3h", 0.0)))
    r_6h = float(reading.get("rainfall_6h_mm", reading.get("r_6h", 0.0)))
    soil = float(reading.get("soil_moisture_pct", 40.0))

    # Catchment saturation-weighted runoff proxy
    soil_factor = np.clip(soil / 100.0, 0.1, 1.0)
    effective_runoff = (r_1h + 0.6 * r_3h + 0.3 * r_6h) * soil_factor

    warn_lvl = float(reading.get("warning_level_m", 5.0))
    danger_lvl = float(reading.get("danger_level_m", 7.0))
    hfl = float(reading.get("hfl_m", 9.5))

    return {
        "latitude": lat,
        "longitude": lon,
        "elevation_m": elev,
        "water_level_m": stage,
        "current_stage_m": stage,
        "rate_of_rise_m_hr": round(rate, 4),
        "rainfall_rate_mmh": round(r_1h, 2),
        "rainfall_15m_mm": round(r_15m, 2),
        "rainfall_1h_mm": round(r_1h, 2),
        "rainfall_3h_mm": round(r_3h, 2),
        "rainfall_6h_mm": round(r_6h, 2),
        "soil_moisture_pct": round(soil, 2),
        "effective_runoff_index": round(effective_runoff, 3),
        "warning_level_m": warn_lvl,
        "danger_level_m": danger_lvl,
        "hfl_m": hfl,
    }
