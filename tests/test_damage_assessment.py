"""
test_damage_assessment.py — Unit Tests for Model M20 Post-Disaster Damage Assessment
=====================================================================================
Verifies:
  1. Sentinel-1 SAR interferometric coherence loss and Damage Proxy Map (DPM).
  2. Copernicus EMS 4-tier structural building damage classification.
  3. Lifeline transportation network (NH-3) and bridge cut-off detection.
  4. NDRF/SDRF Rescue Prioritization Index (RPI) ranking and tactical dispatch.
"""

import unittest
import numpy as np

from ml.damage.building_damage_classifier import (
    AssessedBuilding,
    BuildingDamageClassifier,
)
from ml.damage.config import DamageAssessmentConfig
from ml.damage.lifeline_corridor_assessor import LifelineCorridorAssessor
from ml.damage.rescue_prioritizer import RescuePrioritizationEngine
from ml.damage.sar_coherence_engine import SARCoherenceEngine


class TestDamageAssessment(unittest.TestCase):

    def setUp(self):
        self.config = DamageAssessmentConfig()

    def test_config_rpi_weights_sum_to_one(self):
        total_weight = sum(self.config.rpi_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=4)
        self.assertEqual(len(self.config.rpi_weights), 3)

    def test_sar_coherence_engine(self):
        engine = SARCoherenceEngine()
        shape = (50, 50)

        # Pre-event: high coherence (0.85), high backscatter (-6 dB)
        coh_pre = np.full(shape, 0.85, dtype=np.float32)
        vv_pre = np.full(shape, -6.0, dtype=np.float32)

        # Post-event: severe decorrelation (0.25) and backscatter drop (-12 dB)
        coh_post = np.full(shape, 0.25, dtype=np.float32)
        vv_post = np.full(shape, -12.0, dtype=np.float32)

        dpi_grid, stats = engine.compute_damage_proxy(coh_pre, coh_post, vv_pre, vv_post)

        self.assertGreaterEqual(stats.mean_coherence_loss, 0.45)
        self.assertGreaterEqual(stats.damage_proxy_index, 0.70)
        self.assertEqual(stats.decorrelation_severity, "EXTREME")
        self.assertEqual(dpi_grid.shape, shape)

    def test_building_damage_classifier_tiers(self):
        classifier = BuildingDamageClassifier(self.config)

        # 1. Destroyed Building (high coherence loss 0.58, high NDBI drop 0.32, flooded)
        bld_destroyed = classifier.classify_building(
            building_id="BLD_01",
            settlement_name="Aut_Market",
            lat=31.7485,
            lon=77.2082,
            building_type="RESIDENTIAL",
            sar_coherence_loss=0.58,
            optical_ndbi_drop=0.32,
            is_flooded=True,
        )
        self.assertEqual(bld_destroyed.damage_tier, "DESTROYED")
        self.assertEqual(bld_destroyed.rescue_urgency, "IMMEDIATE_SEARCH_AND_RESCUE")
        self.assertLess(bld_destroyed.structural_integrity_pct, 25.0)

        # 2. Intact Building (minimal coherence loss 0.05, negligible NDBI change 0.02)
        bld_intact = classifier.classify_building(
            building_id="BLD_02",
            settlement_name="Bhuntar",
            lat=31.8795,
            lon=77.1560,
            building_type="HOSPITAL",
            sar_coherence_loss=0.05,
            optical_ndbi_drop=0.02,
            is_flooded=False,
        )
        self.assertEqual(bld_intact.damage_tier, "NEGLIGIBLE_INTACT")
        self.assertEqual(bld_intact.rescue_urgency, "NONE")
        self.assertGreater(bld_intact.structural_integrity_pct, 85.0)

    def test_lifeline_corridor_assessor(self):
        assessor = LifelineCorridorAssessor()
        res = assessor.assess_lifelines(flood_surge_height_m=5.2)

        self.assertGreater(res.total_roads_severed_km, 5.0)
        self.assertGreater(len(res.compromised_bridges), 0)
        self.assertIn("Aut_Market", res.isolated_settlements)

        # Check severed bridge
        bridge_aut = next(b for b in res.compromised_bridges if b.bridge_id == "BR_AUT_01")
        self.assertEqual(bridge_aut.status, "STRUCTURALLY_COMPROMISED")

    def test_rescue_prioritizer_ranking(self):
        classifier = BuildingDamageClassifier(self.config)
        assessor = LifelineCorridorAssessor()
        engine = RescuePrioritizationEngine(self.config)

        # Test buildings across 2 settlements
        buildings = [
            classifier.classify_building("B1", "Aut_Market", 31.74, 77.20, "RESIDENTIAL", 0.60, 0.35, True),
            classifier.classify_building("B2", "Aut_Market", 31.74, 77.20, "SCHOOL", 0.55, 0.30, True),
            classifier.classify_building("B3", "Bhuntar", 31.87, 77.15, "RESIDENTIAL", 0.10, 0.05, False),
        ]

        summaries = classifier.evaluate_settlement_buildings(buildings)
        lifelines = assessor.assess_lifelines()
        targets = engine.rank_rescue_operations(summaries, lifelines)

        self.assertGreater(len(targets), 0)
        # Aut Market (isolated + severe damage) should rank #1
        top_target = targets[0]
        self.assertEqual(top_target.settlement_name, "Aut_Market")
        self.assertEqual(top_target.priority_level, "P0_CRITICAL_AIRLIFT")
        self.assertIn("NDRF", top_target.recommended_tactical_action)


if __name__ == "__main__":
    unittest.main()
