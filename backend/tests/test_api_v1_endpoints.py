"""
backend/tests/test_api_v1_endpoints.py
======================================
Integration tests for the new API v1 endpoints:
  - GET /api/v1/models (Catalog)
  - GET /api/v1/models/{model_id} (Model card)
  - POST /api/v1/models/{model_id}/predict (Adapter inference)
  - POST /api/v1/decision/pipeline/execute (Decision pipeline)
  - POST /api/v1/decision/pipeline/alerts/{id}/authorize (Commander sign-off)
  - POST /api/v1/ingest/rain-gauge (Telemetry ingestion)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_v1_list_models(client):
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "models" in data
    assert "M2" in data["models"]
    assert "M7" in data["models"]


def test_api_v1_get_model_detail(client):
    res = client.get("/api/v1/models/M2")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["model_id"] == "M2"
    assert "metadata" in data
    assert "sha256" in data["metadata"]


def test_api_v1_model_predict_m1(client):
    res = client.post(
        "/api/v1/models/M1/predict",
        json={
            "features": {
                "station_id": "TEST_AWS",
                "latitude": 32.2,
                "longitude": 77.18,
                "elevation_m": 2000.0,
                "slope_deg": 20.0,
                "r_1h": 30.0,
                "rolling_intensity_mmh": 30.0,
            }
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["result"]["model_id"] == "M1"
    assert "execution_time_ms" in data["result"]


def test_api_v1_decision_pipeline_and_authorization(client):
    # 1. Execute Decision Pipeline
    exec_res = client.post(
        "/api/v1/decision/pipeline/execute",
        json={
            "location_name": "Larji_Sainj_Confluence",
            "rainfall_intensity_mmh": 60.0,
            "dam_height_m": 35.0,
            "impounded_volume_m3": 8_500_000.0,
            "simulate_nh3_closure": True,
        },
    )
    assert exec_res.status_code == 200
    pdata = exec_res.json()
    assert pdata["status"] == "AWAITING_COMMANDER_AUTHORIZATION"
    alert_id = pdata["draft_alert_id"]

    # 2. Attempt authorization with unauthorized role -> MUST BE 403
    unauth_res = client.post(
        f"/api/v1/decision/pipeline/alerts/{alert_id}/authorize",
        json={
            "actor_id": "JUNIOR_ANALYST_01",
            "actor_role": "ANALYST",
            "approval_token": "token-12345678",
        },
    )
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error"]["code"] == "UNAUTHORIZED_ALERT_DISPATCH"

    # 3. Authorize with Senior Incident Commander -> MUST BE 200 SUCCESS
    auth_res = client.post(
        f"/api/v1/decision/pipeline/alerts/{alert_id}/authorize",
        json={
            "actor_id": "DC_KULLU_01",
            "actor_role": "SENIOR_INCIDENT_COMMANDER",
            "approval_token": "COMMANDER_SIGN_OFF_CRYPTOGRAPHIC_TOKEN_9999",
        },
    )
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["status"] == "SUCCESS"
    assert auth_data["alert"]["status"] == "DISPATCHED"


def test_api_v1_telemetry_ingestion(client):
    import datetime
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    res = client.post(
        "/api/v1/ingest/rain-gauge",
        json={
            "station_id": "AWS_MANALI_01",
            "timestamp": now_str,
            "rainfall_rate_mmh": 14.5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INGESTED"
    assert data["station_id"] == "AWS_MANALI_01"
    assert data["is_anomalous"] is False
