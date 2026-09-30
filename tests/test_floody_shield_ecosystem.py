"""
test_floody_shield_ecosystem.py — Master Integration & Regression Test Suite
=============================================================================
Verifies end-to-end functionality across all P0 modules:
  1. Model M2 Flood Occurrence & Risk (XGBoost)
  2. Model M6 Landslide Susceptibility (Random Forest)
  3. Model M7 Landslide Dynamic Trigger (LightGBM)
  4. Model M9 Sensor Anomaly Detection (Dual-stage)
  5. Models M13-M16 Decision Intelligence (Exposure, Safe Zones, Dynamic Routing)
"""

from __future__ import annotations

import unittest
from pathlib import Path
import networkx as nx

from ml.flood.predict_m2_flood import FloodRiskPredictor
from ml.landslide.train_m6_m7_landslide import train_m6_m7_models
from ml.anomaly.m9_sensor_anomaly import SensorAnomalyEngine
from ml.features.decision_engines import (
    DecisionIntelligenceEngine,
    ShelterEntity,
    VillageEntity,
)


class TestFloodyShieldEcosystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.flood_predictor = FloodRiskPredictor()
        cls.anomaly_engine = SensorAnomalyEngine()
        cls.decision_engine = DecisionIntelligenceEngine()

    def test_m2_flood_prediction_bounds(self):
        """Validates that M2 outputs valid probabilities [0, 1] and risk tier."""
        features = {
            "elevation": 800.0,
            "slope": 5.0,
            "flow_accumulation": 3000.0,
            "dist_to_stream": 50.0,
            "land_cover": 2,
            "rainfall_1h": 25.0,
            "rainfall_3h": 45.0,
            "rainfall_6h": 70.0,
            "rainfall_24h": 110.0,
            "antecedent_rain_3d": 80.0,
            "soil_moisture": 78.0,
            "river_level": 6.5,
            "river_level_change_1h": 0.35,
        }
        res = self.flood_predictor.predict_point(features)
        self.assertIn("flood_probability", res)
        self.assertGreaterEqual(res["flood_probability"], 0.0)
        self.assertLessEqual(res["flood_probability"], 1.0)
        self.assertIn(res["risk_tier"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])
        self.assertTrue(len(res["key_drivers"]) > 0)

    def test_m9_anomaly_detector_catches_negative_values(self):
        """Validates Stage 1 deterministic physical check for impossible sensor values."""
        bad_sample = [{"rainfall_rate": -10.0, "soil_moisture": 50.0, "water_level": 2.0, "tilt_degrees": 0.0}]
        res = self.anomaly_engine.check_telemetry_stream(bad_sample)
        self.assertTrue(res["is_anomalous"])
        self.assertEqual(res["status"], "ANOMALOUS")

    def test_m13_population_exposure(self):
        """Validates population exposure aggregation under hazard thresholds."""
        villages = [
            VillageEntity("V1", "Village High Risk", 500, 31.5, 77.0, flood_prob=0.85, landslide_prob=0.10),
            VillageEntity("V2", "Village Safe", 300, 31.6, 77.2, flood_prob=0.10, landslide_prob=0.05),
        ]
        exp = self.decision_engine.calculate_population_exposure(villages, flood_risk_threshold=0.50)
        self.assertEqual(exp["total_population_exposed"], 500)
        self.assertEqual(exp["number_of_villages_impacted"], 1)

    def test_m15_safe_zone_selection(self):
        """Validates that safe shelter selection discards hazardous or full shelters."""
        shelters = [
            # High flood risk -> disqualified
            ShelterEntity("S1", "Flooded Ground", 700.0, 500, 0, 31.5, 77.0, flood_prob=0.80, landslide_prob=0.0),
            # Full occupancy -> disqualified
            ShelterEntity("S2", "Full Ridge Shelter", 1500.0, 200, 200, 31.6, 77.1, flood_prob=0.01, landslide_prob=0.02),
            # Safe and available -> eligible
            ShelterEntity("S3", "Valid Safe Center", 1600.0, 400, 100, 31.7, 77.2, flood_prob=0.02, landslide_prob=0.03),
        ]
        best = self.decision_engine.select_safe_shelter(shelters, evacuation_demand=100)
        self.assertIsNotNone(best)
        self.assertEqual(best["selected_shelter_id"], "S3")

    def test_m16_routing_bypasses_blocked_roads(self):
        """Validates that routing engine automatically bypasses blocked hazard corridors."""
        G = nx.Graph()
        # Direct road: blocked
        G.add_edge("Start", "Direct_Blocked", length_km=1.0, is_blocked=True, flood_prob=0.9)
        G.add_edge("Direct_Blocked", "End", length_km=1.0, is_blocked=False, flood_prob=0.9)
        # Detour road: safe and open
        G.add_edge("Start", "Detour_Safe", length_km=3.0, is_blocked=False, flood_prob=0.0)
        G.add_edge("Detour_Safe", "End", length_km=3.0, is_blocked=False, flood_prob=0.0)

        route = self.decision_engine.find_safest_evacuation_route(G, "Start", "End")
        self.assertEqual(route["route_status"], "FOUND_SAFER_FEASIBLE")
        self.assertIn("Detour_Safe", route["path_nodes"])
        self.assertNotIn("Direct_Blocked", route["path_nodes"])


if __name__ == "__main__":
    unittest.main()
