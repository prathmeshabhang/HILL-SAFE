"""
test_natural_dam_detection.py — Unit Tests for Natural River Dam Detection Engine
================================================================================
Verifies:
  1. River network topology & geometric reach cross-sections.
  2. Multi-sensor optical and SAR specular water extraction.
  3. Multi-temporal river change detection (upstream expansion, downstream drop).
  4. Channel obstruction detection & false-positive infrastructure exclusion.
  5. Landslide scar connectivity filter.
  6. Upstream impoundment analysis and defensible volume estimation.
  7. 8-indicator explainable multi-evidence candidate scoring.
  8. Outburst risk assessment with Model M12 breach integration.
  9. Authority field validation registry.
"""

import unittest
import numpy as np

from ml.natural_dam.candidate_detection.evidence_scorer import MultiEvidenceScorer
from ml.natural_dam.change_detection.temporal_river_change import (
    TemporalObservation,
    TemporalRiverChangeEngine,
)
from ml.natural_dam.config import NaturalDamConfig
from ml.natural_dam.downstream_exposure.downstream_impact import DownstreamImpactEngine
from ml.natural_dam.explainability.explainer import NaturalDamExplainer
from ml.natural_dam.impoundment.upstream_impoundment import UpstreamImpoundmentEngine
from ml.natural_dam.inference.pipeline_runner import NaturalDamPipeline
from ml.natural_dam.landslide_source.debris_connectivity import LandslideSourceDetector
from ml.natural_dam.obstruction_detection.channel_blockage import ChannelObstructionDetector
from ml.natural_dam.outburst_risk.outburst_engine import NaturalDamOutburstEngine
from ml.natural_dam.river_analysis.river_network import RiverNetworkEngine
from ml.natural_dam.validation.registry import ValidationRegistry
from ml.natural_dam.water_detection.multi_water import MultiSensorWaterDetector


class TestNaturalDamDetection(unittest.TestCase):

    def setUp(self):
        self.config = NaturalDamConfig()

    def test_config_weights_sum_to_one(self):
        total_weight = sum(self.config.evidence_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=4)
        self.assertEqual(len(self.config.evidence_weights), 8)

    def test_river_network_engine(self):
        river_engine = RiverNetworkEngine()
        net = river_engine.get_network()
        self.assertEqual(net.network_id, "Upper_Beas_Hydro_Network")
        self.assertGreater(len(net.reach_points), 5)

        # Test nearest reach search near Aut Gorge (31.75N, 77.21E)
        nearest_pt, dist_m = net.find_nearest_reach_point(31.750, 77.208)
        self.assertIn("Aut", nearest_pt.river_name)
        self.assertLess(dist_m, 1000.0)

    def test_multi_sensor_water_detector(self):
        detector = MultiSensorWaterDetector()
        shape = (100, 100)

        # Create synthetic MNDWI and SAR arrays
        mndwi = np.full(shape, -0.3, dtype=np.float32)
        mndwi[40:60, 40:60] = 0.45  # Water square in middle

        sar_vv = np.full(shape, -10.0, dtype=np.float32)
        sar_vv[40:60, 40:60] = -19.5  # Specular reflection drop in middle

        res = detector.detect_water(mndwi=mndwi, ndwi=mndwi, sar_vv_db=sar_vv)
        self.assertTrue(res.optical_available)
        self.assertTrue(res.sar_available)
        self.assertGreater(res.water_area_km2, 0.0)
        # Inside water square, probability should be high
        self.assertGreater(res.water_probability[50, 50], 0.80)
        # Outside water square, probability should be low
        self.assertLess(res.water_probability[10, 10], 0.30)

    def test_temporal_river_change_engine(self):
        change_engine = TemporalRiverChangeEngine()
        shape = (100, 100)

        # Baseline water: narrow channel along column 50
        base_mask = np.zeros(shape, dtype=np.uint8)
        base_mask[:, 48:52] = 1

        # Current water: upstream (rows 0-45) expanded into wide lake (cols 30-70),
        # downstream (rows 46-100) dried/constricted
        curr_mask = np.zeros(shape, dtype=np.uint8)
        curr_mask[0:45, 30:70] = 1
        curr_mask[45:100, 49:51] = 1

        obs_base = TemporalObservation("2023-07-01", "T-9d", base_mask, 0.36)
        obs_curr = TemporalObservation("2023-07-10", "T0", curr_mask, 1.80)

        change_res = change_engine.compare_observations(obs_base, obs_curr, reach_center_row=45, days_between=9.0)
        self.assertTrue(change_res.is_expanding_upstream)
        self.assertGreater(change_res.upstream_expansion_pct, 50.0)
        self.assertGreater(change_res.expansion_rate_km2_day, 0.0)

    def test_obstruction_detector_and_false_positive_filter(self):
        detector = ChannelObstructionDetector(self.config)

        # 1. Genuine landslide obstruction: 71% width reduction, rough boulder debris (-9.5 dB)
        res_real = detector.evaluate_obstruction(
            lat=31.7250,
            lon=77.2180,
            pre_event_width_m=42.0,
            post_event_width_m=12.0,
            sar_backscatter_db=-9.5,
            dem_slope_deg=36.0,
        )
        self.assertTrue(res_real.has_obstruction)
        self.assertFalse(res_real.is_false_positive_structure)
        self.assertGreater(res_real.width_reduction_pct, 60.0)

        # 2. Known artificial dam (Pandoh Dam at 31.6708, 77.0583)
        res_fp = detector.evaluate_obstruction(
            lat=31.6708,
            lon=77.0583,
            pre_event_width_m=110.0,
            post_event_width_m=20.0,
            sar_backscatter_db=-10.0,
            dem_slope_deg=20.0,
        )
        self.assertFalse(res_real.is_false_positive_structure)
        self.assertTrue(res_fp.is_false_positive_structure)
        self.assertIn("Pandoh_Dam", res_fp.false_positive_reason)
        self.assertEqual(res_fp.evidence_score, 0.0)

    def test_landslide_debris_source_connectivity(self):
        detector = LandslideSourceDetector(self.config)

        # Connected steep scar 280m from river
        res_connected = detector.evaluate_connectivity(
            dam_lat=31.7250,
            dam_lon=77.2180,
            scar_lat=31.7270,
            scar_lon=77.2195,
            slope_deg=38.0,
            pre_ndvi=0.65,
            post_ndvi=0.20,
            antecedent_rain_mm=90.0,
        )
        self.assertTrue(res_connected.has_connected_debris_source)
        self.assertEqual(res_connected.failure_mechanism, "COHESIVE_ROCK_SLIDE")
        self.assertLess(res_connected.distance_to_channel_m, 500.0)

        # Distant low-slope location (1200m away, 12 deg slope) -> should NOT be connected
        res_unconnected = detector.evaluate_connectivity(
            dam_lat=31.7250,
            dam_lon=77.2180,
            scar_lat=31.7380,
            scar_lon=77.2280,
            slope_deg=12.0,
            pre_ndvi=0.50,
            post_ndvi=0.48,
            antecedent_rain_mm=30.0,
        )
        self.assertFalse(res_unconnected.has_connected_debris_source)

    def test_upstream_impoundment_analysis(self):
        engine = UpstreamImpoundmentEngine()
        res = engine.analyze_impoundment(
            dam_lat=31.7250,
            dam_lon=77.2180,
            baseline_water_area_m2=40_000.0,
            current_water_area_m2=140_000.0,
            elapsed_hours=24.0,
            estimated_dam_height_m=30.0,
        )
        self.assertTrue(res.has_impoundment)
        self.assertGreater(res.expansion_pct, 100.0)
        self.assertIsNotNone(res.estimated_impounded_volume_m3)
        self.assertEqual(res.volume_estimation_method, "V_SHAPED_VALLEY_PYRAMID")
        self.assertGreaterEqual(len(res.impoundment_polygon_coords), 4)

    def test_multi_evidence_candidate_scorer_and_tiers(self):
        scorer = MultiEvidenceScorer(self.config)

        # High-confidence candidate (all 8 indicators positive)
        candidate = scorer.score_candidate(
            dam_id="TEST_DAM_01",
            river_name="Upper_Beas_Constriction",
            lat=31.7250,
            lon=77.2180,
            elevation_m=885.0,
            obstruction_score=0.85,
            upstream_water_expansion_pct=150.0,
            downstream_water_reduction_pct=30.0,
            debris_source_prob=0.88,
            is_narrow_v_gorge=True,
            sar_backscatter_delta_db=-5.5,
            optical_ndvi_drop=0.35,
            antecedent_rainfall_mm=95.0,
        )
        self.assertEqual(candidate.candidate_tier, "HIGH_CONFIDENCE_CANDIDATE")
        self.assertEqual(candidate.status, "AUTHORITY_VALIDATION_REQUIRED")
        self.assertGreaterEqual(candidate.probability, 0.75)
        self.assertEqual(candidate.indicators_passed_count, 8)

        # Explainability audit
        explanation = NaturalDamExplainer.generate_explanation(candidate)
        self.assertIn("High Confidence Candidate", explanation["headline"])
        self.assertIn("8 / 8", explanation["supporting_evidence_ratio"])

    def test_outburst_risk_engine(self):
        engine = NaturalDamOutburstEngine()

        # Valid high risk
        res = engine.assess_outburst_risk(
            impounded_volume_m3=8_500_000.0,
            dam_height_m=35.0,
            forecast_rain_24h_mm=85.0,
            dam_location_name="Sainj_Gorge",
        )
        self.assertIn(res.outburst_risk_level, ("HIGH", "VERY_HIGH"))
        self.assertGreater(res.peak_breach_discharge_m3s, 1000.0)
        self.assertIsNotNone(res.first_reach_lead_time_min)

        # Missing dimensions -> INSUFFICIENT_DATA
        res_unknown = engine.assess_outburst_risk(
            impounded_volume_m3=None,
            dam_height_m=None,
        )
        self.assertEqual(res_unknown.outburst_risk_level, "INSUFFICIENT_DATA")

    def test_validation_registry(self):
        reg = ValidationRegistry()
        rec = reg.record_validation(
            dam_id="ND_BEAS_001",
            status="Confirmed",
            validator_role="HPSDMA_District_Officer",
            notes="Field team inspected site with drone; active rock avalanche blocking channel.",
            evidence_type="DRONE_AERIAL_SURVEY",
        )
        self.assertTrue(rec.validation_id.startswith("VAL-"))
        self.assertEqual(reg.get_latest_status("ND_BEAS_001"), "Confirmed")


if __name__ == "__main__":
    unittest.main()
