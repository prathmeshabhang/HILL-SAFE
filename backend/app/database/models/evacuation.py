"""
backend/app/database/models/evacuation.py
=========================================
SQLAlchemy model for Evacuation Routing & Safe Zone Shelter Allocations.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from backend.app.database.session import Base


class EvacuationRouteModel(Base):
    __tablename__ = "evacuation_routes"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(64), ForeignKey("incidents.id"), nullable=True, index=True)
    origin_name = Column(String(128), nullable=False)
    destination_safe_zone = Column(String(128), nullable=False)
    distance_km = Column(Float, nullable=False)
    estimated_duration_min = Column(Float, nullable=False)
    clearance_status = Column(String(32), nullable=False, default="CLEAR")
    route_geojson = Column(Text, nullable=True)
    computed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "origin_name": self.origin_name,
            "destination_safe_zone": self.destination_safe_zone,
            "distance_km": self.distance_km,
            "estimated_duration_min": self.estimated_duration_min,
            "clearance_status": self.clearance_status,
            "route_geojson": self.route_geojson,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }
