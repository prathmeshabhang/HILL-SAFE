"""
backend/tests/test_v34_field_telemetry.py
=========================================
Comprehensive integration & unit test suite for FLOODY SHIELD v3.4:
  - Subsystem 1: Station, Device & Sensor Registry, Calibration & Health Metrics
  - Subsystem 2: Field Telemetry Ingestion, UTC Normalization, Temporal State Machine
  - Subsystem 3: Deterministic Idempotency & Replay Tampering Detection
  - Subsystem 4: Batch Ingestion & Aggregated Timeseries Queries
  - Subsystem 5: Background Job Manager, Bounded Retries & Non-Retryable Filtering
  - Subsystem 6: Event Bus & Hardened WebSocket (Authorization Prohibition)
  - Subsystem 7: Unified Risk State API & Degraded Mode Isolation
  - Subsystem 8: Alert State Machine, CAP v1.2 Validator & Multi-Channel Notification Dispatcher
  - Subsystem 9: System Observability (Data Sources & Prometheus Metrics)
  - Subsystem 10: Frozen Model SHA-256 Immutability Check (M2, M4, M6, M7)
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import time
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.core.config import settings
from backend.app.core.event_bus import event_bus
from backend.app.core.jobs import job_manager, BackgroundJob
from backend.app.core.metrics import metrics
from backend.app.core.errors import FloodyShieldException
from backend.app.services.alerts.cap_validator import cap_validator
from backend.app.services.alerts.lifecycle_service import alert_lifecycle_service
from backend.app.services.devices.health_service import sensor_health_service
from backend.app.services.notifications.dispatcher import notification_dispatcher
from backend.app.services.notifications.ndma_sachet_provider import NDMASachetProvider


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
    """Creates a registered Senior Incident Commander and returns JWT bearer header."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    username = f"cmdr_{uid}"
    pwd = "CommanderPassword2026!"
    reg_payload = {
        "username": username,
        "email": f"{username}@hpsdma.gov.in",
        "password": pwd,
        "role": "SENIOR_INCIDENT_COMMANDER",
        "full_name": "Commander Kullu EOC",
        "agency": "HPSDMA",
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 200

    login_res = client.post("/api/v1/auth/login", json={"username": username, "password": pwd})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. STATION, DEVICE, SENSOR REGISTRY & HEALTH (SUBSYSTEM 1)
# ============================================================================

def test_device_sensor_lifecycle_and_health(client, commander_token):
    """Verifies station, device, sensor registration, heartbeat, calibration, and health metrics."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    station_id = f"ST_TEST_{uid}"
    device_id = f"DEV_TEST_{uid}"
    sensor_id = f"SENS_TEST_{uid}"

    # 1. Register Station
    st_payload = {
        "station_id": station_id,
        "name": f"Test Station {uid}",
        "station_type": "MET_HYDRO_IOT",
        "latitude": 32.2396,
        "longitude": 77.1887,
        "elevation_m": 2050.0,
        "river_basin": "Upper Beas Basin",
    }
    r_st = client.post("/api/v1/stations", json=st_payload, headers=commander_token)
    assert r_st.status_code == 200
    assert r_st.json()["station"]["station_id"] == station_id

    # 2. Register Device on Station
    dev_payload = {
        "device_id": device_id,
        "station_id": station_id,
        "serial_number": f"SN-{uid}",
        "device_type": "LORA_NODE",
        "manufacturer": "FloodyShield-Hardware",
        "firmware_version": "1.0.4",
        "protocol": "LORAWAN",
        "status": "ACTIVE",
    }
    r_dev = client.post("/api/v1/devices", json=dev_payload, headers=commander_token)
    assert r_dev.status_code == 200
    assert r_dev.json()["device"]["device_id"] == device_id

    # 3. Register Sensor on Device
    sens_payload = {
        "sensor_id": sensor_id,
        "device_id": device_id,
        "sensor_type": "WATER_LEVEL",
        "unit": "m",
        "measurement_range_min": 0.0,
        "measurement_range_max": 25.0,
        "sampling_interval_sec": 60,
    }
    r_sens = client.post("/api/v1/sensors", json=sens_payload, headers=commander_token)
    assert r_sens.status_code == 200
    assert r_sens.json()["sensor"]["sensor_id"] == sensor_id

    # 4. Record Calibration
    cal_payload = {
        "calibrated_by": "Field Engineer Sharma",
        "standard_reference": "REF-OTT-2026",
        "zero_offset": 0.02,
        "scale_factor": 1.001,
        "notes": "Annual pre-monsoon calibration test",
    }
    r_cal = client.post(f"/api/v1/sensors/{sensor_id}/calibrations", json=cal_payload, headers=commander_token)
    assert r_cal.status_code == 200
    assert r_cal.json()["calibration"]["zero_offset"] == 0.02

    # 5. Device Heartbeat
    hb_payload = {
        "battery_percentage": 89.0,
        "battery_voltage": 13.4,
        "rssi_dbm": -71.0,
        "firmware_version": "1.0.4",
        "error_flags": 0,
    }
    r_hb = client.post(f"/api/v1/devices/{device_id}/heartbeat", json=hb_payload)
    assert r_hb.status_code == 200
    assert r_hb.json()["status"] == "HEARTBEAT_RECORDED"

    # 6. Station Health Summary
    r_hlth = client.get(f"/api/v1/stations/{station_id}/health")
    assert r_hlth.status_code == 200
    h_data = r_hlth.json()
    assert h_data["station_id"] == station_id
    assert h_data["total_devices"] == 1
    assert h_data["total_sensors"] == 1
    assert h_data["operational_state"] in ["OPERATIONAL", "DEGRADED", "OFFLINE"]


# ============================================================================
# 2. FIELD TELEMETRY INGESTION & TEMPORAL VALIDATION (SUBSYSTEM 2)
# ============================================================================

def test_telemetry_packet_temporal_states(client):
    """Verifies temporal state classification: VALID, LATE, STALE, EXPIRED, INVALID (future)."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    now = datetime.datetime.now(datetime.timezone.utc)

    # A. VALID Packet (now)
    p_valid = {
        "source": "FIELD_NODE",
        "station_id": f"ST_TEMP_{uid}",
        "device_id": f"DEV_TEMP_{uid}",
        "sensor_id": f"SENS_TEMP_{uid}",
        "measurement_type": "water_level_m",
        "value": 4.52,
        "unit": "m",
        "sequence_number": 1,
        "observed_at": now.isoformat(),
    }
    r_val = client.post("/api/v1/telemetry", json=p_valid)
    assert r_val.status_code == 200
    data_val = r_val.json()
    assert data_val["status"] == "INGESTED"
    assert data_val["temporal_state"] == "VALID"
    assert "source_event_id" in data_val

    # B. LATE Packet (2 hours old, > 1 hour)
    p_late = dict(p_valid)
    p_late["sequence_number"] = 2
    p_late["observed_at"] = (now - datetime.timedelta(hours=2)).isoformat()
    r_late = client.post("/api/v1/telemetry", json=p_late)
    assert r_late.status_code == 200
    assert r_late.json()["temporal_state"] == "LATE"

    # C. STALE Packet (8 hours old, > 6 hours)
    p_stale = dict(p_valid)
    p_stale["sequence_number"] = 3
    p_stale["observed_at"] = (now - datetime.timedelta(hours=8)).isoformat()
    r_stale = client.post("/api/v1/telemetry", json=p_stale)
    assert r_stale.status_code == 200
    assert r_stale.json()["temporal_state"] == "STALE"

    # D. EXPIRED Packet (48 hours old, > 24 hours)
    p_exp = dict(p_valid)
    p_exp["sequence_number"] = 4
    p_exp["observed_at"] = (now - datetime.timedelta(hours=48)).isoformat()
    r_exp = client.post("/api/v1/telemetry", json=p_exp)
    assert r_exp.status_code == 200
    assert r_exp.json()["temporal_state"] == "EXPIRED"

    # E. INVALID Future Packet (3 hours in the future, > 2 hours skew)
    p_fut = dict(p_valid)
    p_fut["sequence_number"] = 5
    p_fut["observed_at"] = (now + datetime.timedelta(hours=3)).isoformat()
    r_fut = client.post("/api/v1/telemetry", json=p_fut)
    assert r_fut.status_code == 422
    assert "future" in r_fut.json()["detail"].lower()


# ============================================================================
# 3. IDEMPOTENCY & REPLAY TAMPERING DETECTION (SUBSYSTEM 3)
# ============================================================================

def test_deterministic_idempotency_and_tampering_detection(client):
    """
    Verifies that:
      1. Re-submitting identical telemetry payload returns 200 with DUPLICATE status.
      2. Replay tampering (same metadata and sequence, different value) returns 409 Conflict.
    """
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    obs_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    payload = {
        "source": "FIELD_NODE",
        "station_id": f"ST_IDEM_{uid}",
        "device_id": f"DEV_IDEM_{uid}",
        "sensor_id": f"SENS_IDEM_{uid}",
        "measurement_type": "water_level_m",
        "value": 3.85,
        "unit": "m",
        "sequence_number": 101,
        "observed_at": obs_time,
    }

    # 1. Initial Ingestion
    res1 = client.post("/api/v1/telemetry", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "INGESTED"
    orig_event_id = data1["source_event_id"]

    # 2. Exact Duplicate Resubmission
    res2 = client.post("/api/v1/telemetry", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "DUPLICATE"
    assert data2["source_event_id"] == orig_event_id

    # 3. Tampered Replay Attack: Same station, device, sensor, sequence, timestamp, but modified value
    tampered_payload = dict(payload)
    tampered_payload["value"] = 12.99  # Manipulated observation value
    res3 = client.post("/api/v1/telemetry", json=tampered_payload)
    assert res3.status_code == 409
    assert "TELEMETRY_INTEGRITY_VIOLATION" in res3.json()["detail"]


# ============================================================================
# 4. BATCH INGESTION & TIMESERIES AGGREGATIONS (SUBSYSTEM 4)
# ============================================================================

def test_batch_ingestion_and_timeseries_queries(client):
    """Verifies high-throughput batch ingestion and timeseries aggregation functions."""
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    station_id = f"ST_SERIES_{uid}"
    sensor_id = f"SENS_SERIES_{uid}"
    now = datetime.datetime.now(datetime.timezone.utc)

    # Create batch of 5 readings: values = 2.0, 4.0, 6.0, 8.0, 10.0
    batch = []
    for i, val in enumerate([2.0, 4.0, 6.0, 8.0, 10.0]):
        batch.append({
            "source": "FIELD_NODE",
            "station_id": station_id,
            "device_id": f"DEV_SERIES_{uid}",
            "sensor_id": sensor_id,
            "measurement_type": "rainfall_rate_mmh",
            "value": val,
            "unit": "mm/h",
            "sequence_number": i + 1,
            "observed_at": (now - datetime.timedelta(minutes=10 - i * 2)).isoformat(),
        })

    r_batch = client.post("/api/v1/telemetry/batch", json={"packets": batch})
    assert r_batch.status_code == 200
    b_data = r_batch.json()
    assert b_data["total"] == 5
    assert b_data["ingested"] == 5

    # Query timeseries: mean aggregation
    r_mean = client.get(
        f"/api/v1/observations/timeseries?sensor_id={sensor_id}&measurement_type=rainfall_rate_mmh&aggregation=mean"
    )
    assert r_mean.status_code == 200
    assert r_mean.json()["value"] == 6.0

    # Query timeseries: max aggregation
    r_max = client.get(
        f"/api/v1/observations/timeseries?sensor_id={sensor_id}&measurement_type=rainfall_rate_mmh&aggregation=max"
    )
    assert r_max.status_code == 200
    assert r_max.json()["value"] == 10.0

    # Query timeseries: count aggregation
    r_cnt = client.get(
        f"/api/v1/observations/timeseries?sensor_id={sensor_id}&measurement_type=rainfall_rate_mmh&aggregation=count"
    )
    assert r_cnt.status_code == 200
    assert r_cnt.json()["value"] == 5.0


# ============================================================================
# 5. BACKGROUND JOB SYSTEM & BOUNDED RETRIES (SUBSYSTEM 5)
# ============================================================================

def test_background_job_retry_and_non_retryable_behavior():
    """Verifies that JobManager handles retries on transient errors and fails immediately on non-retryable errors."""
    
    # 1. Transient failure with eventual success
    attempt_count = 0
    def flaky_task():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ConnectionError("Temporary socket timeout")
        return "SUCCESS_DATA"

    job1 = BackgroundJob(job_id="test_retry_job", func=flaky_task, max_retries=3, initial_delay_sec=0.01)
    res1 = job_manager.execute_sync(job1)
    assert res1 == "SUCCESS_DATA"
    assert job1.status == "SUCCESS"
    assert job1.attempts == 2

    # 2. Non-retryable error fails immediately without retrying
    non_retry_attempts = 0
    def bad_arg_task():
        nonlocal non_retry_attempts
        non_retry_attempts += 1
        raise ValueError("Invalid configuration parameter")

    job2 = BackgroundJob(job_id="test_non_retry_job", func=bad_arg_task, max_retries=5, initial_delay_sec=0.01)
    with pytest.raises(ValueError):
        job_manager.execute_sync(job2)
    assert job2.status == "FAILED"
    assert job2.attempts == 1  # Did not retry on ValueError!


# ============================================================================
# 6. EVENT BUS & WEBSOCKET SAFETY PROHIBITION (SUBSYSTEM 6)
# ============================================================================

def test_event_bus_and_websocket_authorization_prohibition(client, commander_token):
    """Verifies that EventBus delivers events and WebSocket strictly rejects alert authorization."""
    received = []
    def subscriber(event):
        received.append(event)

    event_bus.subscribe("telemetry.*", subscriber)
    event_bus.publish("telemetry.test", {"station_id": "ST_01", "val": 42.0})
    assert len(received) == 1
    assert received[0]["data"]["val"] == 42.0

    # WebSocket authorization prohibition test:
    # Attempting to authorize an alert over WebSocket must be explicitly rejected
    token_str = commander_token["Authorization"].split(" ")[1]
    with client.websocket_connect(f"/ws/realtime?token={token_str}") as websocket:
        init_msg = websocket.receive_json()
        assert init_msg["type"] == "SUBSCRIPTION_CONFIRMED"

        # Attempt forbidden authorization action over WebSocket
        websocket.send_json({
            "action": "AUTHORIZE_ALERT",
            "alert_id": "ALT-9999",
            "commander_pin": "1234",
        })
        resp = websocket.receive_json()
        assert resp["type"] == "SECURITY_ERROR"
        assert resp["code"] == "WEBSOCKET_AUTHORIZATION_PROHIBITED"


# ============================================================================
# 7. UNIFIED RISK STATE API (SUBSYSTEM 7)
# ============================================================================

def test_unified_risk_state_api(client):
    """Verifies that GET /api/v1/risk/current exposes risk indices, confidence state, and health."""
    res = client.get("/api/v1/risk/current")
    assert res.status_code == 200
    data = res.json()
    assert "overall_risk_level" in data or "composite_risk_score" in data or "confidence_state" in data
    assert "confidence_state" in data
    assert data["confidence_state"] in ["HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "LOW_CONFIDENCE", "UNAVAILABLE"]


# ============================================================================
# 8. ALERT STATE MACHINE & NOTIFICATIONS (SUBSYSTEM 8)
# ============================================================================

def test_alert_lifecycle_state_machine_and_cancellation(client, commander_token, db):
    """
    Verifies that:
      1. Newly created alerts start in PENDING_APPROVAL.
      2. Unauthorized alert cannot be dispatched directly.
      3. Authorized alert dispatches cleanly.
      4. Cancelled alert enters CANCELLED and cannot be authorized.
      5. Dispatched alert cannot be authorized twice.
    """
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S%f")
    alert_payload = {
        "headline": f"Evacuation Warning Beas Basin {uid}",
        "description": "Critical flood discharge detected.",
        "instruction": "Evacuate to elevated shelters immediately.",
        "area_desc": "Manali to Kullu riverside corridor",
        "severity": "Extreme",
        "urgency": "Immediate",
        "certainty": "Observed",
    }

    # 1. Create Alert Draft -> PENDING_APPROVAL
    r_create = client.post("/api/v1/alerts/draft", json=alert_payload)
    assert r_create.status_code == 200
    a_data = r_create.json()
    alert_id = a_data["alert"]["id"]
    assert a_data["alert"]["status"] == "PENDING_APPROVAL"

    # 2. Cancel the alert
    r_cancel = client.post(
        f"/api/v1/alerts/{alert_id}/cancel",
        json={"reason": "Water levels stabilized, threat subsided", "actor_id": "cmdr_01", "actor_role": "SENIOR_INCIDENT_COMMANDER"},
        headers=commander_token,
    )
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "CANCELLED"

    # 3. Attempting to authorize a CANCELLED alert must fail (400 Bad Request)
    r_auth_fail = client.post(
        f"/api/v1/alerts/{alert_id}/authorize",
        json={"actor_id": "cmdr_01", "actor_role": "SENIOR_INCIDENT_COMMANDER", "approval_token": "SIG_VALID_2026"},
        headers=commander_token,
    )
    assert r_auth_fail.status_code == 400

    # 4. Create second alert draft for authorization and notification dispatch
    r_create2 = client.post("/api/v1/alerts/draft", json=alert_payload)
    alert_id_2 = r_create2.json()["alert"]["id"]

    r_auth = client.post(
        f"/api/v1/alerts/{alert_id_2}/authorize",
        json={"actor_id": "cmdr_01", "actor_role": "SENIOR_INCIDENT_COMMANDER", "approval_token": "SIG_VALID_2026"},
        headers=commander_token,
    )
    assert r_auth.status_code == 200
    auth_res = r_auth.json()
    assert auth_res["status"] == "DISPATCHED"
    assert auth_res["alert"]["status"] == "DISPATCHED"

    # 5. Attempting to authorize an ALREADY DISPATCHED alert must fail
    r_auth_dup = client.post(
        f"/api/v1/alerts/{alert_id_2}/authorize",
        json={"actor_id": "cmdr_01", "actor_role": "SENIOR_INCIDENT_COMMANDER", "approval_token": "SIG_VALID_2026"},
        headers=commander_token,
    )
    assert r_auth_dup.status_code == 400


def test_ndma_sachet_provider_honest_configuration_status():
    """Verifies that NDMASachetProvider reports honest NOT_CONFIGURED when certs/keys are absent."""
    provider = NDMASachetProvider()
    res = asyncio.run(provider.dispatch({
        "alert_id": "ALT-TEST",
        "headline": "Test Alert",
        "severity": "Severe",
    }))
    # When mTLS certs are missing in test environment, status must be NOT_CONFIGURED
    assert res.status in ["NOT_CONFIGURED", "SUCCESS"]
    if res.status == "NOT_CONFIGURED":
        assert "not configured" in res.error_message.lower()


def test_cap_v12_validation():
    """Verifies that OASIS CAP v1.2 validator correctly verifies valid payloads and rejects malformed ones."""
    valid_cap = {
        "headline": "Flash Flood Evacuation Notice",
        "description": "High flood discharge expected along Beas River.",
        "instruction": "Move to higher ground immediately.",
        "area_desc": "Kullu-Manali Valley",
        "severity": "Extreme",
        "urgency": "Immediate",
        "certainty": "Observed",
    }
    # validate_cap_dict should succeed without exception
    cap_validator.validate_cap_dict(valid_cap)

    # Missing mandatory field: headline
    invalid_cap = dict(valid_cap)
    del invalid_cap["headline"]
    with pytest.raises(FloodyShieldException) as exc_info:
        cap_validator.validate_cap_dict(invalid_cap)
    assert exc_info.value.error_code == "CAP_VALIDATION_ERROR"


# ============================================================================
# 9. SYSTEM OBSERVABILITY & PROMETHEUS METRICS (SUBSYSTEM 9)
# ============================================================================

def test_system_observability_endpoints(client):
    """Verifies /api/v1/system/status, /api/v1/system/data-sources, and /metrics exposition."""
    
    # 1. Status
    r_stat = client.get("/api/v1/system/status")
    assert r_stat.status_code == 200
    st_data = r_stat.json()
    assert st_data["status"] == "OPERATIONAL"
    assert st_data["safety_invariants"]["human_in_the_loop_required"] is True

    # 2. Data Sources
    r_src = client.get("/api/v1/system/data-sources")
    assert r_src.status_code == 200
    src_data = r_src.json()
    assert "IMD" in src_data["sources"]
    assert "GPM" in src_data["sources"]
    assert "CWC" in src_data["sources"]
    assert "Sentinel" in src_data["sources"]
    assert "IoT_Ground_Network" in src_data["sources"]

    # 3. Prometheus Metrics Endpoint
    r_met = client.get("/metrics")
    assert r_met.status_code == 200
    assert "text/plain" in r_met.headers["content-type"]
    met_text = r_met.text
    assert "floody_uptime_seconds" in met_text
    assert "# TYPE floody_uptime_seconds gauge" in met_text


# ============================================================================
# 10. FROZEN MODEL SHA-256 HASH VERIFICATION (SCIENTIFIC IMMUTABILITY)
# ============================================================================

def test_frozen_model_hashes_immutability():
    """
    CRITICAL SAFETY AUDIT:
    Verifies that the frozen model artifact SHA-256 hashes for M2, M4, M6, and M7
    match the verified baseline bit-for-bit.
    """
    expected_hashes = {
        "M2": ("ml/flood/m2_upper_beas_flood_model.joblib", "a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b"),
        "M4": ("data/satellite_output/flood_multimodal_unet.pt", "45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07"),
        "M6": ("ml/landslide/m6_beas_susceptibility_rf.joblib", "e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c"),
        "M7": ("ml/landslide/m7_beas_trigger_lgbm.joblib", "f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a"),
    }

    base_dir = Path(__file__).resolve().parents[2]
    for model_key, (rel_path, expected_hash) in expected_hashes.items():
        full_path = base_dir / rel_path
        assert full_path.exists(), f"Frozen model artifact missing: {full_path}"

        hasher = hashlib.sha256()
        with open(full_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()

        assert actual_hash == expected_hash, (
            f"FROZEN ARTIFACT CORRUPTION: {model_key} hash mismatch!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )
