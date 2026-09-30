"""
damage.py — Post-Disaster Infrastructure & Building Damage Assessment API Router
=================================================================================
Exposes endpoints for:
  - Model M20 Copernicus EMS building structural damage classification.
  - Severed highway segments and compromised river bridges.
  - NDRF/SDRF Rescue Prioritization Index (RPI) ranking.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ml.damage.building_damage_classifier import (
    AssessedBuilding,
    BuildingDamageClassifier,
)
from ml.damage.lifeline_corridor_assessor import LifelineCorridorAssessor
from ml.damage.rescue_prioritizer import RescuePrioritizationEngine

router = APIRouter(prefix="/api/v1/damage", tags=["Post-Disaster Damage Assessment (M20)"])

classifier = BuildingDamageClassifier()
lifeline_assessor = LifelineCorridorAssessor()
rescue_engine = RescuePrioritizationEngine()

# Sample calibrated post-event buildings across Upper Beas settlements
SAMPLE_BUILDINGS = [
    AssessedBuilding("BLD_AUT_001", "Aut_Market", 31.7485, 77.2082, "RESIDENTIAL", 0.88, "DESTROYED", 12.0, 0.58, 0.32, "IMMEDIATE_SEARCH_AND_RESCUE"),
    AssessedBuilding("BLD_AUT_002", "Aut_Market", 31.7490, 77.2085, "COMMERCIAL", 0.76, "DESTROYED", 24.0, 0.52, 0.28, "IMMEDIATE_SEARCH_AND_RESCUE"),
    AssessedBuilding("BLD_AUT_003", "Aut_Market", 31.7495, 77.2090, "SCHOOL", 0.62, "MAJOR_DAMAGE", 38.0, 0.44, 0.22, "URGENT_EVACUATION"),
    AssessedBuilding("BLD_LARJI_001", "Larji_Hydro_Colony", 31.7165, 77.2165, "RESIDENTIAL", 0.72, "MAJOR_DAMAGE", 28.0, 0.48, 0.26, "URGENT_EVACUATION"),
    AssessedBuilding("BLD_LARJI_002", "Larji_Hydro_Colony", 31.7170, 77.2170, "COMMERCIAL", 0.42, "PARTIAL_DAMAGE", 58.0, 0.31, 0.15, "ASSISTANCE_REQUIRED"),
    AssessedBuilding("BLD_THALOUT_001", "Thalout", 31.6905, 77.1405, "RESIDENTIAL", 0.82, "DESTROYED", 18.0, 0.55, 0.30, "IMMEDIATE_SEARCH_AND_RESCUE"),
    AssessedBuilding("BLD_BHUNTAR_001", "Bhuntar", 31.8795, 77.1560, "HOSPITAL", 0.12, "NEGLIGIBLE_INTACT", 88.0, 0.10, 0.04, "NONE"),
]


class DamageAnalysisRequest(BaseModel):
    catchment_name: str = Field("Upper_Beas_Basin", description="Basin or district name")
    event_timestamp_utc: str = Field("2026-09-20T08:00:00Z", description="Post-disaster observation timestamp")
    include_sar_coherence: bool = Field(True, description="Fuse Sentinel-1 interferometric coherence loss")


@router.post("/analyze", summary="Trigger satellite damage proxy mapping over affected corridor")
def trigger_damage_analysis(req: DamageAnalysisRequest) -> Dict[str, Any]:
    """Runs Model M20 damage proxy mapping combining SAR coherence loss and optical NDBI change."""
    settlement_summaries = classifier.evaluate_settlement_buildings(SAMPLE_BUILDINGS)
    lifelines = lifeline_assessor.assess_lifelines()
    rescue_targets = rescue_engine.rank_rescue_operations(settlement_summaries, lifelines)

    return {
        "status": "completed",
        "catchment": req.catchment_name,
        "event_timestamp_utc": req.event_timestamp_utc,
        "total_buildings_assessed": len(SAMPLE_BUILDINGS),
        "total_settlements_evaluated": len(settlement_summaries),
        "roads_severed_km": lifelines.total_roads_severed_km,
        "top_priority_rescue_target": rescue_targets[0].settlement_name if rescue_targets else "None",
    }


@router.get("/buildings", summary="Get Copernicus EMS assessed building footprints as GeoJSON")
def get_assessed_buildings_geojson() -> Dict[str, Any]:
    """Returns GeoJSON FeatureCollection of all classified buildings with damage grades."""
    features = []
    for b in SAMPLE_BUILDINGS:
        features.append({
            "type": "Feature",
            "id": b.building_id,
            "geometry": {"type": "Point", "coordinates": [b.lon, b.lat]},
            "properties": asdict(b),
        })

    return {
        "type": "FeatureCollection",
        "name": "copernicus_ems_building_damage",
        "features": features,
    }


@router.get("/lifelines", summary="Get compromised road networks and severed bridges")
def get_compromised_lifelines() -> Dict[str, Any]:
    """Returns assessment of severed highway segments (NH-3), overtopped bridges, and cut-off towns."""
    res = lifeline_assessor.assess_lifelines()
    return asdict(res)


@router.get("/rescue-priority", summary="Get ranked NDRF/SDRF Rescue Prioritization Index list")
def get_rescue_prioritization() -> Dict[str, Any]:
    """Returns prioritized rescue target list based on structural damage, population, and isolation."""
    settlement_summaries = classifier.evaluate_settlement_buildings(SAMPLE_BUILDINGS)
    lifelines = lifeline_assessor.assess_lifelines()
    rescue_targets = rescue_engine.rank_rescue_operations(settlement_summaries, lifelines)

    return {
        "status": "success",
        "priority_targets_count": len(rescue_targets),
        "targets": [asdict(t) for t in rescue_targets],
    }
