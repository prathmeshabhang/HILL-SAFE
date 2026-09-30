"""
ml/decision/m17_warning_gating/schema.py
=========================================
Typed schemas and data contracts for Model M17: Early Warning Gating & Evacuation Urgency Recommendation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class WarningAlertLevel(str, Enum):
    GREEN_NORMAL = "GREEN_NORMAL"      # Baseline conditions / routine vigilance
    YELLOW_WATCH = "YELLOW_WATCH"      # Advisory watch / low-lying areas on notice
    ORANGE_ALERT = "ORANGE_ALERT"      # High risk / stage evacuation teams and open shelters
    RED_EVACUATE = "RED_EVACUATE"      # Critical emergency / mandatory life-safety evacuation


class EvacuationUrgencyTier(str, Enum):
    IMMEDIATE_ACTION = "IMMEDIATE_ACTION"          # Within 0-30 minutes
    STANDBY_STAGING = "STANDBY_STAGING"            # Within 30-90 minutes
    HEIGHTENED_ADVISORY = "HEIGHTENED_ADVISORY"    # 2-6 hours ahead
    ROUTINE_MONITORING = "ROUTINE_MONITORING"      # Normal conditions


class EvacuationStrategy(str, Enum):
    HORIZONTAL_ROAD_EVACUATION = "HORIZONTAL_ROAD_EVACUATION"  # Evacuate via road network to designated safe shelter
    VERTICAL_SHELTER_IN_PLACE = "VERTICAL_SHELTER_IN_PLACE"    # Egress blocked / flood arrival imminent; move to reinforced high ground
    COMBINED_PRIORITY_EVACUATION = "COMBINED_PRIORITY_EVACUATION" # High-priority vulnerable groups evacuate; others standby


@dataclass
class M17WarningInput:
    reach_or_settlement_id: str
    rainfall_intensity_mmh: float = 0.0          # From M1
    rainfall_3h_mm: float = 0.0                  # From M1
    flood_probability: float = 0.0               # From M2
    river_water_level_m: float = 2.5             # From M10
    warning_level_m: float = 5.0                 # From M10
    danger_level_m: float = 7.0                  # From M10
    hfl_m: float = 9.5                           # From M10
    flood_depth_m: float = 0.0                   # From M11
    flood_arrival_time_min: float = 120.0        # Wave travel time from M11 / M12
    landslide_probability: float = 0.0           # From M6 / M7
    pore_water_pressure_ratio: float = 0.30      # From PWP/SSI
    natural_dam_outburst_discharge_m3s: float = 0.0 # From M12
    at_risk_population: int = 1000               # From M13
    arterial_road_blocked: bool = False          # From M14
    critical_bridge_submerged: bool = False      # From M14

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class M17WarningOutput:
    reach_or_settlement_id: str
    alert_level: WarningAlertLevel
    urgency_tier: EvacuationUrgencyTier
    evacuation_strategy: EvacuationStrategy
    lead_time_minutes: float
    required_evacuation_time_min: float
    evacuation_urgency_index: float              # EUI = RequiredTime / LeadTime
    deterministic_override_triggered: bool
    actionable_recommendations: List[str]
    hazard_synthesis: Dict[str, Any]
    cap_compliant_payload: Dict[str, Any]        # Common Alerting Protocol compliant format
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "NDMA_CAP_PROTOCOL + CWC_FLOOD_CRITERIA + MULTI_HAZARD_SYNTHESIS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "reach_or_settlement_id": self.reach_or_settlement_id,
                "alert_level": self.alert_level.value,
                "urgency_tier": self.urgency_tier.value,
                "evacuation_strategy": self.evacuation_strategy.value,
                "lead_time_minutes": round(self.lead_time_minutes, 1),
                "required_evacuation_time_min": round(self.required_evacuation_time_min, 1),
                "evacuation_urgency_index": round(self.evacuation_urgency_index, 2),
                "deterministic_override_triggered": self.deterministic_override_triggered,
                "actionable_recommendations": self.actionable_recommendations,
                "hazard_synthesis": self.hazard_synthesis,
                "cap_compliant_payload": self.cap_compliant_payload,
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
