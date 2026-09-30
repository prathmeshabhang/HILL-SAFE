"""
test_damage_and_telemetry_api.py — Integration Tests for Damage, Nowcast, and Telemetry APIs
=============================================================================================
Verifies:
  1. POST /api/v1/damage/analyze (satellite damage proxy trigger)
  2. GET  /api/v1/damage/buildings (Copernicus EMS GeoJSON)
  3. GET  /api/v1/damage/lifelines (severed roads and compromised bridges)
  4. GET  /api/v1/damage/rescue-priority (ranked NDRF/SDRF rescue targets)
  5. POST /api/v1/nowcast/forecast (precipitation trajectories)
  6. GET  /api/v1/nowcast/latest (active atmospheric cycle)
  7. POST /api/v1/telemetry/ingest (live ground readings & anomaly filtering)
  8. GET  /api/v1/telemetry/stations (station metadata)
  9. GET  /api/v1/health (includes M1 and M20 models)
"""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestDamageAndTelemetryAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_damage_analyze_endpoint(self):
        payload = {
            "catchment_name": "Upper_Beas_Basin",
            "event_timestamp_utc": "2026-09-20T08:00:00Z",
            "include_sar_coherence": True,
        }
        resp = self.client.post("/api/v1/damage/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertGreater(data["total_buildings_assessed"], 0)
        self.assertGreater(data["roads_severed_km"], 0.0)

    def test_damage_buildings_geojson(self):
        resp = self.client.get("/api/v1/damage/buildings")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertGreater(len(data["features"]), 0)

        f = data["features"][0]
        self.assertIn("damage_tier", f["properties"])
        self.assertIn("structural_integrity_pct", f["properties"])

    def test_damage_lifelines(self):
        resp = self.client.get("/api/v1/damage/lifelines")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("compromised_roads", data)
        self.assertIn("compromised_bridges", data)
        self.assertIn("isolated_settlements", data)

    def test_damage_rescue_priority(self):
        resp = self.client.get("/api/v1/damage/rescue-priority")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["priority_targets_count"], 0)
        top = data["targets"][0]
        self.assertEqual(top["rank"], 1)
        self.assertIn("rescue_priority_index", top)
        self.assertIn("recommended_tactical_action", top)

    def test_nowcast_forecast_endpoint(self):
        payload = {
            "catchment_name": "Upper_Beas_Catchment",
            "current_max_rain_mmh": 82.0,
            "storm_motion_dx_kmh": 15.0,
            "storm_motion_dy_kmh": -5.0,
        }
        resp = self.client.post("/api/v1/nowcast/forecast", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        nowcast = data["nowcast"]
        self.assertEqual(len(nowcast["timesteps"]), 4)
        self.assertIn(nowcast["cloudburst_risk_level"], ("HIGH", "EXTREME"))

    def test_nowcast_latest_endpoint(self):
        resp = self.client.get("/api/v1/nowcast/latest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("nowcast", data)

    def test_telemetry_ingest_valid_and_invalid(self):
        # 1. Valid Reading
        payload_valid = {
            "station_id": "ST_AUT_01",
            "sensor_type": "RIVER_GAUGE",
            "value": 5.8,
        }
        resp_val = self.client.post("/api/v1/telemetry/ingest", json=payload_valid)
        self.assertEqual(resp_val.status_code, 200)
        data_val = resp_val.json()
        self.assertEqual(data_val["status"], "success")
        self.assertTrue(data_val["reading"]["is_valid"])

        # 2. Invalid Anomaly Reading (negative water level)
        payload_invalid = {
            "station_id": "ST_AUT_01",
            "sensor_type": "RIVER_GAUGE",
            "value": -4.2,
        }
        resp_inval = self.client.post("/api/v1/telemetry/ingest", json=payload_invalid)
        self.assertEqual(resp_inval.status_code, 200)
        data_inval = resp_inval.json()
        self.assertEqual(data_inval["status"], "rejected_anomaly")
        self.assertFalse(data_inval["reading"]["is_valid"])

    def test_telemetry_stations(self):
        resp = self.client.get("/api/v1/telemetry/stations")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["total_stations"], 4)

    def test_health_includes_m1_and_m20(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        models = data["system_components"]["models"]
        self.assertIn("M1_Atmospheric_Nowcasting", models)
        self.assertIn("M20_Post_Disaster_Damage_Assessment", models)


if __name__ == "__main__":
    unittest.main()
