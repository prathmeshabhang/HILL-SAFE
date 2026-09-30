"""
backend/tests/test_model_adapters.py
====================================
Unit tests for the ModelAdapter layer, registry verification, and execution timing.
"""

from __future__ import annotations

import pytest

from backend.app.inference.registry import model_registry_service, FROZEN_ARTIFACT_HASHES
from backend.app.inference.adapters import get_model_adapter, ADAPTER_CLASSES


def test_model_registry_verification():
    """Ensures model registry is loaded and frozen artifact hashes are validated."""
    assert len(model_registry_service.registry_data) >= 4
    # Ensure all frozen models are verified
    assert "M2" in FROZEN_ARTIFACT_HASHES
    assert "M4" in FROZEN_ARTIFACT_HASHES
    assert "M6" in FROZEN_ARTIFACT_HASHES
    assert "M7" in FROZEN_ARTIFACT_HASHES


def test_m1_nowcast_adapter_execution():
    adapter = get_model_adapter("M1")
    assert adapter.model_id == "M1"
    res = adapter.predict({
        "station_id": "SYNTH_01",
        "latitude": 32.2,
        "longitude": 77.18,
        "elevation_m": 2000.0,
        "slope_deg": 20.0,
        "r_1h": 25.0,
        "r_3h": 50.0,
        "r_6h": 75.0,
        "rolling_intensity_mmh": 25.0,
    })
    assert res["model_id"] == "M1"
    assert "execution_time_ms" in res
    assert "input_hash" in res
    assert "prediction" in res["output"]


def test_m2_flood_risk_adapter_execution():
    adapter = get_model_adapter("M2")
    assert adapter.model_id == "M2"
    res = adapter.predict({
        "elevation": 900.0,
        "slope": 5.0,
        "flow_accumulation": 2000.0,
        "dist_to_stream": 80.0,
        "land_cover": 3,
        "rainfall_1h": 20.0,
        "rainfall_3h": 45.0,
        "rainfall_6h": 70.0,
        "rainfall_24h": 100.0,
        "antecedent_rain_3d": 80.0,
        "soil_moisture": 75.0,
        "river_level": 5.5,
        "river_level_change_1h": 0.2,
    })
    assert res["model_id"] == "M2"
    assert "flood_probability" in res["output"]
    assert "risk_tier" in res["output"]


def test_m6_susceptibility_adapter_execution():
    adapter = get_model_adapter("M6")
    assert adapter.model_id == "M6"
    res = adapter.predict({
        "elevation": 2200.0,
        "slope": 35.0,
        "aspect": 180.0,
        "curvature": -0.005,
        "lithology": 3,
        "dist_to_stream": 120.0,
        "land_cover": 2,
    })
    assert res["model_id"] == "M6"
    assert "susceptibility_tier" in res["output"]


def test_m7_trigger_adapter_execution():
    adapter = get_model_adapter("M7")
    assert adapter.model_id == "M7"
    res = adapter.predict({
        "susceptibility_class": 2,
        "slope": 38.0,
        "rainfall_1h": 25.0,
        "antecedent_rain_3d": 95.0,
        "soil_moisture": 82.0,
    })
    assert res["model_id"] == "M7"
    assert "trigger_predicted" in res["output"]


def test_pwp_slope_stability_adapter_execution():
    adapter = get_model_adapter("PWP_SSI")
    assert adapter.model_id == "PWP_SSI"
    res = adapter.predict({
        "slope_deg": 35.0,
        "depth_m": 2.0,
        "pore_pressure_kpa": 20.0,
    })
    assert res["model_id"] == "PWP_SSI"
    assert "factor_of_safety" in res["output"]
    assert "slope_stability_indicator" in res["output"]


def test_m16_evacuation_routing_adapter_execution():
    adapter = get_model_adapter("M16")
    assert adapter.model_id == "M16"
    res = adapter.predict({
        "origin_node": "V_BHUNTAR",
        "destination_node": "S_KULLU_COLLEGE",
        "simulate_nh3_closure": True,
    })
    assert res["model_id"] == "M16"
    assert "path_nodes" in res["output"]
    assert "total_distance_km" in res["output"]
    assert res["output"]["route_status"] in ("FOUND_SAFER_FEASIBLE", "UNREACHABLE_CUT_OFF")


def test_m17_warning_gating_adapter_execution():
    adapter = get_model_adapter("M17")
    assert adapter.model_id == "M17"
    res = adapter.predict({
        "reach_or_settlement_id": "REACH_TEST",
        "rainfall_intensity_mmh": 65.0,
        "flood_probability": 0.85,
        "river_water_level_m": 6.8,
        "warning_level_m": 5.0,
        "danger_level_m": 7.0,
        "hfl_m": 9.5,
    })
    assert res["model_id"] == "M17"
    assert "prediction" in res["output"]
