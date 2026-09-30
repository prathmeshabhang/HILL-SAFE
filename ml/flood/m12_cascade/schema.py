"""
ml/flood/m12_cascade/schema.py
==============================
Typed schemas and data contracts for Model M12: Hazard Cascade & Landslide Dam Breach Engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CascadeSeverity(str, Enum):
    LOW_IMPACT = "LOW_IMPACT"
    MODERATE_BREACH = "MODERATE_BREACH"
    MAJOR_DISASTER = "MAJOR_DISASTER"
    CATASTROPHIC_OUTBURST = "CATASTROPHIC_OUTBURST"


class EvacuationUrgency(str, Enum):
    IMMEDIATE_LIFE_SAFETY = "IMMEDIATE_LIFE_SAFETY"
    PREPARE_EVACUATION = "PREPARE_EVACUATION"
    ADVISORY = "ADVISORY"


@dataclass
class DownstreamReachImpact:
    location_name: str
    distance_downstream_km: float
    flood_wave_lead_time_min: float
    peak_arrival_time_min: float
    peak_discharge_m3s: float
    surge_height_above_normal_m: float
    evacuation_urgency: str  # "IMMEDIATE_LIFE_SAFETY", "PREPARE_EVACUATION", "ADVISORY"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LandslideDamBreachResult:
    dam_location: str
    dam_height_m: float
    impounded_volume_m3: float
    peak_outflow_discharge_m3s: float
    breach_formation_time_min: float
    downstream_impacts: List[DownstreamReachImpact]
    cascade_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dam_location": self.dam_location,
            "dam_height_m": round(self.dam_height_m, 2),
            "impounded_volume_m3": round(self.impounded_volume_m3, 1),
            "peak_outflow_discharge_m3s": round(self.peak_outflow_discharge_m3s, 1),
            "breach_formation_time_min": round(self.breach_formation_time_min, 1),
            "downstream_impacts": [i.to_dict() for i in self.downstream_impacts],
            "cascade_summary": self.cascade_summary,
        }


@dataclass
class M12CascadeInput:
    dam_location: str = "Larji_Sainj_Confluence"
    dam_height_m: float = 35.0
    impounded_volume_m3: float = 8_500_000.0
    normal_river_discharge_m3s: float = 450.0
    trigger_type: str = "LANDSLIDE_DAM"
    trigger_probability: float = 0.85

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class M12PredictionOutput:
    dam_location: str
    peak_outflow_discharge_m3s: float
    breach_formation_time_min: float
    cascade_severity: CascadeSeverity
    shortest_evacuation_lead_time_min: float
    impacted_reaches_count: int
    breach_result: LandslideDamBreachResult
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "FROEHLICH_COSTA_BREACH_PHYSICS + HIMALAYAN_CALIBRATION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "dam_location": self.dam_location,
                "peak_outflow_discharge_m3s": round(self.peak_outflow_discharge_m3s, 1),
                "breach_formation_time_min": round(self.breach_formation_time_min, 1),
                "cascade_severity": self.cascade_severity.value,
                "shortest_evacuation_lead_time_min": round(self.shortest_evacuation_lead_time_min, 1),
                "impacted_reaches_count": self.impacted_reaches_count,
                "breach_result": self.breach_result.to_dict(),
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
