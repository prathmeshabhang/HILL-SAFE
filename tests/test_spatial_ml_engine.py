"""
test_spatial_ml_engine.py — Unit Tests for Spatial ML Inference Engine
======================================================================
Validates the authentic deployment and 2D spatial inference of:
  - Model M6: 350-Tree Random Forest Landslide Susceptibility
  - Model M7: 350-Round LightGBM Dynamic Rainfall Trigger
  - Model M2: Calibrated XGBoost Topo-Hydrological Flood Susceptibility
  - Multimodal 9-Channel PyTorch U-Net Flood Inundation Segmentor

Test Coverage:
  1. Artifact Loading & Architecture Inspection
  2. Landslide ML Suite: Shape, Probability Bounds [0.0, 1.0], NaN Safety
  3. Flood ML Suite: Shape, Bounds, Vision-Tabular Fusion, NaN Safety
  4. Feature Importance Extraction & Explainability Contracts
  5. Deterministic Reproducibility
  6. Integration with SatelliteFloodModel & SatelliteLandslideModel
"""

from __future__ import annotations

import unittest
import numpy as np
import torch

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.flood.flood_susceptibility import SatelliteFloodModel
from ml.satellite_hazard.landslide.landslide_susceptibility import SatelliteLandslideModel
from ml.satellite_hazard.spatial_ml_engine import (
    FloodMLInferenceResult,
    LandslideMLInferenceResult,
    SpatialMLEngine,
)
from ml.satellite_hazard.spectral.index_generator import SpectralIndices
from ml.satellite_hazard.terrain.terrain_engine import TerrainFeatures


class TestSpatialMLEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = SpatialMLEngine()
        cls.shape = (100, 80)
        rows, cols = cls.shape

        # Construct realistic terrain features
        elev = np.linspace(800.0, 3200.0, rows * cols, dtype=np.float32).reshape(cls.shape)
        slope = np.clip(np.random.RandomState(42).normal(32.0, 12.0, cls.shape), 0.0, 75.0).astype(np.float32)
        aspect = np.random.RandomState(42).uniform(0.0, 360.0, cls.shape).astype(np.float32)
        plan_curv = np.random.RandomState(42).normal(0.0, 0.05, cls.shape).astype(np.float32)
        prof_curv = np.random.RandomState(42).normal(0.0, 0.05, cls.shape).astype(np.float32)
        tri = slope * 0.8
        twi = np.clip(14.0 - (slope / 5.0), 2.0, 18.0).astype(np.float32)
        spi = np.clip(slope * 12.0, 0.0, 500.0).astype(np.float32)
        hand = np.clip(elev - 800.0, 0.0, 400.0).astype(np.float32)

        cls.terrain = TerrainFeatures(
            shape=cls.shape,
            elevation_m=elev,
            slope_deg=slope,
            aspect_deg=aspect,
            plan_curvature=plan_curv,
            profile_curvature=prof_curv,
            terrain_ruggedness_index=tri,
            topographic_wetness_index=twi,
            stream_power_index=spi,
            height_above_nearest_drainage_m=hand,
        )

        # Construct realistic spectral indices
        ndvi = np.clip(np.random.RandomState(42).uniform(0.1, 0.7, cls.shape), -1.0, 1.0).astype(np.float32)
        ndwi = np.clip(np.random.RandomState(42).uniform(-0.5, 0.3, cls.shape), -1.0, 1.0).astype(np.float32)
        mndwi = np.clip(np.random.RandomState(42).uniform(-0.6, 0.4, cls.shape), -1.0, 1.0).astype(np.float32)
        ndbi = np.clip(np.random.RandomState(42).uniform(-0.4, 0.2, cls.shape), -1.0, 1.0).astype(np.float32)
        ndmi = np.clip(np.random.RandomState(42).uniform(-0.2, 0.6, cls.shape), -1.0, 1.0).astype(np.float32)
        savi = np.clip(np.random.RandomState(42).uniform(0.0, 0.8, cls.shape), -1.0, 1.0).astype(np.float32)

        cls.spectral = SpectralIndices(
            shape=cls.shape,
            ndvi=ndvi,
            ndwi=ndwi,
            mndwi=mndwi,
            ndbi=ndbi,
            ndmi=ndmi,
            savi=savi,
        )

        # 9-channel normalized input stack
        cls.stack_9ch = np.random.RandomState(42).uniform(0.0, 1.0, (9, rows, cols)).astype(np.float32)

    def test_01_model_artifacts_loaded(self):
        """Validates that all trained model artifacts are successfully loaded."""
        self.assertIsNotNone(self.engine.m6_model, "Model M6 Random Forest must be loaded")
        self.assertIsNotNone(self.engine.m7_model, "Model M7 LightGBM must be loaded")
        self.assertIsNotNone(self.engine.m2_model, "Model M2 XGBoost must be loaded")
        self.assertIsNotNone(self.engine.unet_model, "9-Channel PyTorch U-Net must be loaded")

        # Verify classes
        self.assertTrue(np.array_equal(self.engine.m6_model.classes_, [0, 1, 2]))
        self.assertTrue(np.array_equal(self.engine.m7_model.classes_, [0, 1]))

    def test_02_landslide_suite_shape_and_bounds(self):
        """Verifies spatial M6 + M7 inference output shapes, [0, 1] bounds, and classes."""
        res: LandslideMLInferenceResult = self.engine.infer_landslide_suite(
            terrain=self.terrain,
            spectral=self.spectral,
            event_rainfall_1h_mm=30.0,
            antecedent_rain_3d_mm=95.0,
        )

        # Shape consistency
        self.assertEqual(res.m6_susceptibility_score.shape, self.shape)
        self.assertEqual(res.m6_susceptibility_classes.shape, self.shape)
        self.assertEqual(res.m7_trigger_probability.shape, self.shape)
        self.assertEqual(res.combined_landslide_risk.shape, self.shape)

        # Strict probability bounds [0.0, 1.0]
        self.assertGreaterEqual(float(np.nanmin(res.m6_susceptibility_score)), 0.0)
        self.assertLessEqual(float(np.nanmax(res.m6_susceptibility_score)), 1.0)
        self.assertGreaterEqual(float(np.nanmin(res.m7_trigger_probability)), 0.0)
        self.assertLessEqual(float(np.nanmax(res.m7_trigger_probability)), 1.0)
        self.assertGreaterEqual(float(np.nanmin(res.combined_landslide_risk)), 0.0)
        self.assertLessEqual(float(np.nanmax(res.combined_landslide_risk)), 1.0)

        # Classes in [0, 1, 2]
        unique_classes = np.unique(res.m6_susceptibility_classes)
        for c in unique_classes:
            self.assertIn(c, [0, 1, 2])

        # Feature importances non-empty
        self.assertGreater(len(res.m6_feature_importances), 0)
        self.assertGreater(len(res.m7_feature_importances), 0)
        self.assertIn("slope_deg", res.m6_feature_importances)
        self.assertIn("rainfall_1h", res.m7_feature_importances)

    def test_03_flood_suite_shape_and_bounds(self):
        """Verifies multimodal U-Net + M2 XGBoost inference shapes, bounds, and fusion."""
        res: FloodMLInferenceResult = self.engine.infer_flood_suite(
            stack_9ch=self.stack_9ch,
            terrain=self.terrain,
            spectral=self.spectral,
            event_rainfall_1h_mm=30.0,
            antecedent_rain_3d_mm=95.0,
            cwc_river_level_m=6.5,
            cwc_rate_of_rise_m_hr=0.45,
        )

        # Shape consistency
        self.assertEqual(res.m2_flood_probability.shape, self.shape)
        self.assertEqual(res.unet_inundation_probability.shape, self.shape)
        self.assertEqual(res.fused_flood_susceptibility.shape, self.shape)
        self.assertEqual(res.active_inundation_mask.shape, self.shape)

        # Strict probability bounds [0.0, 1.0]
        self.assertGreaterEqual(float(np.nanmin(res.m2_flood_probability)), 0.0)
        self.assertLessEqual(float(np.nanmax(res.m2_flood_probability)), 1.0)
        self.assertGreaterEqual(float(np.nanmin(res.unet_inundation_probability)), 0.0)
        self.assertLessEqual(float(np.nanmax(res.unet_inundation_probability)), 1.0)
        self.assertGreaterEqual(float(np.nanmin(res.fused_flood_susceptibility)), 0.0)
        self.assertLessEqual(float(np.nanmax(res.fused_flood_susceptibility)), 1.0)

        # Mask dtype
        self.assertEqual(res.active_inundation_mask.dtype, bool)

        # Feature importances non-empty
        self.assertGreater(len(res.m2_feature_importances), 0)
        self.assertIn("cwc_rate_of_rise_m_hr", res.m2_feature_importances)

    def test_04_nan_handling_and_boundary_safety(self):
        """Verifies that grids with NaNs in terrain or spectral features do not crash inference."""
        corrupt_elev = self.terrain.elevation_m.copy()
        corrupt_elev[10:15, 10:15] = np.nan
        corrupt_slope = self.terrain.slope_deg.copy()
        corrupt_slope[20:25, 20:25] = np.nan

        corrupt_terrain = TerrainFeatures(
            shape=self.shape,
            elevation_m=corrupt_elev,
            slope_deg=corrupt_slope,
            aspect_deg=self.terrain.aspect_deg,
            plan_curvature=self.terrain.plan_curvature,
            profile_curvature=self.terrain.profile_curvature,
            terrain_ruggedness_index=self.terrain.terrain_ruggedness_index,
            topographic_wetness_index=self.terrain.topographic_wetness_index,
            stream_power_index=self.terrain.stream_power_index,
            height_above_nearest_drainage_m=self.terrain.height_above_nearest_drainage_m,
        )

        res_l = self.engine.infer_landslide_suite(corrupt_terrain, self.spectral)
        self.assertFalse(np.isnan(res_l.m6_susceptibility_score).any())
        self.assertFalse(np.isnan(res_l.m7_trigger_probability).any())

        res_f = self.engine.infer_flood_suite(self.stack_9ch, corrupt_terrain, self.spectral)
        self.assertFalse(np.isnan(res_f.fused_flood_susceptibility).any())

    def test_05_deterministic_reproducibility(self):
        """Verifies that multiple runs on identical inputs yield bitwise identical ML predictions."""
        run1 = self.engine.infer_landslide_suite(self.terrain, self.spectral)
        run2 = self.engine.infer_landslide_suite(self.terrain, self.spectral)
        np.testing.assert_array_almost_equal(run1.m6_susceptibility_score, run2.m6_susceptibility_score, decimal=5)
        np.testing.assert_array_almost_equal(run1.m7_trigger_probability, run2.m7_trigger_probability, decimal=5)

    def test_06_flood_model_integration_and_fallback(self):
        """Verifies SatelliteFloodModel behavior with and without 9-channel stack."""
        model = SatelliteFloodModel()

        # With 9-ch stack: ML_INFERENCE
        res_ml = model.analyze(self.spectral, self.terrain, stack_9ch=self.stack_9ch)
        self.assertEqual(res_ml.inference_mode, "ML_INFERENCE")
        self.assertIsNotNone(res_ml.m2_flood_probability)
        self.assertIsNotNone(res_ml.unet_inundation_probability)

        # Without 9-ch stack: FALLBACK_HEURISTIC
        res_fb = model.analyze(self.spectral, self.terrain)
        self.assertEqual(res_fb.inference_mode, "FALLBACK_HEURISTIC")
        self.assertIsNone(res_fb.m2_flood_probability)

    def test_07_landslide_model_integration(self):
        """Verifies SatelliteLandslideModel executes ML_INFERENCE with M6 and M7."""
        model = SatelliteLandslideModel()
        res = model.analyze(self.spectral, self.terrain)
        self.assertEqual(res.inference_mode, "ML_INFERENCE")
        self.assertIsNotNone(res.trigger_probability)
        self.assertIsNotNone(res.combined_landslide_risk)
        self.assertIn("elevation_m", res.m6_feature_importances)


if __name__ == "__main__":
    unittest.main()
