"""
Tests for M19 Time-to-Impact.

Physics baseline validated against published Himalayan benchmark events.
ML quantile regression declared INSUFFICIENT_EVIDENCE — no real Upper Beas
event timestamps available.
"""

import math
import pytest

from ml.impact.m19_time_to_impact.physics import (
    estimate_travel_time,
    _flood_wave_speed_kmh,
    _landslide_runout_speed_kmh,
    M12_DEFAULT_WAVE_SPEED_KMH,
)
from ml.impact.m19_time_to_impact.schema import (
    ImpactType,
    TTIStatus,
    TTIPredictionMethod,
    M19TimeToImpactInput,
)
from ml.impact.m19_time_to_impact.infer import predict
from ml.impact.m19_time_to_impact.validation import (
    generate_physics_benchmark_report,
    HIMALAYAN_BENCHMARKS,
)


# ---------------------------------------------------------------------------
# Test 1: Flood wave speed uses M12 default when no geometry supplied
# ---------------------------------------------------------------------------

def test_flood_wave_speed_default():
    speed, method = _flood_wave_speed_kmh(None, None, None, None)
    assert speed == pytest.approx(M12_DEFAULT_WAVE_SPEED_KMH)
    assert method == "m12_default_21kmh"


# ---------------------------------------------------------------------------
# Test 2: Flood wave speed uses supplied value preferentially
# ---------------------------------------------------------------------------

def test_flood_wave_speed_supplied():
    speed, method = _flood_wave_speed_kmh(None, None, None, supplied_wave_speed_kmh=35.0)
    assert speed == pytest.approx(35.0)
    assert method == "supplied_from_m12"


# ---------------------------------------------------------------------------
# Test 3: Manning proxy gives physically reasonable speed
# ---------------------------------------------------------------------------

def test_manning_proxy_reasonable():
    # Large discharge, steep slope → faster
    speed, method = _flood_wave_speed_kmh(
        channel_slope_pct=5.0,
        peak_discharge_m3s=500.0,
        floodplain_width_m=80.0,
        supplied_wave_speed_kmh=None,
    )
    assert method == "manning_proxy"
    assert 5.0 < speed < 150.0, f"speed={speed} km/h out of physical range"


# ---------------------------------------------------------------------------
# Test 4: Landslide runout speed uses Hungr formula
# ---------------------------------------------------------------------------

def test_landslide_runout_speed_hungr():
    speed, method = _landslide_runout_speed_kmh(2.0, 30.0, None)
    assert method == "hungr_1995_empirical"
    # H = 2000 * sin(30°) = 1000m; V = 2.7*sqrt(1000)=85.4 m/s → 307 km/h
    # (steep; big H)
    assert speed > 0


# ---------------------------------------------------------------------------
# Test 5: P10 < P50 < P90 ordering
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("impact_type", [
    "FLOOD_INUNDATION", "LANDSLIDE_RUNOUT", "DAM_BREACH_OUTBURST", "DEBRIS_FLOW",
])
def test_quantile_ordering(impact_type):
    result = estimate_travel_time(
        impact_type=impact_type,
        distance_km=10.0,
        channel_slope_pct=3.0,
        peak_discharge_m3s=200.0,
        floodplain_width_m=60.0,
        slope_angle_deg=25.0,
    )
    assert result["p10_min"] <= result["p50_min"], (
        f"p10={result['p10_min']} > p50={result['p50_min']}"
    )
    assert result["p50_min"] <= result["p90_min"], (
        f"p50={result['p50_min']} > p90={result['p90_min']}"
    )


# ---------------------------------------------------------------------------
# Test 6: Longer distance → longer travel time
# ---------------------------------------------------------------------------

def test_distance_monotonicity():
    r5 = estimate_travel_time("FLOOD_INUNDATION", 5.0)
    r20 = estimate_travel_time("FLOOD_INUNDATION", 20.0)
    assert r20["p50_min"] > r5["p50_min"]


# ---------------------------------------------------------------------------
# Test 7: Higher soil saturation → faster arrival
# ---------------------------------------------------------------------------

def test_saturation_accelerates_travel():
    r_dry = estimate_travel_time("FLOOD_INUNDATION", 10.0, soil_saturation_ratio=0.1)
    r_wet = estimate_travel_time("FLOOD_INUNDATION", 10.0, soil_saturation_ratio=0.95)
    assert r_wet["p50_min"] <= r_dry["p50_min"]


# ---------------------------------------------------------------------------
# Test 8: Himalayan benchmark — physics within ±50% of observed
# ---------------------------------------------------------------------------

def test_himalayan_benchmark_pareechu():
    """Pareechu GLOF 2005: observed 1.4h at 30km."""
    result = estimate_travel_time(
        "DAM_BREACH_OUTBURST",
        distance_km=30.0,
        wave_speed_kmh=21.4,
    )
    observed_min = 1.4 * 60
    assert result["p10_min"] <= observed_min * 1.5
    assert result["p90_min"] >= observed_min * 0.5


# ---------------------------------------------------------------------------
# Test 9: Degraded input → DEGRADED_INPUT status
# ---------------------------------------------------------------------------

def test_predict_degraded_input():
    inp = M19TimeToImpactInput(
        impact_type=ImpactType.FLOOD_INUNDATION,
        distance_km=8.0,
        data_quality=0.1,  # critically low
    )
    out = predict(inp)
    assert out.status == TTIStatus.DEGRADED_INPUT


# ---------------------------------------------------------------------------
# Test 10: Full output contract
# ---------------------------------------------------------------------------

def test_predict_full_contract():
    inp = M19TimeToImpactInput(
        impact_type=ImpactType.FLOOD_INUNDATION,
        distance_km=15.0,
        wave_speed_kmh=21.0,
        peak_discharge_m3s=800.0,
        channel_slope_pct=4.0,
        floodplain_width_m=80.0,
        soil_saturation_ratio=0.7,
        data_quality=0.85,
    )
    out = predict(inp)
    assert out.model == "M19_TIME_TO_IMPACT"
    assert out.p10_minutes > 0
    assert out.p50_minutes > 0
    assert out.p90_minutes > 0
    assert 0.0 < out.confidence <= 1.0
    assert out.status == TTIStatus.PREDICTED
    assert out.method == TTIPredictionMethod.KINEMATIC_BASELINE


# ---------------------------------------------------------------------------
# Test 11: Himalayan benchmark report generates correctly
# ---------------------------------------------------------------------------

def test_physics_benchmark_report():
    report = generate_physics_benchmark_report()
    assert report["n_events"] == len(HIMALAYAN_BENCHMARKS)
    assert report["ml_validation_status"] == "INSUFFICIENT_EVIDENCE"
    for row in report["benchmark_events"]:
        assert "predicted_p50_h" in row
        assert row["error_pct"] >= 0
