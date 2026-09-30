"""
natural_dams.py — Natural River Dam & Landslide Outburst Risk API Router
========================================================================
Exposes endpoints for:
  - Multi-temporal satellite detection of landslide dams and channel obstructions.
  - Upstream impounded water polygons and reservoir volume tracking.
  - Multi-evidence scoring and explainable diagnostic breakdowns.
  - Outburst risk and downstream infrastructure exposure.
  - Field and authority ground-truth validation workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from gis.natural_dam.layers.geojson_generator import NaturalDamGeoJSONExporter
from ml.natural_dam.inference.pipeline_runner import (
    CompleteNaturalDamRecord,
    NaturalDamPipeline,
)

router = APIRouter(prefix="/api/v1/natural-dams", tags=["Natural River Dam Detection"])

# Initialize pipeline singleton
pipeline = NaturalDamPipeline()
cached_records: List[CompleteNaturalDamRecord] = pipeline.run_detection_for_corridor()


class AnalyzeDamRequest(BaseModel):
    corridor_name: str = Field("Upper_Beas_Basin", description="Hydrological basin name")
    include_sar_radar: bool = Field(True, description="Enable Sentinel-1 SAR cloud penetration")
    forecast_rain_24h_mm: float = Field(80.0, ge=0.0, le=500.0, description="Forecast precipitation in mm")


class ValidationSubmission(BaseModel):
    status: Literal[
        "Confirmed",
        "Not a Natural Dam",
        "False Detection",
        "Needs Investigation",
        "Unable to Verify",
    ] = Field(..., description="Authority validation classification")
    validator_role: str = Field("HPSDMA_District_Emergency_Officer", description="Designation of official")
    notes: str = Field(..., description="Field inspection or aerial drone observation notes")
    evidence_type: str = Field("GROUND_INSPECTION", description="Type of verification survey")
    photo_url: Optional[str] = Field(None, description="URL or URI to georeferenced evidence photo")


def _find_record_by_id(dam_id: str) -> CompleteNaturalDamRecord:
    for r in cached_records:
        if r.candidate.dam_id == dam_id:
            return r
    raise HTTPException(status_code=404, detail=f"Natural dam candidate '{dam_id}' not found")


@router.post("/analyze", summary="Trigger multi-temporal natural dam detection across river network")
def trigger_natural_dam_analysis(req: AnalyzeDamRequest) -> Dict[str, Any]:
    """Runs end-to-end multi-evidence detection over satellite passes and river network."""
    global cached_records
    cached_records = pipeline.run_detection_for_corridor()

    active_candidates = [r for r in cached_records if not r.candidate.false_positive_rejected]
    rejected_count = len(cached_records) - len(active_candidates)

    return {
        "status": "completed",
        "corridor": req.corridor_name,
        "sar_radar_enabled": req.include_sar_radar,
        "total_sites_analyzed": len(cached_records),
        "candidates_detected": len(active_candidates),
        "false_positives_filtered": rejected_count,
        "timestamp_utc": "2026-09-20T09:30:00Z",
    }


@router.get("", summary="Get all detected natural dam candidates as GeoJSON")
def list_natural_dam_candidates() -> Dict[str, Any]:
    """Returns OGC GeoJSON FeatureCollection of all candidate points and properties."""
    return NaturalDamGeoJSONExporter.export_candidates_geojson(cached_records)


@router.get("/{dam_id}", summary="Get detailed profile, multi-evidence indicators, and explainability")
def get_natural_dam_profile(dam_id: str) -> Dict[str, Any]:
    """Returns exhaustive diagnostic profile and 8-point evidence audit trail for a candidate."""
    r = _find_record_by_id(dam_id)
    c = r.candidate
    return {
        "dam_id": c.dam_id,
        "river_name": c.river_name,
        "coordinates": {"lat": c.lat, "lon": c.lon, "elevation_m": c.elevation_m},
        "candidate_tier": c.candidate_tier,
        "status": c.status,
        "metrics": {
            "detection_probability": c.probability,
            "model_confidence": c.confidence,
            "data_quality": c.data_quality,
            "observation_freshness": c.observation_freshness,
        },
        "indicators": [
            {
                "name": ind.name,
                "description": ind.description,
                "weight": ind.weight,
                "score": ind.score,
                "passed": ind.passed,
                "details": ind.details,
            }
            for ind in c.evidence_indicators
        ],
        "obstruction_summary": {
            "pre_event_width_m": r.obstruction.obstruction_width_m + (r.obstruction.obstruction_width_m * r.obstruction.width_reduction_pct / 100.0),
            "post_event_width_m": r.obstruction.obstruction_width_m,
            "width_reduction_pct": r.obstruction.width_reduction_pct,
            "sar_debris_backscatter_db": r.obstruction.sar_debris_backscatter_db,
        },
        "debris_source_summary": {
            "connected": r.debris_source.has_connected_debris_source,
            "distance_to_channel_m": r.debris_source.distance_to_channel_m,
            "failure_mechanism": r.debris_source.failure_mechanism,
            "flank_slope_deg": r.debris_source.flank_slope_deg,
        },
        "explainability": r.explanation,
    }


@router.get("/{dam_id}/history", summary="Get multi-temporal evolution timeline")
def get_natural_dam_history(dam_id: str) -> Dict[str, Any]:
    """Returns observation timeline tracking candidate emergence, impoundment growth, and stability."""
    r = _find_record_by_id(dam_id)
    return {
        "dam_id": dam_id,
        "river_name": r.candidate.river_name,
        "timeline_events": r.evolution_timeline,
    }


@router.get("/{dam_id}/impoundment", summary="Get upstream impounded water extent and reservoir metrics")
def get_upstream_impoundment(dam_id: str) -> Dict[str, Any]:
    """Returns upstream reservoir geometry polygon, surface area, and estimated volume."""
    r = _find_record_by_id(dam_id)
    geojson = NaturalDamGeoJSONExporter.export_impoundment_geojson([r])
    return {
        "dam_id": dam_id,
        "impounded_water_geojson": geojson,
        "metrics": {
            "has_impoundment": r.impoundment.has_impoundment,
            "surface_area_m2": r.impoundment.impounded_water_area_m2,
            "surface_area_km2": r.impoundment.impounded_water_area_km2,
            "expansion_pct": r.impoundment.expansion_pct,
            "expansion_rate_m2_hr": r.impoundment.expansion_rate_m2_hr,
            "estimated_dam_height_m": r.impoundment.estimated_dam_height_m,
            "estimated_volume_m3": r.impoundment.estimated_impounded_volume_m3,
            "volume_estimation_method": r.impoundment.volume_estimation_method,
        },
    }


@router.get("/{dam_id}/downstream-risk", summary="Get outburst failure potential and wave arrival times")
def get_outburst_risk(dam_id: str) -> Dict[str, Any]:
    """Returns geotechnical breach risk tier and hydraulic surge estimates."""
    r = _find_record_by_id(dam_id)
    ob = r.outburst_risk
    return {
        "dam_id": dam_id,
        "river_name": r.candidate.river_name,
        "outburst_risk_level": ob.outburst_risk_level,
        "risk_score": ob.risk_score,
        "primary_failure_mode": ob.failure_mode,
        "estimated_peak_breach_discharge_m3s": ob.peak_breach_discharge_m3s,
        "first_settlement_lead_time_min": ob.first_reach_lead_time_min,
        "projected_surge_height_m": ob.surge_height_m,
        "geotechnical_rationale": ob.rationale,
    }


@router.get("/{dam_id}/exposure", summary="Get downstream population and infrastructure exposure")
def get_downstream_exposure(dam_id: str) -> Dict[str, Any]:
    """Returns exposed settlements, population count, roads, bridges, and institutions."""
    r = _find_record_by_id(dam_id)
    exp = r.exposure
    return {
        "dam_id": dam_id,
        "exposure_tier": exp.exposure_tier,
        "total_villages_impacted": exp.villages_count,
        "total_population_exposed": exp.population_exposed,
        "roads_compromised_km": exp.roads_compromised_km,
        "bridges_compromised": exp.bridges_compromised,
        "schools_at_risk": exp.schools_at_risk,
        "hospitals_at_risk": exp.hospitals_at_risk,
        "settlements": exp.impacted_settlement_names,
    }


@router.post("/{dam_id}/validate", summary="Submit authority or field validation for candidate")
def validate_natural_dam(dam_id: str, submission: ValidationSubmission) -> Dict[str, Any]:
    """
    Submits ground-truth validation (Confirmed, False Detection, etc.)
    and updates candidate state in the registry.
    """
    r = _find_record_by_id(dam_id)

    record = pipeline.validation_registry.record_validation(
        dam_id=dam_id,
        status=submission.status,
        validator_role=submission.validator_role,
        notes=submission.notes,
        evidence_type=submission.evidence_type,
        photo_url=submission.photo_url,
    )

    # Update candidate operational status
    if submission.status == "Confirmed":
        r.candidate.status = "CONFIRMED_NATURAL_DAM"
    elif submission.status in ("Not a Natural Dam", "False Detection"):
        r.candidate.status = "REJECTED_FALSE_DETECTION"
    elif submission.status == "Needs Investigation":
        r.candidate.status = "HIGH_PRIORITY_INVESTIGATION"

    return {
        "status": "success",
        "validation_id": record.validation_id,
        "dam_id": dam_id,
        "new_candidate_status": r.candidate.status,
        "recorded_at": record.timestamp,
    }
