"""
ml/landslide/m8_deformation/uncertainty.py
==========================================
Uncertainty interval estimation for Model M8 ground movement forecasts.
Grounded in InSAR phase noise, temporal decorrelation, and epistemic horizon dispersion.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np


def compute_deformation_uncertainty_interval(
    predicted_increment_mm: float,
    horizon_days: float,
    insar_coherence: float = 0.85,
    confidence_level: float = 0.80,
) -> Tuple[float, float]:
    """
    Computes [lower, upper] prediction bounds in mm.
    Uncertainty scales with horizon length and inversely with InSAR coherence:
    sigma = sigma_base + horizon * (1.0 - coherence) * sigma_drift
    """
    coherence = max(0.1, min(1.0, insar_coherence))
    # Base measurement noise (~1.5 mm for high-coherence C-band Sentinel-1)
    sigma_meas = 1.5 / coherence
    # Epistemic model forecast drift (grows as sqrt(time))
    sigma_drift = 0.8 * math.sqrt(horizon_days) * (1.0 + (1.0 - coherence) * 2.0)
    
    sigma_total = sigma_meas + sigma_drift
    z_val = 1.28 if confidence_level <= 0.80 else 1.645  # 80% vs 90% quantile

    margin = z_val * sigma_total
    lower = max(0.0, predicted_increment_mm - margin)
    upper = predicted_increment_mm + margin

    return float(round(lower, 2)), float(round(upper, 2))
