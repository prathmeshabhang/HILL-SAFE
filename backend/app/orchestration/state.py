"""
backend/app/orchestration/state.py
==================================
Execution state machine, dependency classification, and result models for Model Orchestrator.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DependencyType(str, Enum):
    HARD = "HARD"          # Failure of parent completely blocks child execution
    SOFT = "SOFT"          # Child can proceed with fallback/degraded parameters
    OPTIONAL = "OPTIONAL"  # Child executed only when input data is available (e.g. satellite scene)


class ModelNodeResult(BaseModel):
    model_id: str
    model_name: str
    state: ExecutionState = ExecutionState.QUEUED
    output: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    input_hash: str = ""
    output_hash: str = ""
    error_message: Optional[str] = None
    quality_state: str = "FRESH"
    evidence_status: str = "PROTOTYPE"
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "state": self.state.value,
            "output": self.output,
            "execution_time_ms": self.execution_time_ms,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "error_message": self.error_message,
            "quality_state": self.quality_state,
            "evidence_status": self.evidence_status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
