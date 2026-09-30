"""
backend/app/api/v1/endpoints/pipeline.py
========================================
REST API endpoints for the Hazard Decision Pipeline and Human Authorization Gateway.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.decision.pipeline import decision_pipeline
from backend.app.decision.authorization_gateway import authorization_gateway

router = APIRouter(prefix="/api/v1/decision/pipeline", tags=["Hazard Decision Pipeline"])


class ExecutePipelineRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Optional incident ID")
    location_name: str = Field("Larji_Sainj_Confluence", description="Target river reach or gorge")
    rainfall_intensity_mmh: float = Field(65.0, ge=0.0, description="Precipitation rate in mm/h")
    dam_height_m: float = Field(35.0, ge=5.0, description="Dam height in meters")
    impounded_volume_m3: float = Field(8_500_000.0, ge=100_000.0, description="Impounded reservoir volume")
    simulate_nh3_closure: bool = Field(True, description="Whether to simulate NH-3 highway severance")


class AuthorizeAlertRequest(BaseModel):
    actor_id: str = Field(..., description="ID of authorizing official")
    actor_role: str = Field(..., description="Role must be SENIOR_INCIDENT_COMMANDER")
    approval_token: str = Field(..., min_length=8, description="Cryptographic commander sign-off token")


@router.post("/execute", summary="Execute end-to-end multi-hazard decision pipeline")
def execute_hazard_pipeline(
    req: ExecutePipelineRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes full hazard chain (M1-M20), produces decision briefing,
    and drafts CAP v1.2 alert in PENDING_APPROVAL status.
    """
    return decision_pipeline.run_pipeline(
        db=db,
        incident_id=req.incident_id,
        location_name=req.location_name,
        rainfall_intensity_mmh=req.rainfall_intensity_mmh,
        dam_height_m=req.dam_height_m,
        impounded_volume_m3=req.impounded_volume_m3,
        simulate_nh3_closure=req.simulate_nh3_closure,
    )


@router.post("/alerts/{alert_id}/authorize", summary="Senior Incident Commander CAP Alert Authorization")
def authorize_alert(
    alert_id: str,
    req: AuthorizeAlertRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Cryptographically authorizes and transitions a CAP v1.2 emergency alert from
    PENDING_APPROVAL to DISPATCHED. Generates an immutable audit log entry.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    dispatched = authorization_gateway.authorize_alert_dispatch(
        db=db,
        alert_id=alert_id,
        actor_id=req.actor_id,
        actor_role=req.actor_role,
        approval_token=req.approval_token,
        ip_address=client_ip,
    )
    return {
        "status": "SUCCESS",
        "message": f"Alert {dispatched.cap_identifier} successfully authorized and dispatched.",
        "alert": dispatched.to_dict(),
    }
