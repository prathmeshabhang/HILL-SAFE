"""
test_real_scene_pipeline.py — Integration & Verification Tests for Real Scene Pipeline
=======================================================================================
Validates the complete workflow on real multi-sensor satellite scenes:
  1. Real Scene Loader & Cloud/Quality Audit
  2. Spatial Alignment & Horn's 3D Curvature Derivation
  3. 9-Channel Multimodal Feature Stack & Tensor Normalization
  4. Parallel 4-Branch Hazard Models (Flood, Landslide, Development, Natural Dam)
  5. Multi-Hazard Fusion & Zoning (Section 36 & Section 23)
  6. GeoTIFF Rasters & OGC GeoJSON Exports
  7. PostGIS Synchronization & SQL Script Generation
  8. Interactive Leaflet Dashboard Generation
  9. FastAPI REST Endpoint: POST /api/v1/satellite/process-real-scene
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from fastapi.testclient import TestClient
import numpy as np
import torch

from backend.app.main import app
from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.ingestion.real_scene_loader import RealSceneLoader
from ml.satellite_hazard.preprocessing.feature_stack import FeatureStackConstructor
from ml.satellite_hazard.preprocessing.spatial_aligner import SpatialAligner
from ml.satellite_hazard.real_scene_pipeline import RealSceneDisasterPipeline, RealScenePipelineResult


class TestRealScenePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = SatelliteProcessingConfig()
        cls.client = TestClient(app)
        cls.pipeline = RealSceneDisasterPipeline(cls.config)

    def test_01_real_scene_loader_and_cloud_audit(self):
        """Validates ingestion of calibrated GeoTIFF granules and SCL cloud masking."""
        loader = RealSceneLoader(self.config)
        bundle = loader.load_scene()

        self.assertEqual(bundle.scene_id, "upper_beas_july2023")
        self.assertIn("B02", bundle.s2_bands)
        self.assertIn("B03", bundle.s2_bands)
        self.assertIn("B04", bundle.s2_bands)
        self.assertIn("B08", bundle.s2_bands)
        self.assertIn("B11", bundle.s2_bands)
        self.assertIn("VV", bundle.sar_bands)
        self.assertIn("VH", bundle.sar_bands)
        self.assertIsNotNone(bundle.dem)
        self.assertIsNotNone(bundle.scl)

        # Quality & Cloud checks
        self.assertGreaterEqual(bundle.valid_data_pct, 90.0)
        self.assertLessEqual(bundle.cloud_cover_pct, 15.0)
        self.assertIn(bundle.data_quality_grade, ["EXCELLENT", "GOOD"])

    def test_02_spatial_alignment_and_geomorphic_curvatures(self):
        """Verifies multi-sensor resampling, Lee speckle filtering, and 3D terrain suite."""
        loader = RealSceneLoader(self.config)
        bundle = loader.load_scene()
        aligner = SpatialAligner(self.config)
        aligned = aligner.align_and_process(bundle)

        # Verification of spatial geometry
        self.assertEqual(aligned.shape, (500, 400))
        self.assertEqual(aligned.slope_deg.shape, (500, 400))
        self.assertEqual(aligned.aspect_deg.shape, (500, 400))
        self.assertEqual(aligned.plan_curvature.shape, (500, 400))
        self.assertEqual(aligned.profile_curvature.shape, (500, 400))
        self.assertEqual(aligned.flow_accumulation.shape, (500, 400))
        self.assertEqual(aligned.hand_m.shape, (500, 400))

        # Check physical boundary sanity
        self.assertGreaterEqual(float(np.nanmin(aligned.dem_elevation_m)), 700.0)
        self.assertLessEqual(float(np.nanmax(aligned.dem_elevation_m)), 4500.0)
        self.assertGreaterEqual(float(np.nanmin(aligned.slope_deg)), 0.0)
        self.assertLessEqual(float(np.nanmax(aligned.slope_deg)), 85.0)

    def test_03_9_channel_feature_stack_and_tensor(self):
        """Validates 9-Channel array and PyTorch tensor shape and [0, 1] normalization."""
        loader = RealSceneLoader(self.config)
        bundle = loader.load_scene()
        aligner = SpatialAligner(self.config)
        aligned = aligner.align_and_process(bundle)

        stacker = FeatureStackConstructor()
        stack = stacker.construct(aligned)

        # 9-channel array verification
        self.assertEqual(stack.array_9ch.shape, (9, 500, 400))
        self.assertEqual(len(stack.channel_names), 9)
        self.assertGreaterEqual(float(np.min(stack.array_9ch)), 0.0)
        self.assertLessEqual(float(np.max(stack.array_9ch)), 1.0)

        # PyTorch tensor verification
        self.assertIsInstance(stack.tensor_9ch, torch.Tensor)
        self.assertEqual(stack.tensor_9ch.shape, (1, 9, 500, 400))
        self.assertEqual(stack.tensor_9ch.dtype, torch.float32)

        # Standardized indices verification
        self.assertIn("NDWI", stack.indices)
        self.assertIn("MNDWI", stack.indices)
        self.assertIn("NDVI", stack.indices)
        self.assertIn("NDBI", stack.indices)

    def test_04_full_pipeline_end_to_end_execution(self):
        """Executes full master pipeline and verifies GIS rasters, GeoJSONs, PostGIS sync, and Dashboard."""
        res: RealScenePipelineResult = self.pipeline.process()

        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.scene_id, "upper_beas_july2023")
        self.assertGreaterEqual(res.valid_data_pct, 90.0)
        self.assertGreaterEqual(res.flood_susceptibility_pct, 0.0)
        self.assertGreaterEqual(res.landslide_susceptibility_pct, 0.0)
        self.assertGreaterEqual(res.natural_dam_candidates_count, 1)

        # Check raster files exist
        for r_name, r_path in res.raster_files.items():
            self.assertTrue(Path(r_path).exists(), f"Missing raster file: {r_name}")

        # Check vector files exist
        for v_name, v_path in res.vector_files.items():
            self.assertTrue(Path(v_path).exists(), f"Missing vector file: {v_name}")

        # Check PostGIS sync outputs
        self.assertIsNotNone(res.postgis_sync.sql_script_path)
        sql_file = Path(res.postgis_sync.sql_script_path)
        self.assertTrue(sql_file.exists())
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_text = f.read()
            self.assertIn("BEGIN;", sql_text)
            self.assertIn("natural_dam_candidates", sql_text)
            self.assertIn("COMMIT;", sql_text)

        # Check Leaflet Dashboard HTML exists
        dash_path = Path(res.dashboard_url)
        self.assertTrue(dash_path.exists())
        with open(dash_path, "r", encoding="utf-8") as f:
            html_text = f.read()
            self.assertIn("FLOODY SHIELD", html_text)
            self.assertIn("leaflet", html_text.lower())

    def test_05_rest_api_endpoint(self):
        """Tests POST /api/v1/satellite/process-real-scene endpoint with FastAPI TestClient."""
        resp = self.client.post("/api/v1/satellite/process-real-scene", json={})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["status"], "COMPLETED")
        self.assertEqual(data["scene_id"], "upper_beas_july2023")
        self.assertIn("data_quality_grade", data)
        self.assertIn("postgis_sync", data)
        self.assertEqual(data["postgis_sync"]["status"], "SUCCESS")
        self.assertGreaterEqual(data["natural_dam_candidates_count"], 1)
        self.assertTrue(Path(data["dashboard_url"]).exists())


if __name__ == "__main__":
    unittest.main()
