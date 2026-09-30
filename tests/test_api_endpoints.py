"""
test_api_endpoints.py — End-to-End Test Suite for FLOODY SHIELD FastAPI Microservice
===================================================================================
Tests all production endpoints:
  - System Health & Model Status
  - Satellite Rasters, Section 36 Critical Zones & Candidate Development Zones
  - Infrastructure Exposure Summary
  - Model M12 Compound Cascade Dam Breach Simulation
  - NDMA Sachet Bilingual CAP v1.2 Alerts (JSON & XML formats)
  - Decision Intelligence Safe Evacuation Routing
"""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestFloodyShieldAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("HILL-SAFE API" in resp.text or "FLOODY SHIELD API" in resp.text)

    def test_health_endpoint(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertEqual(data["version"], "2.1.0")
        self.assertIn("models", data["system_components"])
        self.assertIn("M2_Deep_Flood_HistGBM", data["system_components"]["models"])
        self.assertIn("M12_Compound_Cascade_DamBreach", data["system_components"]["models"])

    def test_satellite_layers(self):
        resp = self.client.get("/api/v1/satellite/layers")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["total_layers"], 5)
        layer_names = [l["filename"] for l in data["layers"]]
        self.assertIn("multi_hazard_risk.tif", layer_names)
        self.assertIn("flood_mask.tif", layer_names)

    def test_satellite_risk_map_metadata(self):
        resp = self.client.get("/api/v1/satellite/risk-map")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["layer_name"], "multi_hazard_risk")
        self.assertIn("bounds", data)

    def test_critical_development_zones_geojson(self):
        resp = self.client.get("/api/v1/satellite/critical-zones")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertGreater(len(data["features"]), 0)
        first_feature = data["features"][0]
        self.assertIn("geometry", first_feature)
        self.assertIn("properties", first_feature)

    def test_candidate_development_zones_with_disclaimer(self):
        resp = self.client.get("/api/v1/satellite/candidate-development-zones")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertGreater(len(data["features"]), 0)

        # Verify statutory disclaimer in both header and body
        self.assertIn("X-Statutory-Notice", resp.headers)
        self.assertIn("statutory_disclaimer", data)
        self.assertIn("Section 36", data["statutory_disclaimer"])
        self.assertIn("IS 1893", data["statutory_disclaimer"])

    def test_satellite_exposure_summary(self):
        resp = self.client.get("/api/v1/satellite/exposure")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_population_exposed", data)
        self.assertGreater(data["total_population_exposed"], 0)
        self.assertIn("zones", data)

    def test_satellite_analyze_endpoint(self):
        payload = {
            "scene_id": "S2_L2A_UPPER_BEAS_20230710",
            "bbox": [77.05, 31.65, 77.30, 32.05],
            "include_sar_radar": True,
            "uncertainty_level": 0.95,
        }
        resp = self.client.post("/api/v1/satellite/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["sar_radar_fused"])

    def test_cascade_simulation(self):
        payload = {
            "dam_location": "Larji_Sainj_Confluence",
            "dam_height_m": 40.0,
            "impounded_volume_m3": 10_000_000.0,
            "normal_river_discharge_m3s": 500.0,
        }
        resp = self.client.post("/api/v1/cascade/simulate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        sim = data["simulation"]
        self.assertGreater(sim["peak_outflow_discharge_m3s"], 1000.0)
        self.assertEqual(len(sim["downstream_impacts"]), 4)

    def test_alerts_cascade_breach_json_and_xml(self):
        payload = {
            "dam_location": "Larji_Sainj_Confluence",
            "dam_height_m": 35.0,
            "impounded_volume_m3": 8_500_000.0,
            "status": "Actual",
            "format": "json",
        }
        # 1. JSON Response
        resp_json = self.client.post("/api/v1/alerts/cascade-breach", json=payload)
        self.assertEqual(resp_json.status_code, 200)
        data = resp_json.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("cap_alert", data)
        self.assertEqual(len(data["cap_alert"]["infos"]), 2)

        # 2. XML Response
        payload["format"] = "xml"
        resp_xml = self.client.post("/api/v1/alerts/cascade-breach", json=payload)
        self.assertEqual(resp_xml.status_code, 200)
        self.assertIn("application/xml", resp_xml.headers["content-type"])
        self.assertIn("<alert", resp_xml.text)
        self.assertIn("urn:oasis:names:tc:emergency:cap:1.2", resp_xml.text)

    def test_alerts_hazard_zone(self):
        payload = {
            "zone_name": "Aut River Corridor",
            "hazard_type": "Flash Flood Inundation",
            "coordinates_polygon": [
                [31.715, 77.145],
                [31.760, 77.170],
                [31.750, 77.195],
                [31.715, 77.145],
            ],
            "format": "json",
        }
        resp = self.client.post("/api/v1/alerts/hazard-zone", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("cap_alert", data)

    def test_decision_evacuation_routing(self):
        payload = {
            "origin_node": "V_BHUNTAR",
            "destination_node": "S_KULLU_COLLEGE",
            "simulate_nh3_closure": True,
        }
        resp = self.client.post("/api/v1/decision/evacuation-route", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("result", data)
        self.assertIn("route_status", data["result"])

    def test_decision_infrastructure_graph(self):
        resp = self.client.get("/api/v1/decision/infrastructure-graph")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total_nodes"], 0)


if __name__ == "__main__":
    unittest.main()
