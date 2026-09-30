"""
test_natural_dam_api.py — Integration Tests for Natural River Dam FastAPI Endpoints
===================================================================================
Verifies:
  1. POST /api/v1/natural-dams/analyze (corridor analysis)
  2. GET  /api/v1/natural-dams (GeoJSON candidates collection)
  3. GET  /api/v1/natural-dams/{dam_id} (profile & explainability)
  4. GET  /api/v1/natural-dams/{dam_id}/history (evolution timeline)
  5. GET  /api/v1/natural-dams/{dam_id}/impoundment (upstream lake GeoJSON)
  6. GET  /api/v1/natural-dams/{dam_id}/downstream-risk (outburst failure risk)
  7. GET  /api/v1/natural-dams/{dam_id}/exposure (impacted population & roads)
  8. POST /api/v1/natural-dams/{dam_id}/validate (authority ground-truth submission)
"""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestNaturalDamAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_analyze_corridor(self):
        payload = {
            "corridor_name": "Upper_Beas_Basin",
            "include_sar_radar": True,
            "forecast_rain_24h_mm": 85.0,
        }
        resp = self.client.post("/api/v1/natural-dams/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertGreater(data["candidates_detected"], 0)
        self.assertGreater(data["false_positives_filtered"], 0)

    def test_list_candidates_geojson(self):
        resp = self.client.get("/api/v1/natural-dams")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(data["name"], "natural_dam_candidates")
        self.assertGreater(len(data["features"]), 0)

        # Inspect first candidate feature
        f = data["features"][0]
        self.assertEqual(f["geometry"]["type"], "Point")
        props = f["properties"]
        self.assertIn("dam_id", props)
        self.assertIn("probability", props)
        self.assertIn("indicators_passed", props)
        self.assertIn("outburst_risk", props)

    def test_candidate_detailed_profile(self):
        resp = self.client.get("/api/v1/natural-dams/ND_BEAS_001")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["dam_id"], "ND_BEAS_001")
        self.assertIn("metrics", data)
        self.assertIn("indicators", data)
        self.assertEqual(len(data["indicators"]), 8)
        self.assertIn("explainability", data)
        self.assertIn("supporting_evidence_ratio", data["explainability"])

    def test_candidate_evolution_history(self):
        resp = self.client.get("/api/v1/natural-dams/ND_BEAS_001/history")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["dam_id"], "ND_BEAS_001")
        self.assertIn("timeline_events", data)
        self.assertGreaterEqual(len(data["timeline_events"]), 2)

    def test_upstream_impoundment_geojson(self):
        resp = self.client.get("/api/v1/natural-dams/ND_BEAS_001/impoundment")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["dam_id"], "ND_BEAS_001")
        self.assertIn("impounded_water_geojson", data)
        self.assertEqual(data["impounded_water_geojson"]["type"], "FeatureCollection")
        self.assertIn("metrics", data)
        self.assertTrue(data["metrics"]["has_impoundment"])
        self.assertGreater(data["metrics"]["surface_area_m2"], 10_000)

    def test_downstream_outburst_risk(self):
        resp = self.client.get("/api/v1/natural-dams/ND_BEAS_001/downstream-risk")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["dam_id"], "ND_BEAS_001")
        self.assertIn(data["outburst_risk_level"], ("HIGH", "VERY_HIGH"))
        self.assertGreater(data["estimated_peak_breach_discharge_m3s"], 500.0)
        self.assertIsNotNone(data["first_settlement_lead_time_min"])

    def test_downstream_exposure(self):
        resp = self.client.get("/api/v1/natural-dams/ND_BEAS_001/exposure")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["dam_id"], "ND_BEAS_001")
        self.assertGreater(data["total_population_exposed"], 1000)
        self.assertGreater(data["roads_compromised_km"], 0.0)
        self.assertGreater(data["bridges_compromised"], 0)

    def test_authority_validation_submission(self):
        payload = {
            "status": "Confirmed",
            "validator_role": "HPSDMA_District_Officer",
            "notes": "Drone confirmed 35m rock avalanche blocking Sainj-Beas channel.",
            "evidence_type": "DRONE_AERIAL_SURVEY",
        }
        resp = self.client.post("/api/v1/natural-dams/ND_BEAS_001/validate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["new_candidate_status"], "CONFIRMED_NATURAL_DAM")
        self.assertTrue(data["validation_id"].startswith("VAL-"))

    def test_candidate_not_found(self):
        resp = self.client.get("/api/v1/natural-dams/NONEXISTENT_DAM")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
