"""
backend/app/api/v1/router.py
============================
Master API v1 Router aggregating all domain-specific routers.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.models import router as models_router
from backend.app.api.v1.endpoints.pipeline import router as pipeline_router
from backend.app.api.v1.endpoints.telemetry_ingest import router as ingest_router
from backend.app.api.v1.endpoints.gis import router as gis_router
from backend.app.api.v1.endpoints.dashboard import router as dashboard_router
from backend.app.api.v1.endpoints.alerts import router as alerts_v1_router
from backend.app.api.v1.endpoints.incidents import router as incidents_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.audit import router as audit_router
from backend.app.api.v1.endpoints.devices import router as devices_router
from backend.app.api.v1.endpoints.field_telemetry import router as field_telemetry_router
from backend.app.api.v1.endpoints.risk import router as risk_router
from backend.app.api.v1.endpoints.analysis import router as analysis_router

# Domain routers
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.cascade import router as cascade_router
from backend.app.routers.damage import router as damage_router
from backend.app.routers.decision import router as decision_router
from backend.app.routers.natural_dams import router as natural_dams_router
from backend.app.routers.nowcast import router as nowcast_router
from backend.app.routers.orchestrator import router as orchestrator_router
from backend.app.routers.satellite import router as satellite_router
from backend.app.routers.telemetry import router as telemetry_router

api_router = APIRouter()

# Register core v3.3 architecture endpoints
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(pipeline_router)
api_router.include_router(ingest_router)
api_router.include_router(gis_router)
api_router.include_router(dashboard_router)
api_router.include_router(alerts_v1_router)
api_router.include_router(incidents_router)
api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(devices_router)
api_router.include_router(field_telemetry_router)
api_router.include_router(risk_router)
api_router.include_router(analysis_router)

# Register legacy and specialized domain endpoints
api_router.include_router(satellite_router)
api_router.include_router(cascade_router)
api_router.include_router(alerts_router)
api_router.include_router(decision_router)
api_router.include_router(natural_dams_router)
api_router.include_router(damage_router)
api_router.include_router(nowcast_router)
api_router.include_router(telemetry_router)
api_router.include_router(orchestrator_router)
