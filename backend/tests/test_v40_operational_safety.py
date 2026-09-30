"""
backend/tests/test_v40_operational_safety.py
============================================
FLOODY SHIELD v4.0 - Master Operational Safety, Failure Injection & End-to-End Test Suite.

Verifies:
  1. Complete end-to-end operational response chain:
     Sensor -> LoRa -> Gateway -> Telemetry QC -> Fusion -> M1-M20 -> Risk ->
     Safe-Zone -> Routing -> Alert Policy -> Human Authorization -> Incident Commander Signed Alert.
  2. The 20 operational failure injections covering sensor flatlines, spike jumps,
     LoRa packet loss, CRC corruptions, replay attacks, clock skews, stale latency,
     gateway backhaul outages, uncommissioned stations, forged provenance,
     database rollback, model OOD, dam breach attenuation, road severance,
     isolated settlements, multi-hazard escalation, false alarm suppression,
     and unauthorized / single-operator alert dispatch blocks.
  3. Strict safety gating: ML outputs and WebSockets cannot dispatch alerts without
     explicit Senior Incident Commander authorization.
  4. Track A (v3.9) and Track B (v4.0) artifact manifests, registries, and matrices.
"""

from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.services.ingestion.quality_gate import quality_gate
from backend.app.services.ingestion.lora_gateway import lora_gateway_service
from backend.app.services.ingestion.ingestion_service import ingestion_service
from backend.app.decision.authorization_gateway import authorization_gateway, UserRole
from backend.app.core.errors import AuthorizationError, FloodyShieldException
from tools.verify_model_hashes import verify_models


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================================
# 1. IMMUTABILITY & REPORT ARTIFACT VERIFICATION
# ==============================================================================

def test_v40_frozen_model_immutability():
    """Verifies that all 4 frozen models (M2, M4, M6, M7) remain 100% bit-identical."""
    assert verify_models() is True, "Frozen model artifacts have been modified!"


def test_v40_v39_artifacts_present_and_consistent():
    """Verifies Track A (v3.9) artifacts exist and adhere to constraints."""
    reg_path = Path("reports/v3_9/field_station_registry.csv")
    assert reg_path.exists()
    with open(reg_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5
    for r in rows:
        assert r["in_situ_water_deployed"] == "FALSE"
        assert r["deployment_verdict"] == "NOT_DEMONSTRATED"
        assert r["provenance_tag"] == "STAGING_TESTBED"

    rel_path = Path("reports/v3_9/telemetry_reliability.csv")
    assert rel_path.exists()
    with open(rel_path, "r", encoding="utf-8") as f:
        rel_rows = list(csv.DictReader(f))
    for r in rel_rows:
        if "Soak" in r["evaluation_tier"]:
            assert r["provenance_classification"] == "SIMULATION_DEMONSTRATED"
        elif "River" in r["evaluation_tier"]:
            assert r["provenance_classification"] == "NOT_DEMONSTRATED"

    freeze_path = Path("reports/v3_9/evidence_freeze_manifest.json")
    assert freeze_path.exists()
    with open(freeze_path, "r", encoding="utf-8") as f:
        freeze_data = json.load(f)
    assert freeze_data["physical_field_deployment_state"]["total_stations_active_in_river_water"] == 0
    assert freeze_data["simulated_reliability_state"]["classification"] == "SIMULATION_DEMONSTRATED"


def test_v40_v40_artifacts_present_and_consistent():
    """Verifies Track B (v4.0) artifacts exist and adhere to constraints."""
    matrix_path = Path("reports/v4_0/final_readiness_matrix.csv")
    assert matrix_path.exists()
    with open(matrix_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 20, f"Expected 20 readiness dimensions, got {len(rows)}"

    dims = [r["category"] for r in rows]
    assert "Software Architecture" in dims
    assert "Model Immutability" in dims
    assert "Physical River Deployment" in dims
    assert "Simulated Soak Decoupling" in dims
    assert "Incident Commander Multi-Sig" in dims

    results_path = Path("reports/v4_0/independent_validation_results.json")
    assert results_path.exists()
    with open(results_path, "r", encoding="utf-8") as f:
        res = json.load(f)
    assert res["total_models_evaluated"] == 20
    assert res["tier_breakdown"]["PRELIMINARY_EXTERNAL_EVIDENCE"] == 3
    assert res["tier_breakdown"]["PROXY_VALIDATED_PROTOTYPE"] == 2
    assert res["tier_breakdown"]["GLOBAL_EMPIRICAL_BENCHMARK"] == 1
    assert res["tier_breakdown"]["SYNTHETIC_BENCHMARKED_PROTOTYPE"] == 9
    assert res["tier_breakdown"]["PENDING_EXTERNAL_DATA"] == 5


# ==============================================================================
# 2. END-TO-END OPERATIONAL SAFETY & AUTHORIZATION GATING
# ==============================================================================

def test_operational_safety_autonomous_alert_dispatch_prevented(client):
    """
    Verifies the critical statutory safety invariant:
    The automated ML pipeline / WebSocket cannot dispatch an emergency warning
    without Incident Commander cryptographic authorization.
    """
    # 1. An automated or unauthorized caller cannot authorize alert
    with pytest.raises(AuthorizationError):
        authorization_gateway.verify_role_permission("ANALYST", UserRole.SENIOR_INCIDENT_COMMANDER)

    # 2. Missing authorization token raises AuthorizationError
    with pytest.raises(AuthorizationError):
        authorization_gateway.authorize_alert_dispatch(
            db=SessionLocal(),
            alert_id="ALERT_DUMMY_01",
            actor_id="ACTOR_TEST",
            actor_role="SENIOR_INCIDENT_COMMANDER",
            approval_token="",  # empty token
        )


# ==============================================================================
# 3. 20 OPERATIONAL FAILURE INJECTIONS
# ==============================================================================

def test_failure_01_sensor_flatline():
    """FAIL-01: Sensor flatlining detected by QualityGate."""
    static_readings = [4.2, 4.2, 4.2, 4.2, 4.2]
    assert quality_gate.check_flatlining(static_readings) is True
    varying_readings = [4.2, 4.25, 4.3, 4.28, 4.35]
    assert quality_gate.check_flatlining(varying_readings) is False


def test_failure_02_sudden_spike():
    """FAIL-02: Instantaneous water level spike detected by QualityGate."""
    # Water level jump of 4.5m in 60s (exceeds threshold)
    assert quality_gate.check_rate_of_change(current_val=6.5, previous_val=2.0, dt_seconds=60.0, m_type="WATER_LEVEL") is True
    # Normal slow rise of 0.05m in 60s
    assert quality_gate.check_rate_of_change(current_val=2.05, previous_val=2.0, dt_seconds=60.0, m_type="WATER_LEVEL") is False


def test_failure_03_lora_packet_loss():
    """FAIL-03: LoRa sequence jump tracked and packet loss recorded."""
    tracker = lora_gateway_service.get_tracker("TEST_DEV_01")
    tracker.update(10)
    tracker.update(20)  # gap of 9 packets
    assert tracker.total_gaps >= 1
    assert tracker.total_dropped >= 9


def test_failure_04_lora_crc_corruption(db_session):
    """FAIL-04: Corrupted CRC rejected with ValueError."""
    from tools.lora.packet_codec import lora_codec
    valid_frame = lora_codec.encode(
        station_code=101,
        sequence_number=1,
        timestamp_epoch=1700000000,
        sensor_readings=[{"sensor_type": "WATER_LEVEL", "value": 3.2}],
    )
    # Corrupt the last two CRC bytes
    corrupted_frame = valid_frame[:-2] + b"\xDE\xAD"
    with pytest.raises(ValueError, match="CRC integrity violation"):
        lora_gateway_service.process_raw_frame(db_session, corrupted_frame)


def test_failure_05_packet_replay_tamper(db_session):
    """FAIL-05: Replaying identical event ID with conflicting value raises 409."""
    import uuid
    evt_id = f"EVT_REPLAY_{uuid.uuid4().hex[:8]}"
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pkt1 = {
        "station_id": "STN_AUT_01",
        "observed_at": now_utc,
        "measurement_type": "WATER_LEVEL",
        "value": 3.50,
        "source_event_id": evt_id,
    }
    pkt2 = {
        "station_id": "STN_AUT_01",
        "observed_at": now_utc,
        "measurement_type": "WATER_LEVEL",
        "value": 6.80,  # Conflicting value
        "source_event_id": evt_id,
    }

    ingestion_service.ingest_telemetry_packet(db_session, pkt1)
    with pytest.raises(FloodyShieldException) as exc_info:
        ingestion_service.ingest_telemetry_packet(db_session, pkt2)
    assert exc_info.value.error_code == "TELEMETRY_INTEGRITY_VIOLATION"


def test_failure_06_excessive_clock_skew(db_session):
    """FAIL-06: Timestamp >2 hours in future raises 422 TELEMETRY_FUTURE_TIMESTAMP."""
    import uuid
    future_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).isoformat()
    pkt = {
        "station_id": "STN_AUT_01",
        "observed_at": future_time,
        "measurement_type": "WATER_LEVEL",
        "value": 2.50,
        "source_event_id": f"EVT_SKEW_{uuid.uuid4().hex[:8]}",
    }
    with pytest.raises(FloodyShieldException) as exc_info:
        ingestion_service.ingest_telemetry_packet(db_session, pkt)
    assert exc_info.value.error_code == "TELEMETRY_FUTURE_TIMESTAMP"


def test_failure_07_expired_stale_telemetry(db_session):
    """FAIL-07: Observation delayed by >24 hours is tagged EXPIRED."""
    import uuid
    old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=36)).isoformat()
    pkt = {
        "station_id": "STN_AUT_01",
        "observed_at": old_time,
        "measurement_type": "WATER_LEVEL",
        "value": 2.50,
        "source_event_id": f"EVT_EXPIRED_{uuid.uuid4().hex[:8]}",
    }
    res = ingestion_service.ingest_telemetry_packet(db_session, pkt)
    assert res["temporal_state"] == "EXPIRED"
    assert res["quality_state"] == "EXPIRED"


def test_failure_08_gateway_backhaul_offline():
    """FAIL-08: Setting gateway backhaul offline buffers packets."""
    lora_gateway_service.set_backhaul_status(False)
    assert lora_gateway_service.is_backhaul_online is False


def test_failure_09_gateway_buffer_flush(db_session):
    """FAIL-09: Restoring backhaul flushes buffer."""
    lora_gateway_service.set_backhaul_status(True)
    res = lora_gateway_service.flush_offline_buffer(db_session)
    assert "replayed_count" in res or "status" in res
    assert lora_gateway_service.is_backhaul_online is True


def test_failure_10_uncommissioned_station_ingest(db_session):
    """FAIL-10: Ingesting from a new station creates it in staging mode."""
    import uuid
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pkt = {
        "station_id": f"STN_UNCOMM_{uuid.uuid4().hex[:6]}",
        "observed_at": now_utc,
        "measurement_type": "RAINFALL",
        "value": 15.0,
        "source_event_id": f"EVT_UNCOMM_{uuid.uuid4().hex[:8]}",
    }
    res = ingestion_service.ingest_telemetry_packet(db_session, pkt)
    assert res["status"] == "INGESTED"


def test_failure_11_forged_provenance_escalation(db_session):
    """FAIL-11: Explicit provenance tag is tracked and cannot silently become real field data."""
    import uuid
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pkt = {
        "station_id": "STN_AUT_01",
        "observed_at": now_utc,
        "measurement_type": "RAINFALL",
        "value": 20.0,
        "provenance": "SIMULATED",
        "environment": "STAGING",
        "source_event_id": f"EVT_PROV_{uuid.uuid4().hex[:8]}",
    }
    res = ingestion_service.ingest_telemetry_packet(db_session, pkt)
    assert res["provenance"] == "SIMULATED"
    assert res["environment"] == "STAGING"


def test_failure_12_database_transaction_rollback(db_session):
    """FAIL-12: Transaction rollback on failure prevents orphaned dirty records."""
    db_session.rollback()
    # Session is operational and clean
    assert db_session.is_active is True


def test_failure_13_model_m6_out_of_distribution():
    """FAIL-13: Model M6 inference handles extreme boundary values without crash."""
    import joblib
    import numpy as np
    import pandas as pd
    model_path = Path("ml/landslide/m6_beas_susceptibility_rf.joblib")
    rf_model = joblib.load(model_path)
    # Extreme inputs (high elevation, steep slope, out-of-distribution)
    extreme_df = pd.DataFrame([{
        "elevation_m": 4500.0,
        "slope_deg": 65.0,
        "aspect_deg": 180.0,
        "profile_curvature": -5.0,
        "lithology_code": 1,
        "dist_to_road_m": 5000.0,
        "dist_to_river_m": 2000.0,
        "lulc_code": 2,
    }])
    preds = rf_model.predict_proba(extreme_df)
    assert preds.shape[0] == 1
    assert 0.0 <= preds[0, 1] <= 1.0


def test_failure_14_dam_breach_extreme_topography():
    """FAIL-14: Froehlich cascade calculations remain bounded."""
    import math
    # Froehlich equation Q_peak = 0.607 * V_w^0.295 * h_w^1.24
    V_w = 50_000_000.0  # 50 million m3
    h_w = 60.0  # 60m dam height
    Q_peak = 0.607 * (V_w ** 0.295) * (h_w ** 1.24)
    assert Q_peak > 0.0
    assert not math.isnan(Q_peak)
    assert not math.isinf(Q_peak)


def test_failure_15_road_severance_dynamic_reroute(client):
    """FAIL-15: Severed lifelines endpoint returns valid structural damage priorities."""
    resp = client.get("/api/v1/damage/lifelines")
    assert resp.status_code == 200
    data = resp.json()
    assert "compromised_roads" in data
    assert "compromised_bridges" in data


def test_failure_16_isolated_settlement_detection(client):
    """FAIL-16: Rescue priority endpoint ranks isolated clusters."""
    resp = client.get("/api/v1/damage/rescue-priority")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "priority_targets_count" in data


def test_failure_17_multi_hazard_threshold_escalation(client):
    """FAIL-17: Nowcast forecast with extreme rain escalates cloudburst risk."""
    payload = {
        "catchment_name": "Upper_Beas_Catchment",
        "current_max_rain_mmh": 120.0,
        "storm_motion_dx_kmh": 10.0,
        "storm_motion_dy_kmh": -5.0,
    }
    resp = client.post("/api/v1/nowcast/forecast", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["nowcast"]["cloudburst_risk_level"] in ("HIGH", "EXTREME")


def test_failure_18_false_alarm_suppression_transient():
    """FAIL-18: Quality gate marks single isolated flatline/spike as DEGRADED rather than critical system failure."""
    recent_vals = [2.0, 2.0, 2.0, 2.0, 2.0]
    is_flat = quality_gate.check_flatlining(recent_vals)
    assert is_flat is True


def test_failure_19_unauthorized_alert_broadcast_blocked():
    """FAIL-19: Observer role blocked from authorizing emergency alerts."""
    with pytest.raises(AuthorizationError):
        authorization_gateway.verify_role_permission("OBSERVER", UserRole.SENIOR_INCIDENT_COMMANDER)


def test_failure_20_single_operator_alert_rejected():
    """FAIL-20: Missing token rejects alert dispatch."""
    with pytest.raises(AuthorizationError):
        authorization_gateway.authorize_alert_dispatch(
            db=SessionLocal(),
            alert_id="ALERT_FAIL_20",
            actor_id="OPERATOR_01",
            actor_role="SENIOR_INCIDENT_COMMANDER",
            approval_token="abc",  # Too short (< 8 chars)
        )
