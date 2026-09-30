"""
ml/flood/m10_water_level/uncertainty.py
=======================================
Quantile and error-dispersion uncertainty intervals for river water level forecasts.
"""

from __future__ import annotations

import math
from typing import Tuple


def compute_stage_uncertainty_interval(
    predicted_stage_m: float,
    horizon_hours: float,
    data_quality: float = 1.0,
    confidence_level: float = 0.80,
) -> Tuple[float, float]:
    """
    Computes [lower, upper] stage bounds in meters.
    Uncertainty scales with forecast horizon and inversely with data quality:
    sigma = sigma_base + 0.15 * sqrt(horizon_hours) / data_quality
    """
    dq = max(0.2, min(1.0, data_quality))
    sigma_base = 0.10  # 10cm base measurement error at gauge
    sigma_drift = (0.18 * math.sqrt(max(0.25, horizon_hours))) / dq
    sigma_total = sigma_base + sigma_drift

    z_val = 1.28 if confidence_level <= 0.80 else 1.645
    margin = z_val * sigma_total

    lower = max(0.0, predicted_stage_m - margin)
    upper = predicted_stage_m + margin
    return float(round(lower, 2)), float(round(upper, 2))
