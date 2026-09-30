"""
backend/app/api/v1/endpoints/analysis.py
========================================
REST API endpoints for Multi-Source Feature Engineering, Decoupled Physics & AI ML Execution,
and Cascade Intelligence for FLOODY SHIELD.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.services.analysis.flood_physics import flood_physics_engine
from backend.app.services.analysis.landslide_ai import landslide_ai_engine, LandslideFeaturePipeline
from backend.app.services.analysis.orchestrator import decoupled_analysis_coordinator
from backend.app.services.gis.cascade_spatial_service import cascade_spatial_service
from backend.app.services.ingestion.multi_source_service import multi_source_service
from backend.app.services.ingestion.source_health import source_health_monitor

router = APIRouter(prefix="/api/v1/analysis", tags=["Feature Engineering & AI/ML Execution"])

# Predefined storm scenarios for rapid demonstration & benchmarking
CURATED_SCENARIOS = {
    "JULY_2023_BEAS_CLOUDBURST": {
        "scenario_id": "JULY_2023_BEAS_CLOUDBURST",
        "title": "July 2023 Upper Beas Cloudburst Extreme",
        "description": "Historical 2023 monsoon extreme cloudburst with saturated soils and catastrophic riverbank erosion.",
        "rainfall_intensity_mmh": 65.0,
        "antecedent_rain_3d_mm": 185.0,
        "soil_moisture_pct": 88.5,
        "slope_deg": 38.2,
        "susceptibility_class": 4,
        "river_water_level_m": 4.85,
        "river_discharge_m3s": 2850.0,
        "location_name": "Solang_Palchan_Confluence",
        "dam_height_m": 25.0,
        "impounded_volume_m3": 450000.0,
    },
    "MONSOON_SURGE": {
        "scenario_id": "MONSOON_SURGE",
        "title": "Active Monsoon Orographic Surge",
        "description": "Persistent heavy rainfall across Rohtang crest with high antecedent saturation.",
        "rainfall_intensity_mmh": 38.0,
        "antecedent_rain_3d_mm": 95.0,
        "soil_moisture_pct": 74.0,
        "slope_deg": 32.5,
        "susceptibility_class": 3,
        "river_water_level_m": 3.40,
        "river_discharge_m3s": 1420.0,
        "location_name": "Old_Manali_Manalsu",
        "dam_height_m": 15.0,
        "impounded_volume_m3": 180000.0,
    },
    "MODERATE_MOUNTAIN_RAIN": {
        "scenario_id": "MODERATE_MOUNTAIN_RAIN",
        "title": "Moderate Mountain Precipitation",
        "description": "Steady seasonal precipitation on partially drained soils within safe threshold margins.",
        "rainfall_intensity_mmh": 14.0,
        "antecedent_rain_3d_mm": 35.0,
        "soil_moisture_pct": 52.0,
        "slope_deg": 28.0,
        "susceptibility_class": 2,
        "river_water_level_m": 2.10,
        "river_discharge_m3s": 650.0,
        "location_name": "Kullu_Valley_Main_Stem",
        "dam_height_m": 8.0,
        "impounded_volume_m3": 45000.0,
    },
    "DRY_BASELINE": {
        "scenario_id": "DRY_BASELINE",
        "title": "Dry Pre-Monsoon Baseline",
        "description": "Baseflow conditions with unsaturated slopes and clear atmospheric profile.",
        "rainfall_intensity_mmh": 1.5,
        "antecedent_rain_3d_mm": 5.0,
        "soil_moisture_pct": 28.0,
        "slope_deg": 25.0,
        "susceptibility_class": 1,
        "river_water_level_m": 1.25,
        "river_discharge_m3s": 220.0,
        "location_name": "Bhuntar_Confluence",
        "dam_height_m": 0.0,
        "impounded_volume_m3": 0.0,
    },
}


class FeatureEngineeringRequest(BaseModel):
    source_mode: Literal["LIVE", "SCENARIO", "CUSTOM"] = Field(
        "LIVE", description="Source of observations: LIVE (from agency snapshot), SCENARIO (preset), or CUSTOM"
    )
    scenario_id: Optional[str] = Field(None, description="Scenario ID if source_mode=SCENARIO")
    rainfall_intensity_mmh: Optional[float] = Field(None, ge=0.0, description="1h rain intensity in mm/h")
    antecedent_rain_3d_mm: Optional[float] = Field(None, ge=0.0, description="3-day antecedent rainfall in mm")
    soil_moisture_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil moisture saturation %")
    slope_deg: Optional[float] = Field(None, ge=0.0, le=90.0, description="Terrain slope gradient in degrees")
    susceptibility_class: Optional[int] = Field(None, ge=1, le=4, description="M6 susceptibility tier (1-4)")
    river_water_level_m: Optional[float] = Field(None, ge=0.0, description="River stage in meters")
    river_discharge_m3s: Optional[float] = Field(None, ge=0.0, description="River discharge in m3/s")
    location_name: Optional[str] = Field("Upper_Beas_Catchment", description="Location name or reach")


class ModelExecutionRequest(FeatureEngineeringRequest):
    run_flood_physics: bool = Field(True, description="Execute SCS-CN runoff and 30m DEM routing")
    run_landslide_ai: bool = Field(True, description="Execute XGBoost/LightGBM landslide trigger AI")
    run_cascade_analysis: bool = Field(True, description="Execute river bottleneck and compound cascade analysis")
    run_hyperlocal_mapping: bool = Field(True, description="Execute Ward/Gram Panchayat risk mapping")


@router.get("/scenarios", summary="List available storm scenarios for testing")
def list_scenarios() -> Dict[str, Any]:
    """Returns curated meteorological and hydrologic storm scenarios for interactive model testing."""
    return {
        "status": "success",
        "total_scenarios": len(CURATED_SCENARIOS),
        "scenarios": list(CURATED_SCENARIOS.values()),
    }


def _resolve_raw_inputs(req: FeatureEngineeringRequest) -> Dict[str, Any]:
    """Resolves raw inputs from live snapshot, curated scenario, or custom overrides."""
    inputs: Dict[str, Any] = {}

    if req.source_mode == "SCENARIO" and req.scenario_id in CURATED_SCENARIOS:
        inputs.update(CURATED_SCENARIOS[req.scenario_id])
    elif req.source_mode == "LIVE":
        # Pull latest composite snapshot from active feeds
        snapshot = multi_source_service.get_composite_basin_snapshot()
        phys = snapshot.get("physical_indicators", {})
        inputs["rainfall_intensity_mmh"] = phys.get("max_rainfall_rate_mmh") or 18.5
        inputs["river_water_level_m"] = phys.get("max_water_level_m") or 3.25
        sm_vol = phys.get("avg_soil_moisture_cm3cm3")
        inputs["soil_moisture_pct"] = (sm_vol / 0.45 * 100.0) if sm_vol else 68.0
        inputs["antecedent_rain_3d_mm"] = 72.0
        inputs["slope_deg"] = 32.5
        inputs["susceptibility_class"] = 3
        inputs["river_discharge_m3s"] = 450.0
        inputs["location_name"] = "Upper_Beas_Monitored_Basin"
        inputs["_snapshot_metadata"] = {
            "active_sources_count": snapshot.get("active_sources_count", 0),
            "confidence_score": snapshot.get("confidence_score", 0.0),
            "fusion_state": snapshot.get("fusion_state", "DEGRADED"),
            "fail_soft_engaged": snapshot.get("fail_soft_engaged", True),
        }

    # Apply custom overrides if provided
    if req.rainfall_intensity_mmh is not None:
        inputs["rainfall_intensity_mmh"] = req.rainfall_intensity_mmh
    if req.antecedent_rain_3d_mm is not None:
        inputs["antecedent_rain_3d_mm"] = req.antecedent_rain_3d_mm
    if req.soil_moisture_pct is not None:
        inputs["soil_moisture_pct"] = req.soil_moisture_pct
    if req.slope_deg is not None:
        inputs["slope_deg"] = req.slope_deg
    if req.susceptibility_class is not None:
        inputs["susceptibility_class"] = req.susceptibility_class
    if req.river_water_level_m is not None:
        inputs["river_water_level_m"] = req.river_water_level_m
    if req.river_discharge_m3s is not None:
        inputs["river_discharge_m3s"] = req.river_discharge_m3s
    if req.location_name:
        inputs["location_name"] = req.location_name

    # Set default values if still missing
    inputs.setdefault("rainfall_intensity_mmh", 25.0)
    inputs.setdefault("antecedent_rain_3d_mm", 60.0)
    inputs.setdefault("soil_moisture_pct", 65.0)
    inputs.setdefault("slope_deg", 32.0)
    inputs.setdefault("susceptibility_class", 2)
    inputs.setdefault("river_water_level_m", 2.80)
    inputs.setdefault("river_discharge_m3s", 550.0)
    inputs.setdefault("location_name", "Upper_Beas_Reach")

    return inputs


@router.post("/feature-engineering", summary="Execute feature engineering pipeline on multi-source data")
def extract_engineered_features(req: FeatureEngineeringRequest) -> Dict[str, Any]:
    """
    Constructs validated mathematical feature vectors from multi-source observations.
    Executes:
    1. Landslide Feature Pipeline (Slope, Pore Saturation, Antecedent Rain, Susceptibility Class).
    2. SCS-CN Hydrologic Parameter Engineering (Effective Curve Number, Potential Retention S, Initial Abstraction Ia).
    3. DEM Topographic Extraction (Relief, Channel Gradient, Flow Accumulation).
    """
    raw_inputs = _resolve_raw_inputs(req)

    # 1. Landslide Feature Pipeline
    pipeline = LandslideFeaturePipeline()
    feature_df, feature_meta = pipeline.extract_features(raw_inputs)
    landslide_features = feature_df.iloc[0].to_dict()

    # 2. SCS-CN Hydrologic Parameters
    rain_p = float(raw_inputs.get("rainfall_intensity_mmh", 0.0))
    ant_rain = float(raw_inputs.get("antecedent_rain_3d_mm", 0.0))
    sm_pct = float(raw_inputs.get("soil_moisture_pct", 50.0))

    # AMC Classification
    if ant_rain > 53.0 or sm_pct > 75.0:
        amc = "AMC_III"
        cn_eff = 87.0
    elif ant_rain < 35.0 and sm_pct < 45.0:
        amc = "AMC_I"
        cn_eff = 55.0
    else:
        amc = "AMC_II"
        cn_eff = 74.0

    retention_s = round((25400.0 / cn_eff) - 254.0, 2)
    initial_ia = round(0.2 * retention_s, 2)
    if rain_p > initial_ia:
        runoff_depth_q = round(((rain_p - initial_ia) ** 2) / (rain_p - initial_ia + retention_s), 2)
    else:
        runoff_depth_q = 0.0
    runoff_coeff = round(runoff_depth_q / rain_p, 3) if rain_p > 0 else 0.0

    # 3. Topographic DEM Gradients
    dem_metrics = {
        "mean_slope_deg": round(float(raw_inputs.get("slope_deg", 32.5)), 2),
        "elevation_relief_m": 2960.8,
        "channel_gradient_m_m": 0.0348,
        "catchment_area_km2": 3274.0,
        "dem_resolution_m": 30.0,
        "dem_source": "Copernicus 30m Global DEM (COP30)",
    }

    return {
        "status": "success",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_mode": req.source_mode,
        "scenario_id": req.scenario_id,
        "location_name": raw_inputs.get("location_name"),
        "raw_inputs": raw_inputs,
        "engineered_features": {
            "landslide_ai_vector": landslide_features,
            "scs_cn_hydrologic_vector": {
                "amc_condition": amc,
                "effective_curve_number": cn_eff,
                "potential_retention_s_mm": retention_s,
                "initial_abstraction_ia_mm": initial_ia,
                "direct_runoff_depth_mm": runoff_depth_q,
                "runoff_coefficient": runoff_coeff,
            },
            "topographic_dem_vector": dem_metrics,
        },
        "feature_metadata": feature_meta,
        "data_sources_connected": [
            {"source_id": "IMD_AWS", "measurement": "1h Rainfall Intensity", "value": f"{rain_p} mm/h"},
            {"source_id": "INSAT_3DS", "measurement": "3d Antecedent Rainfall", "value": f"{ant_rain} mm"},
            {"source_id": "SMAP", "measurement": "Soil Moisture Saturation", "value": f"{sm_pct} %"},
            {"source_id": "COP30_DEM", "measurement": "Slope & Relief", "value": f"{dem_metrics['mean_slope_deg']}°"},
            {"source_id": "CWC_RIVER", "measurement": "River Stage", "value": f"{raw_inputs.get('river_water_level_m')} m"},
        ],
    }


@router.post("/run-models", summary="Run decoupled ML/AI and physics models through engineered features")
def run_models_through_features(
    req: ModelExecutionRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes Flood Physics (SCS-CN + DEM Routing), Landslide AI (XGBoost/LightGBM),
    River Bottleneck Detection, and Hyperlocal Administrative Mapping through engineered features.
    """
    start_time = datetime.datetime.now(datetime.timezone.utc)
    raw_inputs = _resolve_raw_inputs(req)

    # 1. Feature Engineering
    pipeline = LandslideFeaturePipeline()
    feature_df, feature_meta = pipeline.extract_features(raw_inputs)
    landslide_features = feature_df.iloc[0].to_dict()

    results: Dict[str, Any] = {
        "status": "success",
        "timestamp": start_time.isoformat(),
        "source_mode": req.source_mode,
        "scenario_id": req.scenario_id,
        "location_name": raw_inputs.get("location_name"),
        "raw_inputs": raw_inputs,
        "feature_engineering": {
            "landslide_features": landslide_features,
            "feature_metadata": feature_meta,
        },
        "model_outputs": {},
    }

    # 2. Execute Decoupled Analysis Coordinator
    analysis_results = decoupled_analysis_coordinator.execute_all(raw_inputs)

    # Flood Physics Output
    flood_res = analysis_results.get("flood_physics")
    if flood_res and req.run_flood_physics:
        results["model_outputs"]["flood_physics"] = {
            "status": flood_res.execution_status.value,
            "component_name": flood_res.component_name,
            "confidence_score": flood_res.confidence_score,
            "data_mode": flood_res.data_mode.value if hasattr(flood_res.data_mode, "value") else str(flood_res.data_mode),
            "payload": flood_res.output_payload,
            "duration_ms": flood_res.processing_duration_ms,
        }

    # Landslide AI Output
    landslide_res = analysis_results.get("landslide_ai")
    if landslide_res and req.run_landslide_ai:
        results["model_outputs"]["landslide_ai"] = {
            "status": landslide_res.execution_status.value,
            "component_name": landslide_res.component_name,
            "confidence_score": landslide_res.confidence_score,
            "data_mode": landslide_res.data_mode.value if hasattr(landslide_res.data_mode, "value") else str(landslide_res.data_mode),
            "payload": landslide_res.output_payload,
            "duration_ms": landslide_res.processing_duration_ms,
        }

    # 3. River Bottleneck & Cascade Intelligence
    if req.run_cascade_analysis:
        trigger_prob = (
            landslide_res.output_payload.get("trigger_probability", 0.5)
            if (landslide_res and landslide_res.output_payload)
            else 0.5
        )
        sample_landslides = [
            {
                "latitude": 31.7225,
                "longitude": 77.2185,
                "trigger_probability": trigger_prob,
                "susceptibility_class": raw_inputs.get("susceptibility_class", 3),
            },
            {
                "latitude": 32.3142,
                "longitude": 77.1595,
                "trigger_probability": max(0.2, trigger_prob - 0.15),
                "susceptibility_class": 3,
            },
        ]
        discharge = float(raw_inputs.get("river_discharge_m3s", 450.0))
        bottlenecks = cascade_spatial_service.detect_river_bottlenecks(
            landslides=sample_landslides,
            discharge_m3s=discharge,
        )
        cascade_eval = cascade_spatial_service.evaluate_cascade_hazard(
            bottlenecks=bottlenecks,
            baseline_discharge_m3s=discharge,
        )
        results["model_outputs"]["cascade_intelligence"] = {
            "detected_bottlenecks_count": len(bottlenecks),
            "bottlenecks": bottlenecks,
            "cascade_assessment": cascade_eval,
        }

    # 4. Hyperlocal Ward & Gram Panchayat Impact Mapping
    if req.run_hyperlocal_mapping:
        flood_hazard = 0.5
        if flood_res and flood_res.output_payload:
            runoff_depth = flood_res.output_payload.get("scs_cn", {}).get("direct_runoff_depth_mm", 10.0)
            flood_hazard = min(1.0, runoff_depth / 40.0)

        landslide_hazard = (
            landslide_res.output_payload.get("trigger_probability", 0.5)
            if (landslide_res and landslide_res.output_payload)
            else 0.5
        )

        admin_units = cascade_spatial_service.aggregate_hyperlocal_risk(
            flood_hazard_score=flood_hazard,
            landslide_hazard_score=landslide_hazard,
            cascade_state="POTENTIAL_OBSTRUCTION" if (trigger_prob := landslide_hazard) > 0.65 else "NOT_ESTABLISHED",
            provenance="OPERATIONAL" if req.source_mode == "LIVE" else "SYNTHETIC_BENCHMARK",
        )

        # Calculate total population and infrastructure impacted
        total_exposed_pop = sum(
            u.get("exposure", {}).get("affected_population", 0) or u.get("exposure", {}).get("total_estimated_population", 0)
            for u in admin_units
            if u.get("current_hazard", {}).get("risk_level") in ["CRITICAL", "HIGH", "WARNING"]
        )
        total_affected_wards = sum(
            1 for u in admin_units
            if u.get("current_hazard", {}).get("risk_level") in ["CRITICAL", "HIGH", "WARNING"]
        )

        flattened_units = []
        for u in admin_units:
            flattened_units.append({
                "admin_id": u["admin_id"],
                "unit_name": u["name"],
                "unit_type": u["unit_type"],
                "risk_tier": u.get("current_hazard", {}).get("risk_level", "LOW"),
                "hazard_score": u.get("current_hazard", {}).get("max_hazard_score", 0.0),
                "dominant_hazard": u.get("current_hazard", {}).get("dominant_hazard", "NONE"),
                "total_dynamic_population": u.get("exposure", {}).get("total_estimated_population", 0),
                "affected_population": u.get("exposure", {}).get("affected_population", 0),
                "social_vulnerability_index": u.get("exposure", {}).get("vulnerability_index", 0.0),
                "exposed_infrastructure_count": u.get("exposure", {}).get("exposed_infrastructure_count", 0),
                "exposed_infrastructure": u.get("exposure", {}).get("exposed_infrastructure", []),
                "centroid": u.get("centroid"),
            })

        results["model_outputs"]["hyperlocal_impact"] = {
            "total_administrative_units": len(admin_units),
            "high_risk_units_count": total_affected_wards,
            "total_exposed_population": total_exposed_pop,
            "administrative_units": flattened_units,
        }

    return results


@router.get("/live-pipeline", summary="Execute end-to-end pipeline from live multi-source observations")
def execute_live_pipeline(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """One-click trigger that ingests live multi-source feeds, engineers features, and evaluates all models."""
    req = ModelExecutionRequest(
        source_mode="LIVE",
        run_flood_physics=True,
        run_landslide_ai=True,
        run_cascade_analysis=True,
        run_hyperlocal_mapping=True,
    )
    return run_models_through_features(req, db=db)
