"""
backend/app/database/models/incident.py
========================================
SQLAlchemy model for Multi-Hazard Incident Management.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict
import uuid

from sqlalchemy import Column, DateTime, Float, String, Text

from backend.app.database.session import Base


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_type = Column(String(64), nullable=False)
    severity_level = Column(String(32), nullable=False, default="CRITICAL")
    trigger_source = Column(String(64), nullable=False, default="SATELLITE_SYNTHESIS")
    trigger_location = Column(String(128), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    dam_height_m = Column(Float, nullable=True)
    impounded_volume_m3 = Column(Float, nullable=True)
    rainfall_rate_mmh = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "severity_level": self.severity_level,
            "trigger_source": self.trigger_source,
            "trigger_location": self.trigger_location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "dam_height_m": self.dam_height_m,
            "impounded_volume_m3": self.impounded_volume_m3,
            "rainfall_rate_mmh": self.rainfall_rate_mmh,
            "status": self.status,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
