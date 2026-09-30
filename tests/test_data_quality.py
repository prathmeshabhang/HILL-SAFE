"""
test_data_quality.py — Unit Tests for Data Quality & Provenance Layer
====================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_sensor_range, check_spatial_bounds
from ml.data_quality.schema import FlagSeverity, QualityStatus
from ml.data_quality.validator import DataQualityValidator


class TestDataQualityLayer(unittest.TestCase):

    def test_spatial_bounds_check(self):
        # Point inside Upper Beas AOI (Manali: 32.2396, 77.1887, elev: 2050m)
        ok, msg = check_spatial_bounds(32.2396, 77.1887, 2050.0)
        self.assertTrue(ok)
        self.assertIsNone(msg)

        # Point outside Upper Beas AOI (Delhi: 28.6139, 77.2090)
        ok_bad, msg_bad = check_spatial_bounds(28.6139, 77.2090)
        self.assertFalse(ok_bad)
        self.assertIn("Latitude", msg_bad)

    def test_sensor_physical_range_checks(self):
        # Negative rainfall
        ok_neg, msg_neg = check_sensor_range("rainfall_rate_mmh", -5.0)
        self.assertFalse(ok_neg)

        # Valid rainfall
        ok_valid, msg_valid = check_sensor_range("rainfall_rate_mmh", 45.0)
        self.assertTrue(ok_valid)

        # Extreme impossible river water level (50m in mountain gorge)
        ok_high, msg_high = check_sensor_range("water_level_m", 50.0)
        self.assertFalse(ok_high)

    def test_stuck_sensor_detection(self):
        validator = DataQualityValidator(stuck_sensor_window=3)
        history = [
            {"water_level_m": 4.5},
            {"water_level_m": 4.5},
            {"water_level_m": 4.5},
        ]
        rep = validator.validate_record(
            sample_id="test_stuck",
            features={"water_level_m": 4.5},
            recent_history=history,
        )
        stuck_flags = [f for f in rep.flags if f.code == "STUCK_SENSOR"]
        self.assertEqual(len(stuck_flags), 1)
        self.assertEqual(rep.status, QualityStatus.DEGRADED)

    def test_clean_record_validation(self):
        validator = DataQualityValidator()
        prov = DatasetProvenance(
            dataset_id="imd_telemetry_01",
            provenance_type=ProvenanceType.OBSERVATION,
            source_agency="IMD",
            geographic_aoi="Upper Beas",
            temporal_coverage="2023",
            spatial_resolution="Point",
            license_type="Open Govt Data",
            doi_or_url="https://mausam.imd.gov.in",
            is_field_verified=True,
            citation="IMD AWS Telemetry 2023",
        )
        rep = validator.validate_record(
            sample_id="clean_01",
            features={
                "latitude": 32.2,
                "longitude": 77.15,
                "rainfall_rate_mmh": 15.0,
                "water_level_m": 3.2,
            },
            provenance=prov,
        )
        self.assertEqual(rep.status, QualityStatus.VALID)
        self.assertEqual(rep.quality_score, 1.0)
        self.assertTrue(rep.is_usable)
        self.assertEqual(rep.provenance_source, "IMD")


if __name__ == "__main__":
    unittest.main()
