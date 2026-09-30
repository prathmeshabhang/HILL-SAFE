"""
backend/tests/test_backend_foundation.py
========================================
Unit and integration tests for FastAPI backend foundation (Phase 2):
  1. Liveness probe (GET /api/v1/health)
  2. Readiness probe (GET /api/v1/health/ready)
  3. Version metadata (GET /api/v1/version)
  4. System status (GET /api/v1/system/status)
  5. Request ID middleware (X-Request-ID propagation)
  6. Structured exception handler
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.errors import DataQualityError, FloodyShieldException


@pytest.fixture
def client():
    return TestClient(app)


def test_health_liveness(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "HEALTHY")
    assert data["service"] == "floody-shield-backend"
    assert "timestamp" in data
    assert "X-Request-ID" in res.headers


def test_health_readiness(client):
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert "ready" in data
    assert "checks" in data
    assert data["checks"]["model_registry"] is True
    assert data["checks"]["data_root"] is True


def test_version_endpoint(client):
    from backend.app.core.config import settings
    res = client.get("/api/v1/version")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] in ("3.2.0", "3.5.0", "3.6.0", settings.APP_VERSION)
    assert "Upper Beas" in data["target_aoi"]
    assert "Level 1" in data["scientific_level"]


def test_system_status_endpoint(client):
    res = client.get("/api/v1/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert data["safety_invariants"]["human_in_the_loop_required"] is True
    assert data["safety_invariants"]["autonomous_emergency_broadcast"] is False


def test_request_id_propagation(client):
    custom_req_id = "test-custom-uuid-9999"
    res = client.get("/api/v1/health", headers={"X-Request-ID": custom_req_id})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == custom_req_id
    assert res.json()["request_id"] == custom_req_id


def test_structured_domain_exception_handling(client):
    # Dynamically register a test route that raises a FloodyShieldException
    @app.get("/api/v1/test-error")
    def trigger_error():
        raise DataQualityError(
            message="Sensor value is out of physical range",
            details={"field": "rainfall_rate", "value": 999.0},
        )

    res = client.get("/api/v1/test-error")
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "DATA_QUALITY_ERROR"
    assert data["error"]["message"] == "Sensor value is out of physical range"
    assert data["error"]["details"]["field"] == "rainfall_rate"
    assert "request_id" in data["error"]
