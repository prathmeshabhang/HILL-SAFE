"""M20 — Inference: per-asset damage assessment."""

from __future__ import annotations

import logging

import numpy as np

from .change_detection import (
    compute_ndvi_change_score,
    compute_ndwi_change_score,
    compute_sar_coherence_score,
    compute_physics_damage_score,
    fuse_damage_score,
    classify_damage,
)
from .schema import (
    AssessmentStatus,
    DamageClass,
    DamageEvidenceType,
    M20DamageInput,
    M20DamageOutput,
)

logger = logging.getLogger(__name__)

# Asset size proxies for affected_area_m2 estimation
_ASSET_SIZE_M2 = {
    "road": 2500.0,
    "bridge": 800.0,
    "building": 400.0,
    "substation": 600.0,
    "hospital": 1200.0,
    "water_intake": 200.0,
    "orchard": 5000.0,
    "GENERIC": 1000.0,
}


def assess(inp: M20DamageInput) -> M20DamageOutput:
    """
    Assess post-event damage for a single asset.

    Returns M20DamageOutput with:
    - change_detected (bool)
    - damage_class (CHANGE_DETECTED when no labels; NO_DAMAGE if clean)
    - damage_probability (0–1 fused score)
    - evidence_type (CHANGE_DETECTED / MODELLED)
    - external_validation_note: EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE

    NOTE: Supervised damage classification (MINOR/MODERATE/SEVERE) requires
    field survey labels.  This baseline returns CHANGE_DETECTED without labels.
    """
    if inp.data_quality < 0.3:
        return M20DamageOutput(
            asset_id=inp.asset_id,
            hazard_type=inp.hazard_type,
            change_detected=False,
            damage_class=DamageClass.NO_DAMAGE,
            damage_probability=0.0,
            damage_fraction=0.0,
            affected_area_m2=0.0,
            evidence_type=DamageEvidenceType.CHANGE_DETECTED,
            confidence=0.1,
            data_quality=inp.data_quality,
            status=AssessmentStatus.DEGRADED_INPUT,
            notes="Data quality critically low.",
        )

    sat = inp.satellite

    # Compute individual indicator scores
    ndvi_sig, ndvi_det = compute_ndvi_change_score(sat.ndvi_pre, sat.ndvi_post)
    ndwi_sig, ndwi_det = compute_ndwi_change_score(sat.ndwi_pre, sat.ndwi_post)
    sar_sig, sar_det = compute_sar_coherence_score(
        sat.sar_coherence_pre, sat.sar_coherence_post
    )
    phys_sig, phys_det = compute_physics_damage_score(
        inp.flood_depth_m,
        inp.flow_velocity_ms,
        inp.landslide_runout_m,
    )

    any_change = any([ndvi_det, ndwi_det, sar_det, phys_det])

    # Fuse
    damage_prob = fuse_damage_score(ndvi_sig, ndwi_sig, sar_sig, phys_sig)

    # Evidence type
    has_rs = any(
        x is not None
        for x in [sat.ndvi_pre, sat.ndvi_post, sat.sar_coherence_pre, sat.sar_coherence_post]
    )
    has_physics = any(
        x is not None and x > 0
        for x in [inp.flood_depth_m, inp.flow_velocity_ms, inp.landslide_runout_m]
    )

    if has_rs:
        evidence = DamageEvidenceType.CHANGE_DETECTED
    elif has_physics:
        evidence = DamageEvidenceType.MODELLED
    else:
        evidence = DamageEvidenceType.CHANGE_DETECTED

    # Damage class — no supervised labels → use CHANGE_DETECTED classification
    labels_available = False  # No authoritative field labels for Upper Beas
    damage_class = classify_damage(damage_prob, any_change, labels_available)

    # Affected area estimate
    cat_key = inp.asset_category.lower()
    base_area = _ASSET_SIZE_M2.get(cat_key, _ASSET_SIZE_M2["GENERIC"])
    affected_area = base_area * damage_prob

    # Damage fraction (structural loss estimate) — physics proxy
    damage_fraction = 0.0
    if inp.flood_depth_m is not None:
        damage_fraction = float(np.clip(inp.flood_depth_m / 3.0, 0.0, 1.0))
    elif damage_prob > 0:
        damage_fraction = damage_prob * 0.6  # conservative scaling without depth data

    # Confidence: RS data raises confidence; physics-only is more uncertain
    if has_rs and has_physics:
        confidence = 0.70 * inp.data_quality
    elif has_rs:
        confidence = 0.60 * inp.data_quality
    elif has_physics:
        confidence = 0.50 * inp.data_quality
    else:
        confidence = 0.30 * inp.data_quality

    status = (
        AssessmentStatus.ASSESSED
        if any_change or damage_prob > 0
        else AssessmentStatus.INSUFFICIENT_DATA
    )
    if not any_change and damage_prob == 0:
        status = AssessmentStatus.CHANGE_DETECTED_ONLY if has_rs else AssessmentStatus.INSUFFICIENT_DATA

    return M20DamageOutput(
        asset_id=inp.asset_id,
        hazard_type=inp.hazard_type,
        change_detected=any_change,
        damage_class=damage_class,
        damage_probability=round(damage_prob, 4),
        damage_fraction=round(damage_fraction, 4),
        affected_area_m2=round(affected_area, 1),
        evidence_type=evidence,
        confidence=round(confidence, 4),
        data_quality=inp.data_quality,
        status=AssessmentStatus.ASSESSED if any_change else AssessmentStatus.INSUFFICIENT_DATA,
        provenance="M20_CHANGE_DETECTION_BASELINE + NDMA_FRAGILITY_CURVES",
        notes=(
            f"ndvi_det={ndvi_det}, ndwi_det={ndwi_det}, "
            f"sar_det={sar_det}, phys_det={phys_det}. "
            "No supervised damage labels available for Upper Beas — "
            "do not interpret CHANGE_DETECTED as MINOR/MODERATE/SEVERE."
        ),
        external_validation_note="EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE",
    )
