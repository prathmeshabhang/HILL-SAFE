"""
test_frontend_integration.py — End-to-End API Integration Suite for FLOODY SHIELD Frontend
==========================================================================================
Verifies that all API routes, GIS layers, Risk summaries, Model metadata, Alert lifecycles,
and WebSocket streams consumed by the React 19 Frontend application respond with valid schemas
and adhere to life-safety requirements.
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestFrontendIntegration:
    """E2E test suite confirming frontend contract alignment."""

    def test_01_root_health_and_version(self, client):
        """Frontend Welcome and Header system health checks."""
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") in ["HEALTHY", "healthy", "DEGRADED", "degraded"]
        assert "version" in data

        res_v1 = client.get("/api/v1/health")
        assert res_v1.status_code == 200
        data_v1 = res_v1.json()
        assert data_v1.get("status") in ["HEALTHY", "healthy", "DEGRADED", "degraded"]

    def test_02_basin_risk_summary(self, client):
        """Frontend HomePage and SitRep risk state ingestion."""
        res = client.get("/api/v1/risk/current")
        assert res.status_code == 200
        data = res.json()
        # Returns either an active risk dict or default NO_ACTIVE_RISK_ASSESSMENT
        assert "overall_risk_level" in data or "status" in data

    def test_03_telemetry_stations(self, client):
        """Frontend SensorsPage IoT station telemetry list."""
        res = client.get("/api/v1/stations")
        assert res.status_code == 200
        data = res.json()
        assert "stations" in data
        assert isinstance(data["stations"], list)

    def test_04_natural_dam_candidates_geojson(self, client):
        """Frontend NaturalDamPage and GIS Map overlay."""
        res = client.get("/api/v1/natural-dams")
        assert res.status_code == 200
        data = res.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data
        assert isinstance(data["features"], list)
        for feature in data["features"]:
            assert feature.get("type") == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
            assert "dam_id" in feature["properties"]

    def test_05_gis_hazard_zones(self, client):
        """Frontend FloodMapPage multi-hazard layer."""
        res = client.get("/api/v1/gis/hazards")
        assert res.status_code == 200
        data = res.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data

    def test_06_gis_safe_zones(self, client):
        """Frontend EvacuationPage and FloodMapPage safe havens."""
        res = client.get("/api/v1/gis/safe-zones")
        assert res.status_code == 200
        data = res.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data

    def test_07_gis_evacuation_routes(self, client):
        """Frontend EvacuationPage routes."""
        res = client.get("/api/v1/gis/routes")
        assert res.status_code == 200
        data = res.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data

    def test_08_satellite_critical_zones(self, client):
        """Frontend restricted red zones for mountain safety."""
        res = client.get("/api/v1/satellite/critical-zones")
        assert res.status_code == 200
        data = res.json()
        assert data.get("type") == "FeatureCollection"

    def test_09_models_evidence_catalog(self, client):
        """Frontend ModelsPage 20-model ecosystem catalog."""
        res = client.get("/api/v1/models")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert "models" in data
        assert data.get("total_registered_models") >= 15
        model_ids = list(data["models"].keys()) if isinstance(data["models"], dict) else [m["model_id"] for m in data["models"]]
        for expected in ["M2", "M4", "M6", "M7"]:
            assert expected in model_ids

    def test_10_cascade_historical_scenarios(self, client):
        """Frontend HistoricalReplayPage scenario benchmarks."""
        res = client.get("/api/v1/cascade/historical-scenarios")
        assert res.status_code == 200
        data = res.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) >= 3

    def test_11_alert_lifecycle_and_dual_authorization(self, client):
        """
        Life-Safety Invariant Drill:
        Draft alert creation -> Pending -> Incident Commander Sign-off -> DISPATCHED.
        """
        # 1. Create a draft alert
        draft_payload = {
            "headline": "CRITICAL TEST: Flash Flood Surge Upper Beas Reach",
            "description": "Rapid discharge spike detected upstream of Palchan confluence.",
            "instruction": "Immediately evacuate low-lying banks and move to Safe Zone SH-01.",
            "area_desc": "Solang to Old Manali Beas corridor",
            "severity": "Extreme",
            "urgency": "Immediate",
            "certainty": "Observed",
        }
        res_draft = client.post("/api/v1/alerts/draft", json=draft_payload)
        assert res_draft.status_code == 200
        draft_data = res_draft.json()
        assert draft_data["status"] == "DRAFT_CREATED"
        alert_id = draft_data["alert"]["id"]
        assert draft_data["alert"]["status"] == "PENDING_APPROVAL"

        # 2. Try unauthorized approval (invalid role or missing token)
        bad_auth_payload = {
            "actor_id": "OFFICER_OBSERVER",
            "actor_role": "OBSERVER",
            "approval_token": "INVALID_TOKEN",
        }
        res_bad = client.post(f"/api/v1/alerts/{alert_id}/authorize", json=bad_auth_payload)
        assert res_bad.status_code in [400, 401, 403]

        # 3. Authorized Senior Incident Commander Sign-off
        auth_payload = {
            "actor_id": "CMD-01-STATE",
            "actor_role": "SENIOR_INCIDENT_COMMANDER",
            "approval_token": "CMD-SEC-KEY-7781-BEAS",
        }
        res_ok = client.post(f"/api/v1/alerts/{alert_id}/authorize", json=auth_payload)
        assert res_ok.status_code == 200
        ok_data = res_ok.json()
        assert ok_data["status"] == "DISPATCHED"
        assert ok_data["alert"]["status"] == "DISPATCHED"
        assert ok_data["alert"]["authorized_by"] == "CMD-01-STATE"

        # 4. Confirm CAP XML generated
        res_cap = client.get(f"/api/v1/alerts/{alert_id}?format=xml")
        assert res_cap.status_code == 200
        assert "alert" in res_cap.text
        assert "urn:oasis:names:tc:emergency:cap:1.2" in res_cap.text

    def test_12_websocket_event_stream_connection(self, client):
        """Frontend wsClient real-time live event channel handshake."""
        with client.websocket_connect("/ws/v1/events") as websocket:
            # Send client ping / subscription
            websocket.send_text(json.dumps({"type": "SUBSCRIBE", "channels": ["ALERTS", "TELEMETRY"]}))
            # Receive server welcome or acknowledgment
            data = websocket.receive_text()
            assert data is not None
            parsed = json.loads(data)
            assert "type" in parsed or "event" in parsed or "status" in parsed
