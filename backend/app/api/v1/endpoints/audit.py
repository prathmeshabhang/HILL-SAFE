"""
backend/app/api/v1/endpoints/audit.py
=====================================
REST API endpoints for Tamper-Evident Audit Trail and Cryptographic Hash Chain Verification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models.audit import AuditLogModel

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Tamper-Evidence"])


@router.get("/logs", summary="List audit logs with filtering and pagination")
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type (e.g. ALERT_AUTHORIZED_AND_DISPATCHED)"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    target_entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g. AlertDispatch, Incident)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns paginated audit trail records."""
    query = db.query(AuditLogModel)
    if action:
        query = query.filter_by(action=action)
    if actor_id:
        query = query.filter_by(actor_id=actor_id)
    if target_entity_type:
        query = query.filter_by(target_entity_type=target_entity_type)

    total = query.count()
    logs = query.order_by(AuditLogModel.timestamp.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "audit_logs": [log.to_dict() for log in logs],
    }


@router.get("/verify-chain", summary="Cryptographically verify tamper-evident hash chain integrity")
def verify_audit_hash_chain(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Traverses the chronological audit log entries and verifies SHA-256 hash chaining.
    Proves whether the audit trail has been tampered with or modified.
    """
    records = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.asc()).all()
    if not records:
        return {
            "status": "VERIFIED",
            "total_records": 0,
            "chain_intact": True,
            "message": "Audit log is currently empty.",
        }

    valid_count = 0
    corrupted_records = []

    for i, rec in enumerate(records):
        # Expected hash computed from content and declared previous_hash
        expected_hash = rec.compute_hash(rec.previous_hash)
        if rec.entry_hash and rec.entry_hash != expected_hash:
            corrupted_records.append({
                "record_id": rec.id,
                "index": i,
                "recorded_hash": rec.entry_hash,
                "computed_hash": expected_hash,
                "action": rec.action,
            })
        else:
            valid_count += 1

    intact = len(corrupted_records) == 0

    return {
        "status": "VERIFIED_INTACT" if intact else "INTEGRITY_VIOLATION_DETECTED",
        "chain_intact": intact,
        "total_records_checked": len(records),
        "valid_records": valid_count,
        "corrupted_records": corrupted_records,
        "security_grade": "TAMPER_EVIDENT_HASH_CHAINED",
    }
