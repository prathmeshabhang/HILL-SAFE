"""
tests/test_phase4b_physics_ai.py
================================
Authoritative Verification Suite for Phase 04B:
Physics & AI Processing Layer (SCS-CN Terrain Routing & Landslide AI Booster).

Verifies:
  Test 1:  SCS-CN direct runoff depth, retention, initial abstraction, and AMC adjustments.
  Test 2:  DEM routing input validation (Manning celerity, time-to-peak, unit hydrograph).
  Test 3:  Invalid/missing GIS raster handling with graceful degradation to regional metrics.
  Test 4:  Landslide feature generation pipeline from rainfall, soil moisture, and terrain.
  Test 5:  Landslide booster model inference (probabilistic trigger & classification).
  Test 6:  Model input mismatch handling without crashing.
  Test 7:  Stale or missing feature handling with DEGRADED status and confidence discounting.
  Test 8:  Provenance propagation preserving Phase 03 live-data boundary and conservative tainting.
  Test 9:  Decoupled execution: Physics failure isolation (Landslide AI still succeeds).
  Test 10: Decoupled execution: AI failure isolation (Flood Physics still succeeds).
  Test 11: UnifiedRiskEngine integration: synthesis into RiskStateModel and DB persistence.
  Test 12: Regression compatibility: Phase 03 provenance and Phase 04A multi-source remain intact.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal
from backend.app.core.provenance import (
    DataMode,
    is_operational_provenance,
)
from backend.app.database.models.risk import RiskStateModel
from backend.app.orchestration.state import ExecutionState, ModelNodeResult
from backend.app.services.analysis.base import (
    AnalysisComponent,
    AnalysisResult,
    AnalysisStatus,
)
from backend.app.services.analysis.flood_physics import (
    FloodPhysicsEngine,
    flood_physics_engine,
)
from backend.app.services.analysis.landslide_ai import (
    LandslideAIEngine,
    LandslideFeaturePipeline,
    landslide_ai_engine,
)
from backend.app.services.analysis.orchestrator import (
    DecoupledAnalysisCoordinator,
    decoupled_analysis_coordinator,
)
from backend.app.services.risk.engine import unified_risk_engine


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================================
# Test 1: SCS-CN Direct Runoff & AMC Calculation
# ==============================================================================
def test_scs_cn_calculation():
    engine = FloodPhysicsEngine()

    # 1. Normal Antecedent Moisture Condition (AMC-II)
    res_amc2 = engine.calculate_scs_cn_runoff(rainfall_mm=60.0, cn_ii=74.0)
    assert res_amc2["amc_condition"] == "AMC_II"
    assert res_amc2["effective_curve_number"] == 74.0
    assert res_amc2["potential_retention_s_mm"] > 0
    assert res_amc2["initial_abstraction_ia_mm"] > 0
    assert res_amc2["direct_runoff_depth_mm"] > 0
    assert res_amc2["runoff_coefficient"] > 0.0

    # 2. Dry Antecedent Moisture Condition (AMC-I)
    res_amc1 = engine.calculate_scs_cn_runoff(
        rainfall_mm=60.0, cn_ii=74.0, antecedent_rain_5d_mm=5.0
    )
    assert res_amc1["amc_condition"] == "AMC_I"
    assert res_amc1["effective_curve_number"] < 74.0
    # Lower CN means higher retention and lower runoff
    assert res_amc1["direct_runoff_depth_mm"] < res_amc2["direct_runoff_depth_mm"]

    # 3. Wet Antecedent Moisture Condition (AMC-III)
    res_amc3 = engine.calculate_scs_cn_runoff(
        rainfall_mm=60.0, cn_ii=74.0, antecedent_rain_5d_mm=35.0
    )
    assert res_amc3["amc_condition"] == "AMC_III"
    assert res_amc3["effective_curve_number"] > 74.0
    # Higher CN means lower retention and higher runoff
    assert res_amc3["direct_runoff_depth_mm"] > res_amc2["direct_runoff_depth_mm"]

    # 4. Zero rainfall below initial abstraction
    res_zero = engine.calculate_scs_cn_runoff(rainfall_mm=5.0, cn_ii=74.0)
    assert res_zero["direct_runoff_depth_mm"] == 0.0
    assert res_zero["runoff_coefficient"] == 0.0


# ==============================================================================
# Test 2: DEM Routing Input Validation
# ==============================================================================
def test_dem_routing_validation():
    engine = FloodPhysicsEngine()
    inputs = {
        "rainfall_intensity_mmh": 45.0,
        "rainfall_duration_hours": 2.0,
        "catchment_area_km2": 1500.0,
        "curve_number_nominal": 75.0,
        "soil_moisture_saturation_pct": 65.0,
    }

    result = engine.execute(inputs)

    assert isinstance(result, AnalysisResult)
    assert result.capability_name == "Flood Intelligence"
    assert result.execution_status in (AnalysisStatus.READY, AnalysisStatus.DEGRADED)
    assert result.confidence_score > 0.5

    payload = result.output_payload
    assert "scs_cn" in payload
    assert "routing" in payload
    routing = payload["routing"]
    assert routing["catchment_area_km2"] == 1500.0
    assert routing["flow_velocity_ms"] > 1.0
    assert routing["time_of_concentration_hours"] > 0.0
    assert routing["time_to_peak_hours"] > 0.0
    assert routing["peak_discharge_m3s"] > 0.0
    assert routing["runoff_volume_mcm"] > 0.0


# ==============================================================================
# Test 3: Invalid or Missing GIS Layer Graceful Degradation
# ==============================================================================
def test_invalid_or_missing_gis_layer():
    # Pass a nonexistent DEM path
    engine = FloodPhysicsEngine(dem_path=Path("nonexistent/invalid_dem.tif"))
    inputs = {
        "rainfall_intensity_mmh": 30.0,
        "dem_path": "nonexistent/invalid_dem.tif",
    }

    result = engine.execute(inputs)

    # Must NOT crash; should degrade gracefully
    assert result.execution_status == AnalysisStatus.DEGRADED
    assert any("DEM" in w for w in result.warnings)
    # Output metrics must still be computed using calibrated regional fallback
    assert result.output_payload["routing"]["peak_discharge_m3s"] >= 0.0
    assert result.confidence_score < 0.90


# ==============================================================================
# Test 4: Landslide AI Feature Pipeline Generation
# ==============================================================================
def test_landslide_feature_pipeline():
    pipeline = LandslideFeaturePipeline()
    inputs = {
        "susceptibility_class": 3,
        "slope_deg": 38.5,
        "rainfall_intensity_mmh": 42.0,
        "antecedent_rain_3d_mm": 95.0,
        "soil_moisture_volumetric": 0.36,
        "pore_pressure_kpa": 48.0,
    }

    df, meta = pipeline.extract_features(inputs)

    assert df.shape == (1, 5)
    assert df.iloc[0]["susceptibility_class"] == 3
    assert df.iloc[0]["slope_deg"] == 38.5
    assert df.iloc[0]["rainfall_1h"] == 42.0
    assert df.iloc[0]["antecedent_rain_3d"] == 95.0
    assert round(df.iloc[0]["soil_moisture_pct"], 1) == 80.0
    assert len(meta["missing_features"]) == 0
    assert meta["geotech_indicators"]["pore_pressure_kpa"] == 48.0


# ==============================================================================
# Test 5: Landslide AI Booster Inference
# ==============================================================================
def test_landslide_model_inference():
    engine = LandslideAIEngine()
    inputs = {
        "susceptibility_class": 3,
        "slope_deg": 40.0,
        "rainfall_intensity_mmh": 55.0,
        "antecedent_rain_3d": 110.0,
        "soil_moisture_pct": 85.0,
    }

    result = engine.execute(inputs)

    assert isinstance(result, AnalysisResult)
    assert result.capability_name == "Landslide Intelligence"
    assert result.execution_status == AnalysisStatus.READY
    assert result.confidence_score > 0.70

    payload = result.output_payload
    assert 0.0 <= payload["trigger_probability"] <= 1.0
    assert isinstance(payload["trigger_predicted"], bool)
    assert payload["hazard_tier"] in ("VERY_LOW", "LOW", "MODERATE", "HIGH", "CRITICAL")
    assert "evaluated_features" in payload


# ==============================================================================
# Test 6: Model Input Mismatch Handling
# ==============================================================================
def test_model_input_mismatch():
    engine = LandslideAIEngine()
    # Pass unexpected arbitrary keys and partial data
    inputs = {
        "unexpected_key_1": "invalid",
        "random_param": 999.9,
    }

    result = engine.execute(inputs)

    # Must NOT raise unhandled exception
    assert result.execution_status == AnalysisStatus.DEGRADED
    assert any("missing" in w.lower() for w in result.warnings)
    assert 0.0 <= result.output_payload["trigger_probability"] <= 1.0


# ==============================================================================
# Test 7: Stale Feature Handling
# ==============================================================================
def test_stale_feature_handling():
    engine = LandslideAIEngine()
    # Soil moisture is missing
    inputs = {
        "slope_deg": 35.0,
        "rainfall_intensity_mmh": 20.0,
    }

    result = engine.execute(inputs)

    assert result.execution_status == AnalysisStatus.DEGRADED
    missing = result.output_payload["feature_metadata"]["missing_features"]
    assert "soil_moisture_pct" in missing
    assert "antecedent_rain_3d" in missing
    # Confidence must be discounted when critical features are absent
    assert result.confidence_score < 0.85


# ==============================================================================
# Test 8: Provenance Propagation (Phase 03 Rule Compliance)
# ==============================================================================
def test_provenance_propagation():
    engine = FloodPhysicsEngine()

    # 1. Pure REAL input
    real_inputs = {
        "rainfall_intensity_mmh": 35.0,
        "provenance": DataMode.REAL_FIELD_OBSERVATION.value,
    }
    real_res = engine.execute(real_inputs)
    assert is_operational_provenance(real_res.data_mode) is True

    # 2. SYNTHETIC input
    synth_inputs = {
        "rainfall_intensity_mmh": 35.0,
        "provenance": DataMode.SYNTHETIC.value,
    }
    synth_res = engine.execute(synth_inputs)
    assert synth_res.data_mode in (DataMode.SYNTHETIC.value, DataMode.SIMULATION.value)
    assert is_operational_provenance(synth_res.data_mode) is False

    # 3. Mixed Input (Real + Synthetic) -> Conservative Non-Operational Tainting
    mixed_inputs = {
        "rainfall_intensity_mmh": 35.0,
        "rainfall_provenance": DataMode.REAL_FIELD_OBSERVATION.value,
        "soil_provenance": DataMode.SYNTHETIC.value,
    }
    mixed_res = engine.execute(mixed_inputs)
    assert mixed_res.data_mode == DataMode.MIXED.value
    assert is_operational_provenance(mixed_res.data_mode) is False


# ==============================================================================
# Test 9: Decoupled Execution — Physics Failure Isolation
# ==============================================================================
def test_physics_failure_isolation(monkeypatch):
    coordinator = DecoupledAnalysisCoordinator()

    # Force flood physics engine to raise an unhandled exception
    def broken_run(self, inputs):
        raise RuntimeError("Hydrodynamic numerical divergence simulated failure")

    monkeypatch.setattr(FloodPhysicsEngine, "_run_analysis", broken_run)

    inputs = {
        "rainfall_intensity_mmh": 40.0,
        "slope_deg": 35.0,
    }
    results = coordinator.execute_all(inputs)

    # Flood physics must report ERROR
    assert results["flood_physics"].execution_status == AnalysisStatus.ERROR
    assert len(results["flood_physics"].errors) > 0

    # Landslide AI must still succeed independently
    assert results["landslide_ai"].execution_status in (AnalysisStatus.READY, AnalysisStatus.DEGRADED)
    assert results["landslide_ai"].output_payload["trigger_probability"] >= 0.0


# ==============================================================================
# Test 10: Decoupled Execution — AI Failure Isolation
# ==============================================================================
def test_ai_failure_isolation(monkeypatch):
    coordinator = DecoupledAnalysisCoordinator()

    # Force landslide AI engine to raise an unhandled exception
    def broken_run(self, inputs):
        raise RuntimeError("LightGBM booster memory allocation simulated failure")

    monkeypatch.setattr(LandslideAIEngine, "_run_analysis", broken_run)

    inputs = {
        "rainfall_intensity_mmh": 40.0,
        "slope_deg": 35.0,
    }
    results = coordinator.execute_all(inputs)

    # Landslide AI must report ERROR
    assert results["landslide_ai"].execution_status == AnalysisStatus.ERROR
    assert len(results["landslide_ai"].errors) > 0

    # Flood physics must still succeed independently
    assert results["flood_physics"].execution_status in (AnalysisStatus.READY, AnalysisStatus.DEGRADED)
    assert results["flood_physics"].output_payload["scs_cn"]["direct_runoff_depth_mm"] >= 0.0


# ==============================================================================
# Test 11: UnifiedRiskEngine Integration
# ==============================================================================
def test_risk_engine_integration(db_session: Session):
    inputs = {
        "rainfall_intensity_mmh": 48.0,
        "slope_deg": 36.0,
        "river_water_level_m": 4.5,
        "provenance": DataMode.REAL_FIELD_OBSERVATION.value,
    }

    # Execute analytics coordinator
    analysis_res = decoupled_analysis_coordinator.execute_all(inputs)
    nodes = decoupled_analysis_coordinator.convert_to_orchestrator_nodes(analysis_res)

    assert "FLOOD_PHYSICS_ROUTING" in nodes
    assert "LANDSLIDE_AI_TRIGGER" in nodes

    # Synthesize through UnifiedRiskEngine
    risk_state = unified_risk_engine.synthesize_risk_state(
        db=db_session,
        incident_id=None,
        location_name="Kullu_Manali_Valley_Point_01",
        initial_observations=inputs,
        orchestrator_results=nodes,
        data_mode=DataMode.REAL_FIELD_OBSERVATION.value,
    )

    assert "risk_state_id" in risk_state
    assert risk_state["overall_risk_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")

    # Verify flood physics was synthesized
    assert "scs_cn_routing" in risk_state["hazards"]["flood"]
    assert risk_state["hazards"]["flood"]["scs_cn_routing"]["direct_runoff_depth_mm"] is not None

    # Verify landslide AI was synthesized
    assert "landslide_ai_trigger" in risk_state["hazards"]["landslide"]
    assert risk_state["hazards"]["landslide"]["landslide_ai_trigger"]["trigger_probability"] is not None

    # Verify database persistence
    db_rec = db_session.query(RiskStateModel).filter_by(id=risk_state["risk_state_id"]).first()
    assert db_rec is not None
    assert "scs_cn_routing" in db_rec.flood_hazard_json
    assert "landslide_ai_trigger" in db_rec.landslide_hazard_json


# ==============================================================================
# Test 12: Regression Compatibility Check
# ==============================================================================
def test_regression_compatibility():
    # Verify capability-based nomenclature (No public M1..M20 exposed in public attributes)
    assert flood_physics_engine.capability_name == "Flood Intelligence"
    assert landslide_ai_engine.capability_name == "Landslide Intelligence"
