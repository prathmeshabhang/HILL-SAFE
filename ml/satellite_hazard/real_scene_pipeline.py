"""
real_scene_pipeline.py — Master Real-Scene Geospatial Disaster Intelligence Pipeline
=====================================================================================
Executes the full end-to-end mission architecture on real satellite scenes:

REAL SENTINEL-1/2 SCENE
        ↓
Quality / Cloud Check
        ↓
Automatic Preprocessing
        ↓
DEM Alignment
        ↓
9-Channel Feature Stack
        ↓
 ┌──────┼──────────┬─────────────┐
 ↓      ↓          ↓             ↓
Flood  Landslide  River Change  Development
 ↓      ↓          ↓             ↓
 └──────┼──────────┴─────────────┘
        ↓
Natural Dam Detection
        ↓
Multi-Hazard Fusion
        ↓
GeoTIFF + GeoJSON
        ↓
POSTGIS
        ↓
LIVE LEAFLET MAP
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from gis.natural_dam.export.postgis_sync import PostGISSynchronizer, PostGISSyncSummary
from ml.natural_dam.inference.pipeline_runner import NaturalDamPipeline
from ml.satellite_hazard.change_detection.surface_change import SurfaceChangeEngine
from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.development_detection.pressure_engine import DevelopmentPressureEngine
from ml.satellite_hazard.development_risk.hazard_risk_model import DevelopmentHazardModel
from ml.satellite_hazard.export.gis_exporter import GISExporter
from ml.satellite_hazard.exposure.infrastructure_impact import InfrastructureImpactEngine
from ml.satellite_hazard.flood.flood_susceptibility import SatelliteFloodModel
from ml.satellite_hazard.ingestion.real_scene_loader import RealSceneBundle, RealSceneLoader
from ml.satellite_hazard.landslide.landslide_susceptibility import SatelliteLandslideModel
from ml.satellite_hazard.multi_hazard.fusion_engine import MultiHazardFusionEngine
from ml.satellite_hazard.preprocessing.feature_stack import FeatureStackConstructor
from ml.satellite_hazard.preprocessing.spatial_aligner import SpatialAligner
from ml.satellite_hazard.spectral.index_generator import SpectralIndexGenerator, SpectralIndices
from ml.satellite_hazard.terrain.terrain_engine import DEMScene, TerrainEngine, TerrainFeatures
from ml.satellite_hazard.visualization.leaflet_builder import LeafletDashboardBuilder


@dataclass
class RealScenePipelineResult:
    scene_id: str
    status: str
    valid_data_pct: float
    cloud_cover_pct: float
    data_quality_grade: str
    flood_susceptibility_pct: float
    landslide_susceptibility_pct: float
    development_pressure_pct: float
    natural_dam_candidates_count: int
    critical_hazard_zones_count: int
    candidate_safe_zones_count: int
    postgis_sync: PostGISSyncSummary
    raster_files: Dict[str, str]
    vector_files: Dict[str, str]
    dashboard_url: str
    models_metadata: Optional[Dict[str, Any]] = None


class RealSceneDisasterPipeline:
    """
    Unified end-to-end geospatial processor executing remote sensing,
    geomorphic analysis, hazard modeling, natural dam detection, PostGIS sync,
    and Leaflet map rendering.
    """

    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()
        self.output_dir = self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scene_loader = RealSceneLoader(self.config)
        self.spatial_aligner = SpatialAligner(self.config)
        self.spectral_engine = SpectralIndexGenerator(self.config)
        self.terrain_engine = TerrainEngine(self.config)
        self.feature_stack_constructor = FeatureStackConstructor()
        self.flood_model = SatelliteFloodModel(self.config)
        self.landslide_model = SatelliteLandslideModel(self.config)
        self.change_engine = SurfaceChangeEngine()
        self.pressure_engine = DevelopmentPressureEngine(self.config)
        self.dev_risk_model = DevelopmentHazardModel(self.config)
        self.natural_dam_engine = NaturalDamPipeline()
        self.fusion_engine = MultiHazardFusionEngine(self.config)
        self.gis_exporter = GISExporter(self.config)
        self.postgis_sync = PostGISSynchronizer(self.output_dir)
        self.exposure_engine = InfrastructureImpactEngine(self.config)
        self.leaflet_builder = LeafletDashboardBuilder(self.config)

    def process(self, scene_dir: Path | str | None = None) -> RealScenePipelineResult:
        """
        Executes complete pipeline on real scene files from disk.
        """
        target_dir = Path(scene_dir) if scene_dir else Path(__file__).resolve().parents[2] / "data" / "raw" / "scenes" / "upper_beas_july2023"

        print("=" * 75)
        print("FLOODY SHIELD — REAL SATELLITE DISASTER INTELLIGENCE PIPELINE")
        print("=" * 75)

        # 1. REAL SENTINEL-1/2 SCENE INGESTION
        print(f"[1/8] Ingesting real satellite scene from: {target_dir.name}...")
        bundle: RealSceneBundle = self.scene_loader.load_scene(target_dir)

        # 2. QUALITY / CLOUD AUDIT
        print(f"[2/8] Performing SCL Cloud Audit: Cloud={bundle.cloud_cover_pct}%, Valid={bundle.valid_data_pct}% (Grade: {bundle.data_quality_grade})")

        # 3. PREPROCESSING & DEM ALIGNMENT
        print("[3/8] Aligning multi-sensor grid & deriving 3D geomorphic curvatures from Copernicus DEM...")
        aligned = self.spatial_aligner.align_and_process(bundle)
        dem_scene = DEMScene(
            name=bundle.scene_id,
            crs="EPSG:4326",
            bounds=bundle.bounds,
            shape=aligned.shape,
            cell_size_m=float(self.spatial_aligner.cell_size_m),
            elevation=aligned.dem_elevation_m,
            min_elev=float(np.nanmin(aligned.dem_elevation_m)),
            max_elev=float(np.nanmax(aligned.dem_elevation_m)),
            mean_elev=float(np.nanmean(aligned.dem_elevation_m)),
        )
        terrain = self.terrain_engine.process(dem_scene)

        # 4. 9-CHANNEL FEATURE STACK & SPECTRAL INDICES
        print("[4/8] Assembling 9-Channel Normalized Feature Stack (B, 9, H, W)...")
        stack = self.feature_stack_constructor.construct(aligned)
        spectral = self.spectral_engine.calculate_all(aligned.s2_bands)

        # 5. PARALLEL 4-BRANCH EXTRACTION (Flood, Landslide, River Change, Development)
        print("[5/8] Running parallel hazard engines:")
        # Branch 1: Flood (Multimodal PyTorch U-Net + Calibrated XGBoost Model M2)
        flood_res = self.flood_model.analyze(spectral, terrain, stack_9ch=stack.array_9ch)
        if flood_res.inference_mode == "ML_INFERENCE":
            print(f"       • [ML] Multimodal 9-Ch PyTorch U-Net Active Inundation: {flood_res.active_water_area_pct}%")
            print(f"       • [ML] Model M2 Calibrated XGBoost Flood Susceptibility: {flood_res.high_susceptibility_area_pct}%")
        else:
            print(f"       • Flood Inundation & Susceptibility (Heuristic): {flood_res.high_susceptibility_area_pct}%")

        # Branch 2: Landslide (Model M6 Random Forest + Model M7 LightGBM)
        landslide_res = self.landslide_model.analyze(spectral, terrain)
        if landslide_res.inference_mode == "ML_INFERENCE":
            trigger_pct = round(float(np.mean(landslide_res.trigger_probability >= 0.60) * 100.0), 2) if landslide_res.trigger_probability is not None else 0.0
            mean_trig = round(float(np.mean(landslide_res.trigger_probability)), 4) if landslide_res.trigger_probability is not None else 0.0
            print(f"       • [ML] Model M6 Random Forest Landslide Susceptibility: {landslide_res.high_susceptibility_area_pct}%")
            print(f"       • [ML] Model M7 LightGBM Dynamic Rainfall Trigger Area (P>=0.60): {trigger_pct}% (Mean P: {mean_trig})")
        else:
            print(f"       • Landslide Susceptibility (Heuristic): {landslide_res.high_susceptibility_area_pct}%")

        # Branch 3: Development Pressure & Induced Risk
        dev_pressure = self.pressure_engine.evaluate(spectral, terrain)
        dev_risk = self.dev_risk_model.evaluate(dev_pressure, flood_res, landslide_res, terrain)
        print(f"       • Development Pressure & Riparian Encroachment: {dev_pressure.high_pressure_area_pct}%")

        # 6. NATURAL DAM DETECTION & OUTBURST RISK
        print("[6/8] Executing 8-evidence Natural River Dam & Landslide Dam Detection Engine...")
        natural_dam_records = self.natural_dam_engine.run_detection_for_corridor()
        cand_count = len(natural_dam_records)
        print(f"       • Natural Dam Candidates Detected: {cand_count}")

        # Serialize natural dam and impoundment GeoJSONs for GIS and PostGIS sync
        candidate_geojson = self.output_dir / "natural_dam_candidates.geojson"
        impoundment_geojson = self.output_dir / "impounded_water.geojson"
        cand_features = []
        imp_features = []
        for r in natural_dam_records:
            cand_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [r.candidate.lon, r.candidate.lat],
                },
                "properties": {
                    "id": r.candidate.dam_id,
                    "river_name": r.candidate.river_name,
                    "detection_probability": float(r.candidate.probability),
                    "model_confidence": float(r.candidate.confidence),
                    "candidate_tier": r.candidate.candidate_tier,
                    "status": "FALSE_POSITIVE" if r.candidate.false_positive_rejected else "AUTHORITY_VALIDATION_REQUIRED",
                    "elevation_m": float(r.candidate.elevation_m or 0.0),
                    "outburst_risk_level": r.outburst_risk.outburst_risk_level if r.outburst_risk else "LOW",
                    "peak_discharge_m3s": float((r.outburst_risk.peak_breach_discharge_m3s if r.outburst_risk else None) or 0.0),
                    "false_positive": r.candidate.false_positive_rejected,
                    "false_positive_reason": r.candidate.rejection_reason or "",
                },
            })
            if not r.candidate.false_positive_rejected:
                lon, lat = r.candidate.lon, r.candidate.lat
                d = 0.005
                imp_features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [lon - d, lat - d],
                            [lon + d, lat - d],
                            [lon + d, lat + d],
                            [lon - d, lat + d],
                            [lon - d, lat - d],
                        ]],
                    },
                    "properties": {
                        "dam_id": r.candidate.dam_id,
                        "surface_area_m2": float((r.impoundment.impounded_water_area_m2 if r.impoundment else None) or 0.0),
                        "estimated_volume_m3": float((r.impoundment.estimated_impounded_volume_m3 if r.impoundment else None) or 0.0),
                    },
                })

        with open(candidate_geojson, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": cand_features}, f, indent=2)

        with open(impoundment_geojson, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": imp_features}, f, indent=2)

        # 7. MULTI-HAZARD FUSION & ZONING
        print("[7/8] Fusing multi-hazard risks into Section 36 & Section 23 Zones...")
        valid_mask = ~np.isin(aligned.scl, self.config.cloud_scl_classes)
        fusion_res = self.fusion_engine.fuse(
            flood_res=flood_res,
            landslide_res=landslide_res,
            dev_pressure=dev_pressure,
            dev_risk=dev_risk,
            terrain=terrain,
            valid_mask=valid_mask,
        )

        # 8. GEOTIFF + GEOJSON EXPORT, POSTGIS SYNC & LEAFLET MAP
        print("[8/8] Exporting GeoTIFFs, syncing PostGIS, and rendering Live Leaflet Map...")
        export_pkg = self.gis_exporter.export_all(
            flood_res=flood_res,
            landslide_res=landslide_res,
            dev_pressure=dev_pressure,
            dev_risk=dev_risk,
            fusion_res=fusion_res,
        )

        # PostGIS Synchronization
        cdz_geojson = self.output_dir / "critical_development_zones.geojson"
        sync_summary = self.postgis_sync.sync_from_geojson(
            candidate_geojson_path=candidate_geojson,
            impoundment_geojson_path=impoundment_geojson,
            critical_zones_geojson_path=cdz_geojson,
        )
        print(f"       • PostGIS Sync: {sync_summary.candidates_synced} candidates, {sync_summary.impoundments_synced} impoundments. Script: {sync_summary.sql_script_path}")

        # Live Leaflet Map Builder
        html_path = self.leaflet_builder.build_dashboard(export_pkg)
        print(f"       • Live Leaflet Dashboard: {html_path}")
        print("=" * 75)
        print("REAL SATELLITE DISASTER INTELLIGENCE PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 75)

        models_meta = {
            "flood_branch": {
                "inference_mode": flood_res.inference_mode,
                "model_name": flood_res.model_name,
                "model_version": flood_res.model_version,
                "has_unet_segmentation": flood_res.unet_inundation_probability is not None,
                "has_m2_tabular": flood_res.m2_flood_probability is not None,
                "m2_feature_importances": flood_res.m2_feature_importances,
            },
            "landslide_branch": {
                "inference_mode": landslide_res.inference_mode,
                "model_name": landslide_res.model_name,
                "model_version": landslide_res.model_version,
                "has_m6_susceptibility": True,
                "has_m7_dynamic_trigger": landslide_res.trigger_probability is not None,
                "m6_feature_importances": landslide_res.m6_feature_importances,
                "m7_feature_importances": landslide_res.m7_feature_importances,
            },
        }

        return RealScenePipelineResult(
            scene_id=bundle.scene_id,
            status="COMPLETED",
            valid_data_pct=bundle.valid_data_pct,
            cloud_cover_pct=bundle.cloud_cover_pct,
            data_quality_grade=bundle.data_quality_grade,
            flood_susceptibility_pct=flood_res.high_susceptibility_area_pct,
            landslide_susceptibility_pct=landslide_res.high_susceptibility_area_pct,
            development_pressure_pct=dev_pressure.high_pressure_area_pct,
            natural_dam_candidates_count=cand_count,
            critical_hazard_zones_count=export_pkg.total_critical_zones,
            candidate_safe_zones_count=export_pkg.total_candidate_zones,
            postgis_sync=sync_summary,
            raster_files={k: str(v) for k, v in export_pkg.raster_files.items()},
            vector_files={k: str(v) for k, v in export_pkg.vector_files.items()},
            dashboard_url=str(html_path),
            models_metadata=models_meta,
        )


if __name__ == "__main__":
    pipeline = RealSceneDisasterPipeline()
    res = pipeline.process()
    print("\nPipeline Result Summary:")
    print(f"Scene: {res.scene_id} | Status: {res.status}")
    print(f"Data Quality: {res.data_quality_grade} (Valid: {res.valid_data_pct}%)")
    print(f"Natural Dams: {res.natural_dam_candidates_count} | PostGIS Synced: {res.postgis_sync.candidates_synced}")
