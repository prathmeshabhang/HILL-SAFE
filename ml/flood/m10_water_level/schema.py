"""
ml/flood/m10_water_level/schema.py
==================================
Typed schemas and data contracts for Model M10: River Water-Level Forecast Engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StageAlertLevel(str, Enum):
    NORMAL_FLOW = "NORMAL_FLOW"
    WARNING_LEVEL = "WARNING_LEVEL"
    DANGER_LEVEL = "DANGER_LEVEL"
    HIGH_FLOOD_LEVEL = "HIGH_FLOOD_LEVEL"


class WaterLevelHorizon(str, Enum):
    M30 = "30m"
    H1 = "1h"
    H3 = "3h"
    H6 = "6h"


@dataclass
class M10WaterLevelInput:
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    elevation_m: float
    current_stage_m: float
    rate_of_rise_m_hr: float = 0.0
    rainfall_15m_mm: float = 0.0
    rainfall_1h_mm: float = 0.0
    rainfall_3h_mm: float = 0.0
    rainfall_6h_mm: float = 0.0
    soil_moisture_pct: float = 40.0
    warning_level_m: float = 5.0
    danger_level_m: float = 7.0
    hfl_m: float = 9.5
    upstream_discharge_m3s: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StageHorizonForecast:
    horizon: str  # "30m", "1h", "3h", "6h"
    forecasted_stage_m: float
    stage_delta_m: float
    exceedance_prob_danger: float
    uncertainty_lower_m: float
    uncertainty_upper_m: float
    alert_level: StageAlertLevel

    def to_dict(self) -> Dict[str, Any]:
        return {
            "horizon": self.horizon,
            "forecasted_stage_m": round(self.forecasted_stage_m, 2),
            "stage_delta_m": round(self.stage_delta_m, 2),
            "exceedance_prob_danger": round(self.exceedance_prob_danger, 4),
            "uncertainty_range_m": [round(self.uncertainty_lower_m, 2), round(self.uncertainty_upper_m, 2)],
            "alert_level": self.alert_level.value,
        }


@dataclass
class M10PredictionOutput:
    primary_horizon: str
    forecasted_stage_m: float
    stage_delta_m: float
    alert_level: StageAlertLevel
    exceedance_prob_danger: float
    horizon_forecasts: List[StageHorizonForecast]
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "CWC_AWS_TELEMETRY + HYDROLOGICAL_GBDT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "primary_horizon": self.primary_horizon,
                "forecasted_stage_m": round(self.forecasted_stage_m, 2),
                "stage_delta_m": round(self.stage_delta_m, 2),
                "alert_level": self.alert_level.value,
                "exceedance_prob_danger": round(self.exceedance_prob_danger, 4),
                "horizon_forecasts": [h.to_dict() for h in self.horizon_forecasts],
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
