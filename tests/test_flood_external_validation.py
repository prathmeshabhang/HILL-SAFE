"""
test_flood_external_validation.py — Automated Verification for Flood External Validation
========================================================================================
Validates:
  1. Data Integrity & SHA-256 Hash Matching for Upper Beas Flood Inventory
  2. Bounding Box & Upper Beas AOI Compliance (100% inside basin)
  3. Spatial Leakage Audit Integrity (24 points, distance calculations)
  4. Model M2 Frozen External Evaluation Execution & Metrics
  5. Model M4 Multimodal U-Net Point Concordance & Status Declaration
  6. Output GeoJSON and JSON Artefact Generation
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from ml.satellite_hazard.config import StudyAreaConfig
from ml.validation.external.evaluate_m2_flood import run_m2_external_validation
from ml.validation.external.evaluate_m4_unet import run_m4_unet_external_validation

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_FLOOD_CSV = REPO_ROOT / "data" / "external" / "flood" / "raw" / "upper_beas_flood_events_2023_raw.csv"
PROVENANCE_JSON = REPO_ROOT / "data" / "external" / "flood" / "provenance" / "provenance_record.json"
LEAKAGE_CSV = REPO_ROOT / "reports" / "M2_M4_EXTERNAL_LEAKAGE_AUDIT.csv"
PROCESSED_GEOJSON = REPO_ROOT / "data" / "external" / "flood" / "processed" / "upper_beas_flood_external_events.geojson"
M2_METRICS_JSON = REPO_ROOT / "docs" / "m2_external_validation_metrics.json"
M4_METRICS_JSON = REPO_ROOT / "docs" / "m4_unet_external_validation_metrics.json"


class TestFloodExternalValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study_area = StudyAreaConfig()

    def test_raw_dataset_hash_and_structure(self):
        """Ensures the authentic raw flood dataset exists and matches cryptographic fingerprint."""
        self.assertTrue(RAW_FLOOD_CSV.exists(), "Raw flood CSV file must exist")
        with open(RAW_FLOOD_CSV, "rb") as f:
            computed_hash = hashlib.sha256(f.read()).hexdigest()

        with open(PROVENANCE_JSON, "r", encoding="utf-8") as f:
            provenance = json.load(f)

        self.assertEqual(computed_hash, provenance["sha256"], "Cryptographic SHA-256 fingerprint must match")

        df = pd.read_csv(RAW_FLOOD_CSV)
        self.assertEqual(len(df), 24, "External dataset must contain exactly 24 documented points")
        self.assertEqual(df["inundation_observed"].sum(), 12, "Must contain exactly 12 flooded positive sites")
        self.assertEqual((df["inundation_observed"] == 0).sum(), 12, "Must contain exactly 12 unflooded negative sites")

    def test_geographic_bounding_box_compliance(self):
        """Verifies 100% of evaluation coordinates fall within Upper Beas catchment AOI."""
        df = pd.read_csv(RAW_FLOOD_CSV)
        for _, r in df.iterrows():
            lat = float(r["latitude"])
            lon = float(r["longitude"])
            self.assertTrue(
                self.study_area.min_lat <= lat <= self.study_area.max_lat,
                f"Latitude {lat} for {r['event_id']} outside AOI [{self.study_area.min_lat}, {self.study_area.max_lat}]"
            )
            self.assertTrue(
                self.study_area.min_lon <= lon <= self.study_area.max_lon,
                f"Longitude {lon} for {r['event_id']} outside AOI [{self.study_area.min_lon}, {self.study_area.max_lon}]"
            )

    def test_spatial_leakage_audit(self):
        """Verifies the distance-to-training-data audit table."""
        self.assertTrue(LEAKAGE_CSV.exists(), "Spatial leakage CSV must exist")
        df_leak = pd.read_csv(LEAKAGE_CSV)
        self.assertEqual(len(df_leak), 24, "Leakage audit must evaluate all 24 points")
        self.assertTrue(np.all(df_leak["nearest_training_dist_m"] >= 0.0), "Distances must be non-negative")
        self.assertIn("SPATIAL_LEAKAGE_BUFFER_EXCEEDED (<500m)", df_leak["leakage_status"].values)
        self.assertIn("INDEPENDENT_POINT (>500m)", df_leak["leakage_status"].values)

    def test_m2_frozen_evaluation_execution(self):
        """Executes M2 evaluation and verifies metrics structure and values."""
        rep = run_m2_external_validation()
        self.assertEqual(rep["model_name"], "M2_Calibrated_XGBoost_Flood_Occurrence")
        self.assertEqual(rep["sample_size_total"], 24)

        metrics = rep["all_events_metrics"]
        self.assertEqual(metrics["recall"], 1.0, "Model M2 must capture 100% of authentic July 2023 flood sites")
        self.assertGreaterEqual(metrics["roc_auc"], 0.65, "ROC-AUC should reflect positive discriminative power")
        self.assertTrue(M2_METRICS_JSON.exists(), "M2 metrics JSON must be exported")

    def test_m4_unet_evaluation_execution(self):
        """Executes M4 evaluation and verifies point concordance and status declaration."""
        rep = run_m4_unet_external_validation()
        self.assertEqual(rep["model_name"], "Multimodal_9Channel_PyTorch_Flood_UNet")
        self.assertEqual(rep["validation_tier"], "PARTIALLY_VALIDATED")

        concordance = rep["point_concordance_evaluation"]
        self.assertGreater(
            concordance["mean_probability_flooded_sites"],
            concordance["mean_probability_unflooded_sites"],
            "Mean predicted probability must be higher on flooded than unflooded sites"
        )
        self.assertTrue(M4_METRICS_JSON.exists(), "M4 metrics JSON must be exported")

    def test_gis_artefacts_generated(self):
        """Verifies vector GeoJSON outputs are correctly created and non-empty."""
        m2_geojson = REPO_ROOT / "data" / "satellite_output" / "M2_external_validation_points.geojson"
        m4_geojson = REPO_ROOT / "data" / "satellite_output" / "M4_external_validation_points.geojson"
        self.assertTrue(m2_geojson.exists(), "M2 GeoJSON must exist")
        self.assertTrue(m4_geojson.exists(), "M4 GeoJSON must exist")

        with open(m2_geojson, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(len(data["features"]), 24)

        with open(m4_geojson, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(len(data["features"]), 24)


if __name__ == "__main__":
    unittest.main()
