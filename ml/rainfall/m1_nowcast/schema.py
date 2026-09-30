"""
ml/rainfall/m1_nowcast/schema.py
================================
Typed schemas and data contracts for Model M1: Extreme Rainfall & Nowcasting Engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NowcastHorizon(str, Enum):
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H3 = "3h"
    H6 = "6h"
    H24 = "24h"


class CloudburstRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass
class M1InputFeatures:
    timestamp_utc: str
    station_id: str
    latitude: float
    longitude: float
    elevation_m: float
    slope_deg: float = 15.0
    aspect_deg: float = 180.0
    r_15m: float = 0.0
    r_30m: float = 0.0
    r_1h: float = 0.0
    r_3h: float = 0.0
    r_6h: float = 0.0
    r_12h: float = 0.0
    r_24h: float = 0.0
    r_72h: float = 0.0
    rolling_intensity_mmh: float = 0.0
    rainfall_acceleration: float = 0.0
    storm_motion_dx: float = 0.0
    storm_motion_dy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HorizonForecast:
    horizon: str  # "15m", "30m", "1h", "3h", "6h", "24h"
    predicted_rainfall_mm: float
    extreme_rain_probability: float  # P(Intensity >= 60 mm/h or accumulation >= threshold)
    uncertainty_lower_mm: float      # 10th percentile
    uncertainty_upper_mm: float      # 90th percentile
    risk_level: CloudburstRiskLevel

    def to_dict(self) -> Dict[str, Any]:
        return {
            "horizon": self.horizon,
            "predicted_rainfall_mm": round(self.predicted_rainfall_mm, 2),
            "extreme_rain_probability": round(self.extreme_rain_probability, 4),
            "uncertainty_range_mm": [round(self.uncertainty_lower_mm, 2), round(self.uncertainty_upper_mm, 2)],
            "risk_level": self.risk_level.value,
        }


@dataclass
class M1PredictionOutput:
    primary_horizon: str
    predicted_rainfall_mm: float
    extreme_rain_probability: float
    risk_level: CloudburstRiskLevel
    horizon_forecasts: List[HorizonForecast]
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "OBSERVED_TELEMETRY + NOWCAST_MODEL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "primary_horizon": self.primary_horizon,
                "predicted_rainfall_mm": round(self.predicted_rainfall_mm, 2),
                "extreme_rain_probability": round(self.extreme_rain_probability, 4),
                "risk_level": self.risk_level.value,
                "horizon_forecasts": [h.to_dict() for h in self.horizon_forecasts],
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
