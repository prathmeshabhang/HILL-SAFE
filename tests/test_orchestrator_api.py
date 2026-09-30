"""
test_orchestrator_api.py — Integration Tests for Incident Orchestrator & EOC Console
====================================================================================
Verifies:
  1. POST /api/v1/orchestrator/trigger-incident
  2. GET  /api/v1/orchestrator/incidents
  3. GET  /api/v1/orchestrator/incidents/{incident_id}
  4. GET  /api/v1/orchestrator/incidents/{incident_id}/cap-xml
  5. POST /api/v1/orchestrator/incidents/{incident_id}/status
  6. GET  /eoc (Command Center web dashboard)
  7. GET  /api/v1/health (includes Autonomous_Incident_Orchestrator)
"""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestOrchestratorAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_list_incidents(self):
        resp = self.client.get("/api/v1/orchestrator/incidents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_incidents"], 1)
        inc = data["incidents"][0]
        self.assertIn("incident_id", inc)
        self.assertIn("severity_level", inc)

    def test_trigger_incident_endpoint(self):
        payload = {
            "incident_type": "NATURAL_DAM_BREACH",
            "severity_level": "CRITICAL",
            "trigger_source": "SATELLITE_SYNTHESIS",
            "trigger_location": "Larji_Sainj_Confluence",
            "dam_height_m": 38.0,
            "impounded_volume_m3": 9_200_000.0,
            "rainfall_rate_mmh": 72.0,
            "simulate_nh3_closure": True,
            "custom_id": "INC-API-TEST-01",
        }
        resp = self.client.post("/api/v1/orchestrator/trigger-incident", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["incident_id"], "INC-API-TEST-01")
        self.assertIn("peak_outflow_discharge_m3s", data["incident"]["cascade_simulation"])
        self.assertTrue(data["incident"]["evacuation_plan"]["nh3_closure_simulated"])

    def test_get_incident_detail(self):
        resp = self.client.get("/api/v1/orchestrator/incidents/INC-BEAS-LARJI-01")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["incident"]["incident_id"], "INC-BEAS-LARJI-01")
        self.assertIn("statutory_notice", data["incident"])

    def test_get_incident_cap_xml(self):
        resp = self.client.get("/api/v1/orchestrator/incidents/INC-BEAS-LARJI-01/cap-xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/xml", resp.headers["content-type"])
        self.assertIn("<alert", resp.text)
        self.assertIn("urn:oasis:names:tc:emergency:cap:1.2", resp.text)

    def test_update_status(self):
        payload = {"new_status": "CONTAINED", "notes": "Upstream drainage channels operational."}
        resp = self.client.post("/api/v1/orchestrator/incidents/INC-BEAS-LARJI-01/status", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["new_status"], "CONTAINED")
        self.assertIn("drainage channels", data["latest_audit_log"]["action"])

    def test_eoc_dashboard_endpoint(self):
        resp = self.client.get("/eoc")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("FLOODY SHIELD — EMERGENCY OPERATIONS CENTER", resp.text)
        self.assertIn("Leaflet", resp.text)
        self.assertIn("Natural Dam Candidate", resp.text)

    def test_health_check_orchestrator(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Autonomous_Incident_Orchestrator", data["system_components"]["models"])
        self.assertIn("ACTIVE", data["system_components"]["models"]["Autonomous_Incident_Orchestrator"])


if __name__ == "__main__":
    unittest.main()
