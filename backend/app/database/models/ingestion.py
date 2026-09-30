"""
backend/app/database/models/ingestion.py
========================================
SQLAlchemy models for Data Ingestion Runs and Quality Records.
Tracks source fetch runs, records accepted/rejected, and data quality states.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from backend.app.database.session import Base


class DataIngestionRunModel(Base):
    __tablename__ = "data_ingestion_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(64), nullable=False, index=True)  # IMD_AWS, GPM_IMERG, CWC_RIVER, SENTINEL_1, etc.
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    records_fetched = Column(Integer, nullable=False, default=0)
    records_accepted = Column(Integer, nullable=False, default=0)
    records_rejected = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="COMPLETED")  # RUNNING, COMPLETED, FAILED, PARTIAL
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "records_fetched": self.records_fetched,
            "records_accepted": self.records_accepted,
            "records_rejected": self.records_rejected,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DataQualityRecordModel(Base):
    __tablename__ = "data_quality_records"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    ingestion_run_id = Column(String(64), nullable=True, index=True)
    source_id = Column(String(64), nullable=False, index=True)
    station_or_scene_id = Column(String(128), nullable=False)
    observation_timestamp = Column(DateTime, nullable=False, index=True)
    quality_state = Column(String(32), nullable=False, default="FRESH")  # FRESH, STALE, EXPIRED, DEGRADED, CRITICAL_ERROR
    rule_evaluated = Column(String(64), nullable=False)  # SPATIAL_BOUNDS, TEMPORAL_FRESHNESS, PHYSICAL_LIMITS, M9_ISOLATION_FOREST
    passed = Column(String(8), nullable=False, default="PASS")  # PASS, FAIL
    rejection_reason = Column(String(255), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ingestion_run_id": self.ingestion_run_id,
            "source_id": self.source_id,
            "station_or_scene_id": self.station_or_scene_id,
            "observation_timestamp": self.observation_timestamp.isoformat() if self.observation_timestamp else None,
            "quality_state": self.quality_state,
            "rule_evaluated": self.rule_evaluated,
            "passed": self.passed,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
