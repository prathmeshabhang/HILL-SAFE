"""
ml/landslide/m8_deformation/features.py
========================================
Kinematic derivative extraction, hydro-mechanical coupling, and InSAR feature engineering for Model M8.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


def compute_kinematic_derivatives(
    displacement_history: Sequence[float],
    timestep_days: float = 1.0,
) -> Dict[str, float]:
    """
    Computes velocity, acceleration, and inverse velocity from displacement time series.
    """
    if not displacement_history or len(displacement_history) < 2:
        return {
            "velocity_mm_day": 0.0,
            "acceleration_mm_day2": 0.0,
            "inverse_velocity_day_mm": 999.0,
            "rolling_std_displacement": 0.0,
        }

    arr = np.asarray(displacement_history, dtype=float)
    # Velocity between adjacent steps
    diffs = np.diff(arr) / max(1e-4, timestep_days)
    curr_v = float(diffs[-1])

    if len(diffs) >= 2:
        curr_a = float((diffs[-1] - diffs[-2]) / max(1e-4, timestep_days))
    else:
        curr_a = 0.0

    inv_v = 1.0 / max(1e-3, curr_v) if curr_v > 0.0 else 999.0
    rolling_std = float(np.std(arr[-min(len(arr), 5):]))

    return {
        "velocity_mm_day": round(curr_v, 4),
        "acceleration_mm_day2": round(curr_a, 4),
        "inverse_velocity_day_mm": round(inv_v, 4),
        "rolling_std_displacement": round(rolling_std, 4),
    }


def extract_m8_features(
    reading: Dict[str, Any],
    displacement_history: Optional[Sequence[float]] = None,
) -> Dict[str, float]:
    """
    Extracts complete 10-feature vector for Model M8 inference.
    """
    cum_disp = float(reading.get("cumulative_displacement_mm", reading.get("displacement_mm", 0.0)))
    lat = float(reading.get("latitude", 32.22))
    lon = float(reading.get("longitude", 77.18))
    elev = float(reading.get("elevation_m", 1850.0))
    slope = float(reading.get("slope_deg", 28.0))
    rain_72h = float(reading.get("rainfall_72h_mm", 0.0))
    coherence = float(reading.get("insar_coherence", 0.85))
    tilt_rate = float(reading.get("tilt_rate_deg_day", 0.0))
    crack_rate = float(reading.get("crack_width_rate_mm_day", 0.0))

    if displacement_history and len(displacement_history) >= 2:
        kin = compute_kinematic_derivatives(displacement_history)
        v = kin["velocity_mm_day"]
        a = kin["acceleration_mm_day2"]
        inv_v = kin["inverse_velocity_day_mm"]
        r_std = kin["rolling_std_displacement"]
    else:
        v = float(reading.get("velocity_mm_day", 0.0))
        a = float(reading.get("acceleration_mm_day2", 0.0))
        inv_v = 1.0 / max(1e-3, v) if v > 0.0 else 999.0
        r_std = 0.0

    # Hydro-mechanical driving index: rainfall * sin(slope)
    slope_rad = math.radians(min(65.0, max(0.0, slope)))
    hydro_driving = rain_72h * math.sin(slope_rad)

    return {
        "latitude": lat,
        "longitude": lon,
        "elevation_m": elev,
        "slope_deg": slope,
        "displacement_mm": cum_disp,
        "cumulative_displacement_mm": cum_disp,
        "velocity_mm_day": v,
        "acceleration_mm_day2": a,
        "inverse_velocity_day_mm": inv_v,
        "rainfall_72h_mm": rain_72h,
        "hydro_driving_index": round(hydro_driving, 3),
        "insar_coherence": coherence,
        "tilt_rate_deg_day": tilt_rate,
        "crack_width_rate_mm_day": crack_rate,
        "rolling_std_displacement": r_std,
    }
