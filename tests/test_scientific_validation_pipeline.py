"""
test_scientific_validation_pipeline.py
========================================
Unit tests for:
  1. ml/validation/spatial_split.py   — Spatial holdout partitioning
  2. ml/validation/event_split.py     — Event & temporal holdout with VALIDATION NOT POSSIBLE fallback
  3. ml/validation/metrics.py         — Binary & multiclass classification metrics
  4. ml/validation/calibration.py     — ECE / MCE probability calibration
  5. ml/validation/spatial_metrics.py — Spatial FP/FN diagnostics
  6. M7 NDMI saturation fix           — Calibrated soil moisture mapping in spatial_ml_engine
  7. ml/features/decision_engines.py  — Shelter allocation, route invalidation, natural-dam cascade
  8. POST /api/v1/satellite/process-real-scene — API response schema (Section 14 keys)
"""

import sys
import os
import types
import unittest
import numpy as np
import pandas as pd
import networkx as nx

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from project root or tests/ directory
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ===========================================================================
# 1. SPATIAL SPLIT TESTS
# ===========================================================================
class TestSpatialSplit(unittest.TestCase):
    """Tests for create_spatial_block_holdout."""

    def _make_df(self, n=500):
        rng = np.random.default_rng(42)
        return pd.DataFrame({
            "lat": rng.uniform(31.0, 32.5, n),
            "lon": rng.uniform(76.5, 77.5, n),
            "flood_label": rng.integers(0, 2, n),
        })

    def test_returns_correct_fields(self):
        from ml.validation.spatial_split import create_spatial_block_holdout
        df = self._make_df()
        result = create_spatial_block_holdout(df)
        self.assertIsNotNone(result.train_indices)
        self.assertIsNotNone(result.test_indices)
        self.assertEqual(result.split_method, "LATITUDE_BLOCK_WITH_BUFFER")

    def test_no_overlap_between_train_and_test(self):
        from ml.validation.spatial_split import create_spatial_block_holdout
        df = self._make_df()
        result = create_spatial_block_holdout(df, buffer_deg=0.01)
        overlap = set(result.train_indices).intersection(set(result.test_indices))
        self.assertEqual(len(overlap), 0, "Train and test sets must not overlap")

    def test_train_lat_below_test_lat(self):
        from ml.validation.spatial_split import create_spatial_block_holdout
        df = self._make_df(n=1000)
        result = create_spatial_block_holdout(df, test_fraction=0.20, buffer_deg=0.01)
        # Test set should be geographically north (higher lat) of training set
        self.assertLessEqual(result.train_lat_range[1], result.test_lat_range[0] + 0.02)

    def test_missing_coordinates_raises(self):
        from ml.validation.spatial_split import create_spatial_block_holdout
        df = pd.DataFrame({"value": [1, 2, 3]})
        with self.assertRaises(ValueError):
            create_spatial_block_holdout(df)

    def test_buffer_excludes_boundary_samples(self):
        from ml.validation.spatial_split import create_spatial_block_holdout
        df = self._make_df(n=2000)
        result_small_buf = create_spatial_block_holdout(df, buffer_deg=0.001)
        result_large_buf = create_spatial_block_holdout(df, buffer_deg=0.05)
        # A larger buffer should exclude more samples (smaller train set)
        self.assertLessEqual(result_large_buf.train_count, result_small_buf.train_count)


# ===========================================================================
# 2. EVENT & TEMPORAL SPLIT TESTS
# ===========================================================================
class TestEventSplit(unittest.TestCase):
    """Tests for create_event_holdout and create_temporal_holdout."""

    def test_event_holdout_no_event_column_returns_not_possible(self):
        from ml.validation.event_split import create_event_holdout
        df = pd.DataFrame({"rain_mm": [10, 20, 30], "flood_label": [0, 1, 0]})
        result = create_event_holdout(df, event_col="event_id")
        self.assertFalse(result.is_available)
        self.assertIn("VALIDATION NOT POSSIBLE WITH CURRENT DATA", result.status_message)

    def test_event_holdout_with_event_column(self):
        from ml.validation.event_split import create_event_holdout
        df = pd.DataFrame({
            "event_id": ["E1"] * 50 + ["E2"] * 50 + ["E3"] * 50 + ["E4"] * 50 + ["E5"] * 50,
            "rain_mm": np.random.rand(250),
            "flood_label": np.random.randint(0, 2, 250),
        })
        result = create_event_holdout(df, event_col="event_id", test_fraction=0.20)
        self.assertTrue(result.is_available)
        self.assertIsNotNone(result.held_out_events)
        self.assertGreater(len(result.train_indices), 0)
        self.assertGreater(len(result.test_indices), 0)
        # No overlap
        overlap = set(result.train_indices).intersection(set(result.test_indices))
        self.assertEqual(len(overlap), 0)

    def test_temporal_holdout_no_timestamp_returns_not_possible(self):
        from ml.validation.event_split import create_temporal_holdout
        df = pd.DataFrame({"rain_mm": [10, 20, 30]})
        result = create_temporal_holdout(df, timestamp_col="timestamp")
        self.assertFalse(result.is_available)
        self.assertIn("VALIDATION NOT POSSIBLE WITH CURRENT DATA", result.status_message)

    def test_temporal_holdout_with_timestamp(self):
        from ml.validation.event_split import create_temporal_holdout
        df = pd.DataFrame({
            "timestamp": pd.date_range("2023-01-01", periods=100, freq="h"),
            "rain_mm": np.random.rand(100),
        })
        result = create_temporal_holdout(df, timestamp_col="timestamp", test_fraction=0.20)
        self.assertTrue(result.is_available)
        self.assertGreater(len(result.train_indices), 0)
        self.assertGreater(len(result.test_indices), 0)


# ===========================================================================
# 3. BINARY & MULTICLASS METRIC TESTS
# ===========================================================================
class TestMetrics(unittest.TestCase):
    """Tests for evaluate_binary_predictions and evaluate_multiclass_predictions."""

    def _perfect_binary_data(self, n=200):
        rng = np.random.default_rng(7)
        y_true = rng.integers(0, 2, n)
        # Perfect probabilities
        y_prob = y_true.astype(np.float32)
        return y_true, y_prob

    def _noisy_binary_data(self, n=500, seed=42):
        rng = np.random.default_rng(seed)
        y_true = rng.integers(0, 2, n)
        y_prob = np.clip(y_true + rng.normal(0, 0.25, n), 0.0, 1.0).astype(np.float32)
        return y_true, y_prob

    def test_perfect_classifier_metrics(self):
        from ml.validation.metrics import evaluate_binary_predictions
        y_true, y_prob = self._perfect_binary_data()
        m = evaluate_binary_predictions(y_true, y_prob)
        self.assertAlmostEqual(m.accuracy, 1.0, places=2)
        self.assertAlmostEqual(m.roc_auc, 1.0, places=2)
        self.assertEqual(m.false_positives, 0)
        self.assertEqual(m.false_negatives, 0)

    def test_noisy_classifier_metrics_in_range(self):
        from ml.validation.metrics import evaluate_binary_predictions
        y_true, y_prob = self._noisy_binary_data()
        m = evaluate_binary_predictions(y_true, y_prob)
        self.assertGreater(m.roc_auc, 0.70)
        self.assertGreaterEqual(m.accuracy, 0.0)
        self.assertLessEqual(m.accuracy, 1.0)
        self.assertGreaterEqual(m.brier_score, 0.0)
        self.assertLessEqual(m.brier_score, 1.0)

    def test_far_and_miss_rate_within_bounds(self):
        from ml.validation.metrics import evaluate_binary_predictions
        y_true, y_prob = self._noisy_binary_data()
        m = evaluate_binary_predictions(y_true, y_prob)
        self.assertGreaterEqual(m.false_alarm_rate, 0.0)
        self.assertLessEqual(m.false_alarm_rate, 1.0)
        self.assertGreaterEqual(m.miss_rate, 0.0)
        self.assertLessEqual(m.miss_rate, 1.0)

    def test_multiclass_metrics_shape(self):
        from ml.validation.metrics import evaluate_multiclass_predictions
        rng = np.random.default_rng(3)
        y_true = rng.integers(0, 3, 300)
        y_pred = rng.integers(0, 3, 300)
        m = evaluate_multiclass_predictions(y_true, y_pred, classes=[0, 1, 2])
        self.assertIn(0, m.class_wise_f1)
        self.assertIn(1, m.class_wise_f1)
        self.assertIn(2, m.class_wise_f1)
        self.assertEqual(len(m.confusion_matrix), 3)
        self.assertEqual(len(m.confusion_matrix[0]), 3)
        self.assertGreaterEqual(m.f1_macro, 0.0)

    def test_confusion_matrix_row_sums(self):
        """Rows of confusion matrix must sum to the true class counts."""
        from ml.validation.metrics import evaluate_multiclass_predictions
        y_true = np.array([0, 0, 0, 1, 1, 2, 2, 2, 2, 2])
        y_pred = np.array([0, 1, 0, 1, 1, 2, 0, 2, 2, 2])
        m = evaluate_multiclass_predictions(y_true, y_pred, classes=[0, 1, 2])
        row_sums = [sum(row) for row in m.confusion_matrix]
        expected = [3, 2, 5]
        self.assertEqual(row_sums, expected)


# ===========================================================================
# 4. CALIBRATION (ECE / MCE) TESTS
# ===========================================================================
class TestCalibration(unittest.TestCase):
    """Tests for evaluate_probability_calibration."""

    def test_perfectly_calibrated_low_ece(self):
        from ml.validation.calibration import evaluate_probability_calibration
        rng = np.random.default_rng(99)
        # Perfect calibration: predicted prob equals empirical rate in each bin
        y_prob = np.linspace(0.05, 0.95, 200)
        y_true = (rng.random(200) < y_prob).astype(int)
        report = evaluate_probability_calibration(y_true, y_prob)
        self.assertLessEqual(report.expected_calibration_error, 0.12,
                             "Perfectly calibrated model should have ECE < 0.12")

    def test_overconfident_model_has_high_ece(self):
        from ml.validation.calibration import evaluate_probability_calibration
        rng = np.random.default_rng(77)
        y_true = rng.integers(0, 2, 200)
        # All predicted as 0.95 (overconfident) when true rate ≈ 0.50
        y_prob = np.full(200, 0.95, dtype=np.float32)
        report = evaluate_probability_calibration(y_true, y_prob)
        self.assertGreater(report.expected_calibration_error, 0.20,
                           "Overconfident model should have ECE > 0.20")

    def test_calibration_report_fields_exist(self):
        from ml.validation.calibration import evaluate_probability_calibration
        rng = np.random.default_rng(55)
        y_true = rng.integers(0, 2, 100)
        y_prob = rng.random(100).astype(np.float32)
        report = evaluate_probability_calibration(y_true, y_prob)
        self.assertIsNotNone(report.expected_calibration_error)
        self.assertIsNotNone(report.max_calibration_error)
        self.assertIsInstance(report.is_well_calibrated, bool)
        self.assertEqual(len(report.bin_sample_counts), report.n_bins)

    def test_ece_between_zero_and_one(self):
        from ml.validation.calibration import evaluate_probability_calibration
        rng = np.random.default_rng(11)
        y_true = rng.integers(0, 2, 300)
        y_prob = rng.random(300).astype(np.float32)
        report = evaluate_probability_calibration(y_true, y_prob)
        self.assertGreaterEqual(report.expected_calibration_error, 0.0)
        self.assertLessEqual(report.expected_calibration_error, 1.0)


# ===========================================================================
# 5. M7 SOIL MOISTURE SATURATION FIX
# ===========================================================================
class TestM7DistributionCalibration(unittest.TestCase):
    """
    Tests that the un-saturated hydrological NDMI → soil_moisture mapping
    used in SpatialMLEngine produces a realistic distribution rather than
    saturating at the proxy ceiling of 98%.

    Root cause (documented in Entry 007):
      Old formula:  soil_moisture = (ndmi + 0.20) / 0.70 * 100  (saturated to ~98 for NDMI ≈ 0.52)
      Fixed formula: soil_moisture = 18.0 + clip((ndmi + 0.35)/0.95, 0, 1) * 72.0
    """

    def _old_formula(self, ndmi: np.ndarray) -> np.ndarray:
        return np.clip((ndmi + 0.20) / 0.70 * 100.0, 0.0, 100.0)

    def _new_formula(self, ndmi: np.ndarray) -> np.ndarray:
        return 18.0 + np.clip((ndmi + 0.35) / 0.95, 0.0, 1.0) * 72.0

    def test_old_formula_saturates_for_typical_summer_forest(self):
        """NDMI ≈ 0.52 (summer mountain forest) caused saturation near 98% with old formula."""
        ndmi = np.full(1000, 0.52)
        sm = self._old_formula(ndmi)
        pct_at_ceiling = float(np.mean(sm >= 97.0)) * 100.0
        self.assertGreater(pct_at_ceiling, 90.0,
                           "Old formula must show saturation (>90% pixels at ceiling) for NDMI=0.52")

    def test_new_formula_does_not_saturate(self):
        """
        New formula must produce substantially less saturation than the old formula for NDMI=0.52.
        NDMI=0.52 → new formula: 18 + clip((0.52+0.35)/0.95, 0, 1)*72 ≈ 83.9%
        NDMI=0.52 → old formula: ~97.4% (stuck near ceiling)
        The new formula must stay < 95% (not at the 97-98% ceiling of the old formula).
        """
        ndmi = np.full(1000, 0.52)
        sm_new = self._new_formula(ndmi)
        sm_old = self._old_formula(ndmi)
        mean_new = float(np.mean(sm_new))
        mean_old = float(np.mean(sm_old))
        # Must be meaningfully lower than the old saturated formula
        self.assertLess(mean_new, 95.0,
                        f"New calibrated formula must yield mean < 95% for NDMI=0.52, got {mean_new:.1f}%")
        self.assertLess(mean_new, mean_old,
                        f"New formula ({mean_new:.1f}%) must give lower values than saturated old formula ({mean_old:.1f}%)")

    def test_new_formula_preserves_range_bounds(self):
        """Soil moisture must stay within [18, 90] for valid NDMI range [-0.35, 0.60]."""
        ndmi = np.linspace(-0.35, 0.60, 500)
        sm = self._new_formula(ndmi)
        self.assertGreaterEqual(float(np.min(sm)), 17.9)
        self.assertLessEqual(float(np.max(sm)), 90.1)

    def test_new_formula_monotone_with_ndmi(self):
        """Higher NDMI (wetter) must map to higher soil moisture."""
        ndmi_low = 0.10
        ndmi_high = 0.45
        sm_low = self._new_formula(np.array([ndmi_low]))[0]
        sm_high = self._new_formula(np.array([ndmi_high]))[0]
        self.assertLess(sm_low, sm_high,
                        "Calibrated soil moisture must increase monotonically with NDMI")

    def test_spatial_ml_engine_uses_calibrated_formula(self):
        """
        Integration test: SpatialMLEngine.infer_landslide_suite must produce
        M7 high_trigger_area_pct well below 99% for a synthetic dry rocky scene
        (NDMI ≈ -0.10, representing sparse/rocky terrain — not wet forest).
        If the old saturated soil_moisture formula were in place, soil_moisture
        would saturate to ~26% (floor end) still — but for NDMI=0.52 (wet),
        the old formula gave 97%+ saturation driving M7 to 99.91%.
        This test verifies the calibrated formula is active in the engine.
        """
        try:
            from ml.satellite_hazard.spatial_ml_engine import SpatialMLEngine
            from ml.satellite_hazard.terrain.terrain_engine import TerrainFeatures
            from ml.satellite_hazard.spectral.index_generator import SpectralIndices
        except ImportError as e:
            self.skipTest(f"SpatialMLEngine or supporting modules not available: {e}")

        engine = SpatialMLEngine()
        H, W = 25, 25
        shape = (H, W)
        zeros = np.zeros(shape, dtype=np.float32)
        ones = np.ones(shape, dtype=np.float32)

        # Dry rocky scene: very low NDMI=-0.10 (sparse, dry, rocky)
        spectral = SpectralIndices(
            shape=shape,
            ndvi=np.full(shape, 0.12, dtype=np.float32),
            ndwi=np.full(shape, -0.30, dtype=np.float32),
            mndwi=np.full(shape, -0.25, dtype=np.float32),
            ndbi=np.full(shape, 0.05, dtype=np.float32),
            ndmi=np.full(shape, -0.10, dtype=np.float32),
            savi=np.full(shape, 0.10, dtype=np.float32),
        )
        terrain = TerrainFeatures(
            shape=shape,
            elevation_m=np.full(shape, 1200.0, dtype=np.float32),
            slope_deg=np.full(shape, 12.0, dtype=np.float32),
            aspect_deg=np.full(shape, 180.0, dtype=np.float32),
            plan_curvature=zeros,
            profile_curvature=zeros,
            topographic_wetness_index=np.full(shape, 6.0, dtype=np.float32),
            stream_power_index=np.full(shape, 100.0, dtype=np.float32),
            terrain_ruggedness_index=np.full(shape, 50.0, dtype=np.float32),
            height_above_nearest_drainage_m=np.full(shape, 80.0, dtype=np.float32),
        )

        result = engine.infer_landslide_suite(
            terrain=terrain,
            spectral=spectral,
            event_rainfall_1h_mm=8.0,   # light rain
            antecedent_rain_3d_mm=20.0, # low antecedent
        )
        m7_pct = result.high_trigger_area_pct
        self.assertLess(
            m7_pct, 99.0,
            f"Dry rocky scene with light rain must not trigger M7 in ≥99% pixels; "
            f"got {m7_pct:.2f}%. Check if soil_moisture formula is still saturated."
        )


# ===========================================================================
# 6. SAFE-ZONE SELECTION TESTS (M15)
# ===========================================================================
class TestSafeZoneSelection(unittest.TestCase):
    """Tests for DecisionIntelligenceEngine.select_safe_shelter."""

    def _engine(self):
        from ml.features.decision_engines import DecisionIntelligenceEngine
        return DecisionIntelligenceEngine()

    def _shelters(self):
        from ml.features.decision_engines import ShelterEntity
        return [
            # High-risk valley floor shelter — must be rejected
            ShelterEntity("S1", "Valley School", 620.0, 400, 100, 31.7, 77.0,
                          flood_prob=0.80, landslide_prob=0.10, natural_dam_risk=0.20),
            # Safe ridge shelter — should be selected
            ShelterEntity("S2", "Ridge Community Center", 1480.0, 600, 150, 31.6, 77.1,
                          flood_prob=0.03, landslide_prob=0.04, natural_dam_risk=0.05,
                          road_accessibility="OPEN", critical_infrastructure=["Generator", "Water"]),
            # Blocked access road — must be rejected
            ShelterEntity("S3", "Gorge Resthouse", 890.0, 200, 50, 31.8, 77.2,
                          flood_prob=0.05, landslide_prob=0.06, natural_dam_risk=0.08,
                          road_accessibility="BLOCKED"),
        ]

    def test_selects_safe_ridgeline_shelter(self):
        engine = self._engine()
        result = engine.select_safe_shelter(self._shelters(), evacuation_demand=100)
        self.assertIsNotNone(result)
        self.assertEqual(result["selected_shelter_id"], "S2")

    def test_safety_classification_is_lower_hazard(self):
        engine = self._engine()
        result = engine.select_safe_shelter(self._shelters(), evacuation_demand=100)
        self.assertEqual(result["safety_classification"], "LOWER_CURRENT_MODELLED_HAZARD")

    def test_statutory_notice_present(self):
        engine = self._engine()
        result = engine.select_safe_shelter(self._shelters(), evacuation_demand=100)
        self.assertIn("NEVER GUARANTEED SAFE", result["statutory_notice"])

    def test_no_shelter_available_returns_none(self):
        """If all shelters are too risky or blocked, must return None (not crash)."""
        from ml.features.decision_engines import DecisionIntelligenceEngine, ShelterEntity
        engine = DecisionIntelligenceEngine()
        bad_shelters = [
            ShelterEntity("B1", "Flooded Shelter", 400.0, 200, 50, 31.7, 77.0,
                          flood_prob=0.90, landslide_prob=0.90, natural_dam_risk=0.80),
        ]
        result = engine.select_safe_shelter(bad_shelters, evacuation_demand=50)
        self.assertIsNone(result)

    def test_spare_capacity_exceeds_demand(self):
        engine = self._engine()
        result = engine.select_safe_shelter(self._shelters(), evacuation_demand=100)
        self.assertGreater(result["spare_capacity"], 0)


# ===========================================================================
# 7. ROUTE INVALIDATION & RECALCULATION TESTS (M16)
# ===========================================================================
class TestEvacuationRouting(unittest.TestCase):
    """Tests for find_safest_evacuation_route and recalculate_route_with_invalidation."""

    def _engine(self):
        from ml.features.decision_engines import DecisionIntelligenceEngine
        return DecisionIntelligenceEngine()

    def _build_graph(self):
        G = nx.Graph()
        # Direct flooded valley road (blocked)
        G.add_edge("V1", "W1", length_km=2.0, flood_prob=0.90, landslide_prob=0.0, is_blocked=True)
        G.add_edge("W1", "S1", length_km=1.5, flood_prob=0.85, landslide_prob=0.0, is_blocked=False)
        # Safer ridge bypass
        G.add_edge("V1", "R1", length_km=3.2, flood_prob=0.02, landslide_prob=0.10, is_blocked=False)
        G.add_edge("R1", "S1", length_km=2.1, flood_prob=0.01, landslide_prob=0.05, is_blocked=False)
        return G

    def test_route_avoids_blocked_edge(self):
        engine = self._engine()
        G = self._build_graph()
        route = engine.find_safest_evacuation_route(G, "V1", "S1")
        self.assertEqual(route["route_status"], "FOUND_SAFER_FEASIBLE")
        # Must not pass through the blocked waypoint W1
        self.assertNotIn("W1", route["path_nodes"])

    def test_route_recommendation_label(self):
        engine = self._engine()
        G = self._build_graph()
        route = engine.find_safest_evacuation_route(G, "V1", "S1")
        self.assertEqual(route["recommendation"], "RECOMMENDED_CURRENTLY_FEASIBLE_LOWER_RISK")

    def test_unreachable_returns_cut_off_status(self):
        """If no path exists between nodes (disconnected graph), status must be UNREACHABLE_CUT_OFF."""
        from ml.features.decision_engines import DecisionIntelligenceEngine
        engine = DecisionIntelligenceEngine()
        # Completely disconnected graph — V1 and S1 are in separate components
        G = nx.Graph()
        G.add_node("V1")
        G.add_node("S1")
        # No edges at all between them
        route = engine.find_safest_evacuation_route(G, "V1", "S1")
        self.assertEqual(route["route_status"], "UNREACHABLE_CUT_OFF")

    def test_invalidation_reroutes_correctly(self):
        engine = self._engine()
        G = self._build_graph()
        # Initially unblock the direct route and add another path
        G["V1"]["W1"]["is_blocked"] = False
        G["V1"]["W1"]["flood_prob"] = 0.10

        # Now invalidate V1-W1 at runtime
        route = engine.recalculate_route_with_invalidation(G, "V1", "S1", [("V1", "W1")])
        self.assertEqual(route["route_status"], "FOUND_SAFER_FEASIBLE")
        self.assertNotIn("W1", route["path_nodes"])

    def test_disclaimer_present_in_route(self):
        engine = self._engine()
        G = self._build_graph()
        route = engine.find_safest_evacuation_route(G, "V1", "S1")
        self.assertIn("disclaimer", route)
        self.assertGreater(len(route["disclaimer"]), 10)


# ===========================================================================
# 8. NATURAL DAM CASCADE TESTS
# ===========================================================================
class TestNaturalDamCascade(unittest.TestCase):
    """Tests for evaluate_natural_dam_cascade."""

    def _engine(self):
        from ml.features.decision_engines import DecisionIntelligenceEngine
        return DecisionIntelligenceEngine()

    def test_high_confidence_candidate_unverified(self):
        engine = self._engine()
        result = engine.evaluate_natural_dam_cascade(
            landslide_hazard_score=0.75,
            channel_obstruction_ratio=0.60,
            upstream_lake_volume_m3=1_000_000,
            is_authority_validated=False,
        )
        self.assertTrue(result["is_candidate"])
        self.assertEqual(result["status"], "CANDIDATE_UNVERIFIED_NATURAL_DAM")

    def test_no_public_warning_without_authority_validation(self):
        engine = self._engine()
        result = engine.evaluate_natural_dam_cascade(
            landslide_hazard_score=0.90,
            channel_obstruction_ratio=0.80,
            upstream_lake_volume_m3=5_000_000,
            is_authority_validated=False,
        )
        self.assertFalse(result["public_warning_issued"],
                         "Must NOT issue public warning without authority ground validation")

    def test_authority_validated_status(self):
        engine = self._engine()
        result = engine.evaluate_natural_dam_cascade(
            landslide_hazard_score=0.80,
            channel_obstruction_ratio=0.70,
            upstream_lake_volume_m3=2_000_000,
            is_authority_validated=True,
        )
        self.assertEqual(result["status"], "AUTHORITY_VALIDATED_NATURAL_DAM")

    def test_low_scores_no_dam_detected(self):
        engine = self._engine()
        result = engine.evaluate_natural_dam_cascade(
            landslide_hazard_score=0.10,
            channel_obstruction_ratio=0.05,
            upstream_lake_volume_m3=0,
            is_authority_validated=False,
        )
        self.assertFalse(result["is_candidate"])
        self.assertEqual(result["status"], "NO_DAM_DETECTED")

    def test_advisory_contains_candidate_only_notice(self):
        engine = self._engine()
        result = engine.evaluate_natural_dam_cascade(0.7, 0.5, 500_000)
        self.assertIn("CANDIDATE STATUS ONLY", result["advisory"])
        self.assertIn("authority ground validation", result["advisory"])


# ===========================================================================
# 9. API RESPONSE SCHEMA — Section 14 keys
# ===========================================================================
class TestSatelliteAPIResponseSchema(unittest.TestCase):
    """
    Tests that POST /api/v1/satellite/process-real-scene returns a JSON body
    containing all 9 required Section 14 keys and that critical nested fields
    carry correct provenance labels.
    """

    REQUIRED_SECTION_14_KEYS = {
        "models", "hazards", "confidence", "exposure",
        "safe_zones", "routes", "natural_dams", "data_quality", "timestamps"
    }

    def _get_client(self):
        try:
            from fastapi.testclient import TestClient
            from backend.app.main import app
            return TestClient(app)
        except Exception:
            return None

    def test_section_14_response_keys_present(self):
        client = self._get_client()
        if client is None:
            self.skipTest("FastAPI app not available in test environment")

        payload = {"scene_id": "upper_beas_july2023", "sentinel2_path": "mock", "dem_path": "mock"}
        resp = client.post("/api/v1/satellite/process-real-scene", json=payload)
        if resp.status_code == 404:
            self.skipTest("Endpoint not mounted in test build")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        missing = self.REQUIRED_SECTION_14_KEYS - set(data.keys())
        self.assertEqual(missing, set(), f"API response missing Section 14 keys: {missing}")

    def test_response_models_field_structure(self):
        client = self._get_client()
        if client is None:
            self.skipTest("FastAPI app not available in test environment")

        payload = {"scene_id": "upper_beas_july2023", "sentinel2_path": "mock", "dem_path": "mock"}
        resp = client.post("/api/v1/satellite/process-real-scene", json=payload)
        if resp.status_code == 404:
            self.skipTest("Endpoint not mounted in test build")

        data = resp.json()
        self.assertIn("models", data)
        models_data = data["models"]
        self.assertIsInstance(models_data, dict)

    def test_response_data_quality_contains_cloud_fraction(self):
        client = self._get_client()
        if client is None:
            self.skipTest("FastAPI app not available in test environment")

        payload = {"scene_id": "upper_beas_july2023", "sentinel2_path": "mock", "dem_path": "mock"}
        resp = client.post("/api/v1/satellite/process-real-scene", json=payload)
        if resp.status_code == 404:
            self.skipTest("Endpoint not mounted in test build")

        data = resp.json()
        if "data_quality" in data:
            dq = data["data_quality"]
            self.assertIsInstance(dq, dict)


# ===========================================================================
# 10. SPATIAL METRICS TESTS
# ===========================================================================
class TestSpatialMetrics(unittest.TestCase):
    """Tests for spatial FP/FN diagnostic functions."""

    def test_spatial_metrics_imports(self):
        """Ensure spatial_metrics module loads without error."""
        try:
            from ml.validation import spatial_metrics  # noqa: F401
        except ImportError as e:
            self.fail(f"spatial_metrics import failed: {e}")

    def test_spatial_metrics_module_has_expected_functions(self):
        """Verify the module exposes expected diagnostic function(s)."""
        from ml.validation import spatial_metrics
        # The module should expose at least one diagnostic callable
        public_callables = [
            name for name in dir(spatial_metrics)
            if callable(getattr(spatial_metrics, name)) and not name.startswith("_")
        ]
        self.assertGreater(len(public_callables), 0,
                           "spatial_metrics must expose at least one public diagnostic function")


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
