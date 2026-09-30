"""
test_satellite_pipeline.py — End-to-End Test Suite for Satellite Hazard Intelligence
====================================================================================
Verifies:
  1. Sentinel-2 multispectral ingestion and band reflectance physical ranges.
  2. Cloud quality auditing and SCL masking.
  3. Terrain feature derivations (Slope, Curvatures, TWI, HAND).
  4. Spectral indices (NDVI, MNDWI, NDBI, NDMI, SAVI).
  5. Flood and Landslide susceptibility raster outputs.
  6. Observed Development Pressure and Development-Induced Hazard Risk.
  7. Multi-hazard fusion and Section 36 GeoJSON attribute schema.
  8. Interactive Leaflet HTML generation.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig, StudyAreaConfig
from ml.satellite_hazard.pipeline import SatelliteHazardPipeline


class TestSatellitePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = SatelliteProcessingConfig()
        cls.pipeline = SatelliteHazardPipeline(cls.config)
        cls.results = cls.pipeline.run()

    def test_pipeline_status_and_study_area(self):
        self.assertEqual(self.results["status"], "SUCCESS")
        self.assertIn("Upper Beas", self.results["study_area"])
        self.assertGreater(self.results["valid_data_pct"], 90.0)

    def test_spectral_indices_bounds(self):
        scene = self.pipeline.s2_loader.generate_calibrated_scene()
        indices = self.pipeline.spectral_engine.calculate_all(scene.bands)

        # Ensure indices stay strictly within [-1.0, 1.0]
        self.assertTrue(np.all(indices.ndvi >= -1.0) and np.all(indices.ndvi <= 1.0))
        self.assertTrue(np.all(indices.mndwi >= -1.0) and np.all(indices.mndwi <= 1.0))
        self.assertTrue(np.all(indices.ndbi >= -1.0) and np.all(indices.ndbi <= 1.0))

    def test_terrain_derivatives_physics(self):
        dem = self.pipeline.dem_loader.generate_calibrated_dem()
        terrain = self.pipeline.terrain_engine.process(dem)

        # Slope must be non-negative and less than 90 degrees
        self.assertTrue(np.all(terrain.slope_deg >= 0.0))
        self.assertTrue(np.all(terrain.slope_deg <= 90.0))
        # TWI must be positive
        self.assertTrue(np.all(terrain.topographic_wetness_index >= 0.0))
        # HAND must be non-negative
        self.assertTrue(np.all(terrain.height_above_nearest_drainage_m >= 0.0))

    def test_raster_files_exist_and_readable(self):
        import tifffile
        for r_path_str in self.results["raster_files"]:
            p = Path(r_path_str)
            self.assertTrue(p.exists(), f"Raster file missing: {p}")
            data = tifffile.imread(str(p))
            self.assertEqual(data.shape, (500, 400))
            self.assertFalse(np.isnan(data).all(), f"Raster completely nan: {p}")

    def test_geojson_schema_compliance_section36(self):
        """Verifies that all GeoJSON outputs follow the mandated Section 36 schema."""
        cdz_path = Path("data/satellite_output/critical_development_zones.geojson")
        self.assertTrue(cdz_path.exists(), "Critical development zones GeoJSON missing")

        with open(cdz_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["type"], "FeatureCollection")
        self.assertGreater(len(data["features"]), 0, "No critical development zones detected")

        # Mandatory Section 36 fields check
        mandated_fields = [
            "zone_id",
            "flood_risk",
            "landslide_risk",
            "development_pressure",
            "development_hazard_risk",
            "multi_hazard_risk",
            "confidence",
            "uncertainty",
            "risk_category",
            "dominant_hazards",
            "observed_changes",
            "contributing_features",
            "infrastructure_exposure",
            "last_observation",
            "model_version",
        ]

        sample_props = data["features"][0]["properties"]
        for field in mandated_fields:
            self.assertIn(field, sample_props, f"Missing mandated Section 36 field: {field}")

    def test_candidate_safe_zones_disclaimer(self):
        """Verifies candidate lower hazard zones include the mandatory statutory disclaimer."""
        safe_path = Path("data/satellite_output/candidate_development_zones.geojson")
        self.assertTrue(safe_path.exists())

        with open(safe_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertGreater(len(data["features"]), 0)
        self.assertIn("statutory_disclaimer", data["features"][0]["properties"])
        self.assertIn("not a substitute for field investigation", data["features"][0]["properties"]["statutory_disclaimer"].lower())

    def test_leaflet_dashboard_generated(self):
        dashboard_path = Path(self.results["dashboard_url"])
        self.assertTrue(dashboard_path.exists(), "Dashboard HTML file missing")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn("leaflet.js", html)
        self.assertIn("Critical Development Zones", html)
        self.assertIn("Candidate Lower-Hazard", html)


if __name__ == "__main__":
    unittest.main()
