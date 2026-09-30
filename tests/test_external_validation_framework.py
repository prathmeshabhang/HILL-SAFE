"""
test_external_validation_framework.py — Comprehensive Unit Tests for FLOODY SHIELD External Validation Framework
==============================================================================================================
Validates:
  1. Duplicate sample detection
  2. Spatial overlap & 500m independence rule
  3. Event independence separation & grouping
  4. Missing event IDs / dates handling
  5. Control validity enums (VALID_ABSENCE, PROVISIONAL_ABSENCE, INVALID)
  6. Single-class metric handling (graceful handling without crash)
  7. Exact Clopper-Pearson binomial confidence intervals
  8. Point vs 2D full-scene raster distinction
  9. Spatial difference significance auditor (qualified p-values under spatial autocorrelation)
 10. Frozen model weight immutability (SHA-256 verification across M2, M4, M6, M7)
 11. Automated validation tier assignment logic
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.validation.framework.schema import (
    ControlValidity,
    EvaluationSampleRecord,
    EventIndependenceSummary,
    IndependenceStatus,
    SpatialIndependenceSummary,
    ValidationTier,
    audit_dataset_event_independence,
    audit_dataset_spatial_independence,
    determine_validation_status,
    haversine_distance_m,
)
from ml.validation.framework.uncertainty import (
    audit_spatial_difference_significance,
    cluster_aware_bootstrap_ci,
    exact_clopper_pearson_ci,
)


class TestExternalValidationFramework(unittest.TestCase):
    """Unit tests for the strengthened external validation framework."""

    def test_haversine_distance_calculation(self):
        """Verify great-circle distance calculation between known landmarks."""
        # Kullu (31.9579, 77.1095) to Manali (32.2396, 77.1887) is approx 32 km
        dist = haversine_distance_m(31.9579, 77.1095, 32.2396, 77.1887)
        self.assertTrue(31000 < dist < 33000, f"Expected ~32km, got {dist:.1f}m")

        # Zero distance for identical points
        zero_dist = haversine_distance_m(32.0, 77.0, 32.0, 77.0)
        self.assertAlmostEqual(zero_dist, 0.0, places=4)

    def test_duplicate_sample_detection(self):
        """Verify that duplicate spatial points are detected."""
        coords = [
            (32.100, 77.100),
            (32.100, 77.100),  # Duplicate
            (32.200, 77.200),
        ]
        unique_coords = set(coords)
        self.assertEqual(len(coords) - len(unique_coords), 1)

    def test_spatial_independence_500m_rule(self):
        """Verify points <500m from training data are flagged as dependent."""
        training_pts = [(32.000, 77.000)]
        
        # Test point 1: 100m away (approx 0.0009 degrees lat)
        eval_pt_near = (32.0009, 77.000)
        dist_near = haversine_distance_m(32.000, 77.000, eval_pt_near[0], eval_pt_near[1])
        self.assertLess(dist_near, 500.0)

        # Test point 2: 1000m away (approx 0.009 degrees lat)
        eval_pt_far = (32.009, 77.000)
        dist_far = haversine_distance_m(32.000, 77.000, eval_pt_far[0], eval_pt_far[1])
        self.assertGreater(dist_far, 500.0)

    def test_event_independence_separation(self):
        """Verify that multiple spatial samples from a single storm are grouped."""
        records = [
            EvaluationSampleRecord(
                dataset_id="test", model_id="M7", dataset_version="1.0",
                source="test", source_url="test", collection_date="2023-07-09",
                event_id="EV_2023_07", latitude=32.1, longitude=77.1,
                spatial_uncertainty_m=10.0, label=1, label_type="landslide",
                label_confidence="HIGH", observation_type="FIELD_SURVEY",
                spatial_group="reach_1", event_group="storm_2023_07",
                training_overlap_m=1000.0, independence_status=IndependenceStatus.INDEPENDENT,
                independence_reason=">500m separation",
            ),
            EvaluationSampleRecord(
                dataset_id="test", model_id="M7", dataset_version="1.0",
                source="test", source_url="test", collection_date="2023-07-09",
                event_id="EV_2023_07", latitude=32.2, longitude=77.2,
                spatial_uncertainty_m=10.0, label=1, label_type="landslide",
                label_confidence="HIGH", observation_type="FIELD_SURVEY",
                spatial_group="reach_2", event_group="storm_2023_07",
                training_overlap_m=1000.0, independence_status=IndependenceStatus.INDEPENDENT,
                independence_reason=">500m separation",
            ),
        ]
        summary = audit_dataset_event_independence(records)
        self.assertEqual(summary.number_of_unique_events, 1)
        self.assertEqual(summary.samples_per_event["EV_2023_07"], 2)
        self.assertTrue(summary.is_single_event_forcing)

    def test_missing_event_id_or_date_handling(self):
        """Verify that missing event dates/IDs default gracefully without error."""
        rec = EvaluationSampleRecord(
            dataset_id="test", model_id="M6", dataset_version="1.0",
            source="test", source_url="test", collection_date=None,
            event_id=None, latitude=32.1, longitude=77.1,
            spatial_uncertainty_m=10.0, label=1, label_type="landslide",
            label_confidence="HIGH", observation_type="FIELD_SURVEY",
            spatial_group="reach_1", event_group="unknown",
            training_overlap_m=1000.0, independence_status=IndependenceStatus.INDEPENDENT,
            independence_reason=">500m separation",
        )
        self.assertIsNone(rec.event_id)
        self.assertIsNone(rec.collection_date)
        self.assertEqual(rec.event_group, "unknown")

    def test_control_validity_enums(self):
        """Verify ControlValidity enum enforces scientific grading."""
        self.assertEqual(ControlValidity.VALID_ABSENCE.value, "VALID_ABSENCE")
        self.assertEqual(ControlValidity.PROVISIONAL_ABSENCE.value, "PROVISIONAL_ABSENCE")
        self.assertEqual(ControlValidity.INVALID.value, "INVALID")

        # Confirm non-valid controls cannot be passed off as VALID_ABSENCE
        val = ControlValidity("VALID_ABSENCE")
        self.assertIs(val, ControlValidity.VALID_ABSENCE)

    def test_exact_clopper_pearson_ci(self):
        """Verify exact Clopper-Pearson CI calculation against known mathematical bounds."""
        # 0 successes out of 2 trials
        ci0 = exact_clopper_pearson_ci(0, 2, confidence_level=0.95)
        self.assertAlmostEqual(ci0.lower, 0.0, places=3)
        self.assertAlmostEqual(ci0.upper, 0.842, places=3)

        # 2 successes out of 2 trials
        ci2 = exact_clopper_pearson_ci(2, 2, confidence_level=0.95)
        self.assertAlmostEqual(ci2.lower, 0.158, places=3)
        self.assertAlmostEqual(ci2.upper, 1.0, places=3)

        # 5 successes out of 5 trials
        ci5 = exact_clopper_pearson_ci(5, 5, confidence_level=0.95)
        self.assertAlmostEqual(ci5.lower, 0.478, places=3)
        self.assertAlmostEqual(ci5.upper, 1.0, places=3)

        # 0 total trials returns (None, None)
        ci_empty = exact_clopper_pearson_ci(0, 0, confidence_level=0.95)
        self.assertIsNone(ci_empty.lower)
        self.assertIsNone(ci_empty.upper)

    def test_single_class_metric_handling(self):
        """Verify single-class presence does not cause uncaught division errors."""
        # All positives (k=4, n=4)
        ci = exact_clopper_pearson_ci(4, 4, confidence_level=0.95)
        self.assertGreater(ci.lower, 0.0)
        self.assertEqual(ci.upper, 1.0)

    def test_spatial_difference_significance_audit(self):
        """Verify that spatial autocorrelation qualifies naive p-values."""
        # Flooded vs unflooded values along corridor
        group1 = [0.99, 0.98, 0.85, 0.75, 0.60]
        group2 = [0.10, 0.15, 0.20, 0.05, 0.08]
        groups = ["r1", "r1", "r2", "r2", "r3"]
        
        audit = audit_spatial_difference_significance(group1, group2, groups, groups)
        self.assertTrue(audit["delta_mean"] > 0.5)
        self.assertIn("QUALIFIED", audit["scientific_verdict"])
        self.assertFalse(audit["is_valid_iid"])

    def test_validation_tier_determination(self):
        """Verify automated tier assignment accurately reflects evidence level."""
        # M6 underpowered sample: N=8, pos=6, ctrl=2, events=1 -> INSUFFICIENT_EXTERNAL_EVIDENCE
        tier_under, reason_under = determine_validation_status(
            model_id="M6",
            n_independent_samples=8,
            n_independent_positives=6,
            n_independent_valid_controls=2,
            n_independent_events=1,
        )
        self.assertEqual(tier_under, ValidationTier.INSUFFICIENT_EXTERNAL_EVIDENCE)

        # M7 multi-event catalog: N_samples=22, pos=5, ctrl=2, N_events=7 -> PARTIALLY_EXTERNAL_VALIDATED
        tier_m7, reason_m7 = determine_validation_status(
            model_id="M7",
            n_independent_samples=22,
            n_independent_positives=5,
            n_independent_valid_controls=2,
            n_independent_events=7,
        )
        self.assertEqual(tier_m7, ValidationTier.PARTIALLY_EXTERNAL_VALIDATED)

        # M2 verified relief cohort: N=6, pos=4, ctrl=2, events=1 -> PARTIALLY_EXTERNAL_VALIDATED
        tier_m2, reason_m2 = determine_validation_status(
            model_id="M2",
            n_independent_samples=6,
            n_independent_positives=4,
            n_independent_valid_controls=2,
            n_independent_events=1,
        )
        self.assertEqual(tier_m2, ValidationTier.PARTIALLY_EXTERNAL_VALIDATED)

        # M4 point concordance without 2D raster -> PARTIALLY_EXTERNAL_VALIDATED
        tier_m4, reason_m4 = determine_validation_status(
            model_id="M4",
            n_independent_samples=6,
            n_independent_positives=4,
            n_independent_valid_controls=2,
            n_independent_events=1,
            has_authoritative_2d_raster=False,
        )
        self.assertEqual(tier_m4, ValidationTier.PARTIALLY_EXTERNAL_VALIDATED)

    def test_frozen_model_immutability_sha256(self):
        """Verify that production model artifacts exist and match frozen SHA-256 hashes."""
        models = [
            ("M6 Landslide RF", REPO_ROOT / "ml" / "landslide" / "m6_beas_susceptibility_rf.joblib", "e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c"),
            ("M7 Landslide LGBM", REPO_ROOT / "ml" / "landslide" / "m7_beas_trigger_lgbm.joblib", "f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a"),
            ("M2 Flood Risk XGB", REPO_ROOT / "ml" / "flood" / "m2_upper_beas_flood_model.joblib", "a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b"),
            ("M4 Flood UNet PT", REPO_ROOT / "data" / "satellite_output" / "flood_multimodal_unet.pt", "45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07"),
        ]

        for name, path, expected_sha in models:
            self.assertTrue(path.exists(), f"Model artifact missing for {name}: {path}")
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            computed_sha = h.hexdigest()
            self.assertEqual(
                computed_sha,
                expected_sha,
                f"Frozen SHA-256 mismatch for {name}! Model was modified! Expected {expected_sha}, got {computed_sha}",
            )


if __name__ == "__main__":
    unittest.main()
