"""
tests/test_analysis_pipeline.py
================================
Unit and integration tests for Multi-Source Feature Engineering & AI/ML Execution API.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_list_scenarios():
    """Verifies that all curated storm scenarios are returned with required parameters."""
    resp = client.get("/api/v1/analysis/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["total_scenarios"] >= 4
    scenario_ids = [s["scenario_id"] for s in data["scenarios"]]
    assert "JULY_2023_BEAS_CLOUDBURST" in scenario_ids
    assert "MONSOON_SURGE" in scenario_ids
    assert "MODERATE_MOUNTAIN_RAIN" in scenario_ids
    assert "DRY_BASELINE" in scenario_ids


def test_feature_engineering_scenario_mode():
    """Verifies feature extraction and USDA SCS-CN parameter engineering from scenario."""
    req = {
        "source_mode": "SCENARIO",
        "scenario_id": "JULY_2023_BEAS_CLOUDBURST",
    }
    resp = client.post("/api/v1/analysis/feature-engineering", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["source_mode"] == "SCENARIO"

    # Verify Landslide AI 5-D vector
    ls_vec = data["engineered_features"]["landslide_ai_vector"]
    assert ls_vec["susceptibility_class"] == 4
    assert ls_vec["slope_deg"] == 38.2
    assert ls_vec["rainfall_1h"] == 65.0
    assert ls_vec["antecedent_rain_3d"] == 185.0
    assert ls_vec["soil_moisture_pct"] == 88.5

    # Verify SCS-CN Hydrologic vector
    scs_vec = data["engineered_features"]["scs_cn_hydrologic_vector"]
    assert scs_vec["amc_condition"] == "AMC_III"
    assert scs_vec["effective_curve_number"] == 87.0
    assert scs_vec["direct_runoff_depth_mm"] > 25.0
    assert scs_vec["runoff_coefficient"] > 0.40

    # Verify DEM metrics
    dem_vec = data["engineered_features"]["topographic_dem_vector"]
    assert dem_vec["dem_resolution_m"] == 30.0
    assert dem_vec["catchment_area_km2"] == 3274.0


def test_feature_engineering_custom_mode():
    """Verifies feature engineering with custom sensor overrides."""
    req = {
        "source_mode": "CUSTOM",
        "rainfall_intensity_mmh": 20.0,
        "antecedent_rain_3d_mm": 25.0,
        "soil_moisture_pct": 35.0,
        "slope_deg": 22.0,
        "susceptibility_class": 1,
    }
    resp = client.post("/api/v1/analysis/feature-engineering", json=req)
    assert resp.status_code == 200
    data = resp.json()

    scs_vec = data["engineered_features"]["scs_cn_hydrologic_vector"]
    assert scs_vec["amc_condition"] == "AMC_I"
    assert scs_vec["effective_curve_number"] == 55.0


def test_run_models_through_features():
    """Verifies that decoupled ML/AI models run successfully through engineered features."""
    req = {
        "source_mode": "SCENARIO",
        "scenario_id": "JULY_2023_BEAS_CLOUDBURST",
        "run_flood_physics": True,
        "run_landslide_ai": True,
        "run_cascade_analysis": True,
        "run_hyperlocal_mapping": True,
    }
    resp = client.post("/api/v1/analysis/run-models", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

    outputs = data["model_outputs"]
    assert "flood_physics" in outputs
    assert "landslide_ai" in outputs
    assert "cascade_intelligence" in outputs
    assert "hyperlocal_impact" in outputs

    # Verify Flood Physics output
    fp = outputs["flood_physics"]
    assert fp["status"] in ["READY", "COMPLETED"]
    assert fp["payload"]["derived_hazard_tier"] == "CRITICAL"
    assert fp["payload"]["routing"]["peak_discharge_m3s"] > 1000.0

    # Verify Landslide AI output
    ls = outputs["landslide_ai"]
    assert ls["status"] in ["READY", "COMPLETED"]
    assert ls["payload"]["trigger_predicted"] is True
    assert ls["payload"]["trigger_probability"] > 0.80

    # Verify Hyperlocal Impact output
    hl = outputs["hyperlocal_impact"]
    assert hl["total_administrative_units"] == 12
    assert hl["total_exposed_population"] > 0


def test_live_pipeline_endpoint():
    """Verifies the GET /api/v1/analysis/live-pipeline endpoint."""
    resp = client.get("/api/v1/analysis/live-pipeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["source_mode"] == "LIVE"
    assert "flood_physics" in data["model_outputs"]
    assert "landslide_ai" in data["model_outputs"]
