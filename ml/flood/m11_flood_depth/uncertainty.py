"""
ml/flood/m11_flood_depth/uncertainty.py
=======================================
Uncertainty interval estimation for inundation depth and wave arrival time forecasts.
"""

from __future__ import annotations

import math
from typing import Tuple


def compute_depth_uncertainty_interval(
    predicted_depth_m: float,
    hand_m: float,
    data_quality: float = 1.0,
    confidence_level: float = 0.80,
) -> Tuple[float, float]:
    """
    Computes [lower, upper] flood depth bounds in meters.
    Uncertainty scales with terrain complexity (HAND) and inversely with data quality:
    sigma = sigma_base + 0.12 * sqrt(hand_m) / data_quality
    """
    dq = max(0.2, min(1.0, data_quality))
    sigma_base = 0.15
    sigma_terrain = (0.12 * math.sqrt(max(0.1, hand_m))) / dq
    sigma_total = sigma_base + sigma_terrain

    z_val = 1.28 if confidence_level <= 0.80 else 1.645
    margin = z_val * sigma_total

    lower = max(0.0, predicted_depth_m - margin)
    upper = predicted_depth_m + margin
    return float(round(lower, 2)), float(round(upper, 2))
