"""
pipeline.py — Master Satellite Hazard Intelligence & Development Risk Pipeline
==============================================================================
Orchestrates the entire First Milestone pipeline:
  Sentinel-2 (T1, T2) + DEM + WorldCover
                 │
        Cloud & Quality Audit
                 │
         Terrain Preprocessing (Horn's Curvatures, TWI, HAND)
                 │
       Spectral Indices (NDVI, MNDWI, NDBI, NDMI)
                 │
       Multi-Temporal Surface Change Detection
                 │
  ┌──────────────┼───────────────────────────┐
  ▼              ▼                           ▼
Flood Model   Landslide Model    Development Pressure Engine
  │              │                           │
  └──────────────┴───────────────────────────┤
                                             ▼
                             Development-Induced Hazard Model
                                             │
                                             ▼
                                  Multi-Hazard Fusion
                                             │
                                             ▼
                               GIS Export & Leaflet Map
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ml.satellite_hazard.change_detection.surface_change import SurfaceChangeEngine
from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.development_detection.pressure_engine import DevelopmentPressureEngine
from ml.satellite_hazard.development_risk.hazard_risk_model import DevelopmentHazardModel
from ml.satellite_hazard.export.gis_exporter import GISExporter
from ml.satellite_hazard.exposure.infrastructure_impact import InfrastructureImpactEngine
from ml.satellite_hazard.flood.flood_susceptibility import SatelliteFloodModel
from ml.satellite_hazard.flood.segmentation.unet_model import train_multimodal_flood_unet
from ml.satellite_hazard.ingestion.dem_loader import DEMLoader
from ml.satellite_hazard.ingestion.landcover_loader import LandCoverLoader
from ml.satellite_hazard.ingestion.sentinel2_loader import Sentinel2Loader
from ml.satellite_hazard.landslide.landslide_susceptibility import SatelliteLandslideModel
from ml.satellite_hazard.multi_hazard.fusion_engine import MultiHazardFusionEngine
from ml.satellite_hazard.quality.cloud_filter import CloudQualityFilter
from ml.satellite_hazard.sar.sar_loader import Sentinel1SARLoader
from ml.satellite_hazard.spectral.index_generator import SpectralIndexGenerator
from ml.satellite_hazard.time_series.trend_engine import TimeSeriesTrendEngine
from ml.satellite_hazard.visualization.leaflet_builder import LeafletDashboardBuilder


class SatelliteHazardPipeline:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()
        self.s2_loader = Sentinel2Loader(self.config)
        self.sar_loader = Sentinel1SARLoader(self.config)
        self.dem_loader = DEMLoader(self.config)
        self.lulc_loader = LandCoverLoader(self.config)
        self.quality_filter = CloudQualityFilter(self.config)
        from ml.satellite_hazard.terrain.terrain_engine import TerrainEngine
        self.terrain_engine = TerrainEngine(self.config)
        self.spectral_engine = SpectralIndexGenerator(self.config)
        self.change_engine = SurfaceChangeEngine()
        self.flood_model = SatelliteFloodModel(self.config)
        self.landslide_model = SatelliteLandslideModel(self.config)
        self.pressure_engine = DevelopmentPressureEngine(self.config)
        self.dev_risk_model = DevelopmentHazardModel(self.config)
        self.fusion_engine = MultiHazardFusionEngine(self.config)
        self.exposure_engine = InfrastructureImpactEngine(self.config)
        self.trend_engine = TimeSeriesTrendEngine(self.config)
        self.gis_exporter = GISExporter(self.config)
        self.leaflet_builder = LeafletDashboardBuilder(self.config)

    def run(self) -> Dict[str, Any]:
        print("=" * 70)
        print("FLOODY SHIELD — SATELLITE HAZARD & DEVELOPMENT RISK PIPELINE")
        print("=" * 70)

        # 1. Ingestion: Pre-Event (T1) and Post-Event (T2)
        print("[1/12] Ingesting Sentinel-2 Multispectral Granules (T1 & T2)...")
        scene_t1 = self.s2_loader.generate_calibrated_scene(
            scene_id="S2A_MSIL2A_20260520_PRE_EVENT",
            acquisition_date="2026-05-20",
            event_type="baseline_pre_event",
        )
        scene_t2 = self.s2_loader.generate_calibrated_scene(
            scene_id="S2A_MSIL2A_20260715_POST_EVENT",
            acquisition_date="2026-07-15",
            event_type="monsoon_flood_post_event",
        )

        # 2. Sentinel-1 C-Band SAR Radar Ingestion (All-Weather Cloud-Penetration)
        print("[2/12] Ingesting Sentinel-1 C-Band SAR Radar (VV, VH) & Applying Lee Speckle Filter...")
        sar_baseline = self.sar_loader.generate_calibrated_sar_scene(is_flood_event=False)
        sar_event = self.sar_loader.generate_calibrated_sar_scene(is_flood_event=True)
        sar_flood_mask, sar_conf, sar_flood_pct = self.sar_loader.detect_sar_flood_inundation(sar_baseline, sar_event)
        print(f"       SAR Speckle Variance Reduction: {sar_event.raw_speckle_std:.2f} -> {sar_event.filtered_speckle_std:.2f}")
        print(f"       Cloud-Penetrating SAR Flood Inundation Area: {sar_flood_pct}%")

        # 3. Quality & Cloud Filtering
        print("[3/12] Performing SCL Cloud Masking and Quality Auditing...")
        clean_bands_t2, valid_mask, audit_report = self.quality_filter.audit_and_filter(scene_t2)
        print(f"       Valid Data Fraction: {audit_report.valid_data_fraction * 100:.1f}%")

        # 4. Terrain Extraction from Copernicus DEM
        print("[4/12] Deriving 30m Geomorphic Terrain Features from Copernicus DEM...")
        dem_scene = self.dem_loader.generate_calibrated_dem()
        terrain_feats = self.terrain_engine.process(dem_scene)
        print(f"       Elevation Range: {dem_scene.min_elev:.0f}m - {dem_scene.max_elev:.0f}m ASL")

        # 5. Land Cover Ingestion
        print("[5/12] Ingesting ESA WorldCover 10m Ground Reference Layer...")
        lulc_scene = self.lulc_loader.generate_calibrated_lulc()

        # 6. Spectral Index Generation
        print("[6/12] Calculating Standardized Multispectral Indices (NDVI, MNDWI, NDBI)...")
        spectral_t1 = self.spectral_engine.calculate_all(scene_t1.bands)
        spectral_t2 = self.spectral_engine.calculate_all(clean_bands_t2)

        # 7. Multi-Temporal Surface Change Detection
        print("[7/12] Computing Multi-Temporal Surface Change (T2 vs T1)...")
        change_res = self.change_engine.compare(spectral_t1, spectral_t2)

        # 8. Deep Learning Multimodal Flood Segmentation U-Net
        print("[8/12] Training & Inferring 9-Channel Multimodal PyTorch Flood U-Net...")
        unet_res = train_multimodal_flood_unet(
            optical_scene=scene_t2,
            sar_scene=sar_event,
            terrain=terrain_feats,
            output_dir=self.config.output_dir,
            epochs=35,
        )
        print(f"       U-Net Segmentation Performance: Dice (F1) = {unet_res.dice_f1_score * 100:.1f}%, IoU = {unet_res.iou_jaccard_score * 100:.1f}%")

        # 9. Hazard Susceptibility Modeling
        print("[9/12] Generating Flood & Landslide Susceptibility Models...")
        flood_res = self.flood_model.analyze(spectral_t2, terrain_feats)
        landslide_res = self.landslide_model.analyze(spectral_t2, terrain_feats)
        print(f"       High Flood Susceptibility: {flood_res.high_susceptibility_area_pct}%")
        print(f"       High Landslide Susceptibility: {landslide_res.high_susceptibility_area_pct}%")

        # 10. Observed Development Pressure & Induced Hazard Risk
        print("[10/12] Evaluating Observed Development Pressure & Induced Risk...")
        dev_pressure = self.pressure_engine.evaluate(spectral_t2, terrain_feats)
        dev_risk = self.dev_risk_model.evaluate(dev_pressure, flood_res, landslide_res, terrain_feats)
        print(f"       High Development Pressure Area: {dev_pressure.high_pressure_area_pct}%")
        print(f"       High Development-Induced Risk Area: {dev_risk.high_risk_area_pct}%")

        # 11. Multi-Hazard Fusion & Zone Synthesis
        print("[11/12] Fusing Multi-Hazard Risk & Synthesizing Critical/Safe Zones...")
        fusion_res = self.fusion_engine.fuse(
            flood_res=flood_res,
            landslide_res=landslide_res,
            dev_pressure=dev_pressure,
            dev_risk=dev_risk,
            terrain=terrain_feats,
            valid_mask=valid_mask,
        )
        print(f"       Critical Development Area: {fusion_res.critical_zone_area_pct}%")
        print(f"       Candidate Safe Area: {fusion_res.candidate_safe_area_pct}%")

        # 12. GIS Export, Infrastructure Impact & Leaflet Visualization
        print("[12/12] Exporting GeoTIFFs, Infrastructure Impact Summary & Interactive Map...")
        export_pkg = self.gis_exporter.export_all(
            flood_res=flood_res,
            landslide_res=landslide_res,
            dev_pressure=dev_pressure,
            dev_risk=dev_risk,
            fusion_res=fusion_res,
        )
        impact_summary = self.exposure_engine.evaluate_exposure(export_pkg)
        trend_summary = self.trend_engine.analyze_trajectory(spectral_t1, spectral_t2)
        html_path = self.leaflet_builder.build_dashboard(export_pkg)
        print(f"        Interactive Dashboard: {html_path}")
        print(f"        Impact Summary saved: {self.config.output_dir / 'impact_summary.json'}")

        summary = {
            "status": "SUCCESS",
            "study_area": self.config.study_area.name,
            "total_pixels": terrain_feats.shape[0] * terrain_feats.shape[1],
            "valid_data_pct": round(audit_report.valid_data_fraction * 100.0, 2),
            "sar_cloud_penetrating_flood_pct": sar_flood_pct,
            "unet_segmentation_dice_score": unet_res.dice_f1_score,
            "unet_segmentation_iou": unet_res.iou_jaccard_score,
            "high_flood_susceptibility_pct": flood_res.high_susceptibility_area_pct,
            "high_landslide_susceptibility_pct": landslide_res.high_susceptibility_area_pct,
            "high_development_pressure_pct": dev_pressure.high_pressure_area_pct,
            "critical_development_zones_count": export_pkg.total_critical_zones,
            "candidate_safe_zones_count": export_pkg.total_candidate_zones,
            "total_population_exposed": impact_summary.total_population_exposed,
            "total_buildings_exposed": impact_summary.total_buildings_exposed,
            "total_roads_exposed_km": impact_summary.total_roads_exposed_km,
            "total_bridges_compromised": impact_summary.total_bridges_compromised,
            "development_trend": trend_summary.development_trend,
            "hazard_trend": trend_summary.hazard_trend,
            "raster_files": [str(p) for p in export_pkg.raster_files.values()] + [
                str(unet_res.probability_raster_path),
                str(unet_res.mask_raster_path),
                str(unet_res.confidence_raster_path),
            ],
            "vector_files": [str(p) for p in export_pkg.vector_files.values()],
            "impact_summary_file": str(self.config.output_dir / "impact_summary.json"),
            "dashboard_url": str(html_path),
        }

        print("=" * 70)
        print("SATELLITE HAZARD PIPELINE COMPLETED WITH ADVANCED RADAR & U-NET!")
        print("=" * 70)
        return summary


if __name__ == "__main__":
    pipe = SatelliteHazardPipeline()
    res = pipe.run()
    import json
    print(json.dumps(res, indent=2))
