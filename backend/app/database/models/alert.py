"""
backend/app/database/models/alert.py
====================================
SQLAlchemy models for Early Warning Alert Dispatches (ITU-T X.1303 / NDMA CAP v1.2)
and Recipient Acknowledgements.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from backend.app.database.session import Base


class AlertDispatchModel(Base):
    __tablename__ = "alert_dispatches"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(64), ForeignKey("incidents.id"), nullable=True, index=True)
    cap_identifier = Column(String(128), nullable=False, unique=True)
    alert_type = Column(String(32), nullable=False, default="Alert")
    urgency = Column(String(32), nullable=False, default="Immediate")
    severity = Column(String(32), nullable=False, default="Extreme")
    certainty = Column(String(32), nullable=False, default="Observed")
    headline = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    instruction = Column(Text, nullable=True)
    area_desc = Column(String(255), nullable=False)
    polygon_geojson = Column(Text, nullable=True)
    cap_xml = Column(Text, nullable=True)  # Full rendered CAP v1.2 XML document

    authorized_by = Column(String(128), nullable=False)  # Senior Incident Commander ID
    # Status lifecycle: DRAFT, PENDING_APPROVAL, APPROVED, DISPATCHED, ACKNOWLEDGED, RESOLVED, REJECTED, DELIVERY_FAILED
    status = Column(String(32), nullable=False, default="PENDING_APPROVAL")
    dispatched_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        data_mode = "OPERATIONAL"
        if self.cap_identifier:
            cid = self.cap_identifier.upper()
            if "REPLAY" in cid:
                data_mode = "REPLAY"
            elif "SIMULATION" in cid:
                data_mode = "SIMULATION"
            elif "EXERCISE" in cid:
                data_mode = "EXERCISE"
            elif "TEST" in cid or "SYNTHETIC" in cid:
                data_mode = "TEST"
            elif "PROXY" in cid:
                data_mode = "PROXY"

        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "cap_identifier": self.cap_identifier,
            "data_mode": data_mode,
            "is_operational": data_mode == "OPERATIONAL",
            "alert_type": self.alert_type,
            "urgency": self.urgency,
            "severity": self.severity,
            "certainty": self.certainty,
            "headline": self.headline,
            "description": self.description,
            "instruction": self.instruction,
            "area_desc": self.area_desc,
            "polygon_geojson": self.polygon_geojson,
            "authorized_by": self.authorized_by,
            "status": self.status,
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AlertAcknowledgementModel(Base):
    __tablename__ = "alert_acknowledgements"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(64), ForeignKey("alert_dispatches.id"), nullable=False, index=True)
    recipient_id = Column(String(128), nullable=False)  # Agency or EOC commander ID
    channel = Column(String(32), nullable=False, default="EOC_DASHBOARD")  # SMS, SIREN, CAP_FEED, EOC_DASHBOARD
    status = Column(String(32), nullable=False, default="RECEIVED")  # RECEIVED, CONFIRMED, ACTION_TAKEN
    acknowledged_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    notes = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "recipient_id": self.recipient_id,
            "channel": self.channel,
            "status": self.status,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "notes": self.notes,
        }
