"""
backend/app/api/v1/endpoints/alerts.py
======================================
REST API endpoints for Early Warning Alert Lifecycle Management,
Commander Sign-Off, OASIS CAP v1.2 XML serialization, and Acknowledgements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.services.alerts.lifecycle_service import alert_lifecycle_service

router = APIRouter(prefix="/api/v1/alerts", tags=["Early Warning & CAP Alerts"])


class CreateAlertDraftRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Associated Incident UUID")
    headline: str = Field(..., description="Alert headline in English")
    description: str = Field(..., description="Full multi-hazard scenario narrative")
    instruction: str = Field(..., description="Protective civil defense actions")
    area_desc: str = Field(..., description="Target geographic corridor")
    severity: str = Field("Extreme", description="Severity (Extreme, Severe, Moderate, Minor)")
    urgency: str = Field("Immediate", description="Urgency (Immediate, Expected, Future)")
    certainty: str = Field("Observed", description="Certainty (Observed, Likely, Possible)")
    polygon_geojson: Optional[str] = Field(None, description="GeoJSON polygon string")
    data_mode: Optional[str] = Field(None, description="Data mode: OPERATIONAL, SIMULATION, REPLAY, EXERCISE, TEST")
    risk_state_id: Optional[str] = Field(None, description="Optional associated Risk State UUID to inherit provenance")


class AuthorizeAlertRequest(BaseModel):
    actor_id: str = Field(..., description="Incident Commander identifier")
    actor_role: str = Field("SENIOR_INCIDENT_COMMANDER", description="Role (must be SENIOR_INCIDENT_COMMANDER)")
    approval_token: str = Field(..., description="Cryptographic authorization token")


class AcknowledgeAlertRequest(BaseModel):
    recipient_id: str = Field(..., description="Agency or operator identifier")
    channel: str = Field("EOC_DASHBOARD", description="Channel (SMS, SIREN, CAP_FEED, EOC_DASHBOARD)")
    notes: Optional[str] = Field(None, description="Field action notes")


@router.post("/draft", summary="Create early warning alert draft (PENDING_APPROVAL)")
def create_draft_alert(
    req: CreateAlertDraftRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Creates a new CAP alert record in PENDING_APPROVAL status.
    Cannot be dispatched to the public without explicit Commander authorization.
    Enforces safety boundary: non-operational risk states or simulation/replay
    cannot create live operational alert drafts.
    """
    alert = alert_lifecycle_service.create_alert_draft(
        db=db,
        incident_id=req.incident_id,
        headline=req.headline,
        description=req.description,
        instruction=req.instruction,
        area_desc=req.area_desc,
        severity=req.severity,
        urgency=req.urgency,
        certainty=req.certainty,
        polygon_geojson=req.polygon_geojson,
        data_mode=req.data_mode,
        risk_state_id=req.risk_state_id,
    )
    return {
        "status": "DRAFT_CREATED",
        "alert": alert.to_dict(),
    }


@router.post("/{alert_id}/authorize", summary="Commander authorization and CAP dispatch")
def authorize_alert(
    alert_id: str,
    req: AuthorizeAlertRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Statutory Commander Sign-off:
    Validates Senior Incident Commander authority and approval token,
    transitions status to DISPATCHED, renders OASIS CAP v1.2 XML, and logs to tamper-evident audit.
    """
    alert = alert_lifecycle_service.authorize_and_dispatch(
        db=db,
        alert_id=alert_id,
        commander_id=req.actor_id,
        commander_role=req.actor_role,
        approval_token=req.approval_token,
    )
    return {
        "status": "DISPATCHED",
        "alert": alert.to_dict(),
    }


@router.post("/{alert_id}/acknowledge", summary="Acknowledge alert reception")
def acknowledge_alert(
    alert_id: str,
    req: AcknowledgeAlertRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Records emergency agency reception acknowledgement."""
    ack = alert_lifecycle_service.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        recipient_id=req.recipient_id,
        channel=req.channel,
        notes=req.notes,
    )
    return {
        "status": "ACKNOWLEDGED",
        "acknowledgement": ack.to_dict(),
    }


class EvaluateHyperlocalAlertsRequest(BaseModel):
    flood_score: float = Field(0.70, ge=0.0, le=1.0, description="Basin flood hazard score")
    landslide_score: float = Field(0.60, ge=0.0, le=1.0, description="Basin landslide hazard score")
    cascade_state: str = Field("NOT_ESTABLISHED", description="Active river obstruction state")
    provenance: str = Field("REAL_FIELD_OBSERVATION", description="Data provenance mode")
    incident_id: Optional[str] = Field(None, description="Optional incident UUID")


@router.get("/ddma-briefing", summary="Get comprehensive DDMA / EOC operational alert briefing")
def get_ddma_briefing(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns aggregated active alerts, pending drafts, audit events, and channel readiness for EOC dashboard."""
    from backend.app.services.alerts.hyperlocal_connector import hyperlocal_alert_connector
    return hyperlocal_alert_connector.get_ddma_briefing(db)


@router.post("/evaluate-hyperlocal", summary="Evaluate Phase 04C hyperlocal risks and draft alerts")
def evaluate_hyperlocal_alerts(
    req: EvaluateHyperlocalAlertsRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Evaluates current 12 Wards and Gram Panchayats.
    Applies genuine trend analysis, deduplication, and escalation.
    Creates alert drafts for any units crossing warning thresholds.
    """
    from backend.app.services.gis.cascade_spatial_service import cascade_spatial_service
    from backend.app.services.alerts.hyperlocal_connector import hyperlocal_alert_connector

    units = cascade_spatial_service.aggregate_hyperlocal_risk(
        flood_hazard_score=req.flood_score,
        landslide_hazard_score=req.landslide_score,
        cascade_state=req.cascade_state,
        provenance=req.provenance,
    )

    results = hyperlocal_alert_connector.process_hyperlocal_risks(
        db=db,
        units=units,
        incident_id=req.incident_id,
    )

    drafts_created = [r for r in results if r["outcome"] == "DRAFT_CREATED"]
    escalations = [r for r in results if r["outcome"] == "ESCALATED"]
    suppressed = [r for r in results if r["outcome"] == "DUPLICATE_SUPPRESSED"]

    return {
        "status": "EVALUATION_COMPLETE",
        "total_units_evaluated": len(units),
        "drafts_created_count": len(drafts_created),
        "escalations_count": len(escalations),
        "duplicates_suppressed_count": len(suppressed),
        "results": results,
    }


@router.get("/{alert_id}", summary="Get alert details and CAP v1.2 XML")
def get_alert_detail(
    alert_id: str,
    format: str = Query("json", description="Output format: json or xml"),
    db: Session = Depends(get_db),
) -> Any:
    """Returns alert record details or raw OASIS CAP v1.2 XML document."""
    alert = db.query(AlertDispatchModel).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    if format.lower() == "xml":
        if alert.cap_xml:
            return Response(content=alert.cap_xml, media_type="application/xml")
        else:
            raise HTTPException(status_code=400, detail="CAP XML is not yet rendered for this draft alert.")

    return {
        "status": "success",
        "alert": alert.to_dict(),
        "has_xml": bool(alert.cap_xml),
    }


@router.get("", summary="List alerts with filtering")
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status (e.g. PENDING_APPROVAL, DISPATCHED, RESOLVED)"),
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns paginated list of alerts."""
    query = db.query(AlertDispatchModel)
    if status:
        query = query.filter_by(status=status)
    if incident_id:
        query = query.filter_by(incident_id=incident_id)

    total = query.count()
    items = query.order_by(AlertDispatchModel.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": [a.to_dict() for a in items],
    }


class CancelAlertRequest(BaseModel):
    actor_id: str = Field(..., description="Commander identifier")
    actor_role: str = Field("SENIOR_INCIDENT_COMMANDER", description="Role (must be SENIOR_INCIDENT_COMMANDER or ADMIN)")
    reason: str = Field("Threat abated / All-clear issued", description="Reason for cancellation")


@router.post("/{alert_id}/cancel", summary="Commander cancellation / all-clear")
def cancel_alert(
    alert_id: str,
    req: CancelAlertRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Cancels an active alert. Strictly restricted to SENIOR_INCIDENT_COMMANDER or ADMIN."""
    alert = alert_lifecycle_service.cancel_alert(
        db=db,
        alert_id=alert_id,
        commander_id=req.actor_id,
        commander_role=req.actor_role,
        cancellation_reason=req.reason,
    )
    return {"status": "CANCELLED", "alert": alert.to_dict()}
