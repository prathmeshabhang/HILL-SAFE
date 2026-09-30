"""
backend/app/database/models/model_run.py
========================================
SQLAlchemy model for tracking Model Invocations and Audit Provenance.
Maintains model versioning, cryptographic artifact hashes, execution timing,
and scientific evidence status.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, Float, String, Text
from backend.app.database.session import Base


class ModelRunModel(Base):
    __tablename__ = "model_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(32), nullable=False, index=True)  # e.g. M1, M2, ..., M20
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(32), nullable=False, default="3.3.0")
    artifact_hash = Column(String(64), nullable=True)
    evidence_status = Column(String(64), nullable=False, default="PROTOTYPE")

    run_timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Float, nullable=False)

    input_hash = Column(String(64), nullable=False)
    output_hash = Column(String(64), nullable=True)
    input_reference = Column(Text, nullable=True)
    output_reference = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

    status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS, DEGRADED, FAILED, CANCELLED
    quality_state = Column(String(32), nullable=False, default="FRESH")
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "artifact_hash": self.artifact_hash,
            "evidence_status": self.evidence_status,
            "run_timestamp": self.run_timestamp.isoformat() if self.run_timestamp else None,
            "execution_time_ms": self.execution_time_ms,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "output_summary": self.output_summary,
            "confidence_score": self.confidence_score,
            "status": self.status,
            "quality_state": self.quality_state,
            "error_message": self.error_message,
        }
