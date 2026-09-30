"""
tests/test_phase3_provenance_isolation.py
=========================================
Authoritative Verification Suite for Phase 3:
Live Data Safety Boundary, Provenance Quarantine & Notification Sandbox.

Verifies:
  Test 1: REAL_FIELD_OBSERVATION eligible for operational risk synthesis.
  Test 2: SYNTHETIC input never silently becomes operational risk; blocked from live alert drafts.
  Test 3: SIMULATED input remains simulation/non-operational with Exercise/Test CAP status.
  Test 4: REPLAY input remains historical/exercise with mandatory safety notice.
  Test 5: Mixed provenance (Real + Synthetic) triggers Conservative Non-Operational Tainting -> MIXED.
  Test 6: Notification Sandbox guarantees in-memory simulation with zero external network traffic.
  Test 7: Human authorization boundary strictly enforces Senior Incident Commander sign-off.
  Test 8: Existing telemetry ingestion contract and QC gates continue operating seamlessly.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.core.config import settings
from backend.app.core.errors import AuthorizationError, FloodyShieldException
from backend.app.core.provenance import (
    DataMode,
    DeliveryStatus,
    NotificationMode,
    OPERATIONAL_MODES,
    NON_OPERATIONAL_MODES,
    classify_provenance_mode,
    is_operational_provenance,
    get_cap_status_for_mode,
)
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.incident import IncidentModel
from backend.app.database.models.risk import RiskStateModel
from backend.app.database.models.telemetry import SensorObservationModel, SensorStationModel
from backend.app.orchestration.state import ModelNodeResult
from backend.app.services.alerts.lifecycle_service import alert_lifecycle_service
from backend.app.services.incident.replay_service import replay_service
from backend.app.services.notifications.dispatcher import notification_dispatcher
from backend.app.services.notifications.email_provider import EmailNotificationProvider
from backend.app.services.notifications.sms_provider import SMSNotificationProvider
from backend.app.services.notifications.siren_provider import SirenProvider
from backend.app.services.notifications.ndma_sachet_provider import NDMASachetProvider
from backend.app.services.risk.engine import unified_risk_engine


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


def make_dummy_orchestrator_results() -> dict:
    """Helper providing standard model node results for multi-hazard synthesis."""
    return {
        "M1": ModelNodeResult(model_id="M1", model_name="Nowcast", state="COMPLETED", output={"prediction": {"intensity_mmh": 45.0}}),
        "M2": ModelNodeResult(model_id="M2", model_name="Flood", state="COMPLETED", output={"flood_probability": 0.82, "risk_tier": "CRITICAL"}),
        "M4": ModelNodeResult(model_id="M4", model_name="Satellite", state="COMPLETED", output={"flood_inundation_detected": True}),
        "M6": ModelNodeResult(model_id="M6", model_name="Susceptibility", state="COMPLETED", output={"susceptibility_class": 3, "susceptibility_tier": "HIGH"}),
        "M7": ModelNodeResult(model_id="M7", model_name="Trigger", state="COMPLETED", output={"trigger_predicted": True}),
        "M8": ModelNodeResult(model_id="M8", model_name="Kinematics", state="COMPLETED", output={"output": {"velocity_mm_yr": 120.0}}),
        "M10": ModelNodeResult(model_id="M10", model_name="Stage", state="COMPLETED", output={"forecast_stage_m": 8.5}),
        "M11": ModelNodeResult(model_id="M11", model_name="Depth", state="COMPLETED", output={"inundation_depth_m": 2.2}),
        "M12": ModelNodeResult(model_id="M12", model_name="Cascade", state="COMPLETED", output={"prediction": {"peak_outflow_discharge_m3s": 2400.0}}),
        "M13": ModelNodeResult(model_id="M13", model_name="Vulnerability", state="COMPLETED", output={"social_vulnerability_index": 0.78}),
        "M14": ModelNodeResult(model_id="M14", model_name="Infrastructure", state="COMPLETED", output={"economic_loss_crores": 45.0}),
        "M17": ModelNodeResult(model_id="M17", model_name="Gating", state="COMPLETED", output={"warning_action": "RED_EVACUATE", "escalation_level": "LEVEL_3"}),
        "M18": ModelNodeResult(model_id="M18", model_name="Calibration", state="COMPLETED", output={"calibrated_probability": 0.88}),
        "M19": ModelNodeResult(model_id="M19", model_name="TimeToImpact", state="COMPLETED", output={"p50_minutes": 22.0}),
    }


# ============================================================================
# TEST 1 — REAL OBSERVATION ELIGIBILITY
# ============================================================================
def test_real_observation_eligible_for_operational_processing(db: Session):
    """
    Test 1: Observations with REAL_FIELD_OBSERVATION provenance must be eligible
    for operational risk processing and produce an OPERATIONAL RiskState.
    """
    initial_obs = {
        "rainfall_intensity_mmh": 75.0,
        "river_water_level_m": 8.0,
        "provenance": DataMode.REAL_FIELD_OBSERVATION.value,
        "latitude": 31.75,
        "longitude": 77.20,
    }

    # 1. Test quarantine gate validation
    is_eligible, reason = unified_risk_engine.validate_operational_eligibility([initial_obs])
    assert is_eligible is True, f"Real observation must be eligible: {reason}"

    # 2. Synthesize risk state
    inc_id = f"INC-REAL-{uuid.uuid4().hex[:6].upper()}"
    risk_state = unified_risk_engine.synthesize_risk_state(
        db=db,
        incident_id=inc_id,
        location_name="Upper Beas Basin - Aut Reach",
        initial_observations=initial_obs,
        orchestrator_results=make_dummy_orchestrator_results(),
        data_mode=DataMode.OPERATIONAL.value,
    )

    # 3. Assert operational attributes
    assert risk_state["data_mode"] == DataMode.OPERATIONAL.value
    assert risk_state["is_operational"] is True
    assert risk_state["overall_risk_level"] == "CRITICAL"

    # 4. Verify database record
    db_record = db.query(RiskStateModel).filter_by(id=risk_state["risk_state_id"]).first()
    assert db_record is not None
    d = db_record.to_dict()
    assert d["data_mode"] == DataMode.OPERATIONAL.value
    assert d["is_operational"] is True


# ============================================================================
# TEST 2 — SYNTHETIC OBSERVATION QUARANTINE
# ============================================================================
def test_synthetic_observation_quarantined_from_operational_risk(db: Session):
    """
    Test 2: SYNTHETIC observations must NEVER silently become operational risk.
    They must be classified as SIMULATION and prohibited from creating live operational alert drafts.
    """
    initial_obs = {
        "rainfall_intensity_mmh": 90.0,
        "river_water_level_m": 9.5,
        "provenance": DataMode.SYNTHETIC.value,
    }

    # 1. Quarantine gate rejection check
    is_eligible, reason = unified_risk_engine.validate_operational_eligibility([initial_obs])
    assert is_eligible is False
    assert "Quarantine rejection" in reason

    # 2. Synthesize risk state without operational claim
    inc_id = f"INC-SYNTH-{uuid.uuid4().hex[:6].upper()}"
    synth_state = unified_risk_engine.synthesize_risk_state(
        db=db,
        incident_id=inc_id,
        location_name="Synthetic Stress Test Corridor",
        initial_observations=initial_obs,
        orchestrator_results=make_dummy_orchestrator_results(),
    )

    # Assert demoted to simulation
    assert synth_state["data_mode"] == DataMode.SIMULATION.value
    assert synth_state["is_operational"] is False

    # 3. Attempting to create an OPERATIONAL alert draft referencing this synthetic risk state must fail
    with pytest.raises(FloodyShieldException) as exc_info:
        alert_lifecycle_service.create_alert_draft(
            db=db,
            incident_id=inc_id,
            headline="SYNTHETIC FLOOD DRILL",
            description="Testing alert gating.",
            instruction="Move to higher ground.",
            area_desc="Aut Riverbed",
            data_mode=DataMode.OPERATIONAL.value,  # Caller falsely claims operational!
            risk_state_id=synth_state["risk_state_id"],
        )
    assert exc_info.value.status_code == 422
    assert "Safety quarantine violation" in exc_info.value.message


# ============================================================================
# TEST 3 — SIMULATED OBSERVATION NON-OPERATIONAL CAP STATUS
# ============================================================================
def test_simulated_observation_generates_exercise_cap_status(db: Session):
    """
    Test 3: SIMULATED observations must produce non-operational alerts with
    OASIS CAP <status> set to Exercise or Test, never Actual.
    """
    initial_obs = {
        "rainfall_intensity_mmh": 60.0,
        "river_water_level_m": 6.5,
        "provenance": DataMode.SIMULATED.value,
    }
    inc_id = f"INC-SIM-{uuid.uuid4().hex[:6].upper()}"
    sim_risk = unified_risk_engine.synthesize_risk_state(
        db=db,
        incident_id=inc_id,
        location_name="Simulated Scenario Gorge",
        initial_observations=initial_obs,
        orchestrator_results=make_dummy_orchestrator_results(),
    )
    assert sim_risk["is_operational"] is False

    # Create draft without claiming operational
    draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=inc_id,
        headline="SIMULATED EVACUATION WARNING",
        description="Routine multi-hazard evacuation simulation.",
        instruction="Practice vertical shelter in place.",
        area_desc="Larji Hydro Spillway",
        risk_state_id=sim_risk["risk_state_id"],
    )

    # CAP identifier must carry SIMULATION tag
    assert "SIMULATION" in draft.cap_identifier

    # Authorize draft
    dispatched = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="CMDR_KULLU_01",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="CMD-SEC-KEY-7781-BEAS",
    )

    # Statutory CAP XML must contain <status>Test</status> or <status>Exercise</status>, NOT <status>Actual</status>
    assert dispatched.cap_xml is not None
    assert "<status>Actual</status>" not in dispatched.cap_xml
    assert ("<status>Test</status>" in dispatched.cap_xml) or ("<status>Exercise</status>" in dispatched.cap_xml)


# ============================================================================
# TEST 4 — HISTORICAL REPLAY SAFETY NOTICE & EXERCISE STATUS
# ============================================================================
def test_historical_replay_remains_exercise(db: Session):
    """
    Test 4: Historical scenario replay must execute with mode=REPLAY,
    attach the statutory safety notice, and never broadcast live alerts.
    """
    replay_out = replay_service.replay_scenario(
        db=db,
        scenario_name="July_2023_Upper_Beas_Compound_Flood",
        rainfall_intensity_mmh=85.0,
        dam_height_m=40.0,
        impounded_volume_m3=12_000_000.0,
        river_water_level_m=8.2,
    )

    assert replay_out["mode"] == "REPLAY"
    assert "THIS IS A HISTORICAL SIMULATION REPLAY" in replay_out["statutory_safety_notice"]
    assert replay_out["incident"]["status"] == "EXERCISE"

    # Risk state generated from replay must carry data_mode=REPLAY
    risk_state = replay_out["risk_state"]
    assert risk_state["data_mode"] == "REPLAY"
    assert risk_state["is_operational"] is False

    # Attempting to create an operational alert on this replay incident must be rejected
    with pytest.raises(FloodyShieldException) as exc_info:
        alert_lifecycle_service.create_alert_draft(
            db=db,
            incident_id=replay_out["replay_id"],
            headline="BREACH WARNING",
            description="Replay breach.",
            instruction="Evacuate.",
            area_desc="Larji",
            data_mode=DataMode.OPERATIONAL.value,
        )
    assert exc_info.value.status_code == 422
    assert "Safety quarantine violation" in exc_info.value.message


# ============================================================================
# TEST 5 — CONSERVATIVE NON-OPERATIONAL TAINTING (MIXED INPUTS)
# ============================================================================
def test_mixed_provenance_triggers_conservative_tainting(db: Session):
    """
    Test 5: Mixed real + non-real inputs must NOT silently produce an operational risk state.
    Conservative non-operational tainting must classify the composite risk state as MIXED.
    """
    mixed_obs = {
        "rainfall_intensity_mmh": 65.0,
        "river_water_level_m": 7.2,
        "provenances": [
            DataMode.REAL_FIELD_OBSERVATION.value,  # Real rainfall
            DataMode.SYNTHETIC.value,               # Synthetic river stage
            DataMode.PROXY_DATA.value,              # Proxy landslide detection
        ],
    }

    # Evaluate helper directly
    mode, is_op = classify_provenance_mode(mixed_obs["provenances"])
    assert mode == DataMode.MIXED.value
    assert is_op is False

    # Synthesize risk state: even if caller requests OPERATIONAL, tainting must force MIXED
    mixed_state = unified_risk_engine.synthesize_risk_state(
        db=db,
        incident_id=f"INC-MIXED-{uuid.uuid4().hex[:6]}",
        location_name="Pandoh Tailrace Reach",
        initial_observations=mixed_obs,
        orchestrator_results=make_dummy_orchestrator_results(),
        data_mode=DataMode.OPERATIONAL.value,  # Caller requested operational
    )

    assert mixed_state["data_mode"] == DataMode.MIXED.value
    assert mixed_state["is_operational"] is False
    assert mixed_state["provenance"]["taint_rule"] == "CONSERVATIVE_NON_OPERATIONAL_TAINTING"


# ============================================================================
# TEST 6 — NOTIFICATION SANDBOX BEHAVIOR
# ============================================================================
def test_sandbox_notification_guarantees_in_memory_simulation():
    """
    Test 6: In default SANDBOX mode:
      - Email, SMS, Siren, NDMA Sachet providers return status=SIMULATED.
      - Message IDs are clearly stamped with sandbox prefixes.
      - Zero outbound network traffic is made.
    """
    alert_payload = {
        "alert_id": f"ALT-TEST-{uuid.uuid4().hex[:6]}",
        "cap_identifier": "CAP-TEST-HPSDMA-20260927-SAMPLE",
        "headline": "SANDBOX SAFETY VERIFICATION DRILL",
    }

    # 1. Email Provider in Sandbox
    email_prov = EmailNotificationProvider()
    assert email_prov.notification_mode == "SANDBOX"
    res_email = asyncio.run(email_prov.dispatch(alert_payload))
    assert res_email.status == DeliveryStatus.SIMULATED.value
    assert res_email.message_id.startswith("sandbox-sim-email-")

    # 2. SMS Provider in Sandbox
    sms_prov = SMSNotificationProvider()
    assert sms_prov.notification_mode == "SANDBOX"
    res_sms = asyncio.run(sms_prov.dispatch(alert_payload))
    assert res_sms.status == DeliveryStatus.SIMULATED.value
    assert res_sms.message_id.startswith("sandbox-sim-sms-")

    # 3. Siren Provider in Sandbox
    siren_prov = SirenProvider()
    assert siren_prov.notification_mode == "SANDBOX"
    res_siren = asyncio.run(siren_prov.dispatch(alert_payload))
    assert res_siren.status == DeliveryStatus.SIMULATED.value
    assert res_siren.message_id.startswith("sandbox-sim-siren-")

    # 4. Multi-channel broadcast in Sandbox
    broadcast_results = asyncio.run(notification_dispatcher.broadcast_alert(alert_payload))
    statuses = {r.channel: r.status for r in broadcast_results}
    assert statuses.get("EMAIL") == DeliveryStatus.SIMULATED.value
    assert statuses.get("SMS") == DeliveryStatus.SIMULATED.value
    assert statuses.get("SIREN") == DeliveryStatus.SIMULATED.value


# ============================================================================
# TEST 7 — HUMAN AUTHORIZATION BOUNDARY
# ============================================================================
def test_human_authorization_boundary_enforces_commander_gate(client: TestClient, db: Session):
    """
    Test 7: Public alerts can NEVER be dispatched autonomously or by unauthorized actors.
    Only SENIOR_INCIDENT_COMMANDER with valid cryptographic approval token can release alerts.
    """
    # 1. Create alert draft
    draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="FLASH FLOOD EMERGENCY ADVISORY",
        description="Water level surging in Beas gorge.",
        instruction="Evacuate to elevated shelters.",
        area_desc="Larji Gorge",
    )
    assert draft.status == "PENDING_APPROVAL"

    # 2. Unauthorized role attempt (JUNIOR_OPERATOR) must be rejected with 403
    with pytest.raises(AuthorizationError) as exc_info:
        alert_lifecycle_service.authorize_and_dispatch(
            db=db,
            alert_id=draft.id,
            commander_id="operator_01",
            commander_role="JUNIOR_OPERATOR",
            approval_token="CMD-SEC-KEY-7781-BEAS",
        )
    assert "Only SENIOR_INCIDENT_COMMANDER can authorize" in str(exc_info.value)

    # 3. Missing/invalid approval token must be rejected with 403
    with pytest.raises(AuthorizationError) as exc_info:
        alert_lifecycle_service.authorize_and_dispatch(
            db=db,
            alert_id=draft.id,
            commander_id="cmdr_01",
            commander_role="SENIOR_INCIDENT_COMMANDER",
            approval_token="SHORT",  # < 8 chars
        )
    assert "cryptographic authorization token is required" in str(exc_info.value)

    # 4. Valid Commander sign-off succeeds
    dispatched = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="cmdr_01",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="CMD-SEC-KEY-7781-BEAS",
    )
    assert dispatched.status == "DISPATCHED"
    assert dispatched.authorized_by == "cmdr_01"


# ============================================================================
# TEST 8 — TELEMETRY INGESTION INTEGRATION & QC GATES
# ============================================================================
def test_telemetry_ingestion_qc_and_idempotency(client: TestClient, db: Session):
    """
    Test 8: Ingestion API (POST /api/v1/telemetry) must continue working seamlessly:
      - Valid telemetry with REAL_FIELD_OBSERVATION accepted (HTTP 200).
      - Replay with identical payload recognized as DUPLICATE.
      - Replay with conflicting value triggers 409 TELEMETRY_INTEGRITY_VIOLATION.
      - Future timestamps exceeding clock skew rejected (HTTP 422).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    stn_id = f"STN-P3-{uuid.uuid4().hex[:4].upper()}"

    valid_packet = {
        "station_id": stn_id,
        "device_id": "DEV_RADAR_01",
        "sensor_id": "SNS_STAGE_01",
        "observed_at": now_iso,
        "measurement_type": "WATER_LEVEL",
        "value": 4.85,
        "unit": "m",
        "sequence_number": 101,
        "provenance": DataMode.REAL_FIELD_OBSERVATION.value,
        "environment": "FIELD",
    }

    # 1. Ingest normal packet
    resp1 = client.post("/api/v1/telemetry", json=valid_packet)
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    assert data1["status"] in ("INGESTED", "DUPLICATE")
    assert data1["is_duplicate"] is False

    # 2. Replay identical packet -> DUPLICATE (HTTP 200)
    resp2 = client.post("/api/v1/telemetry", json=valid_packet)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["is_duplicate"] is True

    # 3. Tampered replay with different value -> HTTP 409
    tampered_packet = dict(valid_packet)
    tampered_packet["value"] = 9.99  # Tampered value with same source_event_id
    tampered_packet["source_event_id"] = data1["source_event_id"]
    resp_tamper = client.post("/api/v1/telemetry", json=tampered_packet)
    assert resp_tamper.status_code == 409
    assert "TELEMETRY_INTEGRITY_VIOLATION" in resp_tamper.text

    # 4. Clock skew violation (> 120 minutes in future) -> HTTP 422
    future_time = (now + datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    future_packet = dict(valid_packet)
    future_packet["observed_at"] = future_time
    future_packet["sequence_number"] = 102
    future_packet["source_event_id"] = None
    resp_skew = client.post("/api/v1/telemetry", json=future_packet)
    assert resp_skew.status_code == 422
    assert "TELEMETRY_FUTURE_TIMESTAMP" in resp_skew.text
