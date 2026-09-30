"""
backend/app/database/models/spatial.py
======================================
SQLAlchemy models for Infrastructure Assets, Population Zones, and Safe Zones.
Supports PostGIS spatial queries (points, lines, polygons) with fallback to GeoJSON text.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from backend.app.database.session import Base


class InfrastructureAssetModel(Base):
    __tablename__ = "infrastructure_assets"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    asset_type = Column(String(64), nullable=False)  # HIGHWAY_NH3, BRIDGE, TUNNEL, POWER_SUBSTATION, HOSPITAL
    sector = Column(String(64), nullable=False, default="AUT_LARJI_CORRIDOR")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geometry_geojson = Column(Text, nullable=True)  # LineString or Polygon GeoJSON
    replacement_cost_inr = Column(Float, nullable=False, default=10_000_000.0)
    criticality_tier = Column(String(16), nullable=False, default="TIER_1")  # TIER_1 (Life safety), TIER_2, TIER_3
    is_operational = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "asset_type": self.asset_type,
            "sector": self.sector,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geometry_geojson": self.geometry_geojson,
            "replacement_cost_inr": self.replacement_cost_inr,
            "criticality_tier": self.criticality_tier,
            "is_operational": self.is_operational,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PopulationZoneModel(Base):
    __tablename__ = "population_zones"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    ward_name = Column(String(128), nullable=False)
    settlement_name = Column(String(128), nullable=False)  # Manali, Kullu, Bhuntar, Pandoh, Aut
    resident_population = Column(Integer, nullable=False, default=1000)
    peak_tourist_population = Column(Integer, nullable=False, default=500)
    vulnerability_index = Column(Float, nullable=False, default=0.5)
    geometry_geojson = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ward_name": self.ward_name,
            "settlement_name": self.settlement_name,
            "resident_population": self.resident_population,
            "peak_tourist_population": self.peak_tourist_population,
            "total_estimated_population": self.resident_population + self.peak_tourist_population,
            "vulnerability_index": self.vulnerability_index,
            "geometry_geojson": self.geometry_geojson,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SafeZoneModel(Base):
    __tablename__ = "safe_zones"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    safe_zone_type = Column(String(64), nullable=False, default="COMMUNITY_CENTER")  # COMMUNITY_CENTER, GROUND, SCHOOL
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=False)
    capacity_headcount = Column(Integer, nullable=False, default=500)
    suitability_score = Column(Float, nullable=False, default=0.9)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "safe_zone_type": self.safe_zone_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": self.elevation_m,
            "capacity_headcount": self.capacity_headcount,
            "suitability_score": self.suitability_score,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
