"""
backend/app/api/v1/endpoints/risk.py
====================================
Authoritative REST API endpoints for unified multi-hazard risk state retrieval.
Transparently separates hazard probabilities, composite risk, confidence, quality, and impact.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models.risk import RiskStateModel, RiskZoneModel
from backend.app.services.risk.engine import unified_risk_engine

router = APIRouter(prefix="/api/v1/risk", tags=["Unified Multi-Hazard Risk State"])


@router.get("/current", summary="Get authoritative current basin risk state")
def get_current_risk(
    location_name: Optional[str] = Query(None, description="Specific corridor/location filter"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    risk = unified_risk_engine.get_current_risk(db, location_name=location_name)
    if not risk:
        return {
            "status": "NO_ACTIVE_RISK_ASSESSMENT",
            "overall_risk_level": "LOW",
            "confidence_state": "UNAVAILABLE",
            "message": "No active multi-hazard risk assessment recorded.",
        }
    return risk


@router.get("/history", summary="Query historical risk state evaluations")
def get_risk_history(
    incident_id: Optional[str] = Query(None, description="Filter by incident UUID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    records = unified_risk_engine.get_risk_history(db, incident_id=incident_id, limit=limit, offset=offset)
    return {
        "total": len(records),
        "limit": limit,
        "offset": offset,
        "risk_states": records,
    }


@router.get("/zones", summary="List spatial risk zone corridors")
def get_risk_zones(
    risk_state_id: Optional[str] = Query(None, description="Filter by RiskState UUID"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (CRITICAL, HIGH, MODERATE, LOW)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    query = db.query(RiskZoneModel)
    if risk_state_id:
        query = query.filter(RiskZoneModel.risk_state_id == risk_state_id)
    if risk_level:
        query = query.filter(RiskZoneModel.risk_level == risk_level.upper())

    zones = query.all()
    return {
        "total_zones": len(zones),
        "zones": [z.to_dict() for z in zones],
    }


@router.get("/{incident_id}", summary="Get consolidated risk state for a specific incident")
def get_incident_risk(
    incident_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    risk = unified_risk_engine.get_incident_risk(db, incident_id)
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk state for incident '{incident_id}' not found")
    return risk
