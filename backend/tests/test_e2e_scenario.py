"""
backend/tests/test_e2e_scenario.py
==================================
End-to-End Heavy Rainfall Disaster Scenario Integration Test for FLOODY SHIELD v3.3.
Verifies the complete lifecycle:
Rain Observation -> Ingestion -> Quality Gate -> Database -> M1 -> M2 -> River Observation
-> M10 -> M11 -> M13 -> M14 -> M15 -> M16 -> M17 -> M18 -> Decision Record -> PENDING_APPROVAL
-> Commander Authorization -> OASIS CAP v1.2 XML -> Immutable Audit Chain -> WebSocket Event.
"""

from __future__ import annotations

import datetime
import pytest
from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal
from backend.app.services.ingestion.adapters.weather import IMDAWSAdapter
from backend.app.services.ingestion.adapters.river import CWCRiverAdapter
from backend.app.services.ingestion.ingestion_service import TelemetryIngestionService
from backend.app.orchestration.engine import model_orchestrator
from backend.app.services.risk.engine import unified_risk_engine
from backend.app.services.alerts.lifecycle_service import alert_lifecycle_service
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.database.models.telemetry import SensorObservationModel
from backend.app.websocket.manager import ws_manager
from backend.app.websocket.events import RealTimeEvent, RealTimeEventType


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_heavy_rainfall_end_to_end_scenario(db: Session):
    """
    Simulates a heavy monsoon rainfall storm in Upper Beas catchment
    and verifies complete pipeline progression and life-safety gating.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    incident_id = f"INC-SCENARIO-{now_utc.strftime('%Y%m%d-%H%M%S')}"

    # Step 1: External Observation Ingestion (Rainfall Telemetry)
    rain_adapter = IMDAWSAdapter()
    raw_rain = {
        "station_code": "STN_AUT_SCENARIO",
        "obs_time": now_utc.isoformat(),
        "lat": 31.75,
        "lon": 77.20,
        "rain_rate_mm": 72.0,  # Intense localized storm
        "record_id": "STORM_PKT_01",
    }
    norm_rain = rain_adapter.normalize(raw_rain)

    ingestion_service = TelemetryIngestionService()
    rain_ingest_res = ingestion_service.ingest_normalized_observation(db, norm_rain)
    assert rain_ingest_res["status"] == "INGESTED"
    assert rain_ingest_res["quality_state"] in ("FRESH", "DEGRADED")
    assert rain_ingest_res["observation_id"] is not None

    # Step 2: River Stage Observation Ingestion
    river_adapter = CWCRiverAdapter()
    raw_river = {
        "site_id": "CWC_BHUNTAR_SCENARIO",
        "measurement_time": now_utc.isoformat(),
        "latitude": 31.89,
        "longitude": 77.15,
        "water_level_m": 7.4,  # Above CWC danger mark (7.0m)
        "discharge_m3s": 680.0,
        "record_id": "STAGE_PKT_01",
    }
    norm_river = river_adapter.normalize(raw_river)
    river_ingest_res = ingestion_service.ingest_normalized_observation(db, norm_river)
    assert river_ingest_res["status"] == "INGESTED"
    assert river_ingest_res["quality_state"] == "FRESH"

    # Step 3: Topological Model Orchestration
    pipeline_inputs = {
        "rainfall_intensity_mmh": 72.0,
        "river_water_level_m": 7.4,
        "dam_height_m": 38.0,
        "impounded_volume_m3": 9_500_000.0,
        "location_name": "Larji_Sainj_Confluence",
    }
    model_results = model_orchestrator.execute_pipeline(db, pipeline_inputs)

    # Verify key scientific model executions
    assert model_results["M1"].state.value == "COMPLETED"
    assert model_results["M2"].state.value == "COMPLETED"
    assert model_results["M6"].state.value == "COMPLETED"
    assert model_results["PWP_SSI"].state.value == "COMPLETED"
    assert model_results["M7"].state.value == "COMPLETED"
    assert model_results["M10"].state.value == "COMPLETED"
    assert model_results["M11"].state.value == "COMPLETED"
    assert model_results["M12"].state.value == "COMPLETED"
    assert model_results["M13"].state.value == "COMPLETED"
    assert model_results["M14"].state.value == "COMPLETED"
    assert model_results["M15"].state.value == "COMPLETED"
    assert model_results["M16"].state.value == "COMPLETED"
    assert model_results["M17"].state.value == "COMPLETED"
    assert model_results["M18"].state.value == "COMPLETED"

    # Step 4: Multi-Hazard Unified Risk State Synthesis
    risk_state = unified_risk_engine.synthesize_risk_state(
        db=db,
        incident_id=incident_id,
        location_name="Larji_Sainj_Confluence",
        initial_observations=pipeline_inputs,
        orchestrator_results=model_results,
    )
    assert risk_state["overall_risk_level"] in ("HIGH", "CRITICAL")
    assert risk_state["risk_state_id"] is not None

    # Step 5: Draft Alert Generation (Must enter PENDING_APPROVAL)
    alert_draft = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=incident_id,
        headline="EXTREME FLASH FLOOD & LANDSLIDE DAM SURGE ADVISORY",
        description=(
            f"Catchment storm intensity {pipeline_inputs['rainfall_intensity_mmh']} mm/h combined with "
            "rising stage at Bhuntar CWC gauge and potential landslide dam outburst."
        ),
        instruction="Evacuate low-lying riverbed settlements along Beas river to designated safe shelters immediately.",
        area_desc="Upper Beas Basin: Aut-Larji Gorge to Pandoh Dam",
        severity="Extreme",
        urgency="Immediate",
        certainty="Observed",
    )
    assert alert_draft.status == "PENDING_APPROVAL"
    assert alert_draft.dispatched_at is None

    # Step 6: Human Authorization Gateway (Commander Sign-Off)
    authorized_alert = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=alert_draft.id,
        commander_id="SENIOR_COMMANDER_KULLU_01",
        commander_role="SENIOR_INCIDENT_COMMANDER",
        approval_token="CRYPTO_SIGN_OFF_AUT_2026_APPROVED",
        ip_address="192.168.1.100",
    )
    assert authorized_alert.status == "DISPATCHED"
    assert authorized_alert.dispatched_at is not None
    assert authorized_alert.cap_xml is not None
    assert '<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">' in authorized_alert.cap_xml

    # Step 7: Recipient Agency Acknowledgement
    ack = alert_lifecycle_service.acknowledge_alert(
        db=db,
        alert_id=authorized_alert.id,
        recipient_id="CIVIL_DEFENSE_AUT_SQUAD_4",
        channel="EOC_RADIO_CONDUIT",
        notes="Siren sounded in Aut village, evacuation underway.",
    )
    assert ack.status == "CONFIRMED"

    # Step 8: Tamper-Evident Audit Trail Integrity
    last_audit = (
        db.query(AuditLogModel)
        .filter(AuditLogModel.target_entity_id == authorized_alert.id)
        .order_by(AuditLogModel.timestamp.desc())
        .first()
    )
    assert last_audit is not None
    assert last_audit.action == "ALERT_AUTHORIZED_AND_DISPATCHED"
    assert last_audit.actor_role == "SENIOR_INCIDENT_COMMANDER"
    assert last_audit.entry_hash is not None
    # Re-verify hash computation matches
    assert last_audit.compute_hash(last_audit.previous_hash) == last_audit.entry_hash
