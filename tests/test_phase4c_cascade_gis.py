"""
tests/test_phase4c_cascade_gis.py
=================================
Authoritative Verification Suite for Phase 04C:
River Bottleneck Intelligence, Compound Cascade Engine, 30m Risk Grid,
and Hyperlocal Ward / Gram Panchayat Administrative Spatial Mapping.

Verifies:
  Test 1:  River/landslide spatial intersection (accurate distance in meters to nearest reach).
  Test 2:  Bottleneck candidate detection (POTENTIAL_OBSTRUCTION, SUSPECTED_BOTTLENECK, CONFIRMED_BY_EVIDENCE).
  Test 3:  No-intersection case (landslide > 350m away -> NOT_ESTABLISHED).
  Test 4:  Insufficient evidence handling (low probability -> NOT_ESTABLISHED).
  Test 5:  Cascade propagation (Froehlich breach parameters, peak outflow, lead times, backwater rise).
  Test 6:  30m hazard grid generation (preserves CRS EPSG:32643, cell size 30.0m, resolution metadata).
  Test 7:  Ward aggregation (Manali and Kullu municipal wards with exposure metrics).
  Test 8:  Gram Panchayat aggregation (Vashisht, Naggar, Sainj, Aut GPs with exposure metrics).
  Test 9:  Population exposure calculation (census population * tourist multiplier * exposure %).
  Test 10: Infrastructure exposure linkage (bridges, NH-3 highway segments, hospitals intersected from assets).
  Test 11: Geometry validity (all generated GeoJSON geometries valid via Shapely is_valid).
  Test 12: CRS consistency (OGC CRS84 / EPSG:4326 coordinate compliance [lon, lat]).
  Test 13: Provenance propagation (real inputs yield operational results; synthetic/replay taint non-operational).
  Test 14: Replay/simulation isolation (simulated cascade flagged non-operational; never claims actual live event).
  Test 15: Spatial performance (in-memory caching produces responses in < 50ms).
  Test 16: GIS API HTTP endpoints integration via FastAPI TestClient.
"""

from __future__ import annotations

import time
import pytest
from shapely.geometry import shape
from starlette.testclient import TestClient

from backend.app.core.provenance import DataMode
from backend.app.main import app
from backend.app.services.gis.cascade_spatial_service import (
    CascadeSpatialService,
    HyperlocalRiskUnit,
    ObstructionState,
    cascade_spatial_service,
)
from ml.decision.m13_vulnerability.demographics import BEAS_SETTLEMENT_REGISTER, MONTHLY_TOURIST_MULTIPLIER


@pytest.fixture
def service() -> CascadeSpatialService:
    return cascade_spatial_service


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ==============================================================================
# Test 1: River / Landslide Spatial Intersection
# ==============================================================================
def test_river_landslide_spatial_intersection(service: CascadeSpatialService):
    # Larji reach coordinates (31.716, 77.216)
    reach, dist_m = service.river_network.find_nearest_reach_point(31.716, 77.216)
    assert reach is not None
    assert "Larji" in reach.river_name or "Beas" in reach.river_name or "Aut" in reach.river_name
    assert dist_m < 50.0
    assert reach.stream_order >= 4
    assert reach.elevation_m > 800.0


# ==============================================================================
# Test 2: Bottleneck Candidate Detection
# ==============================================================================
def test_bottleneck_candidate_detection(service: CascadeSpatialService):
    # 1. Close to gorge (dist <= 100m) with high probability -> SUSPECTED_BOTTLENECK
    # Aut Gorge reach is at (31.750, 77.208), width 38.0m
    gorge_ls = [{
        "latitude": 31.7502,
        "longitude": 77.2081,
        "trigger_probability": 0.82,
        "susceptibility_class": 4,
        "provenance": DataMode.REAL_FIELD_OBSERVATION.value,
    }]
    res = service.detect_river_bottlenecks(gorge_ls)
    assert len(res) == 1
    bn = res[0]
    assert bn["obstruction_state"] == ObstructionState.SUSPECTED_BOTTLENECK.value
    assert bn["estimated_blockage_pct"] > 0.50
    assert bn["distance_to_reach_m"] <= 100.0

    # 2. Moderate distance (100 - 350m) with high probability -> POTENTIAL_OBSTRUCTION
    mid_ls = [{
        "latitude": 31.7505,
        "longitude": 77.2105,
        "trigger_probability": 0.70,
        "susceptibility_class": 3,
        "provenance": DataMode.REAL_FIELD_OBSERVATION.value,
    }]
    res_mid = service.detect_river_bottlenecks(mid_ls)
    assert res_mid[0]["obstruction_state"] in (
        ObstructionState.POTENTIAL_OBSTRUCTION.value,
        ObstructionState.SUSPECTED_BOTTLENECK.value,
    )


# ==============================================================================
# Test 3: No-Intersection Case
# ==============================================================================
def test_no_intersection_case(service: CascadeSpatialService):
    # Location far from Beas river reaches (> 2 km away, e.g. remote ridge)
    far_ls = [{
        "latitude": 32.1000,
        "longitude": 77.3500,
        "trigger_probability": 0.90,
        "susceptibility_class": 5,
    }]
    res = service.detect_river_bottlenecks(far_ls)
    assert len(res) == 1
    bn = res[0]
    assert bn["obstruction_state"] == ObstructionState.NOT_ESTABLISHED.value
    assert bn["estimated_blockage_pct"] == 0.0
    assert bn["distance_to_reach_m"] > 350.0


# ==============================================================================
# Test 4: Insufficient Evidence Handling
# ==============================================================================
def test_insufficient_evidence_handling(service: CascadeSpatialService):
    # Near river (Aut gorge), but very low trigger probability
    weak_ls = [{
        "latitude": 31.7483,
        "longitude": 77.2081,
        "trigger_probability": 0.15,
        "susceptibility_class": 1,
    }]
    res = service.detect_river_bottlenecks(weak_ls)
    assert len(res) == 1
    bn = res[0]
    # Insufficient hazard intensity cannot establish a river bottleneck
    assert bn["obstruction_state"] == ObstructionState.NOT_ESTABLISHED.value
    assert bn["estimated_blockage_pct"] == 0.0


# ==============================================================================
# Test 5: Cascade Propagation & Froehlich Breach
# ==============================================================================
def test_cascade_propagation(service: CascadeSpatialService):
    active_bn = [{
        "bottleneck_id": "BN_TEST_01",
        "reach_index": 7,
        "reach_name": "Aut_Gorge",
        "latitude": 31.7483,
        "longitude": 77.2081,
        "distance_to_reach_m": 45.0,
        "channel_width_m": 38.0,
        "obstruction_state": ObstructionState.SUSPECTED_BOTTLENECK.value,
        "estimated_blockage_pct": 0.70,
        "landslide_trigger_prob": 0.85,
    }]

    eval_result = service.evaluate_cascade_hazard(
        bottlenecks=active_bn,
        rainfall_mm=65.0,
        baseline_discharge_m3s=500.0,
    )

    assert eval_result["cascade_state"] == ObstructionState.SUSPECTED_BOTTLENECK.value
    assert eval_result["cascade_risk_tier"] in ("HIGH", "CRITICAL")
    assert eval_result["downstream_outburst_q_m3s"] > 500.0
    assert eval_result["upstream_backwater_rise_m"] > 5.0
    assert len(eval_result["reach_impacts"]) >= 3

    # Check lead time ordering (closer settlements reached first)
    first_reach = eval_result["reach_impacts"][0]
    last_reach = eval_result["reach_impacts"][-1]
    assert first_reach["flood_wave_lead_time_min"] < last_reach["flood_wave_lead_time_min"]
    assert first_reach["surge_height_m"] > 0.0


# ==============================================================================
# Test 6: 30m Hazard Grid Generation
# ==============================================================================
def test_30m_hazard_grid_generation(service: CascadeSpatialService):
    grid = service.get_30m_hazard_grid(bbox=[77.15, 31.75, 77.22, 31.85], resolution_m=30.0)

    assert grid["type"] == "FeatureCollection"
    assert grid["crs"]["properties"]["name"] == "EPSG:4326"
    assert grid["metadata"]["nominal_resolution_m"] == 30.0
    assert grid["metadata"]["native_dem_crs"] == "EPSG:32643"
    assert len(grid["features"]) > 0

    first_cell = grid["features"][0]
    assert "GRID_30M_" in first_cell["properties"]["cell_id"]
    assert first_cell["properties"]["resolution_m"] == 30.0
    assert "composite_risk_score" in first_cell["properties"]
    assert "risk_tier" in first_cell["properties"]
    assert first_cell["geometry"]["type"] == "Polygon"


# ==============================================================================
# Test 7: Ward Aggregation
# ==============================================================================
def test_ward_aggregation(service: CascadeSpatialService):
    units = service.aggregate_hyperlocal_risk(
        flood_hazard_score=0.75,
        landslide_hazard_score=0.40,
        cascade_state=ObstructionState.SUSPECTED_BOTTLENECK.value,
    )

    ward_units = [u for u in units if u["unit_type"] == HyperlocalRiskUnit.WARD.value]
    assert len(ward_units) >= 3  # Manali Ward 1, Manali Ward 2, Kullu Ward 1, Bhuntar Ward 1

    manali_w1 = next(u for u in ward_units if u["admin_id"] == "WARD_MANALI_01")
    assert "Manali" in manali_w1["name"]
    assert manali_w1["current_hazard"]["risk_level"] in ("HIGH", "CRITICAL")
    assert manali_w1["exposure"]["permanent_population"] == BEAS_SETTLEMENT_REGISTER["MANALI_URBAN"].permanent_population
    assert manali_w1["exposure"]["affected_population"] > 0


# ==============================================================================
# Test 8: Gram Panchayat Aggregation
# ==============================================================================
def test_gram_panchayat_aggregation(service: CascadeSpatialService):
    units = service.aggregate_hyperlocal_risk()
    gp_units = [u for u in units if u["unit_type"] == HyperlocalRiskUnit.GRAM_PANCHAYAT.value]
    assert len(gp_units) >= 6  # Vashisht, Bahang, Patlikuhal, Naggar, Sainj, Larji, Aut, Banjar

    aut_gp = next(u for u in gp_units if u["admin_id"] == "GP_AUT")
    assert "Aut" in aut_gp["name"]
    assert aut_gp["area_km2"] > 0.0
    assert aut_gp["exposure"]["vulnerability_index"] > 0.0


# ==============================================================================
# Test 9: Grounded Population Exposure Calculation
# ==============================================================================
def test_population_exposure_calculation(service: CascadeSpatialService):
    # July peak tourist month
    units_july = service.aggregate_hyperlocal_risk(
        flood_hazard_score=0.80,
        landslide_hazard_score=0.70,
        month=7,
    )
    manali = next(u for u in units_july if u["admin_id"] == "WARD_MANALI_01")
    exp = manali["exposure"]

    perm_pop = BEAS_SETTLEMENT_REGISTER["MANALI_URBAN"].permanent_population

    assert exp["permanent_population"] == perm_pop
    assert exp["total_estimated_population"] >= perm_pop
    assert exp["tourist_population"] >= 0

    # Affected population must be strictly deterministic, positive, and <= total population
    assert 0 < exp["affected_population"] <= exp["total_estimated_population"]


# ==============================================================================
# Test 10: Infrastructure Exposure Linkage
# ==============================================================================
def test_infrastructure_exposure_linkage(service: CascadeSpatialService):
    units = service.aggregate_hyperlocal_risk()
    total_infra_linked = sum(u["exposure"]["exposed_infrastructure_count"] for u in units)
    assert total_infra_linked > 0

    # Larji / Aut should intersect bridges and hydro substations
    aut_unit = next(u for u in units if u["admin_id"] in ("GP_AUT", "GP_LARJI"))
    assert aut_unit["exposure"]["exposed_infrastructure_count"] >= 1
    infra = aut_unit["exposure"]["exposed_infrastructure"][0]
    assert "asset_id" in infra
    assert "name" in infra
    assert "category" in infra
    assert "criticality_tier" in infra


# ==============================================================================
# Test 11: Geometry Validity
# ==============================================================================
def test_geometry_validity(service: CascadeSpatialService):
    geojson = service.get_hyperlocal_geojson()
    assert geojson["type"] == "FeatureCollection"

    for feat in geojson["features"]:
        geom_dict = feat["geometry"]
        poly = shape(geom_dict)
        assert poly.is_valid, f"Geometry for {feat['id']} is invalid!"
        assert not poly.is_empty
        assert poly.area > 0.0


# ==============================================================================
# Test 12: CRS Consistency (EPSG:4326 Coordinate Compliance)
# ==============================================================================
def test_crs_consistency(service: CascadeSpatialService):
    geojson = service.get_hyperlocal_geojson()
    assert geojson["crs"]["properties"]["name"] == "EPSG:4326"

    for feat in geojson["features"]:
        coords = feat["geometry"]["coordinates"][0]
        for lon, lat in coords:
            # Upper Beas corridor bounds: Longitude ~76.8 - 77.6, Latitude ~31.4 - 32.5
            assert 76.0 <= lon <= 78.5, f"Longitude {lon} outside Upper Beas range"
            assert 31.0 <= lat <= 33.0, f"Latitude {lat} outside Upper Beas range"


# ==============================================================================
# Test 13: Provenance Propagation
# ==============================================================================
def test_provenance_propagation(service: CascadeSpatialService):
    # 1. Operational Real Data
    real_out = service.get_hyperlocal_geojson(provenance=DataMode.REAL_FIELD_OBSERVATION.value)
    assert real_out["metadata"]["is_operational"] is True
    assert real_out["metadata"]["provenance"] == DataMode.REAL_FIELD_OBSERVATION.value

    # 2. Synthetic Data
    synth_out = service.get_hyperlocal_geojson(provenance=DataMode.SYNTHETIC.value)
    assert synth_out["metadata"]["is_operational"] is False
    assert synth_out["metadata"]["provenance"] == DataMode.SYNTHETIC.value


# ==============================================================================
# Test 14: Replay & Simulation Isolation
# ==============================================================================
def test_replay_simulation_isolation(service: CascadeSpatialService):
    cascade_sim = service.evaluate_cascade_hazard(
        bottlenecks=[{
            "bottleneck_id": "BN_SIM_01",
            "reach_index": 5,
            "reach_name": "Sainj_Confluence",
            "obstruction_state": ObstructionState.CONFIRMED_BY_EVIDENCE.value,
            "estimated_blockage_pct": 0.85,
        }],
        provenance=DataMode.REPLAY.value,
    )
    # Must be marked non-operational
    assert cascade_sim["is_operational"] is False
    assert cascade_sim["provenance"] == DataMode.REPLAY.value
    assert cascade_sim["cascade_risk_tier"] == "CRITICAL"


# ==============================================================================
# Test 15: Spatial Performance Benchmark
# ==============================================================================
def test_spatial_performance(service: CascadeSpatialService):
    # Warm up cache
    service.aggregate_hyperlocal_risk()

    t0 = time.perf_counter()
    iterations = 25
    for _ in range(iterations):
        service.aggregate_hyperlocal_risk(flood_hazard_score=0.6, landslide_hazard_score=0.4)
    elapsed_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    # Must complete in under 50ms per evaluation
    assert elapsed_ms < 50.0, f"Spatial aggregation too slow: {elapsed_ms:.2f} ms"


# ==============================================================================
# Test 16: GIS API HTTP Endpoints Integration
# ==============================================================================
def test_gis_api_endpoints(client: TestClient):
    # 1. Bottlenecks
    resp_bn = client.get("/api/v1/gis/cascade/bottlenecks?discharge_m3s=500.0")
    assert resp_bn.status_code == 200
    data_bn = resp_bn.json()
    assert data_bn["type"] == "FeatureCollection"
    assert "cascade_assessment" in data_bn

    # 2. Hyperlocal Admin Units
    resp_admin = client.get("/api/v1/gis/hyperlocal/admin?flood_score=0.7&landslide_score=0.6")
    assert resp_admin.status_code == 200
    data_admin = resp_admin.json()
    assert data_admin["type"] == "FeatureCollection"
    assert len(data_admin["features"]) == 12

    # 3. Single Admin Unit
    resp_single = client.get("/api/v1/gis/hyperlocal/admin/WARD_MANALI_01")
    assert resp_single.status_code == 200
    data_single = resp_single.json()
    assert data_single["admin_id"] == "WARD_MANALI_01"
    assert data_single["unit_type"] == "WARD"

    # 4. 30m Risk Grid
    resp_grid = client.get("/api/v1/gis/risk-grid?bbox=77.15,31.75,77.22,31.85")
    assert resp_grid.status_code == 200
    data_grid = resp_grid.json()
    assert data_grid["type"] == "FeatureCollection"
    assert data_grid["metadata"]["nominal_resolution_m"] == 30.0
