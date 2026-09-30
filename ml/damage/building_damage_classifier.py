"""
building_damage_classifier.py — Copernicus EMS Structural Damage Classification
================================================================================
Classifies individual building footprints into Copernicus EMS damage grades
by fusing Sentinel-1 SAR Damage Proxy Maps with Sentinel-2 NDBI / optical shifts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.damage.config import DamageAssessmentConfig


@dataclass
class AssessedBuilding:
    building_id: str
    settlement_name: str
    lat: float
    lon: float
    building_type: str         # "RESIDENTIAL", "COMMERCIAL", "HOSPITAL", "SCHOOL"
    damage_score: float        # Normalized 0.0 to 1.0
    damage_tier: str           # "DESTROYED", "MAJOR_DAMAGE", "PARTIAL_DAMAGE", "NEGLIGIBLE_INTACT"
    structural_integrity_pct: float
    sar_coherence_loss: float
    optical_ndbi_drop: float
    rescue_urgency: str        # "IMMEDIATE_SEARCH_AND_RESCUE", "URGENT_EVACUATION", "ASSISTANCE_REQUIRED", "NONE"


@dataclass
class SettlementDamageSummary:
    settlement_name: str
    total_buildings: int
    destroyed_count: int
    major_damage_count: int
    partial_damage_count: int
    intact_count: int
    critical_facilities_damaged: List[str]
    aggregate_damage_rate_pct: float


class BuildingDamageClassifier:
    def __init__(self, config: Optional[DamageAssessmentConfig] = None):
        self.config = config or DamageAssessmentConfig()

    def classify_building(
        self,
        building_id: str,
        settlement_name: str,
        lat: float,
        lon: float,
        building_type: str,
        sar_coherence_loss: float,
        optical_ndbi_drop: float,
        is_flooded: bool = False,
    ) -> AssessedBuilding:
        """
        Combines SAR phase decorrelation with optical built-up degradation.
        """
        # Damage fusion: 60% SAR Coherence Loss + 25% Optical NDBI Drop + 15% Flood Inundation Flag
        s_sar = min(1.0, max(0.0, sar_coherence_loss / 0.55))
        s_opt = min(1.0, max(0.0, optical_ndbi_drop / 0.35))
        s_fld = 1.0 if is_flooded else 0.0

        raw_score = 0.60 * s_sar + 0.25 * s_opt + 0.15 * s_fld
        damage_score = round(float(np.clip(raw_score, 0.0, 1.0)), 3)

        # Copernicus EMS damage grading
        tier = "NEGLIGIBLE_INTACT"
        for t_name, t_min in self.config.damage_tiers:
            if damage_score >= t_min:
                tier = t_name
                break

        structural_integrity = round(max(0.0, (1.0 - damage_score) * 100.0), 1)

        # Life-safety rescue urgency
        if tier == "DESTROYED":
            urgency = "IMMEDIATE_SEARCH_AND_RESCUE"
        elif tier == "MAJOR_DAMAGE":
            urgency = "URGENT_EVACUATION"
        elif tier == "PARTIAL_DAMAGE":
            urgency = "ASSISTANCE_REQUIRED"
        else:
            urgency = "NONE"

        return AssessedBuilding(
            building_id=building_id,
            settlement_name=settlement_name,
            lat=lat,
            lon=lon,
            building_type=building_type,
            damage_score=damage_score,
            damage_tier=tier,
            structural_integrity_pct=structural_integrity,
            sar_coherence_loss=round(sar_coherence_loss, 3),
            optical_ndbi_drop=round(optical_ndbi_drop, 3),
            rescue_urgency=urgency,
        )

    def evaluate_settlement_buildings(
        self,
        buildings: List[AssessedBuilding],
    ) -> List[SettlementDamageSummary]:
        """Aggregates building classifications across settlements."""
        by_settlement: Dict[str, List[AssessedBuilding]] = {}
        for b in buildings:
            by_settlement.setdefault(b.settlement_name, []).append(b)

        summaries = []
        for name, b_list in by_settlement.items():
            tot = len(b_list)
            des = sum(1 for b in b_list if b.damage_tier == "DESTROYED")
            maj = sum(1 for b in b_list if b.damage_tier == "MAJOR_DAMAGE")
            part = sum(1 for b in b_list if b.damage_tier == "PARTIAL_DAMAGE")
            intact = sum(1 for b in b_list if b.damage_tier == "NEGLIGIBLE_INTACT")

            damaged_critical = [
                f"{b.building_type}_{b.building_id}"
                for b in b_list
                if b.building_type in ("HOSPITAL", "SCHOOL") and b.damage_tier in ("DESTROYED", "MAJOR_DAMAGE")
            ]

            agg_rate = round(((des + maj) / max(tot, 1)) * 100.0, 1)

            summaries.append(
                SettlementDamageSummary(
                    settlement_name=name,
                    total_buildings=tot,
                    destroyed_count=des,
                    major_damage_count=maj,
                    partial_damage_count=part,
                    intact_count=intact,
                    critical_facilities_damaged=damaged_critical,
                    aggregate_damage_rate_pct=agg_rate,
                )
            )

        return summaries
