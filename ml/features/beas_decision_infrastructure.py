"""
beas_decision_infrastructure.py — FLOODY SHIELD Real Catchment Decision Engine
================================================================================
Embeds the authentic geographical and infrastructure topology of the
Upper Beas Catchment (Kullu–Manali corridor, Himachal Pradesh) into Models M13–M16:
  - Real Villages: Manali, Naggar, Kullu Town, Bhuntar, Aut, Larji, Banjar.
  - Real Shelters: Naggar Castle Ridge, Bhuntar High Grounds, Kullu College.
  - Real Arteries: NH-3 (Chandigarh-Manali Highway), Parvati Valley Link, Aut Tunnel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import networkx as nx
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from decision_engines import (
    DecisionIntelligenceEngine,
    ShelterEntity,
    VillageEntity,
)


def build_upper_beas_infrastructure_graph() -> Tuple[nx.Graph, List[VillageEntity], List[ShelterEntity]]:
    """Constructs the road-stream-community topology of the Kullu-Beas Basin."""

    # 1. Real Villages along the Beas River Corridor
    villages = [
        VillageEntity(id="V_MANALI", name="Manali Urban & Old Manali", population=8500, lat=32.2396, lon=77.1887, flood_prob=0.88, landslide_prob=0.45),
        VillageEntity(id="V_NAGGAR", name="Naggar Heritage Ridge", population=2800, lat=32.1154, lon=77.1724, flood_prob=0.08, landslide_prob=0.62),
        VillageEntity(id="V_KULLU", name="Kullu District Headquarters", population=18500, lat=31.9579, lon=77.1095, flood_prob=0.78, landslide_prob=0.20),
        VillageEntity(id="V_BHUNTAR", name="Bhuntar Confluence & Airport Zone", population=5200, lat=31.8789, lon=77.1554, flood_prob=0.94, landslide_prob=0.15),
        VillageEntity(id="V_AUT", name="Aut Gorge Settlement", population=1900, lat=31.7483, lon=77.2081, flood_prob=0.82, landslide_prob=0.78),
        VillageEntity(id="V_LARJI", name="Larji Dam Hydro Corridor", population=1200, lat=31.7167, lon=77.2167, flood_prob=0.86, landslide_prob=0.80),
        VillageEntity(id="V_BANJAR", name="Banjar Tirthan Valley Hub", population=3400, lat=31.6372, lon=77.3436, flood_prob=0.35, landslide_prob=0.72),
    ]

    # 2. Feasible High-Ground Shelters
    shelters = [
        # In flood danger zone (Bhuntar low grounds) -> should be filtered out
        ShelterEntity(id="S_BHUNTAR_LOW", name="Bhuntar Ground School", elevation_m=1084.0, capacity=600, current_occupancy=450, lat=31.879, lon=77.156, flood_prob=0.92, landslide_prob=0.05),
        # High safe ridge shelter above Naggar
        ShelterEntity(id="S_NAGGAR_RIDGE", name="Naggar High Ridge Community Camp", elevation_m=1850.0, capacity=1200, current_occupancy=250, lat=32.118, lon=77.175, flood_prob=0.02, landslide_prob=0.08),
        # Elevated Government College above Kullu town
        ShelterEntity(id="S_KULLU_COLLEGE", name="Kullu Elevated Degree College", elevation_m=1350.0, capacity=2000, current_occupancy=400, lat=31.962, lon=77.115, flood_prob=0.04, landslide_prob=0.06),
        # Tirthan high monastery shelter
        ShelterEntity(id="S_BANJAR_HIGH", name="Banjar Hilltop Emergency Center", elevation_m=1720.0, capacity=800, current_occupancy=100, lat=31.642, lon=77.348, flood_prob=0.03, landslide_prob=0.09),
    ]

    # 3. Road Network Graph (NH-3 Chandigarh-Manali Highway & Tributary Links)
    G = nx.Graph()

    # Route 1: NH-3 Low-lying Highway directly beside Beas River (Flooded / Blocked in monsoon)
    G.add_edge("V_BHUNTAR", "NH3_Beas_Bank_Km12", length_km=4.2, flood_prob=0.95, landslide_prob=0.10, is_blocked=True)
    G.add_edge("NH3_Beas_Bank_Km12", "S_KULLU_COLLEGE", length_km=5.1, flood_prob=0.90, landslide_prob=0.10, is_blocked=True)

    # Route 2: Elevated Western Ridge Bypass Road (Safe from flood and active debris flows)
    G.add_edge("V_BHUNTAR", "Western_Ridge_Pass_Junction", length_km=6.5, flood_prob=0.02, landslide_prob=0.12, is_blocked=False)
    G.add_edge("Western_Ridge_Pass_Junction", "S_KULLU_COLLEGE", length_km=4.8, flood_prob=0.01, landslide_prob=0.08, is_blocked=False)

    return G, villages, shelters


if __name__ == "__main__":
    engine = DecisionIntelligenceEngine()
    G, villages, shelters = build_upper_beas_infrastructure_graph()

    print("=" * 65)
    print("UPPER BEAS (KULLU-MANALI) DECISION INTELLIGENCE AUDIT")
    print("=" * 65)

    # 1. Exposure
    exp = engine.calculate_population_exposure(villages, flood_risk_threshold=0.70, landslide_risk_threshold=0.70)
    print(f"Total Exposed Population : {exp['total_population_exposed']} residents")
    print(f"High-Risk Localities     : {exp['number_of_villages_impacted']} villages")
    for v in exp["exposed_villages"]:
        print(f"  * {v['name']:<32} | Risk: {v['hazard_type']} (P_flood={v['flood_prob']}, P_slide={v['landslide_prob']})")

    # 2. Shelter Allocation
    shelter = engine.select_safe_shelter(shelters, evacuation_demand=500)
    print(f"\nSafe Shelter Allocated   : {shelter['name']}")
    print(f"  Elevation: {shelter['elevation_m']}m | Spare Beds: {shelter['spare_capacity']}")

    # 3. Routing from flooded Bhuntar airport confluence to Kullu safe college
    route = engine.find_safest_evacuation_route(G, "V_BHUNTAR", "S_KULLU_COLLEGE")
    print(f"\nDynamic Evacuation Route (Bhuntar -> Kullu Shelter):")
    print(f"  Status    : {route['route_status']}")
    print(f"  Path      : {' -> '.join(route['path_nodes'])} ({route['total_distance_km']} km)")
    print(f"  Advisory  : {route['advisory']}")
    print("=" * 65)
