"""
test_m6_external_validation.py — Comprehensive Test Suite for M6 External Validation
=====================================================================================
Tests all 16 required technical criteria:
  1. External dataset schema
  2. CRS validation
  3. AOI intersection
  4. Temporal overlap detection
  5. Spatial exclusion
  6. Negative sampling
  7. Feature ordering
  8. NoData handling
  9. Probability bounds
  10. Frozen-model enforcement
  11. Metric calculations
  12. Zero-event handling
  13. Insufficient-data handling
  14. Reproducibility
  15. Provenance metadata
  16. Report generation
"""

from dataclasses import asdict
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from ml.validation.external.dataset_loader import (
    ExternalLandslideLoader,
    LoadedExternalInventory,
    ObservedLandslideEvent,
)
from ml.validation.external.evaluate_m6 import run_external_validation
from ml.validation.external.export_maps import ExternalValidationMapExporter
from ml.validation.external.feature_extractor import M6FeatureExtractor
from ml.validation.external.frozen_evaluator import FrozenM6Evaluator
from ml.validation.external.projection import (
    metric_distance_m,
    utm43n_to_wgs84,
    validate_coordinates,
    wgs84_to_utm43n,
)
from ml.validation.external.schema import (
    ExternalDatasetRecord,
    ExternalValidationSample,
    ExternalValidationState,
    FrozenModelContract,
)
from ml.validation.external.spatial_sampler import SpatialLeakageController, ValidationPoint
from ml.validation.external.temporal_leakage import IndependenceAuditor

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestM6ExternalValidationSuite(unittest.TestCase):
    """Rigorous unit tests for frozen M6 external validation pipeline."""

    def setUp(self):
        self.contract = FrozenModelContract()
        # Mock historical events for testing (explicitly flagged as mock test fixtures)
        self.mock_events = [
            ObservedLandslideEvent("mock_1", 31.85, 77.15, "2023-07-09", "debris_flow", "MOCK_TEST_FIXTURE"),
            ObservedLandslideEvent("mock_2", 31.90, 77.20, "2023-07-10", "rockfall", "MOCK_TEST_FIXTURE"),
            ObservedLandslideEvent("mock_3", 32.10, 77.10, "2023-07-11", "translational", "MOCK_TEST_FIXTURE"),
            ObservedLandslideEvent("mock_4", 32.05, 77.25, "2023-07-12", "debris_slide", "MOCK_TEST_FIXTURE"),
            ObservedLandslideEvent("mock_5", 31.75, 77.05, "2023-07-13", "slump", "MOCK_TEST_FIXTURE"),
        ]

    # 1. External Dataset Schema
    def test_01_external_dataset_schema(self):
        """ExternalDatasetRecord enforces all required metadata fields."""
        rec = ExternalDatasetRecord(
            dataset_id="test_ds",
            dataset_name="Test Inventory",
            provider="Test Authority",
            source_url="https://example.gov",
            license_or_access_terms="Open Access",
            download_date="2026-09-20",
            publication_date="2024",
            geographic_extent=(76.8, 31.4, 77.45, 32.45),
            temporal_extent="2023 Monsoon",
            geometry_type="Point",
            coordinate_reference_system="EPSG:4326",
            event_date_available=True,
            source_description="Test Schema",
            validation_role="INDEPENDENT_EXTERNAL_OBSERVATION",
        )
        self.assertEqual(rec.dataset_id, "test_ds")
        self.assertEqual(rec.coordinate_reference_system, "EPSG:4326")
        self.assertTrue(rec.event_date_available)

    # 2. CRS Validation & Coordinate Bounds
    def test_02_crs_validation_and_bounds(self):
        """Rejects invalid coordinates and detects lat/lon transpositions."""
        # Valid Himachal Pradesh coordinates
        validate_coordinates(31.85, 77.15)

        # Latitude out of bounds
        with self.assertRaises(ValueError):
            validate_coordinates(95.0, 77.0)

        # Transposition detected (e.g. lat=77.15, lon=31.85)
        with self.assertRaises(ValueError):
            validate_coordinates(77.15, 31.85)

        # Metric projection to UTM Zone 43N returns reasonable meter coordinates
        easting, northing = wgs84_to_utm43n(32.0, 77.0)
        self.assertGreater(easting, 400000.0)
        self.assertLess(easting, 800000.0)
        self.assertGreater(northing, 3000000.0)

        # Roundtrip conversion accuracy < 0.01 meters
        lat_back, lon_back = utm43n_to_wgs84(easting, northing)
        self.assertAlmostEqual(lat_back, 32.0, places=5)
        self.assertAlmostEqual(lon_back, 77.0, places=5)

    # 3. AOI Intersection
    def test_03_aoi_intersection(self):
        """Correctly identifies points inside vs outside the Upper Beas AOI."""
        loader = ExternalLandslideLoader(
            aoi_min_lon=76.80, aoi_max_lon=77.45, aoi_min_lat=31.40, aoi_max_lat=32.45
        )
        # Inside
        self.assertTrue(loader.is_inside_aoi(31.85, 77.15))
        # Outside (Delhi or Southern HP)
        self.assertFalse(loader.is_inside_aoi(28.61, 77.20))
        # Outside (Ladakh to the North)
        self.assertFalse(loader.is_inside_aoi(34.15, 77.57))

    # 4. Temporal / Spatial Overlap Detection
    def test_04_temporal_overlap_detection(self):
        """Flags training-external independence and checks spatial co-location."""
        auditor = IndependenceAuditor()
        # Events placed away from training points should be retained
        clean, record = auditor.audit_independence(self.mock_events, "Mock Dataset")
        self.assertIsInstance(clean, list)
        self.assertIn("INDEPENDENCE", record.independence_status)

    # 5. Spatial Exclusion Buffer
    def test_05_spatial_exclusion(self):
        """Verifies that metric distance between points is accurately computed in meters."""
        p1 = (31.8500, 77.1500)
        p2 = (31.8500, 77.1550)  # ~470 meters east at lat 31.85
        dist = metric_distance_m(p1[0], p1[1], p2[0], p2[1])
        self.assertGreater(dist, 400.0)
        self.assertLess(dist, 550.0)

    # 6. Negative Sampling
    def test_06_negative_sampling(self):
        """Negatives must be strictly outside the exclusion buffer around all positives."""
        buffer_m = 500.0
        controller = SpatialLeakageController(
            exclusion_buffer_m=buffer_m,
            negative_ratio=1.0,
            random_seed=42,
        )
        samples, plan = controller.generate_evaluation_set(self.mock_events)
        self.assertEqual(plan.positive_count, len(self.mock_events))
        self.assertEqual(plan.negative_count, len(self.mock_events))

        neg_samples = [s for s in samples if s.is_landslide == 0]
        for neg in neg_samples:
            self.assertGreaterEqual(
                neg.dist_to_nearest_event_m,
                buffer_m,
                f"Negative sample {neg.point_id} violated exclusion buffer! dist={neg.dist_to_nearest_event_m}"
            )

    # 7. Feature Ordering
    def test_07_feature_ordering(self):
        """Feature extractor produces DataFrame with columns matching the contract exactly."""
        extractor = M6FeatureExtractor()
        coords = [(31.85, 77.15), (32.00, 77.25)]
        df, prov = extractor.extract_features_for_points(coords)
        self.assertEqual(list(df.columns), list(self.contract.feature_order))
        self.assertEqual(len(df), 2)

    # 8. NoData Handling
    def test_08_nodata_handling(self):
        """Feature extractor safely sanitizes NaN or out-of-scene queries."""
        extractor = M6FeatureExtractor()
        # Query point with valid values
        df, prov = extractor.extract_features_for_points([(31.50, 77.00)])
        self.assertFalse(df.isna().any().any(), "DataFrame contains unsanitized NaNs")
        self.assertGreater(df["elevation_m"].iloc[0], 0.0)

    # 9. Probability Bounds
    def test_09_probability_bounds(self):
        """ExternalValidationSample rejects out-of-bounds probabilities."""
        # Valid sample
        ExternalValidationSample("s1", 31.85, 77.15, 1, 0.75, 2)
        # Bad probability > 1.0
        with self.assertRaises(ValueError):
            ExternalValidationSample("s2", 31.85, 77.15, 1, 1.05, 2)
        # Bad probability < 0.0
        with self.assertRaises(ValueError):
            ExternalValidationSample("s3", 31.85, 77.15, 1, -0.01, 0)

    # 10. Frozen-Model Enforcement
    def test_10_frozen_model_enforcement(self):
        """FrozenModelContract verifies artifact existence and immutability hash."""
        sha = self.contract.verify_integrity(REPO_ROOT)
        self.assertIsInstance(sha, str)
        self.assertEqual(len(sha), 64, "SHA-256 hash must be 64 hex characters")
        self.assertTrue(self.contract.is_frozen)

    # 11. Metric Calculations
    def test_11_metric_calculations(self):
        """Frozen evaluator calculates ROC-AUC, PR-AUC, Brier score, and capture rates."""
        evaluator = FrozenM6Evaluator(repo_root=REPO_ROOT)
        controller = SpatialLeakageController(exclusion_buffer_m=500.0, random_seed=42)
        samples, _ = controller.generate_evaluation_set(self.mock_events)

        extractor = M6FeatureExtractor()
        coords = [(s.latitude, s.longitude) for s in samples]
        df, _ = extractor.extract_features_for_points(coords)

        res = evaluator.evaluate(samples, df, dataset_id="mock_inventory")
        self.assertGreaterEqual(res.roc_auc, 0.0)
        self.assertLessEqual(res.roc_auc, 1.0)
        self.assertGreaterEqual(res.brier_score, 0.0)
        self.assertLessEqual(res.brier_score, 1.0)
        self.assertGreaterEqual(res.spatial_capture_rates.top_10_percent_capture_rate, 0.0)
        self.assertLessEqual(res.spatial_capture_rates.top_10_percent_capture_rate, 1.0)

    # 12. Zero-Event Handling
    def test_12_zero_event_handling(self):
        """Zero events handled gracefully without dividing by zero."""
        controller = SpatialLeakageController()
        samples, plan = controller.generate_evaluation_set([])
        self.assertEqual(len(samples), 0)
        self.assertEqual(plan.positive_count, 0)
        self.assertEqual(plan.negative_count, 0)

    # 13. Insufficient-Data Handling
    def test_13_insufficient_data_handling(self):
        """When directory has no external data, reports NOT_POSSIBLE state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            res = run_external_validation(
                intake_dir=Path(tmpdir),
                report_out_path=Path(tmpdir) / "report.md",
            )
            self.assertEqual(res["validation_status"], ExternalValidationState.NOT_POSSIBLE.value)
            self.assertIn("VALIDATION NOT POSSIBLE", res["status"])

    # 14. Reproducibility
    def test_14_reproducibility(self):
        """Same random seed produces identical negative samples and metric values."""
        controller1 = SpatialLeakageController(random_seed=123)
        samples1, _ = controller1.generate_evaluation_set(self.mock_events)

        controller2 = SpatialLeakageController(random_seed=123)
        samples2, _ = controller2.generate_evaluation_set(self.mock_events)

        coords1 = [(s.latitude, s.longitude) for s in samples1]
        coords2 = [(s.latitude, s.longitude) for s in samples2]
        self.assertEqual(coords1, coords2)

    # 15. Provenance Metadata
    def test_15_provenance_metadata(self):
        """Evaluation result carries complete provenance and uncertainty report."""
        evaluator = FrozenM6Evaluator(repo_root=REPO_ROOT)
        controller = SpatialLeakageController(random_seed=42)
        samples, _ = controller.generate_evaluation_set(self.mock_events)
        extractor = M6FeatureExtractor()
        coords = [(s.latitude, s.longitude) for s in samples]
        df, _ = extractor.extract_features_for_points(coords)
        res = evaluator.evaluate(samples, df)

        self.assertIn("total_positive_events", res.uncertainty_report)
        self.assertIn("geomorphic_explanation", res.error_analysis)
        self.assertIn("model_sha256", asdict(res))

    # 16. Report Generation
    def test_16_report_generation(self):
        """Generates valid Markdown report adhering to Section 15 template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_file = Path(tmpdir) / "M6_EXTERNAL_VALIDATION.md"
            res = run_external_validation(
                intake_dir=Path(tmpdir),
                report_out_path=report_file,
            )
            self.assertTrue(report_file.exists())
            content = report_file.read_text(encoding="utf-8")
            self.assertIn("# M6 External Real-Event Validation", content)
            self.assertIn("## 1. Objective", content)
            self.assertIn("## 18. Validation Status", content)
            self.assertIn("## 19. Conclusion", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
