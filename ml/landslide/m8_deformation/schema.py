"""
ml/landslide/m8_deformation/schema.py
======================================
Typed schemas and data contracts for Model M8: Ground Movement & Slope Deformation Forecast.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MovementRegime(str, Enum):
    STABLE = "STABLE"
    LINEAR_CREEP = "LINEAR_CREEP"
    ACCELERATING = "ACCELERATING"
    CRITICAL_FAILURE_IMMINENT = "CRITICAL_FAILURE_IMMINENT"


class ForecastHorizon(str, Enum):
    H24 = "24h"
    H72 = "72h"
    D7 = "7d"


@dataclass
class M8DeformationInput:
    sensor_or_pixel_id: str
    latitude: float
    longitude: float
    elevation_m: float
    slope_deg: float
    current_displacement_mm: float = 0.0
    cumulative_displacement_mm: float = 0.0
    velocity_mm_day: float = 0.0
    acceleration_mm_day2: float = 0.0
    rainfall_72h_mm: float = 0.0
    insar_coherence: float = 0.85
    tilt_rate_deg_day: float = 0.0
    crack_width_rate_mm_day: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeformationHorizonForecast:
    horizon: str  # "24h", "72h", "7d"
    predicted_displacement_increment_mm: float
    cumulative_projected_displacement_mm: float
    uncertainty_lower_mm: float
    uncertainty_upper_mm: float
    regime: MovementRegime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "horizon": self.horizon,
            "predicted_displacement_increment_mm": round(self.predicted_displacement_increment_mm, 2),
            "cumulative_projected_displacement_mm": round(self.cumulative_projected_displacement_mm, 2),
            "uncertainty_range_mm": [round(self.uncertainty_lower_mm, 2), round(self.uncertainty_upper_mm, 2)],
            "regime": self.regime.value,
        }


@dataclass
class M8PredictionOutput:
    current_velocity_mm_day: float
    acceleration_mm_day2: float
    movement_regime: MovementRegime
    time_to_failure_est_hours: Optional[float]
    horizon_forecasts: List[DeformationHorizonForecast]
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "INSAR_GNSS_TELEMETRY + KINEMATIC_SAITO_GBDT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "current_velocity_mm_day": round(self.current_velocity_mm_day, 3),
                "acceleration_mm_day2": round(self.acceleration_mm_day2, 3),
                "movement_regime": self.movement_regime.value,
                "time_to_failure_est_hours": round(self.time_to_failure_est_hours, 1) if self.time_to_failure_est_hours is not None else None,
                "horizon_forecasts": [h.to_dict() for h in self.horizon_forecasts],
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
