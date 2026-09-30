"""
backend/tests/test_decision_pipeline.py
=======================================
Unit and integration tests for Decision Pipeline, Human Authorization Gateway,
RBAC permission boundaries, and audit trail verification.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.database.models import AlertDispatchModel, AuditLogModel
from backend.app.core.errors import AuthorizationError
from backend.app.decision.authorization_gateway import authorization_gateway, UserRole
from backend.app.decision.pipeline import decision_pipeline


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_decision_pipeline_execution_and_draft_alert(db_session):
    """Verifies complete end-to-end hazard chain execution and draft alert creation."""
    res = decision_pipeline.run_pipeline(
        db=db_session,
        incident_id="INC-TEST-9999",
        location_name="Larji_Sainj_Confluence",
        rainfall_intensity_mmh=75.0,
        dam_height_m=35.0,
        impounded_volume_m3=8_500_000.0,
        simulate_nh3_closure=True,
    )

    assert res["incident_id"] == "INC-TEST-9999"
    assert res["status"] == "AWAITING_COMMANDER_AUTHORIZATION"
    assert "draft_alert_id" in res
    assert "hazard_summary" in res
    assert "m12_cascade_breach" in res["hazard_summary"]
    assert "evacuation_support" in res

    # Verify drafted alert in database is PENDING_APPROVAL
    alert = db_session.query(AlertDispatchModel).filter_by(id=res["draft_alert_id"]).first()
    assert alert is not None
    assert alert.status == "PENDING_APPROVAL"
    assert alert.authorized_by == "PENDING_COMMANDER_SIGN_OFF"


def test_human_authorization_gateway_rejects_unauthorized_roles(db_session):
    """Verifies that non-commanders CANNOT authorize alert dispatches."""
    pipeline_res = decision_pipeline.run_pipeline(db=db_session)
    alert_id = pipeline_res["draft_alert_id"]

    # 1. OBSERVER attempt -> MUST FAIL
    with pytest.raises(AuthorizationError) as exc_info:
        authorization_gateway.authorize_alert_dispatch(
            db=db_session,
            alert_id=alert_id,
            actor_id="OBSERVER_USER_01",
            actor_role="OBSERVER",
            approval_token="valid-token-123456",
        )
    assert "Insufficient permissions" in str(exc_info.value)

    # 2. ANALYST attempt -> MUST FAIL
    with pytest.raises(AuthorizationError) as exc_info:
        authorization_gateway.authorize_alert_dispatch(
            db=db_session,
            alert_id=alert_id,
            actor_id="ANALYST_USER_01",
            actor_role="ANALYST",
            approval_token="valid-token-123456",
        )
    assert "Insufficient permissions" in str(exc_info.value)

    # 3. Verify alert remains PENDING_APPROVAL
    alert = db_session.query(AlertDispatchModel).filter_by(id=alert_id).first()
    assert alert.status == "PENDING_APPROVAL"


def test_human_authorization_gateway_approves_commander_and_audits(db_session):
    """Verifies that Senior Incident Commander can authorize dispatch and generates audit log."""
    pipeline_res = decision_pipeline.run_pipeline(db=db_session)
    alert_id = pipeline_res["draft_alert_id"]

    dispatched_alert = authorization_gateway.authorize_alert_dispatch(
        db=db_session,
        alert_id=alert_id,
        actor_id="DC_KULLU_OFFICER_01",
        actor_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="SECURE_COMMANDER_CRYPTO_TOKEN_9999",
        ip_address="10.0.1.5",
    )

    assert dispatched_alert.status == "DISPATCHED"
    assert dispatched_alert.authorized_by == "DC_KULLU_OFFICER_01"
    assert dispatched_alert.dispatched_at is not None

    # Verify immutable audit log
    audit_entry = (
        db_session.query(AuditLogModel)
        .filter_by(target_entity_id=alert_id, action="PUBLIC_ALERT_DISPATCH_AUTHORIZATION")
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.actor_id == "DC_KULLU_OFFICER_01"
    assert audit_entry.actor_role == "SENIOR_INCIDENT_COMMANDER"
    assert audit_entry.ip_address == "10.0.1.5"
