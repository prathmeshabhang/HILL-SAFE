"""
rescue_prioritizer.py — NDRF/SDRF Rescue Prioritization Index (RPI) Engine
============================================================================
Calculates composite Rescue Prioritization Index to guide immediate deployment
of NDRF water-rescue teams, SDRF mountain rescue units, and IAF helicopter airlifts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ml.damage.building_damage_classifier import (
    AssessedBuilding,
    BuildingDamageClassifier,
    SettlementDamageSummary,
)
from ml.damage.config import DamageAssessmentConfig
from ml.damage.lifeline_corridor_assessor import (
    LifelineAssessmentResult,
    LifelineCorridorAssessor,
)


@dataclass
class RescueTarget:
    rank: int
    settlement_name: str
    rescue_priority_index: float  # 0.0 to 1.0
    priority_level: str           # "P0_CRITICAL_AIRLIFT", "P1_HIGH_URGENCY", "P2_ELEVATED", "P3_STANDARD"
    estimated_trapped_population: int
    severed_access: bool
    damaged_buildings_count: int
    recommended_tactical_action: str


SAMPLE_ASSESSED_BUILDINGS = [
    AssessedBuilding("BLD_AUT_001", "Aut_Market", 31.7485, 77.2082, "RESIDENTIAL", 0.88, "DESTROYED", 12.0, 0.58, 0.32, "IMMEDIATE_SEARCH_AND_RESCUE"),
    AssessedBuilding("BLD_AUT_002", "Aut_Market", 31.7490, 77.2085, "COMMERCIAL", 0.76, "DESTROYED", 24.0, 0.52, 0.28, "IMMEDIATE_SEARCH_AND_RESCUE"),
    AssessedBuilding("BLD_AUT_003", "Aut_Market", 31.7495, 77.2090, "SCHOOL", 0.62, "MAJOR_DAMAGE", 38.0, 0.44, 0.22, "URGENT_EVACUATION"),
    AssessedBuilding("BLD_LARJI_001", "Larji_Hydro_Colony", 31.7165, 77.2165, "RESIDENTIAL", 0.72, "MAJOR_DAMAGE", 28.0, 0.48, 0.26, "URGENT_EVACUATION"),
    AssessedBuilding("BLD_LARJI_002", "Larji_Hydro_Colony", 31.7170, 77.2170, "COMMERCIAL", 0.42, "PARTIAL_DAMAGE", 58.0, 0.31, 0.15, "ASSISTANCE_REQUIRED"),
    AssessedBuilding("BLD_THALOUT_001", "Thalout", 31.6905, 77.1405, "RESIDENTIAL", 0.82, "DESTROYED", 18.0, 0.55, 0.30, "IMMEDIATE_SEARCH_AND_RESCUE"),
    AssessedBuilding("BLD_BHUNTAR_001", "Bhuntar", 31.8795, 77.1560, "HOSPITAL", 0.12, "NEGLIGIBLE_INTACT", 88.0, 0.10, 0.04, "NONE"),
]


class RescuePrioritizationEngine:
    def __init__(self, config: Optional[DamageAssessmentConfig] = None):
        self.config = config or DamageAssessmentConfig()
        self._classifier = BuildingDamageClassifier(self.config)
        self._lifeline_assessor = LifelineCorridorAssessor()

    def get_all_priorities(self) -> List[RescueTarget]:
        """Calculates prioritized rescue targets across calibrated baseline settlements."""
        summaries = self._classifier.evaluate_settlement_buildings(SAMPLE_ASSESSED_BUILDINGS)
        lifelines = self._lifeline_assessor.assess_lifelines()
        return self.rank_rescue_operations(summaries, lifelines)

    def rank_rescue_operations(
        self,
        damage_summaries: List[SettlementDamageSummary],
        lifelines: LifelineAssessmentResult,
        population_by_settlement: Optional[Dict[str, int]] = None,
    ) -> List[RescueTarget]:
        pops = population_by_settlement or {
            "Aut_Market": 1900,
            "Larji_Hydro_Colony": 1200,
            "Thalout": 850,
            "Pandoh_Dam": 1600,
            "Bhuntar": 5200,
        }

        w = self.config.rpi_weights
        targets = []

        for summ in damage_summaries:
            name = summ.settlement_name
            pop = pops.get(name, 1000)
            is_isolated = name in lifelines.isolated_settlements

            # Factor 1: Damage Severity Score (0.0 to 1.0)
            f_damage = summ.aggregate_damage_rate_pct / 100.0

            # Factor 2: Vulnerable Population Exposure (scaled to ~3000 max)
            f_pop = min(1.0, pop / 3000.0)

            # Factor 3: Isolation Factor (1.0 if completely cut off, 0.2 if accessible)
            f_iso = 1.0 if is_isolated else 0.20

            rpi = w["damage_severity"] * f_damage + w["vulnerable_population"] * f_pop + w["isolation_factor"] * f_iso
            rpi = round(float(rpi), 3)

            # Trapped population estimate: ratio of destroyed/major damaged buildings times population
            trapped_est = int(pop * min(1.0, f_damage * 1.25))

            if rpi >= 0.70 or (is_isolated and f_damage >= 0.50):
                lvl = "P0_CRITICAL_AIRLIFT"
                action = "Deploy NDRF swift-water rescue rafts and request IAF helicopter airlift to extract stranded civilians."
            elif rpi >= 0.45:
                lvl = "P1_HIGH_URGENCY"
                action = "Dispatch SDRF mechanized road clearing units and emergency medical triage corridor."
            elif rpi >= 0.25:
                lvl = "P2_ELEVATED"
                action = "Establish temporary relief distribution center and activate local high-ground community shelter."
            else:
                lvl = "P3_STANDARD"
                action = "Routine civil defense patrol and geotechnical damage audit."

            targets.append(
                RescueTarget(
                    rank=0,
                    settlement_name=name,
                    rescue_priority_index=rpi,
                    priority_level=lvl,
                    estimated_trapped_population=trapped_est,
                    severed_access=is_isolated,
                    damaged_buildings_count=summ.destroyed_count + summ.major_damage_count,
                    recommended_tactical_action=action,
                )
            )

        # Sort descending by RPI score
        targets.sort(key=lambda t: t.rescue_priority_index, reverse=True)
        for i, t in enumerate(targets):
            t.rank = i + 1

        return targets


# Public alias
RescuePrioritizer = RescuePrioritizationEngine

