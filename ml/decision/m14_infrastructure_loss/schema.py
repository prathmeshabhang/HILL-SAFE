"""
ml/decision/m14_infrastructure_loss/schema.py
==============================================
Typed schemas and data contracts for Model M14: Infrastructure Damage & Loss Estimation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DamageState(str, Enum):
    NEGLIGIBLE_INTACT = "NEGLIGIBLE_INTACT"      # Damage < 5%
    SLIGHT_DAMAGE = "SLIGHT_DAMAGE"              # Damage 5% - 25% (minor cleaning / repairs)
    MODERATE_DAMAGE = "MODERATE_DAMAGE"          # Damage 25% - 50% (structural remediation needed)
    EXTENSIVE_DAMAGE = "EXTENSIVE_DAMAGE"        # Damage 50% - 80% (severe impairment, partial rebuild)
    COLLAPSED_DESTROYED = "COLLAPSED_DESTROYED"  # Damage > 80% (total structural loss)


class AssetCategory(str, Enum):
    TRANSPORTATION_ROAD = "TRANSPORTATION_ROAD"
    TRANSPORTATION_BRIDGE = "TRANSPORTATION_BRIDGE"
    POWER_SUBSTATION = "POWER_SUBSTATION"
    HEALTHCARE_HOSPITAL = "HEALTHCARE_HOSPITAL"
    WATER_INTAKE = "WATER_INTAKE"
    AGRICULTURE_ORCHARD = "AGRICULTURE_ORCHARD"


class LifelineStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    PARTIALLY_DEGRADED = "PARTIALLY_DEGRADED"
    IMPASSABLE_CUT_OFF = "IMPASSABLE_CUT_OFF"
    STRUCTURALLY_FAILED = "STRUCTURALLY_FAILED"


@dataclass
class InfrastructureAsset:
    asset_id: str
    name: str
    category: AssetCategory
    replacement_value_lakhs_inr: float   # In INR Lakhs (1 Lakh = 100,000 INR)
    critical_elevation_m: float          # Inundation threshold elevation
    soffit_or_deck_height_m: float       # Bridge deck or building plinth height above ground
    lat: float
    lon: float
    reach_name: str
    criticality_tier: int = 1            # 1 (vital hospital/arterial) to 3 (local farm access)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d


@dataclass
class M14DamageInput:
    asset_id: str
    flood_depth_m: float = 0.0           # Peak inundation depth above ground/deck
    flow_velocity_ms: float = 0.0        # Flow velocity in m/s
    debris_impact_flag: bool = False     # Boulders/logs carried by flood wave (from M12)
    inundation_duration_hours: float = 2.0  # Duration of active submergence
    custom_asset: Optional[InfrastructureAsset] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class M14PredictionOutput:
    asset_id: str
    asset_name: str
    category: AssetCategory
    damage_state: DamageState
    structural_damage_ratio: float       # D in [0.0, 1.0]
    estimated_direct_loss_lakhs_inr: float
    service_outage_hours: float
    lifeline_status: LifelineStatus
    lifeline_criticality_score: float    # Criticality-weighted impact score
    damage_rationale: str
    confidence: float
    uncertainty: Dict[str, Any]
    data_quality: float
    model_version: str
    applicability: str
    provenance: str = "NDMA_FLASH_FLOOD_GUIDELINES + USACE_DEPTH_DAMAGE_TABLES + BEAS_INFRA_INVENTORY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": {
                "asset_id": self.asset_id,
                "asset_name": self.asset_name,
                "category": self.category.value,
                "damage_state": self.damage_state.value,
                "structural_damage_ratio": round(self.structural_damage_ratio, 4),
                "estimated_direct_loss_lakhs_inr": round(self.estimated_direct_loss_lakhs_inr, 2),
                "service_outage_hours": round(self.service_outage_hours, 1),
                "lifeline_status": self.lifeline_status.value,
                "lifeline_criticality_score": round(self.lifeline_criticality_score, 3),
                "damage_rationale": self.damage_rationale,
            },
            "confidence": round(self.confidence, 4),
            "uncertainty": self.uncertainty,
            "data_quality": round(self.data_quality, 4),
            "model_version": self.model_version,
            "applicability": self.applicability,
            "provenance": self.provenance,
        }
