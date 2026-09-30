"""
backend/tests/test_v37_operational_pilot.py
===========================================
Unit & Integration Test Suite for FLOODY SHIELD v3.7 Operational Pilot:
  1. Station Commissioning Lifecycle (PLANNED -> SURVEYED -> INSTALLED -> COMMISSIONED/ACTIVE)
  2. Strict Commissioning Verification Gate (5/5 checks required)
  3. Provenance & Environment Tagging & Filtering (REAL, SIMULATED, FIELD, TEST)
  4. Real-time Quality Control Gates (Flatline & Rate-of-Change Spike Detection)
  5. Telemetry & Hardware Health Summary Aggregation (24h, 72h, 7d windows)
"""

from __future__ import annotations

import datetime
from typing import Any, Dict
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.database.models.telemetry import SensorStationModel, SensorObservationModel


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


@pytest.fixture
def commander_token(client):
    """Creates an authenticated Senior Incident Commander JWT bearer header."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    username = f"cmdr_v37_{uid}"
    pwd = "CommanderPassword2026!"
    reg_payload = {
        "username": username,
        "email": f"{username}@hpsdma.gov.in",
        "password": pwd,
        "role": "SENIOR_INCIDENT_COMMANDER",
        "full_name": "Commander Kullu Pilot",
        "agency": "HPSDMA",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    login_res = client.post("/api/v1/auth/login", json={"username": username, "password": pwd})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_token(client):
    """Creates an authenticated Analyst JWT bearer header."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    username = f"analyst_v37_{uid}"
    pwd = "AnalystPassword2026!"
    reg_payload = {
        "username": username,
        "email": f"{username}@hpsdma.gov.in",
        "password": pwd,
        "role": "ANALYST",
        "full_name": "Analyst Solang",
        "agency": "HPSDMA",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    login_res = client.post("/api/v1/auth/login", json={"username": username, "password": pwd})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. STATION COMMISSIONING LIFECYCLE TESTS
# ============================================================================

def test_station_commissioning_lifecycle_full(client, commander_token, analyst_token):
    """Tests full station lifecycle from PLANNED through SURVEYED, INSTALLED, to ACTIVE."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    station_id = f"STN_PILOT_{uid}"

    # Step 1: Register station in PLANNED state
    create_payload = {
        "station_id": station_id,
        "name": f"Beas Pilot Station {uid}",
        "station_type": "MET_HYDRO_IOT",
        "latitude": 32.2500,
        "longitude": 77.1800,
        "elevation_m": 2100.0,
        "river_basin": "Upper Beas Basin",
        "status": "PLANNED",
    }
    res_reg = client.post("/api/v1/stations", json=create_payload, headers=analyst_token)
    assert res_reg.status_code == 200
    st_data = res_reg.json()["station"]
    assert st_data["status"] == "PLANNED"

    # Step 2: Record Survey
    survey_payload = {
        "surveyor_name": "Er. R. Sharma (HPSDMA)",
        "survey_notes": "Site has direct line of sight to Rohtang gateway. Solid bedrock anchor available.",
        "coordinates_verified": True,
        "elevation_m": 2105.5,
        "site_suitability_score": 94.5,
    }
    res_survey = client.post(f"/api/v1/stations/{station_id}/survey", json=survey_payload, headers=analyst_token)
    assert res_survey.status_code == 200
    assert res_survey.json()["status"] == "SURVEYED"
    assert res_survey.json()["station"]["elevation_m"] == 2105.5

    # Step 3: Record Installation
    install_payload = {
        "installer_name": "Kullu Sensor Ops Team",
        "hardware_manifest": {
            "solar_panel_watts": 50,
            "battery_ah": 24,
            "mast_height_m": 3.5,
            "sensors": ["TippingBucket_01", "RadarWaterLevel_01"],
        },
        "firmware_version": "v3.7.0-beta",
        "notes": "Installed securely with lightning arrester.",
    }
    res_install = client.post(f"/api/v1/stations/{station_id}/install", json=install_payload, headers=analyst_token)
    assert res_install.status_code == 200
    assert res_install.json()["status"] == "INSTALLED"

    # Step 4: Commissioning Gate Failure (incomplete checklist)
    incomplete_comm = {
        "commissioner_name": "Col. V. Pathania (EOC Commander)",
        "sensor_check": True,
        "calibration_check": True,
        "lora_check": False,  # Failing check
        "battery_check": True,
        "timestamp_check": True,
        "remarks": "LoRa link test failed on initial attempt.",
    }
    res_comm_fail = client.post(f"/api/v1/stations/{station_id}/commission", json=incomplete_comm, headers=commander_token)
    assert res_comm_fail.status_code == 400
    assert "lora_check" in res_comm_fail.json()["detail"]

    # Step 5: Successful Commissioning
    complete_comm = {
        "commissioner_name": "Col. V. Pathania (EOC Commander)",
        "sensor_check": True,
        "calibration_check": True,
        "lora_check": True,
        "battery_check": True,
        "timestamp_check": True,
        "remarks": "Antenna reoriented. SNR +8.5dB. Commissioning certified.",
    }
    res_comm_ok = client.post(f"/api/v1/stations/{station_id}/commission", json=complete_comm, headers=commander_token)
    assert res_comm_ok.status_code == 200
    comm_st = res_comm_ok.json()["station"]
    assert comm_st["status"] == "ACTIVE"
    assert comm_st["is_active"] is True
    assert comm_st["commissioned_by"] == "Col. V. Pathania (EOC Commander)"
    assert comm_st["commissioned_at"] is not None

    # Step 6: Query Commissioning Status
    res_query = client.get(f"/api/v1/stations/{station_id}/commissioning")
    assert res_query.status_code == 200
    q_data = res_query.json()
    assert q_data["station_id"] == station_id
    assert q_data["status"] == "ACTIVE"
    comm_data = q_data["commissioning_data"]
    assert comm_data["survey"]["surveyor_name"] == "Er. R. Sharma (HPSDMA)"
    assert comm_data["installation"]["installer_name"] == "Kullu Sensor Ops Team"
    assert comm_data["commissioning"]["verification_status"] == "PASSED"


# ============================================================================
# 2. PROVENANCE & ENVIRONMENT GATING TESTS
# ============================================================================

def test_telemetry_provenance_and_environment_filtering(client):
    """Tests provenance tagging on ingestion and retrieval filtering."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    station_id = f"STN_PROV_{uid}"
    now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Ingest REAL / FIELD observation
    real_pkt = {
        "source_id": "UPPER_BEAS_IOT",
        "station_id": station_id,
        "device_id": f"DEV_{uid}_01",
        "observed_at": now_ts,
        "measurement_type": "WATER_LEVEL",
        "value": 4.12,
        "unit": "m",
        "sequence_number": 1,
        "provenance": "REAL",
        "environment": "FIELD",
    }
    r_real = client.post("/api/v1/telemetry", json=real_pkt)
    assert r_real.status_code == 200
    assert r_real.json()["provenance"] == "REAL"
    assert r_real.json()["environment"] == "FIELD"

    # Ingest SIMULATED / TEST observation
    sim_pkt = {
        "source_id": "UPPER_BEAS_IOT",
        "station_id": station_id,
        "device_id": f"DEV_{uid}_01",
        "observed_at": now_ts,
        "measurement_type": "RAINFALL",
        "value": 12.5,
        "unit": "mm/h",
        "sequence_number": 2,
        "provenance": "SIMULATED",
        "environment": "TEST",
    }
    r_sim = client.post("/api/v1/telemetry", json=sim_pkt)
    assert r_sim.status_code == 200
    assert r_sim.json()["provenance"] == "SIMULATED"
    assert r_sim.json()["environment"] == "TEST"

    # Query filtered by provenance=REAL
    q_real = client.get(f"/api/v1/observations/timeseries?station_id={station_id}&provenance=REAL")
    assert q_real.status_code == 200
    data_real = q_real.json()["data"]
    assert len(data_real) == 1
    assert data_real[0]["provenance"] == "REAL"

    # Query filtered by provenance=SIMULATED
    q_sim = client.get(f"/api/v1/observations/timeseries?station_id={station_id}&provenance=SIMULATED")
    assert q_sim.status_code == 200
    data_sim = q_sim.json()["data"]
    assert len(data_sim) == 1
    assert data_sim[0]["provenance"] == "SIMULATED"


# ============================================================================
# 3. STREAM QUALITY CONTROL GATES (FLATLINE & SPIKE DETECTION)
# ============================================================================

def test_stream_qc_flatline_detection(client):
    """Verifies that 5+ repeated identical values trigger QC_FLATLINE flag and DEGRADED state."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    station_id = f"STN_FLAT_{uid}"
    base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=30)

    # Ingest 5 identical observations at 2-minute intervals
    for i in range(5):
        pkt = {
            "source_id": "UPPER_BEAS_IOT",
            "station_id": station_id,
            "device_id": f"DEV_{uid}_01",
            "observed_at": (base_time + datetime.timedelta(minutes=i * 2)).isoformat(),
            "measurement_type": "RAINFALL",
            "value": 18.5,  # Fixed non-zero stuck reading
            "unit": "mm/h",
            "sequence_number": i + 1,
            "provenance": "TEST",
        }
        res = client.post("/api/v1/telemetry", json=pkt)
        assert res.status_code == 200
        if i == 4:
            # 5th reading should trigger flatline detection
            assert "QC_FLATLINE" in (res.json().get("qc_flags") or "")
            assert res.json()["quality_state"] == "DEGRADED"


def test_stream_qc_rate_of_change_spike_detection(client):
    """Verifies sudden implausible jumps trigger QC_SPIKE flag and DEGRADED state."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    station_id = f"STN_SPIKE_{uid}"
    t0 = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
    t1 = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=4)

    # Normal river stage at t0
    p1 = {
        "source_id": "UPPER_BEAS_IOT",
        "station_id": station_id,
        "device_id": f"DEV_{uid}_01",
        "observed_at": t0.isoformat(),
        "measurement_type": "WATER_LEVEL",
        "value": 2.5,
        "unit": "m",
        "sequence_number": 1,
    }
    r1 = client.post("/api/v1/telemetry", json=p1)
    assert r1.status_code == 200

    # Implausible sudden surge (+6m in 1 minute) at t1
    p2 = {
        "source_id": "UPPER_BEAS_IOT",
        "station_id": station_id,
        "device_id": f"DEV_{uid}_01",
        "observed_at": t1.isoformat(),
        "measurement_type": "WATER_LEVEL",
        "value": 8.5,
        "unit": "m",
        "sequence_number": 2,
    }
    r2 = client.post("/api/v1/telemetry", json=p2)
    assert r2.status_code == 200
    assert "QC_SPIKE" in (r2.json().get("qc_flags") or "")
    assert r2.json()["quality_state"] == "DEGRADED"


# ============================================================================
# 4. TELEMETRY & HARDWARE HEALTH SUMMARY ENDPOINT
# ============================================================================

def test_telemetry_health_summary_endpoint(client):
    """Tests GET /api/v1/telemetry/health/summary across aggregation windows."""
    for window in ["24h", "72h", "7d", "30d"]:
        res = client.get(f"/api/v1/telemetry/health/summary?window={window}")
        assert res.status_code == 200
        data = res.json()
        assert data["window"] == window
        assert "total_stations" in data
        assert "active_stations" in data
        assert "packet_delivery_ratio" in data
        assert "provenance_breakdown" in data
        assert "health_distribution" in data
        assert isinstance(data["stations"], list)
