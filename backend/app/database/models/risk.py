"""
backend/app/database/models/risk.py
===================================
SQLAlchemy models for Unified Multi-Hazard Risk States and Dynamic Risk Zones.
Preserves raw observations, modelled features, predicted probabilities,
and uncertainty metrics for complete provenance.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from backend.app.database.session import Base


class RiskStateModel(Base):
    __tablename__ = "risk_states"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(64), ForeignKey("incidents.id"), nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    location_name = Column(String(128), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Hazard branches (JSON serializations)
    flood_hazard_json = Column(Text, nullable=True)
    landslide_hazard_json = Column(Text, nullable=True)
    cascade_hazard_json = Column(Text, nullable=True)

    # Impact assessment branches
    population_impact_json = Column(Text, nullable=True)
    infrastructure_impact_json = Column(Text, nullable=True)

    # Summary metrics
    overall_risk_level = Column(String(32), nullable=False, default="MODERATE")  # LOW, MODERATE, HIGH, EXTREME
    confidence_score = Column(Float, nullable=False, default=0.85)
    quality_state = Column(String(32), nullable=False, default="FRESH")  # FRESH, STALE, DEGRADED
    provenance_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        import json
        conf = self.confidence_score if self.confidence_score is not None else 0.85
        if conf >= 0.80:
            conf_state = "HIGH_CONFIDENCE"
        elif conf >= 0.50:
            conf_state = "MODERATE_CONFIDENCE"
        else:
            conf_state = "LOW_CONFIDENCE"

        data_mode = "SIMULATION"
        is_operational = False
        prov_dict = {}
        if self.provenance_json:
            try:
                prov_dict = json.loads(self.provenance_json)
                if isinstance(prov_dict, dict):
                    data_mode = prov_dict.get("data_mode", "SIMULATION")
                    is_operational = bool(prov_dict.get("is_operational", False))
            except Exception:
                pass

        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "overall_risk_level": self.overall_risk_level,
            "confidence_score": self.confidence_score,
            "confidence_state": conf_state,
            "quality_state": self.quality_state,
            "model_health_state": "HEALTHY" if self.quality_state == "FRESH" else "DEGRADED",
            "data_mode": data_mode,
            "is_operational": is_operational,
            "provenance": prov_dict or self.provenance_json,
            "flood_hazard": self.flood_hazard_json,
            "landslide_hazard": self.landslide_hazard_json,
            "cascade_hazard": self.cascade_hazard_json,
            "population_impact": self.population_impact_json,
            "infrastructure_impact": self.infrastructure_impact_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RiskZoneModel(Base):
    __tablename__ = "risk_zones"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    zone_type = Column(String(64), nullable=False)  # INUNDATION_ZONE, LANDSLIDE_RUNOUT, SECTION_36_RESTRICTED
    risk_level = Column(String(32), nullable=False, default="HIGH")
    geometry_geojson = Column(Text, nullable=False)  # GeoJSON polygon geometry
    is_active = Column(String(16), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "zone_type": self.zone_type,
            "risk_level": self.risk_level,
            "geometry_geojson": self.geometry_geojson,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
