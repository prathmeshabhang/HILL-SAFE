"""
ml/data_quality/schema.py
========================
Data structures, status enums, and reports for the FLOODY SHIELD Data Quality Layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class QualityStatus(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    CRITICAL_ERROR = "CRITICAL_ERROR"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"          # age_seconds <= configured threshold
    STALE = "STALE"          # age_seconds > threshold (degraded warning)
    EXPIRED = "EXPIRED"      # age_seconds > 3x threshold (critical error)
    UNKNOWN = "UNKNOWN"


class FlagSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class DataLatencyRecord:
    observation_time: str      # ISO 8601 UTC
    ingestion_time: str        # ISO 8601 UTC
    latency_seconds: float
    age_seconds: float
    freshness_status: FreshnessStatus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_time": self.observation_time,
            "ingestion_time": self.ingestion_time,
            "latency_seconds": round(self.latency_seconds, 2),
            "age_seconds": round(self.age_seconds, 2),
            "freshness_status": self.freshness_status.value,
        }


@dataclass
class QualityFlag:
    code: str
    severity: FlagSeverity
    message: str
    field_name: Optional[str] = None
    observed_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "field_name": self.field_name,
            "observed_value": self.observed_value,
        }


@dataclass
class DataQualityReport:
    sample_id: str
    quality_score: float  # [0.0, 1.0]
    status: QualityStatus
    checks_performed: int
    checks_passed: int
    flags: List[QualityFlag] = field(default_factory=list)
    provenance_source: str = "UNKNOWN"
    latency: Optional[DataLatencyRecord] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_usable(self) -> bool:
        return self.status in (QualityStatus.VALID, QualityStatus.DEGRADED)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "quality_score": round(self.quality_score, 4),
            "status": self.status.value,
            "checks_performed": self.checks_performed,
            "checks_passed": self.checks_passed,
            "is_usable": self.is_usable,
            "flags": [f.to_dict() for f in self.flags],
            "provenance_source": self.provenance_source,
            "latency": self.latency.to_dict() if self.latency else None,
            "metadata": self.metadata,
        }
