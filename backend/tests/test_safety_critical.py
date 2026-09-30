"""
backend/tests/test_safety_critical.py
=====================================
The 10 Mandatory Life-Safety & Scientific Integrity Regression Tests for FLOODY SHIELD v3.3.
Enforces strict boundaries around AI autonomism, role-based authorization,
quality gating, model failure visibility, deduplication, and provenance traceability.
"""

from __future__ import annotations

import datetime
import pytest
from sqlalchemy.orm import Session

from backend.app.core.errors import AuthorizationError, DataQualityError
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.model_run import ModelRunModel
from backend.app.database.models.telemetry import SensorObservationModel
from backend.app.database.session import SessionLocal
from backend.app.decision.authorization_gateway import HumanAuthorizationGateway, UserRole
from backend.app.decision.pipeline import HazardDecisionPipeline
from backend.app.orchestration.engine import ModelOrchestrator
from backend.app.orchestration.graph import MODEL_GRAPH, ModelNodeDef
from backend.app.orchestration.state import DependencyType, ExecutionState
from backend.app.services.alerts.lifecycle_service import AlertLifecycleService
from backend.app.services.ingestion.adapters.weather import IMDAWSAdapter
from backend.app.services.ingestion.ingestion_service import TelemetryIngestionService
from backend.app.services.ingestion.quality_gate import TelemetryQualityGate, QualityState


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# Test 1: An AI prediction cannot directly dispatch a public alert
# ---------------------------------------------------------------------------
def test_ai_prediction_cannot_directly_dispatch_alert(db: Session):
    """
    SAFETY INVARIANT 1:
    The automated hazard pipeline must NEVER dispatch a public alert on its own.
    Pipeline outputs must remain strictly in PENDING_APPROVAL status.
    """
    pipeline = HazardDecisionPipeline()
    result = pipeline.run_pipeline(
        db=db,
        location_name="Aut_Larji_Gorge",
        rainfall_intensity_mmh=95.0,
        dam_height_m=45.0,
        impounded_volume_m3=10_000_000.0,
    )

    assert result["status"] == "AWAITING_COMMANDER_AUTHORIZATION"
    draft_id = result["draft_alert_id"]

    # Verify directly in the database
    alert = db.query(AlertDispatchModel).filter_by(id=draft_id).first()
    assert alert is not None
    assert alert.status == "PENDING_APPROVAL"
    assert alert.authorized_by == "PENDING_COMMANDER_SIGN_OFF"
    assert alert.dispatched_at is None


# ---------------------------------------------------------------------------
# Test 2: An OBSERVER cannot authorize an alert
# ---------------------------------------------------------------------------
def test_observer_cannot_authorize_alert(db: Session):
    """
    SAFETY INVARIANT 2:
    An actor with OBSERVER role must be rejected with AuthorizationError (HTTP 403 equivalent).
    """
    lifecycle = AlertLifecycleService()
    alert = lifecycle.create_alert_draft(
        db=db,
        incident_id="INC-OBS-TEST",
        headline="FLASH FLOOD THREAT",
        description="Dangerous river rise",
        instruction="Evacuate low ground",
        area_desc="Upper Beas Basin",
    )

    with pytest.raises(AuthorizationError) as exc_info:
        lifecycle.authorize_and_dispatch(
            db=db,
            alert_id=alert.id,
            commander_id="observer_user_01",
            commander_role=UserRole.OBSERVER.value,
            approval_token="valid_cryptographic_token_12345",
        )
    assert "Unauthorized" in str(exc_info.value)
    # Assert database state was not modified
    db.refresh(alert)
    assert alert.status == "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# Test 3: An ANALYST cannot authorize an alert
# ---------------------------------------------------------------------------
def test_analyst_cannot_authorize_alert(db: Session):
    """
    SAFETY INVARIANT 3:
    An actor with ANALYST role has model and data access, but lacks statutory command authority.
    Must be rejected with AuthorizationError.
    """
    lifecycle = AlertLifecycleService()
    alert = lifecycle.create_alert_draft(
        db=db,
        incident_id="INC-ANALYST-TEST",
        headline="LANDSLIDE DAM WARNING",
        description="Lake breach likely",
        instruction="Follow bypass corridor",
        area_desc="Larji Gorge",
    )

    with pytest.raises(AuthorizationError) as exc_info:
        lifecycle.authorize_and_dispatch(
            db=db,
            alert_id=alert.id,
            commander_id="analyst_user_02",
            commander_role=UserRole.ANALYST.value,
            approval_token="valid_cryptographic_token_12345",
        )
    assert "Unauthorized" in str(exc_info.value)
    db.refresh(alert)
    assert alert.status == "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# Test 4: A SENIOR_INCIDENT_COMMANDER with invalid credentials cannot authorize
# ---------------------------------------------------------------------------
def test_commander_invalid_credentials_rejected(db: Session):
    """
    SAFETY INVARIANT 4:
    Even a verified SENIOR_INCIDENT_COMMANDER must provide a valid, non-empty cryptographic approval token.
    Short, blank, or missing tokens must fail.
    """
    lifecycle = AlertLifecycleService()
    alert = lifecycle.create_alert_draft(
        db=db,
        incident_id="INC-TOKEN-TEST",
        headline="EMERGENCY DAM BREACH ALERT",
        description="Massive surge expected",
        instruction="Take high ground",
        area_desc="Bhuntar Corridor",
    )

    # Missing / empty token
    with pytest.raises(AuthorizationError) as exc_info:
        lifecycle.authorize_and_dispatch(
            db=db,
            alert_id=alert.id,
            commander_id="col_sharma_commander",
            commander_role=UserRole.SENIOR_INCIDENT_COMMANDER.value,
            approval_token="",
        )
    assert "cryptographic authorization token is required" in str(exc_info.value)

    # Token too short (< 8 chars)
    with pytest.raises(AuthorizationError) as exc_info_short:
        lifecycle.authorize_and_dispatch(
            db=db,
            alert_id=alert.id,
            commander_id="col_sharma_commander",
            commander_role=UserRole.SENIOR_INCIDENT_COMMANDER.value,
            approval_token="abc",
        )
    assert "cryptographic authorization token is required" in str(exc_info_short.value)


# ---------------------------------------------------------------------------
# Test 5: A valid commander can authorize a valid pending alert
# ---------------------------------------------------------------------------
def test_valid_commander_authorizes_pending_alert(db: Session):
    """
    SAFETY INVARIANT 5:
    A verified commander with a valid token successfully transitions an alert to DISPATCHED,
    renders OASIS CAP v1.2 XML, and logs an immutable audit trail entry.
    """
    lifecycle = AlertLifecycleService()
    alert = lifecycle.create_alert_draft(
        db=db,
        incident_id="INC-AUTH-OK",
        headline="UPPER BEAS FLASH FLOOD WARNING",
        description="Severe water level rise at Bhuntar gauge.",
        instruction="Avoid riverbed and stay above 1200m elevation.",
        area_desc="Bhuntar to Pandoh Corridor",
    )

    authorized_alert = lifecycle.authorize_and_dispatch(
        db=db,
        alert_id=alert.id,
        commander_id="commander_verma_007",
        commander_role=UserRole.SENIOR_INCIDENT_COMMANDER.value,
        approval_token="SECRET_HPSDMA_TOKEN_2026_DISPATCH",
        ip_address="10.24.18.5",
    )

    assert authorized_alert.status == "DISPATCHED"
    assert authorized_alert.authorized_by == "commander_verma_007"
    assert authorized_alert.dispatched_at is not None
    assert authorized_alert.cap_xml is not None
    assert '<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">' in authorized_alert.cap_xml
    assert alert.cap_identifier in authorized_alert.cap_xml


# ---------------------------------------------------------------------------
# Test 6: A CRITICAL_ERROR quality state blocks unsafe decision execution
# ---------------------------------------------------------------------------
def test_critical_error_quality_state_blocks_decision(db: Session):
    """
    SAFETY INVARIANT 6:
    Telemetry flagged with physical bounds violation (e.g. negative rain or stage)
    triggers DataQualityError with CRITICAL_ERROR state and blocks ingestion.
    """
    gate = TelemetryQualityGate()

    # Negative rainfall
    with pytest.raises(DataQualityError) as exc_rain:
        gate.validate_physical_limits({"rainfall_rate_mmh": -15.0})
    assert "Negative rainfall rate" in str(exc_rain.value)
    assert exc_rain.value.details["quality_state"] == QualityState.CRITICAL_ERROR.value

    # Negative river stage
    with pytest.raises(DataQualityError) as exc_stage:
        gate.validate_physical_limits({"water_level_m": -2.0})
    assert "Negative river stage" in str(exc_stage.value)
    assert exc_stage.value.details["quality_state"] == QualityState.CRITICAL_ERROR.value

    # Coordinates outside AOI
    with pytest.raises(DataQualityError) as exc_geo:
        gate.validate_spatial_bounds(latitude=25.0, longitude=85.0)
    assert "outside Upper Beas catchment AOI" in str(exc_geo.value)


# ---------------------------------------------------------------------------
# Test 7: A failed model does not become probability 0 or 0.5
# ---------------------------------------------------------------------------
def test_failed_model_does_not_become_zero_probability(db: Session):
    """
    SAFETY INVARIANT 7:
    If a model fails during orchestration, it must explicitly record FAILED state and error message.
    It must NEVER be silently mapped to 0.0 or 0.5, which would disguise an error as low or moderate risk.
    """
    # Create custom graph with a deliberately broken model
    test_graph = {
        "M_FAILING": ModelNodeDef(
            model_id="M_FAILING",
            model_name="Broken Model for Test",
            adapter_key="NON_EXISTENT_ADAPTER_KEY",
            evidence_status="TEST_STUB",
            dependencies={},
            is_root=True,
        )
    }
    orchestrator = ModelOrchestrator(graph=test_graph)
    results = orchestrator.execute_pipeline(db, {})

    node_res = results["M_FAILING"]
    assert node_res.state == ExecutionState.FAILED
    assert node_res.output == {}
    assert node_res.error_message is not None
    assert "No adapter registered" in node_res.error_message

    # Verify persisted ModelRun in database
    run_record = (
        db.query(ModelRunModel)
        .filter_by(model_id="M_FAILING")
        .order_by(ModelRunModel.run_timestamp.desc())
        .first()
    )
    assert run_record is not None
    assert run_record.status == "FAILED"
    assert run_record.quality_state == "CRITICAL_ERROR"


# ---------------------------------------------------------------------------
# Test 8: A duplicate observation does not create duplicate logical records
# ---------------------------------------------------------------------------
def test_duplicate_observation_deduplicated(db: Session):
    """
    SAFETY INVARIANT 8:
    Re-transmitting the exact same observation twice must be recognized as a duplicate
    using its idempotency hash and MUST NOT create a second logical database record.
    """
    ingestion = TelemetryIngestionService()
    adapter = IMDAWSAdapter()

    obs_time = datetime.datetime.now(datetime.timezone.utc)
    raw_payload = {
        "station_code": "STN_DEDUP_TEST_01",
        "obs_time": obs_time.isoformat(),
        "lat": 31.95,
        "lon": 77.10,
        "rain_rate_mm": 42.5,
        "record_id": "PACKET_1001",
    }

    norm1 = adapter.normalize(raw_payload)
    res1 = ingestion.ingest_normalized_observation(db, norm1)
    assert res1["status"] == "INGESTED"
    assert res1["is_duplicate"] is False
    obs_id_1 = res1["observation_id"]

    # Ingest duplicate observation
    norm2 = adapter.normalize(raw_payload)
    res2 = ingestion.ingest_normalized_observation(db, norm2)
    assert res2["status"] == "DUPLICATE_IGNORED"
    assert res2["is_duplicate"] is True
    assert res2["observation_id"] == obs_id_1

    # Verify only 1 record exists with this idempotency hash
    matching = (
        db.query(SensorObservationModel)
        .filter_by(idempotency_hash=norm1.idempotency_hash)
        .all()
    )
    assert len(matching) == 1


# ---------------------------------------------------------------------------
# Test 9: A stale observation cannot silently appear fresh
# ---------------------------------------------------------------------------
def test_stale_observation_flagged(db: Session):
    """
    SAFETY INVARIANT 9:
    Observations older than the staleness threshold (> 3 hours) must be explicitly flagged
    as STALE and older than 24 hours as EXPIRED. They cannot silently appear as FRESH.
    """
    gate = TelemetryQualityGate(stale_threshold_hours=3.0, expired_threshold_hours=24.0)

    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Fresh observation (30 mins old)
    fresh_time = now - datetime.timedelta(minutes=30)
    eval_fresh = gate.validate_temporal_freshness(fresh_time)
    assert eval_fresh["quality_state"] == QualityState.FRESH.value
    assert eval_fresh["is_fresh"] is True

    # 2. Stale observation (5 hours old)
    stale_time = now - datetime.timedelta(hours=5)
    eval_stale = gate.validate_temporal_freshness(stale_time)
    assert eval_stale["quality_state"] == QualityState.STALE.value
    assert eval_stale["is_fresh"] is False

    # 3. Expired observation (36 hours old)
    expired_time = now - datetime.timedelta(hours=36)
    eval_expired = gate.validate_temporal_freshness(expired_time)
    assert eval_expired["quality_state"] == QualityState.EXPIRED.value
    assert eval_expired["is_fresh"] is False


# ---------------------------------------------------------------------------
# Test 10: A model run can be traced to its input data
# ---------------------------------------------------------------------------
def test_model_run_traceability(db: Session):
    """
    SAFETY INVARIANT 10:
    Every model execution record must store its exact input_hash, output_hash,
    model_version, and execution timestamps for immutable scientific auditability.
    """
    orchestrator = ModelOrchestrator()
    inputs = {
        "M1": {
            "station_id": "STN_TRACE_TEST",
            "latitude": 31.75,
            "longitude": 77.20,
            "elevation_m": 1050.0,
            "slope_deg": 28.0,
            "r_1h": 50.0,
            "rolling_intensity_mmh": 50.0,
        }
    }
    results = orchestrator.execute_pipeline(db, inputs, target_nodes=["M1"])
    m1_res = results["M1"]
    assert m1_res.state == ExecutionState.COMPLETED
    assert len(m1_res.input_hash) == 64  # Valid SHA-256
    assert len(m1_res.output_hash) == 64

    # Query DB record directly
    db_run = (
        db.query(ModelRunModel)
        .filter_by(input_hash=m1_res.input_hash)
        .first()
    )
    assert db_run is not None
    assert db_run.model_id == "M1"
    assert db_run.status == "COMPLETED"
    assert db_run.execution_time_ms > 0.0
    assert db_run.model_version == "3.3.0"
    assert db_run.input_hash == m1_res.input_hash
    assert db_run.output_hash == m1_res.output_hash
