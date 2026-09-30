"""
decision_engines.py — FLOODY SHIELD Models M13, M14, M15, M16
================================================================
Implements core Decision Intelligence Engines:
  - Model M13: Population Exposure Engine (GIS overlay)
  - Model M14: Infrastructure Impact Engine (Roads, bridges, hospitals)
  - Model M15: Safe-Zone & Shelter Selection (Multi-criteria feasibility optimization)
  - Model M16: Dynamic Evacuation Route Optimization (Risk-weighted Dijkstra)

OPERATIONAL PRINCIPLE:
----------------------
"We don't stop at predicting the disaster. We convert prediction into action."
Shortest path is rarely safest path in an active flood/landslide corridor.
"""

from __future__ import annotations

import heapq
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np


@dataclass
class VillageEntity:
    id: str
    name: str
    population: int
    lat: float
    lon: float
    flood_prob: float
    landslide_prob: float


@dataclass
class ShelterEntity:
    id: str
    name: str
    elevation_m: float
    capacity: int
    current_occupancy: int
    lat: float
    lon: float
    flood_prob: float
    landslide_prob: float
    natural_dam_risk: float = 0.0
    road_accessibility: str = "OPEN"
    critical_infrastructure: List[str] = None

    def __post_init__(self):
        if self.critical_infrastructure is None:
            self.critical_infrastructure = []


class DecisionIntelligenceEngine:
    def __init__(self):
        pass

    # -------------------------------------------------------------
    # Model M13: Population Exposure Engine
    # -------------------------------------------------------------
    def calculate_population_exposure(
        self,
        villages: List[VillageEntity],
        flood_risk_threshold: float = 0.50,
        landslide_risk_threshold: float = 0.50,
    ) -> Dict[str, Any]:
        """
        Overlays hazard footprints with village demographic registers.
        """
        exposed_villages = []
        total_exposed_population = 0

        for v in villages:
            is_flood_exposed = v.flood_prob >= flood_risk_threshold
            is_slide_exposed = v.landslide_prob >= landslide_risk_threshold

            if is_flood_exposed or is_slide_exposed:
                hazard_type = "COMPOUND_CASCADE" if (is_flood_exposed and is_slide_exposed) else (
                    "FLOOD" if is_flood_exposed else "LANDSLIDE"
                )
                total_exposed_population += v.population
                exposed_villages.append({
                    "village_id": v.id,
                    "name": v.name,
                    "population_at_risk": v.population,
                    "hazard_type": hazard_type,
                    "flood_prob": round(v.flood_prob, 2),
                    "landslide_prob": round(v.landslide_prob, 2),
                })

        return {
            "model": "M13_Population_Exposure",
            "total_population_exposed": total_exposed_population,
            "number_of_villages_impacted": len(exposed_villages),
            "exposed_villages": exposed_villages,
        }

    # -------------------------------------------------------------
    # Model M14: Infrastructure Impact Engine
    # -------------------------------------------------------------
    def evaluate_infrastructure_impact(
        self,
        road_segments: List[Dict[str, Any]],
        bridges: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Assesses road passability, bridge overtopping risks, and isolated nodes.
        """
        compromised_roads = []
        compromised_bridges = []

        for r in road_segments:
            # Segment is blocked if flood probability > 0.65 or landslide trigger > 0.60
            if r.get("flood_prob", 0.0) >= 0.65 or r.get("landslide_prob", 0.0) >= 0.60:
                compromised_roads.append({
                    "road_id": r["id"],
                    "name": r.get("name", "Local Road"),
                    "status": "IMPASSABLE_BLOCKED",
                    "reason": "Hazard threshold exceedance",
                })

        for b in bridges:
            if b.get("river_level_m", 0.0) >= b.get("freeboard_clearance_m", 5.0):
                compromised_bridges.append({
                    "bridge_id": b["id"],
                    "name": b["name"],
                    "status": "SUBMERGED_UNSAFE",
                    "river_level_m": b.get("river_level_m"),
                })

        return {
            "model": "M14_Infrastructure_Impact",
            "compromised_roads_count": len(compromised_roads),
            "compromised_bridges_count": len(compromised_bridges),
            "compromised_roads": compromised_roads,
            "compromised_bridges": compromised_bridges,
        }

    # -------------------------------------------------------------
    # Model M15: Safe-Zone & Shelter Allocator
    # -------------------------------------------------------------
    def select_safe_shelter(
        self,
        shelters: List[ShelterEntity],
        evacuation_demand: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Selects feasible shelter based on: safe elevation, low compound risk,
        road accessibility, natural dam outburst distance, and available beds.
        Never designates a location 'GUARANTEED SAFE' — outputs 'LOWER_CURRENT_MODELLED_HAZARD'.
        """
        candidates = []
        for s in shelters:
            spare_capacity = s.capacity - s.current_occupancy
            # Eligibility gate: low hazard on shelter grounds, open access, and available beds
            is_accessible = getattr(s, "road_accessibility", "OPEN") != "BLOCKED"
            low_hazard = (s.flood_prob < 0.25) and (s.landslide_prob < 0.25) and (getattr(s, "natural_dam_risk", 0.0) < 0.30)

            if low_hazard and is_accessible and spare_capacity > 0:
                infra_bonus = len(getattr(s, "critical_infrastructure", [])) * 5.0
                score = (spare_capacity * 0.4) + (s.elevation_m * 0.08) - (s.flood_prob * 80) - (s.landslide_prob * 60) + infra_bonus
                candidates.append((score, s, spare_capacity))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_shelter, spare = candidates[0]

        return {
            "model": "M15_Safe_Zone_Allocator",
            "selected_shelter_id": best_shelter.id,
            "name": best_shelter.name,
            "elevation_m": best_shelter.elevation_m,
            "capacity": best_shelter.capacity,
            "current_occupancy": best_shelter.current_occupancy,
            "spare_capacity": spare,
            "estimated_demand": evacuation_demand,
            "hazard_exposure": {
                "flood_risk": best_shelter.flood_prob,
                "landslide_risk": best_shelter.landslide_prob,
                "natural_dam_risk": getattr(best_shelter, "natural_dam_risk", 0.0),
            },
            "accessibility": getattr(best_shelter, "road_accessibility", "OPEN"),
            "critical_infrastructure": getattr(best_shelter, "critical_infrastructure", []),
            "suitability_score": round(best_score, 1),
            "status": "FEASIBLE_SAFE",
            "safety_classification": "LOWER_CURRENT_MODELLED_HAZARD",
            "statutory_notice": "NEVER GUARANTEED SAFE: Designated as lower current modelled hazard subject to local geotechnical and weather inspection.",
        }

    # -------------------------------------------------------------
    # Model M16: Dynamic Risk-Weighted Evacuation Routing
    # -------------------------------------------------------------
    def find_safest_evacuation_route(
        self,
        graph: nx.Graph,
        origin_node: str,
        destination_node: str,
    ) -> Dict[str, Any]:
        """
        Computes safest feasible path using dynamic hazard penalty weights:
        Edge Cost = Distance * (1 + 12 * P_flood^2 + 12 * P_landslide^2 + inf * is_blocked)
        Considers distance, flood risk, landslide risk, road blockage, and bridge status.
        """
        def risk_cost_func(u, v, edge_attrs):
            dist = edge_attrs.get("length_km", 1.0)
            bridge_down = edge_attrs.get("bridge_status", "OPEN") in ["SUBMERGED", "COLLAPSED", "BLOCKED"]
            if edge_attrs.get("is_blocked", False) or bridge_down:
                return float("inf")
            p_flood = edge_attrs.get("flood_prob", 0.0)
            p_slide = edge_attrs.get("landslide_prob", 0.0)
            # Severe exponential penalty for active hazard corridors
            penalty = 1.0 + (12.0 * (p_flood**2)) + (12.0 * (p_slide**2))
            return dist * penalty

        try:
            path = nx.dijkstra_path(graph, origin_node, destination_node, weight=risk_cost_func)
            total_km = sum(
                graph[path[i]][path[i + 1]].get("length_km", 1.0) for i in range(len(path) - 1)
            )
            return {
                "model": "M16_Dynamic_Safe_Routing",
                "route_status": "FOUND_SAFER_FEASIBLE",
                "recommendation": "RECOMMENDED_CURRENTLY_FEASIBLE_LOWER_RISK",
                "path_nodes": path,
                "total_distance_km": round(total_km, 2),
                "advisory": "Route avoids active flood channels and high-risk debris corridors.",
                "disclaimer": "Safety cannot be guaranteed; represents currently modelled lower-risk corridor. Drivers must heed on-ground emergency signs.",
            }
        except nx.NetworkXNoPath:
            return {
                "model": "M16_Dynamic_Safe_Routing",
                "route_status": "UNREACHABLE_CUT_OFF",
                "recommendation": "NO_FEASIBLE_ROUTE_FOUND",
                "path_nodes": [],
                "total_distance_km": 0.0,
                "advisory": "All connecting corridors blocked by hazards. Recommend high-ground shelter-in-place and prioritize rescue dispatch.",
                "disclaimer": "Safety cannot be guaranteed; corridors cut off.",
            }

    def recalculate_route_with_invalidation(
        self,
        graph: nx.Graph,
        origin_node: str,
        destination_node: str,
        invalidated_edges: List[Tuple[str, str]],
    ) -> Dict[str, Any]:
        """
        Invalidates compromised edges and dynamically recalculates the currently feasible lower-risk route.
        """
        g = graph.copy()
        for u, v in invalidated_edges:
            if g.has_edge(u, v):
                g[u][v]["is_blocked"] = True
            elif g.has_edge(v, u):
                g[v][u]["is_blocked"] = True
        return self.find_safest_evacuation_route(g, origin_node, destination_node)

    # -------------------------------------------------------------
    # Natural Dam Cascade Integration
    # -------------------------------------------------------------
    def evaluate_natural_dam_cascade(
        self,
        landslide_hazard_score: float,
        channel_obstruction_ratio: float,
        upstream_lake_volume_m3: float,
        is_authority_validated: bool = False,
    ) -> Dict[str, Any]:
        """
        Models the physical cascade sequence:
          Landslide -> Possible River Obstruction -> Upstream Accumulation -> Candidate Natural Dam -> Downstream Exposure
        Mandates that outputs remain 'candidate' until validated by field authority.
        """
        is_candidate = (landslide_hazard_score >= 0.50) and (channel_obstruction_ratio >= 0.35)
        status = "AUTHORITY_VALIDATED_NATURAL_DAM" if (is_candidate and is_authority_validated) else (
            "CANDIDATE_UNVERIFIED_NATURAL_DAM" if is_candidate else "NO_DAM_DETECTED"
        )
        return {
            "model": "Natural_Dam_Cascade_Engine",
            "cascade_sequence": "Landslide -> Channel Obstruction -> Upstream Lake -> Natural Dam Candidate -> Downstream Exposure",
            "is_candidate": is_candidate,
            "status": status,
            "is_authority_validated": is_authority_validated,
            "public_warning_issued": False if not is_authority_validated else (upstream_lake_volume_m3 > 500_000),
            "advisory": "CANDIDATE STATUS ONLY: Automated satellite detection requires authority ground validation before issuing public alerts.",
            "hazard_metrics": {
                "landslide_hazard": round(landslide_hazard_score, 3),
                "channel_obstruction_ratio": round(channel_obstruction_ratio, 3),
                "upstream_lake_volume_m3": round(upstream_lake_volume_m3, 1),
            },
        }


if __name__ == "__main__":
    engine = DecisionIntelligenceEngine()

    # 1. Test Exposure (M13)
    sample_villages = [
        VillageEntity("V1", "Kullu Gorge Village", 650, 31.8, 77.1, flood_prob=0.82, landslide_prob=0.10),
        VillageEntity("V2", "Dharamsala Ridge Settlement", 420, 32.1, 76.3, flood_prob=0.05, landslide_prob=0.74),
        VillageEntity("V3", "Plateau Basti", 310, 31.5, 76.8, flood_prob=0.10, landslide_prob=0.08),
    ]
    exp = engine.calculate_population_exposure(sample_villages)
    print("=" * 60)
    print("DECISION INTELLIGENCE SUITE TEST")
    print("=" * 60)
    print("Model M13 (Population Exposure):")
    print(f"  Total exposed: {exp['total_population_exposed']} people across {exp['number_of_villages_impacted']} villages")

    # 2. Test Safe Shelter Allocator (M15)
    sample_shelters = [
        ShelterEntity("S1", "Valley Secondary School", 650.0, 300, 280, 31.8, 77.1, flood_prob=0.75, landslide_prob=0.05),
        ShelterEntity("S2", "High Ridge Community Center", 1450.0, 500, 120, 31.7, 77.0, flood_prob=0.02, landslide_prob=0.05),
    ]
    shelter = engine.select_safe_shelter(sample_shelters, evacuation_demand=150)
    print("\nModel M15 (Safe-Zone Selection):")
    print(f"  Selected Shelter: {shelter['name']} (Elevation: {shelter['elevation_m']}m, Free beds: {shelter['spare_capacity']})")

    # 3. Test Routing (M16)
    G = nx.Graph()
    # Route A (Direct but flooded valley road): Village -> Waypoint 1 -> Shelter
    G.add_edge("Village_V1", "Valley_Road_1", length_km=2.0, flood_prob=0.90, landslide_prob=0.0, is_blocked=True)
    G.add_edge("Valley_Road_1", "Ridge_Shelter_S2", length_km=1.5, flood_prob=0.85, landslide_prob=0.0, is_blocked=False)
    # Route B (Slightly longer ridge bypass, zero flood): Village -> Ridge_Pass -> Shelter
    G.add_edge("Village_V1", "Ridge_Pass", length_km=3.2, flood_prob=0.02, landslide_prob=0.10, is_blocked=False)
    G.add_edge("Ridge_Pass", "Ridge_Shelter_S2", length_km=2.1, flood_prob=0.01, landslide_prob=0.05, is_blocked=False)

    route = engine.find_safest_evacuation_route(G, "Village_V1", "Ridge_Shelter_S2")
    print("\nModel M16 (Dynamic Evacuation Routing):")
    print(f"  Status: {route['route_status']}")
    print(f"  Chosen Safest Path: {' -> '.join(route['path_nodes'])} ({route['total_distance_km']} km)")
    print(f"  Advisory: {route['advisory']}")
    print("=" * 60)
