"""M20 — Change detection baseline.

Approach
--------
1. NDVI change:     δNDVI = NDVI_pre − NDVI_post  (positive = vegetation loss)
2. NDWI change:     δNDWI = NDWI_post − NDWI_pre  (positive = new water / flooding)
3. SAR coherence:   coherence drop = coh_pre − coh_post  (positive = surface change)
4. Physics proxy:   inundation depth from M11 / flow velocity from M10

These indicators are fused into a damage probability score.
No supervised classification is possible without labelled post-event field surveys
(which are not available for Upper Beas at this project stage).

Damage class thresholds (approximate, for evidence presentation)
------------------------------------------------------------------
    CHANGE_DETECTED:  any indicator above detection threshold
    MINOR:            damage_prob < 0.35
    MODERATE:         0.35 ≤ damage_prob < 0.65
    SEVERE:           damage_prob ≥ 0.65

These thresholds are NOT validated against labelled damage assessments.
The system outputs CHANGE_DETECTED_ONLY status when supervised labels
are unavailable, and MODELLED evidence type for physics-derived estimates.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np

# Detection thresholds
NDVI_CHANGE_THRESHOLD = 0.10        # δNDVI ≥ 0.10 → vegetation loss detected
NDWI_CHANGE_THRESHOLD = 0.08        # δNDWI ≥ 0.08 → water ingress detected
SAR_COHERENCE_THRESHOLD = 0.15      # coherence drop ≥ 0.15 → surface change
FLOOD_DEPTH_MINOR_M = 0.30          # Flood depth at which minor damage begins
FLOOD_DEPTH_MODERATE_M = 1.0        # Moderate damage threshold
FLOOD_DEPTH_SEVERE_M = 2.5          # Severe damage threshold


def compute_ndvi_change_score(
    ndvi_pre: Optional[float],
    ndvi_post: Optional[float],
) -> Tuple[float, bool]:
    """
    Returns (delta_ndvi_signal, change_detected).
    Signal is 0–1 normalized.
    """
    if ndvi_pre is None or ndvi_post is None:
        return 0.0, False
    delta = float(ndvi_pre) - float(ndvi_post)  # positive → loss
    detected = delta >= NDVI_CHANGE_THRESHOLD
    signal = float(np.clip(delta / 0.5, 0.0, 1.0))  # saturates at Δ=0.5
    return signal, detected


def compute_ndwi_change_score(
    ndwi_pre: Optional[float],
    ndwi_post: Optional[float],
) -> Tuple[float, bool]:
    """
    Returns (water_ingress_signal, change_detected).
    """
    if ndwi_pre is None or ndwi_post is None:
        return 0.0, False
    delta = float(ndwi_post) - float(ndwi_pre)  # positive → more water
    detected = delta >= NDWI_CHANGE_THRESHOLD
    signal = float(np.clip(delta / 0.5, 0.0, 1.0))
    return signal, detected


def compute_sar_coherence_score(
    coh_pre: Optional[float],
    coh_post: Optional[float],
) -> Tuple[float, bool]:
    """
    Returns (coherence_loss_signal, change_detected).
    """
    if coh_pre is None or coh_post is None:
        return 0.0, False
    drop = float(coh_pre) - float(coh_post)
    detected = drop >= SAR_COHERENCE_THRESHOLD
    signal = float(np.clip(drop / 0.6, 0.0, 1.0))
    return signal, detected


def compute_physics_damage_score(
    flood_depth_m: Optional[float],
    flow_velocity_ms: Optional[float],
    landslide_runout_m: Optional[float],
) -> Tuple[float, bool]:
    """
    Physics proxy damage score derived from M10/M11 outputs.

    Uses simplified NDMA-style fragility curves:
    - Linear damage fraction over [0, 3m] flood depth
    - Drag force for velocity damage (0.5*ρ*v²)
    """
    score = 0.0
    detected = False

    if flood_depth_m is not None and flood_depth_m > 0:
        depth_score = float(np.clip(flood_depth_m / 3.0, 0.0, 1.0))
        score = max(score, depth_score)
        if flood_depth_m >= FLOOD_DEPTH_MINOR_M:
            detected = True

    if flow_velocity_ms is not None and flow_velocity_ms > 0:
        # Drag pressure = 0.5 * 1000 kg/m³ * v² / 1000 (→ kPa)
        drag_kpa = 0.5 * 1.0 * (flow_velocity_ms ** 2)
        # Concrete bridge failure at ~50 kPa; RC wall at ~100 kPa
        vel_score = float(np.clip(drag_kpa / 50.0, 0.0, 1.0))
        score = max(score, vel_score)
        if flow_velocity_ms >= 1.5:
            detected = True

    if landslide_runout_m is not None and landslide_runout_m > 0:
        runout_score = float(np.clip(landslide_runout_m / 200.0, 0.0, 1.0))
        score = max(score, runout_score)
        if landslide_runout_m > 5.0:
            detected = True

    return score, detected


def fuse_damage_score(
    ndvi_signal: float,
    ndwi_signal: float,
    sar_signal: float,
    physics_signal: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Weighted fusion of damage indicators.

    Default weights reflect observational confidence hierarchy:
    - Physics (M10/M11 derived) has highest weight when available
    - SAR coherence is most reliable RS indicator
    """
    if weights is None:
        weights = {
            "physics": 0.40,
            "sar": 0.30,
            "ndwi": 0.18,
            "ndvi": 0.12,
        }
    total_w = sum(weights.values())
    score = (
        weights["physics"] * physics_signal
        + weights["sar"] * sar_signal
        + weights["ndwi"] * ndwi_signal
        + weights["ndvi"] * ndvi_signal
    ) / total_w
    return float(np.clip(score, 0.0, 1.0))


def classify_damage(
    damage_prob: float,
    any_change_detected: bool,
    labels_available: bool = False,
) -> str:
    """
    Map damage probability to damage class.

    If no supervised labels available, returns CHANGE_DETECTED rather
    than MINOR/MODERATE/SEVERE to avoid overclaiming classification.
    """
    from .schema import DamageClass

    if not any_change_detected:
        return DamageClass.NO_DAMAGE

    if not labels_available:
        return DamageClass.CHANGE_DETECTED

    if damage_prob < 0.35:
        return DamageClass.MINOR
    elif damage_prob < 0.65:
        return DamageClass.MODERATE
    else:
        return DamageClass.SEVERE
