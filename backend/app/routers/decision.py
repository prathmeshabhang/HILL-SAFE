"""
decision.py — Decision Intelligence & Safe Evacuation Routing API Router
========================================================================
Exposes Models M13, M14, M15, M16:
  - Population exposure overlay
  - Infrastructure compromise checking
  - Multi-criteria shelter selection
  - Dynamic risk-weighted Dijkstra evacuation routing
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.features.beas_decision_infrastructure import build_upper_beas_infrastructure_graph
from ml.features.decision_engines import DecisionIntelligenceEngine

router = APIRouter(prefix="/api/v1/decision", tags=["Decision Intelligence & Evacuation"])
decision_engine = DecisionIntelligenceEngine()
graph_network, registered_villages, registered_shelters = build_upper_beas_infrastructure_graph()


class EvacuationRouteRequest(BaseModel):
    origin_node: str = Field("V_BHUNTAR", description="Starting village or settlement node ID")
    destination_node: str = Field("S_KULLU_COLLEGE", description="Target shelter or safe zone node ID")
    simulate_nh3_closure: bool = Field(True, description="Whether to mark NH-3 Aut-Pandoh as submerged/blocked")


@router.post("/evacuation-route", summary="Find safest risk-weighted evacuation path")
def find_evacuation_route(req: EvacuationRouteRequest) -> Dict[str, Any]:
    """
    Computes safest evacuation corridor around active flood and landslide hazards using Model M16.
    If NH-3 is flooded/blocked, calculates bypass route via safer higher-elevation alignments.
    """
    g = graph_network.copy()

    if req.simulate_nh3_closure:
        # Mark NH-3 edges along Beas gorge as blocked
        for u, v, d in g.edges(data=True):
            if "NH3" in str(u) or "NH3" in str(v) or "NH3" in d.get("road_name", ""):
                d["is_blocked"] = True

    route_res = decision_engine.find_safest_evacuation_route(
        graph=g,
        origin_node=req.origin_node,
        destination_node=req.destination_node,
    )

    return {
        "status": "success",
        "query": {
            "origin": req.origin_node,
            "destination": req.destination_node,
            "nh3_closed": req.simulate_nh3_closure,
        },
        "result": route_res,
    }


@router.get("/infrastructure-graph", summary="Get Beas corridor infrastructure network summary")
def get_infrastructure_graph_summary() -> Dict[str, Any]:
    """Returns summary of graph nodes, monitored bridges, roads, and designated shelters."""
    g = graph_network
    return {
        "status": "success",
        "total_nodes": g.number_of_nodes(),
        "total_edges": g.number_of_edges(),
        "nodes": list(g.nodes()),
        "designated_shelters": [s.name for s in registered_shelters],
        "monitored_villages": [v.name for v in registered_villages],
    }
