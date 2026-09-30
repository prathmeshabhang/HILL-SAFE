"""
ml/rainfall/m1_nowcast/features.py
==================================
Feature engineering for Model M1: Multi-window accumulations, intensity gradients, and orography.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


def calculate_orographic_factor(elevation_m: float, slope_deg: float) -> float:
    """Estimates orographic rain enhancement factor in Himalayan topography."""
    elev_norm = np.clip((elevation_m - 900.0) / 3000.0, 0.0, 1.0)
    slope_rad = math.radians(min(60.0, max(0.0, slope_deg)))
    # Orographic updraft lifts moist valley air, amplifying precipitation by up to 1.6x
    return float(1.0 + (0.6 * elev_norm * math.sin(slope_rad)))


def extract_features_from_history(
    current_reading: Dict[str, Any],
    rainfall_15m_history: Optional[Sequence[float]] = None,
) -> Dict[str, float]:
    """
    Constructs the complete 14-feature vector from telemetry and past series.
    """
    r_current = float(current_reading.get("rainfall_rate_mmh", current_reading.get("r_15m", 0.0)))
    elev = float(current_reading.get("elevation_m", 1250.0))
    slope = float(current_reading.get("slope_deg", 18.0))

    if rainfall_15m_history and len(rainfall_15m_history) > 0:
        hist = list(rainfall_15m_history)
    else:
        hist = [r_current]

    # Convert 15m rate history to accumulations
    # 15m step accumulation = rate * 0.25h
    step_acc = [h * 0.25 for h in hist]

    r_15m = float(step_acc[-1]) if len(step_acc) >= 1 else r_current * 0.25
    r_30m = float(sum(step_acc[-2:])) if len(step_acc) >= 2 else r_15m * 2.0
    r_1h = float(sum(step_acc[-4:])) if len(step_acc) >= 4 else r_30m * 2.0
    r_3h = float(sum(step_acc[-12:])) if len(step_acc) >= 12 else r_1h * 3.0
    r_6h = float(sum(step_acc[-24:])) if len(step_acc) >= 24 else r_3h * 2.0
    r_12h = float(sum(step_acc[-48:])) if len(step_acc) >= 48 else r_6h * 2.0
    r_24h = float(sum(step_acc[-96:])) if len(step_acc) >= 96 else r_12h * 2.0
    r_72h = float(sum(step_acc[-288:])) if len(step_acc) >= 288 else r_24h * 3.0

    # Acceleration: rate change over last two 15-min intervals
    if len(hist) >= 2:
        accel = float((hist[-1] - hist[-2]) / 0.25)  # mm/h^2
    else:
        accel = 0.0

    orog = calculate_orographic_factor(elev, slope)

    return {
        "latitude": float(current_reading.get("latitude", 32.2)),
        "longitude": float(current_reading.get("longitude", 77.15)),
        "rainfall_rate_mmh": round(r_current, 2),
        "r_15m": round(r_15m, 2),
        "r_30m": round(r_30m, 2),
        "r_1h": round(r_1h, 2),
        "r_3h": round(r_3h, 2),
        "r_6h": round(r_6h, 2),
        "r_12h": round(r_12h, 2),
        "r_24h": round(r_24h, 2),
        "r_72h": round(r_72h, 2),
        "rolling_intensity_mmh": round(r_current, 2),
        "rainfall_acceleration": round(accel, 2),
        "elevation_m": round(elev, 1),
        "slope_deg": round(slope, 1),
        "orographic_factor": round(orog, 3),
        "storm_motion_dx": float(current_reading.get("storm_motion_dx", 12.0)),
    }
