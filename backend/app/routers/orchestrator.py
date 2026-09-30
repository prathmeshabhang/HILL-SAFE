"""
orchestrator.py — FLOODY SHIELD Incident Response & Autonomous Orchestrator Router
==================================================================================
Exposes endpoints for:
  - Triggering autonomous multi-hazard incident pipelines
  - Querying active and historical incident briefings
  - Inspecting statutory CAP v1.2 XML dispatches
  - Managing incident lifecycle status (ACTIVE, CONTAINED, RESOLVED)
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ml.orchestrator.incident_manager import IncidentRecord, get_incident_manager

router = APIRouter(prefix="/api/v1/orchestrator", tags=["Incident Response & Orchestration"])


class TriggerIncidentRequest(BaseModel):
    incident_type: str = Field("NATURAL_DAM_BREACH", description="Type of incident (e.g. NATURAL_DAM_BREACH, CLOUDBURST_FLASH_FLOOD)")
    severity_level: Literal["CRITICAL", "SEVERE", "MODERATE"] = Field("CRITICAL", description="Severity grading")
    trigger_source: str = Field("SATELLITE_SYNTHESIS", description="Detection origin (e.g. SATELLITE_SYNTHESIS, IOT_GROUND_SENSOR)")
    trigger_location: str = Field("Larji_Sainj_Confluence", description="River reach or geographic sector")
    dam_height_m: float = Field(35.0, ge=5.0, le=200.0, description="Estimated dam height in meters")
    impounded_volume_m3: float = Field(8_500_000.0, ge=100_000.0, description="Impounded water reservoir volume in m3")
    rainfall_rate_mmh: float = Field(65.0, ge=0.0, description="Catchment rainfall rate in mm/hr")
    simulate_nh3_closure: bool = Field(True, description="Whether to simulate NH-3 highway severance")
    status: Literal["ACTIVE", "CONTAINED", "RESOLVED", "EXERCISE"] = Field("ACTIVE", description="Initial incident status")
    custom_id: Optional[str] = Field(None, description="Optional custom incident ID")


class UpdateStatusRequest(BaseModel):
    new_status: Literal["ACTIVE", "CONTAINED", "RESOLVED", "EXERCISE"]
    notes: str = Field("", description="Field operations or civil defense notes")


@router.post("/trigger-incident", summary="Trigger autonomous end-to-end incident response")
def trigger_incident(req: TriggerIncidentRequest) -> Dict[str, Any]:
    """
    Executes complete autonomous pipeline:
    M12 Dam Breach Simulation -> Exposure Overlay -> M15/M16 Safe Route Solving ->
    M20 Rescue Prioritization -> NDMA Sachet CAP v1.2 Bilingual Alert Generation.
    """
    mgr = get_incident_manager()
    record = mgr.trigger_incident(
        incident_type=req.incident_type,
        severity_level=req.severity_level,
        trigger_source=req.trigger_source,
        trigger_location=req.trigger_location,
        dam_height_m=req.dam_height_m,
        impounded_volume_m3=req.impounded_volume_m3,
        rainfall_rate_mmh=req.rainfall_rate_mmh,
        simulate_nh3_closure=req.simulate_nh3_closure,
        status=req.status,
        custom_id=req.custom_id,
    )
    return {
        "status": "success",
        "incident_id": record.incident_id,
        "incident": asdict(record),
    }


@router.get("/incidents", summary="List all active and historical incidents")
def list_incidents() -> Dict[str, Any]:
    mgr = get_incident_manager()
    incidents = mgr.list_incidents()
    return {
        "total_incidents": len(incidents),
        "incidents": [
            {
                "incident_id": i.incident_id,
                "timestamp_utc": i.timestamp_utc,
                "incident_type": i.incident_type,
                "severity_level": i.severity_level,
                "trigger_location": i.trigger_location,
                "status": i.status,
                "headline_en": i.cap_alert_summary_en,
                "headline_hi": i.cap_alert_summary_hi,
            }
            for i in incidents
        ],
    }


@router.get("/incidents/{incident_id}", summary="Get comprehensive incident briefing")
def get_incident_details(incident_id: str) -> Dict[str, Any]:
    mgr = get_incident_manager()
    record = mgr.get_incident(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return {
        "status": "success",
        "incident": asdict(record),
    }


@router.get("/incidents/{incident_id}/cap-xml", summary="Download official CAP v1.2 XML payload")
def get_incident_cap_xml(incident_id: str) -> Response:
    mgr = get_incident_manager()
    record = mgr.get_incident(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return Response(content=record.cap_alert_xml, media_type="application/xml")


@router.post("/incidents/{incident_id}/status", summary="Update incident status and append audit note")
def update_incident_status(incident_id: str, req: UpdateStatusRequest) -> Dict[str, Any]:
    mgr = get_incident_manager()
    record = mgr.update_incident_status(incident_id, req.new_status, req.notes)
    if not record:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return {
        "status": "success",
        "incident_id": incident_id,
        "new_status": record.status,
        "latest_audit_log": record.audit_log[-1],
    }
