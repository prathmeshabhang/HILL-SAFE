"""
ml/flood/m11_flood_depth/schema.py
==================================
Typed schemas and data contracts for Model M11: Flood Propagation & Depth Forecast Engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class InundationSeverity(str, Enum):
    NO_INUNDATION = "NO_INUNDATION"
    SHALLOW_NUISANCE = "SHALLOW_NUISANCE"        # Depth 0.05m - 0.30m
    MODERATE_FLOODING = "MODERATE_FLOODING"      # Depth 0.30m - 1.00m
    SEVERE_DANGER = "SEVERE_DANGER"              # Depth 1.00m - 2.50m
    CATASTROPHIC_SUBMERGENCE = "CATASTROPHIC_SUBMERGENCE"  # Depth > 2.50m


@dataclass
class ReachInundationForecast:
    reach_id: str
    reach_name: str
    distance_from_upstream_km: float
    wave_arrival_time_min: float
    peak_arrival_time_min: float
    routed_discharge_m3s: float
    peak_reach_stage_m: float
    max_inundation_depth_m: float
    inundated_area_sqkm: float
    severity: InundationSeverity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reach_id": self.reach_id,
            "reach_name": self.reach_name,
            "distance_from_upstream_km": round(self.distance_from_upstream_km, 1),
            "wave_arrival_time_min": round(self.wave_arrival_time_min, 1),
            "peak_arrival_time_min": round(self.peak_arrival_time_min, 1),
            "routed_discharge_m3s": round(self.routed_discharge_m3s, 1),
            "peak_reach_stage_m": round(self.peak_reach_stage_m, 2),
            "max_inundation_depth_m": round(self.max_inundation_depth_m, 2),
            "inundated_area_sqkm": round(self.inundated_area_sqkm, 3),
            "severity": self.severity.value,
        }


@dataclass
class M11FloodDepthInput:
    source_stage_m: float
    source_discharge_m3s: float
    target_reach_id: str = "REACH_03_PATLIKUHAL_KULLU"
    hand_m: float = 1.5
    distance_to_river_m: float = 85.0
    slope_deg: float = 6.0
    elevation_m: float = 1200.0
    latitude: float = 31.96
    longitude: float = 77.11

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class M11PredictionOutput:
    target_reach_id: str
    forecasted_depth_m: float
    inundation_severity: InundationSeverity
    flood_wave_arrival_time_min: float
    peak_arrival_time_min: float
    reach_forecasts: List[ReachInundationForecast]
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "COPERNICUS_DEM_HAND + MUSKINGUM_CUNGE_GBDT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "target_reach_id": self.target_reach_id,
                "forecasted_depth_m": round(self.forecasted_depth_m, 2),
                "inundation_severity": self.inundation_severity.value,
                "flood_wave_arrival_time_min": round(self.flood_wave_arrival_time_min, 1),
                "peak_arrival_time_min": round(self.peak_arrival_time_min, 1),
                "reach_forecasts": [r.to_dict() for r in self.reach_forecasts],
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
