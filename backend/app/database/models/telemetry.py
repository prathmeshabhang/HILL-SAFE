"""
backend/app/database/models/telemetry.py
=========================================
SQLAlchemy models for IoT Telemetry Stations and Observations.
Includes provenance, source identifiers, quality states, and deduplication hashes.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.database.session import Base


class SensorStationModel(Base):
    __tablename__ = "sensor_stations"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    station_type = Column(String(64), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=True)
    river_basin = Column(String(128), default="Upper Beas Basin")
    status = Column(String(32), nullable=False, default="PLANNED")  # PLANNED, SURVEYED, INSTALLED, COMMISSIONED, ACTIVE, DEGRADED, OFFLINE, RETIRED
    commissioning_data = Column(Text, nullable=True)
    commissioned_at = Column(DateTime, nullable=True)
    commissioned_by = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, nullable=True)

    observations = relationship("SensorObservationModel", back_populates="station", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        import json
        comm_data = None
        if self.commissioning_data:
            try:
                comm_data = json.loads(self.commissioning_data)
            except Exception:
                comm_data = self.commissioning_data
        return {
            "id": self.id,
            "station_id": self.id,
            "name": self.name,
            "station_type": self.station_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": self.elevation_m,
            "river_basin": self.river_basin,
            "status": self.status,
            "commissioned_at": self.commissioned_at.isoformat() if self.commissioned_at else None,
            "commissioned_by": self.commissioned_by,
            "commissioning_data": comm_data,
            "is_active": self.is_active,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
        }


class SensorObservationModel(Base):
    __tablename__ = "sensor_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(64), ForeignKey("sensor_stations.id"), nullable=False, index=True)
    data_source_id = Column(String(64), nullable=True, default="UPPER_BEAS_IOT", index=True)
    device_id = Column(String(64), nullable=True, index=True)
    sensor_id = Column(String(64), nullable=True, index=True)
    source_event_id = Column(String(128), nullable=True, unique=True, index=True)
    idempotency_hash = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    observed_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    measurement_type = Column(String(64), nullable=True, index=True)
    value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    sequence_number = Column(Integer, nullable=True)
    rainfall_rate_mmh = Column(Float, nullable=True)
    water_level_m = Column(Float, nullable=True)
    pore_pressure_kpa = Column(Float, nullable=True)
    displacement_mm = Column(Float, nullable=True)
    acoustic_emission_db = Column(Float, nullable=True)
    is_anomalous = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    anomaly_reason = Column(String(255), nullable=True)
    quality_state = Column(String(32), nullable=False, default="FRESH")  # FRESH, STALE, EXPIRED, DEGRADED, CRITICAL_ERROR
    temporal_state = Column(String(32), nullable=False, default="VALID")  # VALID, LATE, STALE, EXPIRED, INVALID
    provenance = Column(String(32), nullable=False, default="SIMULATED", index=True)  # REAL, SIMULATED, REPLAY, TEST, PLANNED
    environment = Column(String(32), nullable=False, default="TEST", index=True)  # FIELD, TEST, LAB, STAGING
    qc_flags = Column(String(255), nullable=True)
    provenance_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    station = relationship("SensorStationModel", back_populates="observations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "station_id": self.station_id,
            "device_id": self.device_id,
            "sensor_id": self.sensor_id,
            "source_event_id": self.source_event_id,
            "data_source_id": self.data_source_id,
            "idempotency_hash": self.idempotency_hash,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "measurement_type": self.measurement_type,
            "value": self.value,
            "unit": self.unit,
            "sequence_number": self.sequence_number,
            "rainfall_rate_mmh": self.rainfall_rate_mmh,
            "water_level_m": self.water_level_m,
            "pore_pressure_kpa": self.pore_pressure_kpa,
            "displacement_mm": self.displacement_mm,
            "acoustic_emission_db": self.acoustic_emission_db,
            "is_anomalous": self.is_anomalous,
            "anomaly_score": self.anomaly_score,
            "anomaly_reason": self.anomaly_reason,
            "quality_state": self.quality_state,
            "temporal_state": self.temporal_state,
            "provenance": self.provenance,
            "environment": self.environment,
            "qc_flags": self.qc_flags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
