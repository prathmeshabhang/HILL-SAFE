"""
test_validation_audit.py — Comprehensive Unit Tests for Validation-Audit Layer
==============================================================================
Validates:
  1. test_zero_negative_controls
  2. test_single_class_auc_not_estimable
  3. test_independent_sample_split
  4. test_non_independent_sample_split
  5. test_threshold_metrics_require_threshold
  6. test_exact_binomial_ci_small_n
  7. test_event_count_differs_from_point_count
  8. test_single_event_not_called_independent_n22
  9. test_invalid_control_excluded
 10. test_m4_point_validation_not_called_2d_validation
 11. test_no_synthetic_controls
 12. Invariant verification: indep + non_indep + unknown == total
 13. Invariant verification: event_count <= point_count
 14. Invariant verification: if event_count < 2: event_level_auc is None / NOT_ESTIMABLE
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from ml.validation.audit import (
    ClassBalanceAudit,
    ControlItemAudit,
    ControlQualityAudit,
    ControlValidity,
    EventIndependenceAudit,
    IndependenceStatus,
    MetricResult,
    MetricStatus,
    ModelValidationAuditResult,
    SpatialIndependenceAudit,
    ValidationTier,
    ValidationUnit,
    audit_class_balance,
    audit_event_structure,
    audit_flood_controls,
    audit_spatial_independence,
    check_discrimination_metric_eligibility,
    check_event_level_auc_eligibility,
    evaluate_audited_metrics,
    exact_binomial_ci,
    wilson_score_ci,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = REPO_ROOT / "reports" / "validation_audit"


class TestValidationAuditLayer(unittest.TestCase):
    def test_zero_negative_controls(self):
        """Verifies that a dataset with zero negative controls is flagged as single-class."""
        y_pos_only = np.ones(20, dtype=int)
        cb = audit_class_balance(y_pos_only)
        self.assertTrue(cb.is_single_class)
        self.assertEqual(cb.positive_count, 20)
        self.assertEqual(cb.negative_count, 0)
        self.assertEqual(cb.single_class_label, 1)

    def test_single_class_auc_not_estimable(self):
        """Verifies that ROC-AUC and PR-AUC are marked NOT_ESTIMABLE on single-class data."""
        y_pos_only = np.ones(20, dtype=int)
        cb = audit_class_balance(y_pos_only)
        roc_check = check_discrimination_metric_eligibility(cb, "roc_auc")
        self.assertIsNotNone(roc_check)
        self.assertEqual(roc_check.status, MetricStatus.NOT_ESTIMABLE)
        self.assertIn("not_estimable_due_to_single_class", roc_check.reason)
        self.assertIsNone(roc_check.value)

    def test_independent_sample_split(self):
        """Verifies spatial independence categorization for points > 500m."""
        df_test = pd.DataFrame([
            {"latitude": 32.0, "longitude": 77.0},  # point A
            {"latitude": 32.1, "longitude": 77.1},  # point B
        ])
        train_lats = np.array([31.0])  # > 100 km away
        train_lons = np.array([76.0])

        audit, df_enriched = audit_spatial_independence(df_test, train_lats, train_lons, buffer_threshold_m=500.0)
        self.assertEqual(audit.independent_count, 2)
        self.assertEqual(audit.non_independent_count, 0)
        self.assertEqual(audit.total_samples, 2)
        self.assertTrue(all(df_enriched["is_spatially_independent"]))

    def test_non_independent_sample_split(self):
        """Verifies spatial non-independence categorization for points <= 500m."""
        df_test = pd.DataFrame([
            {"latitude": 32.0001, "longitude": 77.0001},  # ~15m from train point
        ])
        train_lats = np.array([32.0000])
        train_lons = np.array([77.0000])

        audit, df_enriched = audit_spatial_independence(df_test, train_lats, train_lons, buffer_threshold_m=500.0)
        self.assertEqual(audit.independent_count, 0)
        self.assertEqual(audit.non_independent_count, 1)
        self.assertEqual(audit.total_samples, 1)
        self.assertFalse(df_enriched["is_spatially_independent"].iloc[0])

    def test_threshold_metrics_require_threshold(self):
        """Verifies threshold-dependent metrics explicitly store the evaluation threshold."""
        y_true = np.array([1, 1, 0, 0])
        y_prob = np.array([0.9, 0.4, 0.8, 0.1])
        cb = audit_class_balance(y_true)

        metrics = evaluate_audited_metrics(y_true, y_prob, cb, threshold=0.50, threshold_source="Custom test cutoff")
        rec = metrics["recall"]
        self.assertTrue(rec.is_threshold_dependent)
        self.assertEqual(rec.threshold, 0.50)
        self.assertEqual(rec.threshold_source, "Custom test cutoff")

    def test_exact_binomial_ci_small_n(self):
        """Verifies exact Clopper-Pearson CI calculation on small samples (e.g. 6/6 recall)."""
        ci = exact_binomial_ci(count=6, nobs=6, alpha=0.05)
        self.assertTrue(ci.is_reliable)
        self.assertAlmostEqual(ci.upper, 1.0, places=4)
        self.assertAlmostEqual(ci.lower, 0.5407, places=3)
        self.assertLess(ci.lower, 1.0, "100% observed recall must have lower bound < 1.0 showing true uncertainty")

    def test_event_count_differs_from_point_count(self):
        """Verifies detection of clustered spatial points under a common event."""
        df_storm = pd.DataFrame([
            {"point_id": f"P{i}", "rainfall_event_id": "STORM_2023_01"}
            for i in range(10)
        ])
        ev_audit = audit_event_structure(df_storm, event_id_col="rainfall_event_id")
        self.assertEqual(ev_audit.total_points, 10)
        self.assertEqual(ev_audit.total_events, 1)
        self.assertTrue(ev_audit.is_clustered_forcing)

    def test_single_event_not_called_independent_n22(self):
        """Verifies that a dataset with 1 event and 22 points rejects event-level ROC-AUC."""
        ev_audit = EventIndependenceAudit(
            total_points=22,
            total_events=1,
            is_clustered_forcing=True,
            forcing_description="July 9-10 storm",
            primary_unit=ValidationUnit.SPATIAL_SAMPLE,
            event_ids=["STORM_JULY_9_10"],
        )
        auc_check = check_event_level_auc_eligibility(ev_audit)
        self.assertIsNotNone(auc_check)
        self.assertEqual(auc_check.status, MetricStatus.NOT_ESTIMABLE)
        self.assertIn("not_estimable_due_to_single_event", auc_check.reason)

    def test_invalid_control_excluded(self):
        """Verifies negative controls are classified according to the 5-point checklist."""
        df_ctrls = pd.DataFrame([
            {
                "event_id": "C1",
                "location_name": "Dhalpur Civic Relief Ground",
                "latitude": 31.956,
                "longitude": 77.112,
                "inundation_observed": 0,
                "source_document": "HPSDMA PDNA 2023",
                "hazard_type": "elevated_civic_ridge",
                "event_date": "2023-07-09",
            },
            {
                "event_id": "C2",
                "location_name": "Remote High Alpine Moraine",
                "latitude": 32.321,
                "longitude": 77.149,
                "inundation_observed": 0,
                "source_document": "NRSC Flood Assessment",
                "hazard_type": "high_alpine_moraine",
                "event_date": "2023-07-09",
            },
        ])
        ctrl_audit = audit_flood_controls(df_ctrls)
        self.assertEqual(ctrl_audit.total_controls, 2)
        self.assertEqual(ctrl_audit.valid_controls_count, 1)
        self.assertEqual(ctrl_audit.provisional_controls_count, 1)
        self.assertEqual(ctrl_audit.invalid_controls_count, 0)

    def test_m4_point_validation_not_called_2d_validation(self):
        """Verifies that M4 point concordance is distinguished from 2D segmentation."""
        with open(AUDIT_DIR / "m4_audit.json", "r", encoding="utf-8") as f:
            m4_data = json.load(f)

        self.assertEqual(m4_data["primary_validation_unit"], "point")
        self.assertEqual(m4_data["metrics"]["external_2d_dice"]["status"], "NOT_ESTIMABLE")
        self.assertEqual(m4_data["metrics"]["external_2d_iou"]["status"], "NOT_ESTIMABLE")
        self.assertIn("not_available_authoritative_mask_missing", m4_data["metrics"]["external_2d_dice"]["reason"])

    def test_no_synthetic_controls(self):
        """Ensures M6 audit preserves the authentic zero-negative-control ground truth without synthetic sampling."""
        with open(AUDIT_DIR / "m6_audit.json", "r", encoding="utf-8") as f:
            m6_data = json.load(f)

        self.assertEqual(m6_data["class_balance"]["positive_count"], 20)
        self.assertEqual(m6_data["class_balance"]["negative_count"], 0)
        self.assertTrue(m6_data["class_balance"]["is_single_class"])
        self.assertEqual(m6_data["metrics"]["roc_auc"]["status"], "NOT_ESTIMABLE")

    def test_invariants(self):
        """Verifies core mathematical invariants across all model audit files."""
        for fname in ["m6_audit.json", "m7_audit.json", "m2_audit.json", "m4_audit.json"]:
            path = AUDIT_DIR / fname
            self.assertTrue(path.exists(), f"{fname} must exist")
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)

            # Invariant 1: independent + non_independent + unknown == total
            sp = d["spatial_independence"]
            self.assertEqual(
                sp["independent_count"] + sp["non_independent_count"] + sp["unknown_count"],
                sp["total_samples"],
                f"Invariant broken in {fname}: indep + non_indep + unknown != total",
            )
            self.assertLessEqual(sp["independent_count"], sp["total_samples"])

            # Invariant 2: event_count <= point_count (if present)
            if d.get("event_audit") is not None:
                ev = d["event_audit"]
                self.assertLessEqual(ev["total_events"], ev["total_points"])
                if ev["total_events"] < 2:
                    self.assertEqual(
                        d["metrics"]["event_level_roc_auc"]["status"],
                        "NOT_ESTIMABLE",
                        f"Event-level ROC-AUC must be NOT_ESTIMABLE when event count < 2 in {fname}",
                    )


if __name__ == "__main__":
    unittest.main()
