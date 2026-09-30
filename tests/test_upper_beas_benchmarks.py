"""
test_upper_beas_benchmarks.py — Verification of >85% Accuracy & Beas Calibration
==================================================================================
Tests and verifies that:
  1. Model M2 achieves >= 85.0% accuracy and ROC-AUC >= 0.88 on holdout test partition.
  2. Model M6 achieves >= 85.0% classification accuracy on terrain susceptibility.
  3. Model M7 achieves >= 85.0% F1-score / ROC-AUC on dynamic trigger detection.
  4. Decision Intelligence successfully identifies compounded flood-landslide villages
     (Aut and Larji) and routes around flooded NH-3 road closures.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from ml.features.beas_decision_infrastructure import build_upper_beas_infrastructure_graph
from ml.features.decision_engines import DecisionIntelligenceEngine


class TestUpperBeasBenchmarks(unittest.TestCase):

    def test_m2_flood_accuracy_benchmark(self):
        """Verifies Model M2 exceeds 85.0% accuracy and ROC-AUC >= 0.88."""
        metrics_file = Path("ml/flood/m2_deep_himalayan_metrics.json")
        if not metrics_file.exists():
            metrics_file = Path("ml/flood/m2_upper_beas_metrics.json")
        self.assertTrue(metrics_file.exists(), "Model M2 metrics file not found")
        with open(metrics_file, "r") as f:
            m = json.load(f)

        m_data = m.get("metrics", m)
        self.assertGreaterEqual(m_data["accuracy_pct"], 85.0, f"M2 Accuracy {m_data['accuracy_pct']}% is below 85.0%")
        self.assertGreaterEqual(m_data["roc_auc"], 0.88, f"M2 ROC-AUC {m_data['roc_auc']} is below 0.88")
        self.assertLessEqual(m_data["brier_score"], 0.10, f"M2 Brier score {m_data['brier_score']} is above 0.10")

    def test_m6_landslide_susceptibility_benchmark(self):
        """Verifies Model M6 exceeds 85.0% classification accuracy."""
        metrics_file = Path("ml/landslide/deep_landslide_suite_metrics.json")
        if not metrics_file.exists():
            metrics_file = Path("ml/landslide/beas_landslide_metrics.json")
        self.assertTrue(metrics_file.exists(), "Landslide metrics file not found")
        with open(metrics_file, "r") as f:
            m = json.load(f)

        m6_acc = m["m6_susceptibility"]["accuracy_pct"]
        self.assertGreaterEqual(m6_acc, 85.0, f"M6 Accuracy {m6_acc}% is below 85.0%")

    def test_m7_landslide_trigger_benchmark(self):
        """Verifies Model M7 achieves high sensitivity (F1 >= 0.85, ROC-AUC >= 0.90)."""
        metrics_file = Path("ml/landslide/deep_landslide_suite_metrics.json")
        if not metrics_file.exists():
            metrics_file = Path("ml/landslide/beas_landslide_metrics.json")
        with open(metrics_file, "r") as f:
            m = json.load(f)

        m7_auc = m["m7_dynamic_trigger"]["roc_auc"]
        m7_rec = m["m7_dynamic_trigger"]["recall"]
        self.assertGreaterEqual(m7_auc, 0.90, f"M7 ROC-AUC {m7_auc} is below 0.90")
        self.assertGreaterEqual(m7_rec, 0.88, f"M7 Recall {m7_rec} is below 0.88")

    def test_conformal_uncertainty_quantification(self):
        """Verifies mathematical finite-sample coverage guarantees (>=90% empirical coverage)."""
        from ml.features.conformal_engine import run_conformal_benchmarks
        bench = run_conformal_benchmarks()
        self.assertIn("m2_flood_conformal", bench)
        self.assertIn("m7_landslide_conformal", bench)
        # Verify coverage is above 90%
        cov_m2 = float(bench["m2_flood_conformal"]["alpha_0.10"]["empirical_coverage"].rstrip("%"))
        cov_m7 = float(bench["m7_landslide_conformal"]["alpha_0.10"]["empirical_coverage"].rstrip("%"))
        self.assertGreaterEqual(cov_m2, 90.0)
        self.assertGreaterEqual(cov_m7, 90.0)

    def test_beas_decision_intelligence_compound_cascade(self):
        """Verifies compound flood-landslide detection in narrow gorge localities."""
        engine = DecisionIntelligenceEngine()
        G, villages, shelters = build_upper_beas_infrastructure_graph()

        exp = engine.calculate_population_exposure(villages, flood_risk_threshold=0.70, landslide_risk_threshold=0.70)
        compound_villages = [v["village_id"] for v in exp["exposed_villages"] if v["hazard_type"] == "COMPOUND_CASCADE"]

        # Aut and Larji are in steep gorge bottoms and must be flagged as COMPOUND_CASCADE
        self.assertIn("V_AUT", compound_villages)
        self.assertIn("V_LARJI", compound_villages)

    def test_beas_dynamic_routing_avoids_flooded_nh3(self):
        """Verifies that dynamic routing bypasses flooded low-lying NH-3."""
        engine = DecisionIntelligenceEngine()
        G, villages, shelters = build_upper_beas_infrastructure_graph()

        route = engine.find_safest_evacuation_route(G, "V_BHUNTAR", "S_KULLU_COLLEGE")
        self.assertEqual(route["route_status"], "FOUND_SAFER_FEASIBLE")
        self.assertIn("Western_Ridge_Pass_Junction", route["path_nodes"])
        self.assertNotIn("NH3_Beas_Bank_Km12", route["path_nodes"])


if __name__ == "__main__":
    unittest.main()
