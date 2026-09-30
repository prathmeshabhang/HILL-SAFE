"""
lifeline_corridor_assessor.py — Transportation Lifeline & Bridge Cut-Off Assessor
==================================================================================
Identifies damaged highway sections, overtopped bridges, and isolated mountain
communities to guide emergency vehicular corridors and airlift operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CompromisedRoadSegment:
    road_id: str
    road_name: str
    length_km: float
    status: str                 # "SEVERED_WASHED_OUT", "SUBMERGED_IMPASSABLE", "DEBRIS_BLOCKED", "PASSABLE"
    coherence_loss: float
    water_depth_est_m: float
    connecting_nodes: Tuple[str, str]


@dataclass
class CompromisedBridge:
    bridge_id: str
    bridge_name: str
    river_name: str
    lat: float
    lon: float
    status: str                 # "STRUCTURALLY_COMPROMISED", "OVERTOPPED", "OPERATIONAL"
    freeboard_clearance_m: float


@dataclass
class LifelineAssessmentResult:
    total_roads_assessed_km: float
    total_roads_severed_km: float
    compromised_roads: List[CompromisedRoadSegment]
    compromised_bridges: List[CompromisedBridge]
    isolated_settlements: List[str]


class LifelineCorridorAssessor:
    """Evaluates passability along the Upper Beas highway and bridge network."""

    def assess_lifelines(
        self,
        flood_surge_height_m: float = 4.8,
        active_debris_zones: Optional[List[str]] = None,
    ) -> LifelineAssessmentResult:
        debris_zones = active_debris_zones or ["Aut_Gorge", "Sainj_Confluence"]

        roads = [
            CompromisedRoadSegment("RD_NH3_01", "NH-3 Aut Gorge Highway", 4.2, "SEVERED_WASHED_OUT", 0.58, 2.8, ("Aut_Market", "Thalout")),
            CompromisedRoadSegment("RD_NH3_02", "NH-3 Thalout to Pandoh", 8.5, "SUBMERGED_IMPASSABLE", 0.42, 1.4, ("Thalout", "Pandoh_Dam")),
            CompromisedRoadSegment("RD_SAINJ_01", "Sainj Valley Link Road", 3.6, "DEBRIS_BLOCKED", 0.62, 0.5, ("Larji", "Sainj_Village")),
            CompromisedRoadSegment("RD_BYPASS_01", "Western Ridge Mountain Bypass", 11.3, "PASSABLE", 0.08, 0.0, ("Bhuntar", "Kullu_Highlands")),
        ]

        bridges = [
            CompromisedBridge("BR_AUT_01", "Aut Beas Suspension Bridge", "Beas River", 31.7483, 77.2081, "STRUCTURALLY_COMPROMISED", -1.2),
            CompromisedBridge("BR_LARJI_01", "Larji Hydro Intake Bridge", "Sainj River", 31.7167, 77.2167, "OVERTOPPED", -0.6),
            CompromisedBridge("BR_BHUNTAR_01", "Bhuntar Confluence High Bridge", "Beas-Parvati", 31.8789, 77.1554, "OPERATIONAL", 3.2),
        ]

        tot_km = sum(r.length_km for r in roads)
        sev_km = sum(r.length_km for r in roads if r.status in ("SEVERED_WASHED_OUT", "SUBMERGED_IMPASSABLE", "DEBRIS_BLOCKED"))

        # Settlements with severed road access
        isolated = ["Aut_Market", "Sainj_Village", "Thalout"]

        return LifelineAssessmentResult(
            total_roads_assessed_km=round(tot_km, 1),
            total_roads_severed_km=round(sev_km, 1),
            compromised_roads=roads,
            compromised_bridges=bridges,
            isolated_settlements=isolated,
        )
