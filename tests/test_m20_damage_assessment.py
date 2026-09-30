"""
Tests for M20 Post-Event Damage Assessment.

SYNTHETIC — PIPELINE TEST ONLY for indicator scores.
External damage ground truth is UNAVAILABLE for Upper Beas.
"""

import pytest

from ml.assessment.m20_damage_assessment.change_detection import (
    compute_ndvi_change_score,
    compute_ndwi_change_score,
    compute_sar_coherence_score,
    compute_physics_damage_score,
    fuse_damage_score,
    classify_damage,
    NDVI_CHANGE_THRESHOLD,
    NDWI_CHANGE_THRESHOLD,
    SAR_COHERENCE_THRESHOLD,
)
from ml.assessment.m20_damage_assessment.schema import (
    DamageClass,
    DamageEvidenceType,
    AssessmentStatus,
    SatelliteObservation,
    M20DamageInput,
)
from ml.assessment.m20_damage_assessment.infer import assess
from ml.assessment.m20_damage_assessment.validation import (
    generate_validation_report,
    EXTERNAL_VALIDATION_STATUS,
)


# ---------------------------------------------------------------------------
# Test 1: NDVI change detection
# ---------------------------------------------------------------------------

def test_ndvi_no_change():
    signal, detected = compute_ndvi_change_score(0.6, 0.58)
    assert not detected
    assert signal < NDVI_CHANGE_THRESHOLD


def test_ndvi_change_detected():
    signal, detected = compute_ndvi_change_score(0.7, 0.4)  # delta = 0.3
    assert detected
    assert signal > 0


# ---------------------------------------------------------------------------
# Test 2: NDWI change detection
# ---------------------------------------------------------------------------

def test_ndwi_flood_detected():
    signal, detected = compute_ndwi_change_score(0.1, 0.5)  # delta = 0.4
    assert detected
    assert signal > 0


def test_ndwi_no_change():
    signal, detected = compute_ndwi_change_score(0.3, 0.33)
    assert not detected


# ---------------------------------------------------------------------------
# Test 3: SAR coherence loss
# ---------------------------------------------------------------------------

def test_sar_coherence_surface_change():
    signal, detected = compute_sar_coherence_score(0.8, 0.5)  # drop = 0.3
    assert detected
    assert signal > 0


def test_sar_no_change():
    signal, detected = compute_sar_coherence_score(0.7, 0.68)
    assert not detected


# ---------------------------------------------------------------------------
# Test 4: Physics damage score
# ---------------------------------------------------------------------------

def test_physics_deep_flood_damage():
    score, detected = compute_physics_damage_score(
        flood_depth_m=2.0, flow_velocity_ms=None, landslide_runout_m=None
    )
    assert detected
    assert score > 0.5


def test_physics_no_flood():
    score, detected = compute_physics_damage_score(None, None, None)
    assert not detected
    assert score == 0.0


# ---------------------------------------------------------------------------
# Test 5: Fuse score is bounded [0, 1]
# ---------------------------------------------------------------------------

def test_fuse_score_bounded():
    for _ in range(20):
        import random
        s = fuse_damage_score(
            random.random(), random.random(), random.random(), random.random()
        )
        assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# Test 6: classify_damage without labels → CHANGE_DETECTED
# ---------------------------------------------------------------------------

def test_classify_no_labels_returns_change_detected():
    dc = classify_damage(0.8, True, labels_available=False)
    assert dc == DamageClass.CHANGE_DETECTED


def test_classify_no_change():
    dc = classify_damage(0.0, False, labels_available=False)
    assert dc == DamageClass.NO_DAMAGE


# ---------------------------------------------------------------------------
# Test 7: Full assess — flood scenario returns ASSESSED
# ---------------------------------------------------------------------------

def test_assess_flood_with_depth():
    """SYNTHETIC — PIPELINE TEST ONLY."""
    inp = M20DamageInput(
        asset_id="BRIDGE_NH3_KULLU",
        hazard_type="FLOOD",
        satellite=SatelliteObservation(
            ndvi_pre=0.65,
            ndvi_post=0.30,
            ndwi_pre=0.05,
            ndwi_post=0.60,
            sar_coherence_pre=0.82,
            sar_coherence_post=0.35,
        ),
        flood_depth_m=2.5,
        flow_velocity_ms=3.5,
        asset_category="bridge",
        data_quality=0.85,
    )
    out = assess(inp)
    assert out.change_detected is True
    assert out.damage_class == DamageClass.CHANGE_DETECTED  # no labels → CHANGE_DETECTED
    assert 0.0 < out.damage_probability <= 1.0
    assert out.status == AssessmentStatus.ASSESSED
    assert out.external_validation_note == "EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE"


# ---------------------------------------------------------------------------
# Test 8: No satellite + no physics → INSUFFICIENT_DATA
# ---------------------------------------------------------------------------

def test_assess_no_data():
    inp = M20DamageInput(
        asset_id="ROAD_SEGMENT_01",
        hazard_type="FLOOD",
        satellite=SatelliteObservation(),  # all None
        data_quality=0.8,
    )
    out = assess(inp)
    assert out.change_detected is False
    assert out.damage_class == DamageClass.NO_DAMAGE


# ---------------------------------------------------------------------------
# Test 9: Degraded data quality
# ---------------------------------------------------------------------------

def test_assess_degraded_quality():
    inp = M20DamageInput(
        asset_id="ASSET_LOW_QUALITY",
        hazard_type="LANDSLIDE",
        satellite=SatelliteObservation(ndvi_pre=0.7, ndvi_post=0.2),
        data_quality=0.05,  # critically degraded
    )
    out = assess(inp)
    assert out.status == AssessmentStatus.DEGRADED_INPUT


# ---------------------------------------------------------------------------
# Test 10: Output model field is correct
# ---------------------------------------------------------------------------

def test_assess_model_field():
    inp = M20DamageInput(
        asset_id="HOSPITAL_KULLU",
        hazard_type="FLOOD",
        satellite=SatelliteObservation(ndwi_pre=0.1, ndwi_post=0.5),
        flood_depth_m=1.0,
        asset_category="hospital",
        data_quality=0.9,
    )
    out = assess(inp)
    assert out.model == "M20_DAMAGE_ASSESSMENT"
    assert 0.0 <= out.damage_fraction <= 1.0
    assert out.affected_area_m2 >= 0.0


# ---------------------------------------------------------------------------
# Test 11: Validation report states EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE
# ---------------------------------------------------------------------------

def test_validation_report_status():
    report = generate_validation_report()
    assert report["external_validation"] == EXTERNAL_VALIDATION_STATUS
    assert "validation_plan" in report
    assert "change_detection_baseline" in report
