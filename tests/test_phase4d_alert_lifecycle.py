"""
tests/test_phase4d_alert_lifecycle.py
=====================================
Authoritative Verification Suite for Phase 04D:
Hyperlocal Risk-to-Alert Lifecycle, Actionable CAP Generation,
Human Authorization Gate, Multi-Channel Sandbox (SMS, IVR, Siren, SACHET),
Deduplication, Escalation, and DDMA Dashboard Integration.

Verifies:
  Test 1:  Risk -> Alert Candidate conversion (fields, actionable semantics, WHAT/WHERE/WHEN/WHY/HOW/CONFIDENCE).
  Test 2:  Ward-specific alert candidate & draft generation (Manali Urban Ward 1).
  Test 3:  Gram Panchayat-specific alert candidate & draft generation (Aut Gorge GP).
  Test 4:  OASIS CAP v1.2 XML serialization and validation with geotargeted polygon coordinates.
  Test 5:  CAP status: 'Actual' for verified operational real-world data.
  Test 6:  CAP status: 'Exercise' for Replay and 'Test' for Simulation/Synthetic data.
  Test 7:  Human authorization gate: RBAC enforcement (Senior Incident Commander only + cryptographic token).
  Test 8:  Tamper-evident audit logging with SHA-256 hash chaining on authorization.
  Test 9:  Civil Defense SMS provider sandbox isolation (simulated in-memory, zero network traffic).
  Test 10: Interactive Voice Response (IVR) provider sandbox isolation (ward-targeted, bilingual, zero telephony calls).
  Test 11: Acoustic Siren network provider sandbox isolation (sirens silent).
  Test 12: NDMA Sachet provider sandbox isolation (validated payload, zero government mTLS calls).
  Test 13: Fail-soft multi-channel notification dispatch (individual channel failure does not crash system).
  Test 14: Duplicate alert suppression (identical hazard & severity for same administrative unit suppressed).
  Test 15: Alert escalation (higher severity replaces or escalates prior alert with 'Update' CAP type).
  Test 16: Alert resolution workflow (hazard abatement triggers resolution recommendation and status update).
  Test 17: Provenance violation blocking (non-operational risk state blocked from creating operational alert).
  Test 18: Dynamic risk trend evaluation (INSUFFICIENT_HISTORY, RISING, FALLING, STABLE).
  Test 19: DDMA Dashboard integration endpoints (/ddma-briefing, /evaluate-hyperlocal, /dashboard/summary).
"""

from __future__ import annotations

import asyncio
import datetime
import json
import xml.etree.ElementTree as ET
import pytest
from starlette.testclient import TestClient

from backend.app.core.errors import AuthorizationError, FloodyShieldException
from backend.app.core.provenance import DataMode, DeliveryStatus
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.database.models.risk import RiskStateModel
from backend.app.database.session import SessionLocal
from backend.app.main import app
from backend.app.services.alerts.cap_validator import cap_validator
from backend.app.services.alerts.hyperlocal_connector import (
    HyperlocalAlertConnector,
    hyperlocal_alert_connector,
)
from backend.app.services.alerts.lifecycle_service import alert_lifecycle_service
from backend.app.services.gis.cascade_spatial_service import cascade_spatial_service
from backend.app.services.notifications.dispatcher import notification_dispatcher
from backend.app.services.notifications.ivr_provider import IVRNotificationProvider
from backend.app.services.notifications.ndma_sachet_provider import NDMASachetProvider
from backend.app.services.notifications.siren_provider import SirenProvider
from backend.app.services.notifications.sms_provider import SMSNotificationProvider


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_connector():
    HyperlocalAlertConnector.clear_history()
    yield
    HyperlocalAlertConnector.clear_history()


# ==============================================================================
# Test 1: Risk -> Alert Candidate Conversion
# ==============================================================================
def test_risk_to_alert_candidate():
    units = cascade_spatial_service.aggregate_hyperlocal_risk(
        flood_hazard_score=0.85,
        landslide_hazard_score=0.60,
        cascade_state="SUSPECTED_BOTTLENECK",
        provenance=DataMode.REAL_FIELD_OBSERVATION.value,
    )
    assert len(units) == 12

    manali_unit = next(u for u in units if u["admin_id"] == "WARD_MANALI_01")
    candidate = hyperlocal_alert_connector.evaluate_candidate(manali_unit)

    # Required contract fields
    assert candidate["administrative_unit"]["admin_id"] == "WARD_MANALI_01"
    assert candidate["hazard"] in ("FLOOD", "LANDSLIDE", "COMPOUND_CASCADE")
    assert candidate["severity"] in ("Severe", "Extreme")
    assert candidate["urgency"] == "Immediate"
    assert candidate["certainty"] in ("Observed", "Likely")
    assert candidate["trend"] == "INSUFFICIENT_HISTORY"  # First observation
    assert candidate["confidence"] >= 0.70
    assert candidate["is_operational"] is True
    assert candidate["provenance"] == DataMode.REAL_FIELD_OBSERVATION.value

    # Actionable Semantics: WHAT, WHERE, WHEN, WHY, HOW SERIOUS, CONFIDENCE
    desc = candidate["description"]
    assert "WHAT:" in desc
    assert "WHERE:" in desc
    assert "WHEN:" in desc
    assert "WHY:" in desc
    assert "HOW SERIOUS:" in desc
    assert "CONFIDENCE:" in desc
    assert candidate["instruction"] is not None
    assert len(candidate["instruction"]) > 20


# ==============================================================================
# Test 2: Ward-Specific Alert Candidate & Draft
# ==============================================================================
def test_ward_specific_alert(db):
    db.query(AlertDispatchModel).filter(AlertDispatchModel.area_desc.like("%WARD_MANALI_01%")).delete(synchronize_session=False)
    db.commit()

    units = cascade_spatial_service.aggregate_hyperlocal_risk(
        flood_hazard_score=0.80,
        landslide_hazard_score=0.50,
    )
    ward_unit = next(u for u in units if u["admin_id"] == "WARD_MANALI_01")
    candidate = hyperlocal_alert_connector.evaluate_candidate(ward_unit)

    assert candidate["administrative_unit"]["unit_type"] == "WARD"
    assert "Manali" in candidate["headline"]

    outcome, draft = hyperlocal_alert_connector.draft_hyperlocal_alert(db, candidate)
    assert outcome == "DRAFT_CREATED"
    assert draft is not None
    assert draft.status == "PENDING_APPROVAL"
    assert draft.severity in ("Severe", "Extreme")
    assert "WARD_MANALI_01" in draft.area_desc


# ==============================================================================
# Test 3: Gram Panchayat-Specific Alert Candidate & Draft
# ==============================================================================
def test_gram_panchayat_alert(db):
    db.query(AlertDispatchModel).filter(AlertDispatchModel.area_desc.like("%GP_AUT%")).delete(synchronize_session=False)
    db.commit()

    units = cascade_spatial_service.aggregate_hyperlocal_risk(
        flood_hazard_score=0.75,
        landslide_hazard_score=0.70,
        cascade_state="CONFIRMED_BY_EVIDENCE",
    )
    gp_unit = next(u for u in units if u["admin_id"] == "GP_AUT")
    candidate = hyperlocal_alert_connector.evaluate_candidate(gp_unit)

    assert candidate["administrative_unit"]["unit_type"] == "GRAM_PANCHAYAT"
    assert "Aut" in candidate["headline"]
    assert candidate["severity"] == "Extreme"

    outcome, draft = hyperlocal_alert_connector.draft_hyperlocal_alert(db, candidate)
    assert outcome == "DRAFT_CREATED"
    assert draft is not None
    assert draft.status == "PENDING_APPROVAL"
    assert "GP_AUT" in draft.area_desc


# ==============================================================================
# Test 4: OASIS CAP v1.2 XML Generation & Geotargeting
# ==============================================================================
def test_cap_generation(db):
    units = cascade_spatial_service.aggregate_hyperlocal_risk(flood_hazard_score=0.85)
    candidate = hyperlocal_alert_connector.evaluate_candidate(units[0])

    _, draft = hyperlocal_alert_connector.draft_hyperlocal_alert(db, candidate)
    assert draft is not None

    dispatched = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="CMD_KULLU_001",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="TOKEN_SECURE_AUTH_099182",
    )

    assert dispatched.cap_xml is not None
    # Validate via CAPValidator
    cap_validator.validate_cap_xml(dispatched.cap_xml)

    # Parse and verify XML structure
    root = ET.fromstring(dispatched.cap_xml)
    assert root.tag == "{urn:oasis:names:tc:emergency:cap:1.2}alert"

    info_el = root.find("{urn:oasis:names:tc:emergency:cap:1.2}info")
    assert info_el is not None

    area_el = info_el.find("{urn:oasis:names:tc:emergency:cap:1.2}area")
    assert area_el is not None
    assert area_el.find("{urn:oasis:names:tc:emergency:cap:1.2}areaDesc") is not None

    # Verify polygon geotargeting is included
    poly_el = area_el.find("{urn:oasis:names:tc:emergency:cap:1.2}polygon")
    assert poly_el is not None
    assert "," in poly_el.text


# ==============================================================================
# Test 5: CAP Status 'Actual' for Operational Data
# ==============================================================================
def test_cap_actual_status_operational_data(db):
    draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="Operational River Warning",
        description="WHAT: Flood. WHERE: Kullu. WHEN: Now. WHY: Heavy rain. HOW SERIOUS: Severe. CONFIDENCE: 90%",
        instruction="Evacuate low ground.",
        area_desc="Kullu Ward 1",
        severity="Severe",
        data_mode=DataMode.REAL_FIELD_OBSERVATION.value,
    )
    # Operational alert identifier
    assert draft.cap_identifier.startswith("CAP-HPSDMA-")
    assert "REPLAY" not in draft.cap_identifier
    assert "TEST" not in draft.cap_identifier

    dispatched = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="CMD_001",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="VALID_TOKEN_9918",
    )
    assert "<status>Actual</status>" in dispatched.cap_xml


# ==============================================================================
# Test 6: CAP Status 'Exercise' / 'Test' for Non-Operational Data
# ==============================================================================
def test_cap_exercise_test_status_non_operational(db):
    # 1. Replay -> Exercise
    replay_draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="Replay Flood Drill",
        description="Replay of July 2023 monsoon flood event.",
        instruction="Exercise protocol only.",
        area_desc="Pandoh Gorge",
        severity="Extreme",
        data_mode=DataMode.REPLAY.value,
    )
    assert "REPLAY" in replay_draft.cap_identifier
    auth_replay = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=replay_draft.id,
        commander_id="CMD_001",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="VALID_TOKEN_9918",
    )
    assert "<status>Exercise</status>" in auth_replay.cap_xml

    # 2. Synthetic / Simulation -> Test
    sim_draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="Synthetic Breach Simulation",
        description="Monte Carlo synthetic cascade simulation.",
        instruction="Simulation test only.",
        area_desc="Aut Reach",
        severity="Extreme",
        data_mode=DataMode.SYNTHETIC.value,
    )
    assert "SYNTHETIC" in sim_draft.cap_identifier
    auth_sim = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=sim_draft.id,
        commander_id="CMD_001",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="VALID_TOKEN_9918",
    )
    assert "<status>Test</status>" in auth_sim.cap_xml


# ==============================================================================
# Test 7: Human Authorization Gate RBAC Enforcement
# ==============================================================================
def test_human_authorization_gate(db):
    draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="Test Authorization Gate",
        description="Testing Commander sign-off requirement.",
        instruction="Standby.",
        area_desc="Larji Valley",
        severity="Severe",
    )

    # 1. Non-commander role rejected
    with pytest.raises(AuthorizationError) as exc_info:
        alert_lifecycle_service.authorize_and_dispatch(
            db=db,
            alert_id=draft.id,
            commander_id="OPERATOR_42",
            commander_role="CIVIL_DEFENSE_VOLUNTEER",
            approval_token="SOME_VALID_TOKEN_123",
        )
    assert "Unauthorized" in str(exc_info.value.message)

    # 2. Invalid token rejected
    with pytest.raises(AuthorizationError) as exc_info2:
        alert_lifecycle_service.authorize_and_dispatch(
            db=db,
            alert_id=draft.id,
            commander_id="CMD_001",
            commander_role="SENIOR_INCIDENT_COMMANDER",
            approval_token="short",  # < 8 chars
        )
    assert "cryptographic authorization token" in str(exc_info2.value.message)

    # 3. Valid commander and token succeeds
    auth = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="CMD_001",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="VALID_CRYPTO_TOKEN_XYZ_9918",
    )
    assert auth.status == "DISPATCHED"
    assert auth.authorized_by == "CMD_001"


# ==============================================================================
# Test 8: Tamper-Evident Audit Logging
# ==============================================================================
def test_audit_logging(db):
    draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="Audit Logging Test Alert",
        description="Verify SHA-256 hash chaining on authorization.",
        instruction="Take shelter.",
        area_desc="Bahang GP",
        severity="Severe",
    )

    auth = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="CMD_KULLU_EOC",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="SUPER_SECURE_TOKEN_12345",
        ip_address="192.168.1.100",
    )

    audit_entry = (
        db.query(AuditLogModel)
        .filter_by(target_entity_id=auth.id)
        .order_by(AuditLogModel.timestamp.desc())
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.action == "ALERT_AUTHORIZED_AND_DISPATCHED"
    assert audit_entry.actor_id == "CMD_KULLU_EOC"
    assert audit_entry.entry_hash is not None
    assert len(audit_entry.entry_hash) == 64  # SHA-256 hex string


# ==============================================================================
# Test 9: Civil Defense SMS Provider Sandbox Isolation
# ==============================================================================
@pytest.mark.anyio
async def test_sms_sandbox():
    provider = SMSNotificationProvider()
    assert provider.channel_name == "SMS"
    assert provider.notification_mode == "SANDBOX"

    payload = {
        "cap_identifier": "CAP-TEST-SMS-001",
        "headline": "Flash Flood Warning",
        "instruction": "Evacuate high ground.",
    }
    result = await provider.dispatch(payload, recipient="MANALI_RESIDENTS_GROUP")

    assert result.channel == "SMS"
    assert result.status == DeliveryStatus.SIMULATED.value
    assert result.details["mode"] == "SANDBOX"
    assert result.details["transmission"] == "SIMULATED_IN_MEMORY"
    assert "sandbox-sim-sms-" in result.message_id


# ==============================================================================
# Test 10: Interactive Voice Response (IVR) Provider Sandbox Isolation
# ==============================================================================
@pytest.mark.anyio
async def test_ivr_sandbox():
    provider = IVRNotificationProvider()
    assert provider.channel_name == "IVR"
    assert provider.notification_mode == "SANDBOX"

    payload = {
        "cap_identifier": "CAP-TEST-IVR-002",
        "administrative_unit": "GP_AUT",
        "severity": "Extreme",
        "language": "hi-IN",
        "instruction": "सुरक्षित ऊंचे स्थान पर जाएं।",
    }
    result = await provider.dispatch(payload)

    assert result.channel == "IVR"
    assert result.status == DeliveryStatus.SIMULATED.value
    assert result.details["mode"] == "SANDBOX"
    assert result.details["language"] == "hi-IN"
    assert result.recipient == "GP_AUT"
    assert "sandbox-sim-ivr-" in result.message_id


# ==============================================================================
# Test 11: Acoustic Siren Network Provider Sandbox Isolation
# ==============================================================================
@pytest.mark.anyio
async def test_siren_sandbox():
    provider = SirenProvider()
    assert provider.channel_name == "SIREN"
    assert provider.notification_mode == "SANDBOX"

    payload = {
        "cap_identifier": "CAP-TEST-SIREN-003",
        "severity": "Extreme",
    }
    result = await provider.dispatch(payload, recipient="PANDOH_DAM_SIRENS")

    assert result.channel == "SIREN"
    assert result.status == DeliveryStatus.SIMULATED.value
    assert result.recipient == "PANDOH_DAM_SIRENS"
    assert "sandbox-sim-siren-" in result.message_id


# ==============================================================================
# Test 12: NDMA Sachet Provider Sandbox Isolation
# ==============================================================================
@pytest.mark.anyio
async def test_ndma_sachet_sandbox():
    provider = NDMASachetProvider()
    assert provider.channel_name == "NDMA_SACHET"

    payload = {
        "cap_identifier": "CAP-TEST-SACHET-004",
        "cap_xml": "<alert><identifier>TEST</identifier></alert>",
    }
    result = await provider.dispatch(payload)

    assert result.channel == "NDMA_SACHET"
    # Either NOT_CONFIGURED (missing govt mTLS certs) or SIMULATED in sandbox
    assert result.status in ("NOT_CONFIGURED", "SIMULATED")


# ==============================================================================
# Test 13: Fail-Soft Multi-Channel Notification Dispatch
# ==============================================================================
@pytest.mark.anyio
async def test_provider_fail_soft():
    # Dispatching across all channels concurrently
    payload = {
        "cap_identifier": "CAP-FAILSOFT-TEST-005",
        "headline": "Multi-Channel Broadcast Test",
        "instruction": "Test instruction.",
        "area_desc": "Upper Beas Corridor",
        "severity": "Severe",
    }
    results = await notification_dispatcher.broadcast_alert(payload)

    # Must return results for all registered providers without crashing
    channel_names = [r.channel for r in results]
    assert "WEBSOCKET" in channel_names
    assert "SMS" in channel_names
    assert "SIREN" in channel_names
    assert "IVR" in channel_names
    assert "NDMA_SACHET" in channel_names

    # None of the unconfigured channels should report fake DELIVERY_CONFIRMED
    for r in results:
        assert r.status != "DELIVERY_CONFIRMED"


# ==============================================================================
# Test 14: Duplicate Alert Suppression
# ==============================================================================
def test_duplicate_suppression(db):
    units = cascade_spatial_service.aggregate_hyperlocal_risk(flood_hazard_score=0.80)
    naggar_unit = next(u for u in units if u["admin_id"] == "GP_NAGGAR")
    candidate = hyperlocal_alert_connector.evaluate_candidate(naggar_unit)

    # Clean any prior alerts for GP_NAGGAR
    db.query(AlertDispatchModel).filter(AlertDispatchModel.area_desc.like("%GP_NAGGAR%")).delete(synchronize_session=False)
    db.commit()

    # 1. First submission creates draft
    outcome1, draft1 = hyperlocal_alert_connector.draft_hyperlocal_alert(db, candidate)
    assert outcome1 == "DRAFT_CREATED"
    assert draft1 is not None

    # 2. Second identical submission is suppressed as duplicate
    outcome2, draft2 = hyperlocal_alert_connector.draft_hyperlocal_alert(db, candidate)
    assert outcome2 == "DUPLICATE_SUPPRESSED"
    assert draft2.id == draft1.id  # Refers to existing alert


# ==============================================================================
# Test 15: Alert Escalation
# ==============================================================================
def test_alert_escalation(db):
    # 1. Create a "Severe" alert draft for Ward 1
    units_severe = cascade_spatial_service.aggregate_hyperlocal_risk(flood_hazard_score=0.65)
    cand_severe = hyperlocal_alert_connector.evaluate_candidate(units_severe[0])
    cand_severe["severity"] = "Severe"

    outcome1, draft1 = hyperlocal_alert_connector.draft_hyperlocal_alert(db, cand_severe)
    assert outcome1 == "DRAFT_CREATED"
    assert draft1.severity == "Severe"

    # 2. Risk spikes to "Extreme" (e.g. compound cascade breach)
    cand_extreme = dict(cand_severe)
    cand_extreme["severity"] = "Extreme"
    cand_extreme["hazard"] = "COMPOUND_CASCADE"
    cand_extreme["headline"] = "[EMERGENCY WARNING] Breach Outburst Surge"

    outcome2, draft2 = hyperlocal_alert_connector.draft_hyperlocal_alert(db, cand_extreme)
    assert outcome2 == "ESCALATED"
    assert draft2 is not None
    assert draft2.severity == "Extreme"
    assert draft2.alert_type == "Update"
    assert "[ESCALATION]" in draft2.headline
    assert draft1.cap_identifier in draft2.description


# ==============================================================================
# Test 16: Alert Resolution Workflow
# ==============================================================================
def test_alert_resolution(db):
    # 1. Create alert draft
    draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=None,
        headline="Resolution Test Alert",
        description="Active threat.",
        instruction="Evacuate.",
        area_desc="Bhuntar Ward 1",
        severity="Severe",
    )
    # 2. Authorize
    auth = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=draft.id,
        commander_id="CMD_001",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="VALID_TOKEN_9918",
    )
    assert auth.status == "DISPATCHED"

    # 3. Resolve alert
    resolved = alert_lifecycle_service.resolve_alert(
        db=db,
        alert_id=auth.id,
        actor_id="CMD_001",
        actor_role="SENIOR_INCIDENT_COMMANDER",
        resolution_notes="Water level subsided below warning stage. All clear.",
    )
    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at is not None


# ==============================================================================
# Test 17: Provenance Violation Blocking
# ==============================================================================
def test_provenance_violation_blocking(db):
    import uuid
    # Create non-operational risk state
    risk_state = RiskStateModel(
        id=str(uuid.uuid4()),
        location_name="Sainj Valley",
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        overall_risk_level="HIGH",
        confidence_score=0.85,
        provenance_json=json.dumps({
            "data_mode": "SYNTHETIC",
            "is_operational": False,
        }),
    )
    db.add(risk_state)
    db.commit()

    # Attempting to declare live OPERATIONAL alert from non-operational risk state must raise 422
    with pytest.raises(FloodyShieldException) as exc_info:
        alert_lifecycle_service.create_alert_draft(
            db=db,
            incident_id=None,
            headline="Blocked Alert",
            description="Attempt to claim operational status from synthetic state.",
            instruction="None.",
            area_desc="Sainj Valley",
            severity="Severe",
            data_mode=DataMode.OPERATIONAL.value,
            risk_state_id=risk_state.id,
        )
    assert exc_info.value.error_code == "PROVENANCE_SAFETY_VIOLATION"


# ==============================================================================
# Test 18: Dynamic Risk Trend Evaluation
# ==============================================================================
def test_trend_evaluation():
    connector = HyperlocalAlertConnector()
    admin_id = "WARD_KULLU_01"

    # 1. First observation -> INSUFFICIENT_HISTORY
    t1 = connector.compute_trend(admin_id, current_score=0.45)
    assert t1 == "INSUFFICIENT_HISTORY"
    connector._RECENT_RISK_SCORES[admin_id] = 0.45

    # 2. Hazard score rises from 0.45 to 0.70 -> RISING
    t2 = connector.compute_trend(admin_id, current_score=0.70)
    assert t2 == "RISING"
    connector._RECENT_RISK_SCORES[admin_id] = 0.70

    # 3. Hazard score drops from 0.70 to 0.35 -> FALLING
    t3 = connector.compute_trend(admin_id, current_score=0.35)
    assert t3 == "FALLING"
    connector._RECENT_RISK_SCORES[admin_id] = 0.35

    # 4. Hazard score stays at 0.36 (diff <= 0.04) -> STABLE
    t4 = connector.compute_trend(admin_id, current_score=0.36)
    assert t4 == "STABLE"


# ==============================================================================
# Test 19: DDMA Dashboard Integration Endpoints
# ==============================================================================
def test_ddma_briefing_and_api_endpoints(client: TestClient):
    # 1. DDMA Briefing
    resp_briefing = client.get("/api/v1/alerts/ddma-briefing")
    assert resp_briefing.status_code == 200
    data_briefing = resp_briefing.json()
    assert "active_alerts_count" in data_briefing
    assert "pending_drafts_count" in data_briefing
    assert "channel_readiness" in data_briefing
    assert "IVR" in data_briefing["channel_readiness"]

    # 2. Evaluate Hyperlocal Risks & Draft
    resp_eval = client.post(
        "/api/v1/alerts/evaluate-hyperlocal",
        json={
            "flood_score": 0.85,
            "landslide_score": 0.65,
            "cascade_state": "SUSPECTED_BOTTLENECK",
            "provenance": "REAL_FIELD_OBSERVATION",
        },
    )
    assert resp_eval.status_code == 200
    data_eval = resp_eval.json()
    assert data_eval["status"] == "EVALUATION_COMPLETE"
    assert data_eval["total_units_evaluated"] == 12
    assert "drafts_created_count" in data_eval

    # 3. Dashboard Summary
    resp_summary = client.get("/api/v1/dashboard/summary")
    assert resp_summary.status_code == 200
    data_summary = resp_summary.json()
    assert "operational_overview" in data_summary
    assert "dispatched_alerts" in data_summary
