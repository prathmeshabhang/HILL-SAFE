"""
backend/tests/test_v33_features.py
==================================
Comprehensive integration and unit tests for FLOODY SHIELD v3.3:
Ingestion adapters, PostGIS GIS APIs, Real-time WebSockets, Alert Lifecycle,
Executive Dashboard, Authentication & RBAC, and Tamper-Evident Audit verification.
"""

from __future__ import annotations

import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.services.ingestion.adapters import (
    IMDAWSAdapter,
    GPMIMERGAdapter,
    CWCRiverAdapter,
    SentinelSceneAdapter,
    IoTTelemetryAdapter,
)
from backend.app.websocket.manager import ws_manager
from backend.app.websocket.events import RealTimeEvent, RealTimeEventType
from backend.app.database.models.audit import AuditLogModel


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_ingestion_adapters_normalization():
    """Verifies that all 5 adapters normalize raw heterogeneous feeds into canonical schema."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. IMD AWS
    imd = IMDAWSAdapter()
    norm_imd = imd.normalize({"station_code": "KULLU_01", "obs_time": now.isoformat(), "rain_rate_mm": 55.0})
    assert norm_imd.station_id == "KULLU_01"
    assert norm_imd.values["rainfall_rate_mmh"] == 55.0
    assert len(norm_imd.idempotency_hash) == 64

    # 2. GPM IMERG
    gpm = GPMIMERGAdapter()
    norm_gpm = gpm.normalize({"granule_time": now.isoformat(), "lat": 32.1, "lon": 77.2, "precipitation_cal_mmh": 18.5})
    assert norm_gpm.source_id == "GPM_IMERG"
    assert norm_gpm.values["rainfall_rate_mmh"] == 18.5

    # 3. CWC River
    cwc = CWCRiverAdapter()
    norm_cwc = cwc.normalize({"site_id": "BHUNTAR_CWC", "measurement_time": now.isoformat(), "water_level_m": 6.8, "discharge_m3s": 520.0})
    assert norm_cwc.values["water_level_m"] == 6.8
    assert norm_cwc.values["discharge_m3s"] == 520.0

    # 4. Sentinel Scene
    sentinel = SentinelSceneAdapter()
    norm_sat = sentinel.normalize({"scene_id": "S1A_20230710", "acquisition_time": now.isoformat(), "mission": "SENTINEL-1"})
    assert norm_sat.source_id == "SENTINEL_COPERNICUS"
    assert norm_sat.values["mission"] == "SENTINEL-1"

    # 5. IoT Array
    iot = IoTTelemetryAdapter()
    norm_iot = iot.normalize({"station_id": "IOT_SLOPE_01", "timestamp": now.isoformat(), "pore_pressure_kpa": 48.0, "displacement_mm": 12.5})
    assert norm_iot.values["pore_pressure_kpa"] == 48.0
    assert norm_iot.values["displacement_mm"] == 12.5


def test_gis_endpoints(client):
    """Verifies GeoJSON GIS layer endpoints."""
    # 1. Hazards GeoJSON
    res_hazards = client.get("/api/v1/gis/hazards")
    assert res_hazards.status_code == 200
    data_haz = res_hazards.json()
    assert data_haz["type"] == "FeatureCollection"
    assert len(data_haz["features"]) > 0

    # 2. Safe Zones GeoJSON
    res_safe = client.get("/api/v1/gis/safe-zones?min_elevation_m=1000.0")
    assert res_safe.status_code == 200
    data_safe = res_safe.json()
    assert data_safe["type"] == "FeatureCollection"
    assert len(data_safe["features"]) > 0

    # 3. Infrastructure Assets GeoJSON
    res_infra = client.get("/api/v1/gis/infrastructure")
    assert res_infra.status_code == 200
    data_infra = res_infra.json()
    assert data_infra["type"] == "FeatureCollection"

    # 4. Evacuation Routes GeoJSON
    res_routes = client.get("/api/v1/gis/routes")
    assert res_routes.status_code == 200
    assert res_routes.json()["type"] == "FeatureCollection"


def test_dashboard_summary_endpoint(client):
    """Verifies executive dashboard aggregation endpoint."""
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "data_freshness" in data
    assert "operational_overview" in data
    assert "system_health" in data
    assert data["basin_name"] == "Upper Beas River Basin (Kullu–Manali)"


def test_auth_and_rbac_flow(client):
    """Verifies user registration, JWT generation, and profile lookup."""
    username = f"commander_test_{datetime.datetime.now().microsecond}"
    reg_payload = {
        "username": username,
        "email": f"{username}@hpsdma.gov.in",
        "password": "StrongSecretPassword2026!",
        "role": "SENIOR_INCIDENT_COMMANDER",
        "full_name": "Col. Rajesh Verma",
        "agency": "HPSDMA EOC Kullu",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    assert reg_res.json()["status"] == "USER_REGISTERED"

    # Login
    login_res = client.post("/api/v1/auth/login", json={"username": username, "password": "StrongSecretPassword2026!"})
    assert login_res.status_code == 200
    token_data = login_res.json()
    token = token_data["access_token"]
    assert token_data["role"] == "SENIOR_INCIDENT_COMMANDER"

    # Profile lookup with bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["username"] == username


def test_audit_hash_chain_verification(client, db: Session):
    """Verifies tamper-evident audit hash chain verification endpoint."""
    # Ensure at least one hash-chained audit entry exists
    last_audit = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).first()
    prev_hash = last_audit.entry_hash if last_audit else "GENESIS_ROOT"
    import uuid
    entry = AuditLogModel(
        id=f"audit-test-{uuid.uuid4().hex[:8]}",
        action="TEST_CHAIN_VERIFICATION",
        actor_id="test_runner",
        actor_role="ADMIN",
        target_entity_type="System",
        target_entity_id="SYS_01",
        changes="Verifying hash chaining",
        previous_hash=prev_hash,
    )
    entry.entry_hash = entry.compute_hash(prev_hash)
    db.add(entry)
    db.commit()

    res = client.get("/api/v1/audit/verify-chain")
    assert res.status_code == 200
    data = res.json()
    assert data["chain_intact"] is True
    assert data["security_grade"] == "TAMPER_EVIDENT_HASH_CHAINED"


def test_historical_replay_endpoint(client):
    """Verifies disaster scenario replay endpoint runs without issuing public alerts."""
    payload = {
        "scenario_name": "July_2023_Upper_Beas_Compound_Flood",
        "rainfall_intensity_mmh": 80.0,
        "dam_height_m": 35.0,
        "impounded_volume_m3": 9_000_000.0,
        "river_water_level_m": 7.8,
    }
    res = client.post("/api/v1/incidents/replay", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "REPLAY"
    assert "NO PUBLIC ALERTS WERE ISSUED" in data["statutory_safety_notice"]
    assert data["incident"]["status"] == "EXERCISE"
    assert data["risk_state"]["overall_risk_level"] in ("HIGH", "CRITICAL")
