"""
backend/tests/test_database_layer.py
====================================
Unit tests for SQLAlchemy models, session management, transactions, and rollbacks.
"""

from __future__ import annotations

import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.database.models import (
    IncidentModel,
    SensorStationModel,
    SensorObservationModel,
    ModelRunModel,
    AlertDispatchModel,
    EvacuationRouteModel,
    AuditLogModel,
)


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_incident_model_crud(test_db):
    incident = IncidentModel(
        id="INC-TEST-001",
        incident_type="NATURAL_DAM_BREACH",
        severity_level="CRITICAL",
        trigger_location="Larji_Sainj_Confluence",
        dam_height_m=35.0,
        impounded_volume_m3=8_500_000.0,
        rainfall_rate_mmh=72.5,
        status="ACTIVE",
    )
    test_db.add(incident)
    test_db.commit()

    retrieved = test_db.query(IncidentModel).filter_by(id="INC-TEST-001").first()
    assert retrieved is not None
    assert retrieved.incident_type == "NATURAL_DAM_BREACH"
    assert retrieved.dam_height_m == 35.0
    d = retrieved.to_dict()
    assert d["id"] == "INC-TEST-001"
    assert d["status"] == "ACTIVE"


def test_sensor_station_and_observation_relationship(test_db):
    station = SensorStationModel(
        id="STN_MANALI_01",
        name="Manali River Observation Post",
        station_type="RIVER_GAUGE",
        latitude=32.2396,
        longitude=77.1887,
        elevation_m=2050.0,
        river_basin="Upper Beas Basin",
    )
    test_db.add(station)
    test_db.commit()

    obs = SensorObservationModel(
        station_id="STN_MANALI_01",
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        water_level_m=4.25,
        rainfall_rate_mmh=45.0,
        is_anomalous=False,
    )
    test_db.add(obs)
    test_db.commit()

    stn = test_db.query(SensorStationModel).filter_by(id="STN_MANALI_01").first()
    assert len(stn.observations) == 1
    assert stn.observations[0].water_level_m == 4.25
    assert stn.observations[0].station.name == "Manali River Observation Post"


def test_model_run_provenance_logging(test_db):
    run = ModelRunModel(
        model_id="M12",
        model_name="Compound Cascade Dam Breach",
        execution_time_ms=145.2,
        input_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        output_summary="Peak breach discharge: 2840 m3/s",
        confidence_score=0.92,
        status="SUCCESS",
    )
    test_db.add(run)
    test_db.commit()

    retrieved = test_db.query(ModelRunModel).filter_by(model_id="M12").first()
    assert retrieved is not None
    assert retrieved.confidence_score == 0.92
    assert "2840" in retrieved.output_summary


def test_alert_dispatch_and_audit_trail(test_db):
    alert = AlertDispatchModel(
        incident_id=None,
        cap_identifier="CAP-HPSDMA-2026-0001",
        alert_type="Alert",
        severity="Extreme",
        urgency="Immediate",
        certainty="Observed",
        headline="FLASH FLOOD & DAM OUTBURST EVACUATION ORDER",
        description="Immediate evacuation ordered for Pandoh downstream sector.",
        area_desc="Pandoh to Aut River Corridor",
        authorized_by="CMD_HPSDMA_DEPUTY_COMMISSIONER",
        status="DISPATCHED",
    )
    audit = AuditLogModel(
        action="ALERT_DISPATCH_AUTHORIZATION",
        actor_id="OFFICER_HP_7719",
        actor_role="SENIOR_INCIDENT_COMMANDER",
        target_entity_type="AlertDispatch",
        target_entity_id="CAP-HPSDMA-2026-0001",
        changes='{"status": "DISPATCHED", "authorized": true}',
    )
    test_db.add_all([alert, audit])
    test_db.commit()

    saved_alert = test_db.query(AlertDispatchModel).filter_by(cap_identifier="CAP-HPSDMA-2026-0001").first()
    saved_audit = test_db.query(AuditLogModel).filter_by(actor_id="OFFICER_HP_7719").first()

    assert saved_alert is not None
    assert saved_alert.status == "DISPATCHED"
    assert saved_audit is not None
    assert saved_audit.actor_role == "SENIOR_INCIDENT_COMMANDER"


def test_session_rollback_on_integrity_error(test_db):
    # SensorObservationModel requires a valid station_id FK if enforced, or we can trigger unique constraint
    incident = IncidentModel(id="INC-DUP", incident_type="FLOOD", trigger_location="Kullu")
    test_db.add(incident)
    test_db.commit()

    # Attempt duplicate insert
    dup = IncidentModel(id="INC-DUP", incident_type="LANDSLIDE", trigger_location="Manali")
    test_db.add(dup)
    import warnings
    from sqlalchemy.exc import SAWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SAWarning)
        with pytest.raises(Exception):
            test_db.commit()

    test_db.rollback()
    # Ensure session recovered and can query original record
    original = test_db.query(IncidentModel).filter_by(id="INC-DUP").first()
    assert original.incident_type == "FLOOD"
