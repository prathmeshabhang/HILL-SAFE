"""
ml/anomaly/m9_sensor/schema.py
==============================
Typed schemas and data contracts for Model M9: IoT Sensor Anomaly Detection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SensorAnomalyType(str, Enum):
    NONE = "NONE"
    PHYSICAL_RANGE_VIOLATION = "PHYSICAL_RANGE_VIOLATION"
    STUCK_SENSOR = "STUCK_SENSOR"
    RATE_OF_CHANGE_SPIKE = "RATE_OF_CHANGE_SPIKE"
    MULTIVARIATE_DRIFT = "MULTIVARIATE_DRIFT"
    CROSS_SENSOR_INCONSISTENCY = "CROSS_SENSOR_INCONSISTENCY"
    MISSING_STREAM = "MISSING_STREAM"


class SensorStatus(str, Enum):
    NORMAL = "NORMAL"
    ANOMALOUS = "ANOMALOUS"
    FAULTY = "FAULTY"


@dataclass
class M9InputFeatures:
    station_id: str
    timestamp_utc: str
    rainfall_rate_mmh: float = 0.0
    water_level_m: float = 0.0
    soil_moisture_pct: float = 0.0
    tilt_deg: float = 0.0
    pore_pressure_kpa: float = 0.0
    temperature_c: float = 15.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class M9PredictionOutput:
    sensor_status: SensorStatus
    anomaly_score: float  # Continuous [0.0, 1.0], where >0.50 is anomalous
    anomaly_type: SensorAnomalyType
    is_valid_reading: bool
    recommended_action: str
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "sensor_status": self.sensor_status.value,
                "anomaly_score": round(self.anomaly_score, 4),
                "anomaly_type": self.anomaly_type.value,
                "is_valid_reading": self.is_valid_reading,
                "recommended_action": self.recommended_action,
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "flags": self.flags,
        }
