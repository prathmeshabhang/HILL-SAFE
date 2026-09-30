"""
backend/app/api/v1/endpoints/incidents.py
=========================================
REST API endpoints for Multi-Hazard Incident Management, Complete Timeline Tracing, and Scenario Replay.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models.incident import IncidentModel
from backend.app.database.models.risk import RiskStateModel
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.model_run import ModelRunModel
from backend.app.database.models.evacuation import EvacuationRouteModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.services.incident.replay_service import replay_service

router = APIRouter(prefix="/api/v1/incidents", tags=["Incident Management & Provenance History"])


class CreateIncidentRequest(BaseModel):
    incident_type: str = Field(..., description="e.g. NATURAL_DAM_BREACH, CLOUDBURST_FLASH_FLOOD, LANDSLIDE_DAM")
    severity_level: str = Field("CRITICAL", description="CRITICAL, SEVERE, MODERATE")
    trigger_source: str = Field("SATELLITE_SYNTHESIS", description="SATELLITE_SYNTHESIS, IOT_GROUND_SENSOR")
    trigger_location: str = Field(..., description="e.g. Larji_Sainj_Confluence, Aut_Gorge")
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    dam_height_m: Optional[float] = Field(None)
    impounded_volume_m3: Optional[float] = Field(None)
    rainfall_rate_mmh: Optional[float] = Field(None)
    summary: Optional[str] = Field(None)


class HistoricalReplayRequest(BaseModel):
    scenario_name: str = Field("July_2023_Upper_Beas_Compound_Flood")
    rainfall_intensity_mmh: float = Field(85.0, ge=0.0, le=500.0)
    dam_height_m: float = Field(40.0, ge=5.0, le=150.0)
    impounded_volume_m3: float = Field(12_000_000.0, ge=100_000.0)
    river_water_level_m: float = Field(8.2, ge=0.0, le=50.0)


@router.post("", summary="Register or trigger new multi-hazard incident")
def create_incident(
    req: CreateIncidentRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Registers a new active civil defense incident."""
    inc_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    incident = IncidentModel(
        id=inc_id,
        incident_type=req.incident_type,
        severity_level=req.severity_level,
        trigger_source=req.trigger_source,
        trigger_location=req.trigger_location,
        latitude=req.latitude,
        longitude=req.longitude,
        dam_height_m=req.dam_height_m,
        impounded_volume_m3=req.impounded_volume_m3,
        rainfall_rate_mmh=req.rainfall_rate_mmh,
        status="ACTIVE",
        summary=req.summary or f"Operational incident initialized at {req.trigger_location}",
    )
    db.add(incident)
    db.commit()
    return {
        "status": "INCIDENT_CREATED",
        "incident": incident.to_dict(),
    }


@router.get("/{incident_id}", summary="Get full incident timeline, models, alerts, and audit provenance")
def get_incident_history(
    incident_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns the complete end-to-end incident history:
    Incident Details -> Associated Model Runs -> Synthesized Risk States -> Evacuation Routes -> Draft/Dispatched Alerts -> Audit Trail.
    """
    incident = db.query(IncidentModel).filter_by(id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    risk_states = db.query(RiskStateModel).filter_by(incident_id=incident_id).all()
    routes = db.query(EvacuationRouteModel).filter_by(incident_id=incident_id).all()
    alerts = db.query(AlertDispatchModel).filter_by(incident_id=incident_id).all()
    audits = (
        db.query(AuditLogModel)
        .filter(AuditLogModel.target_entity_id == incident_id)
        .order_by(AuditLogModel.timestamp.desc())
        .all()
    )

    return {
        "incident": incident.to_dict(),
        "risk_states": [r.to_dict() for r in risk_states],
        "evacuation_routes": [rt.to_dict() for rt in routes],
        "alerts": [a.to_dict() for a in alerts],
        "audit_trail": [ad.to_dict() for ad in audits],
    }


@router.get("", summary="List incidents with pagination")
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, CONTAINED, RESOLVED, EXERCISE)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns paginated list of operational incidents."""
    query = db.query(IncidentModel)
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    items = query.order_by(IncidentModel.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "incidents": [i.to_dict() for i in items],
    }


@router.post("/replay", summary="Trigger historical disaster scenario replay (mode=REPLAY)")
def trigger_historical_replay(
    req: HistoricalReplayRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes a historical event reconstruction through the complete pipeline.
    All outputs marked EXERCISE / REPLAY. Zero external alert broadcasts.
    """
    return replay_service.replay_scenario(
        db=db,
        scenario_name=req.scenario_name,
        rainfall_intensity_mmh=req.rainfall_intensity_mmh,
        dam_height_m=req.dam_height_m,
        impounded_volume_m3=req.impounded_volume_m3,
        river_water_level_m=req.river_water_level_m,
    )
