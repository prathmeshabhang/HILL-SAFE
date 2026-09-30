"""
main.py — FLOODY SHIELD Production FastAPI Microservice
======================================================
High-throughput REST API for:
  - Multi-hazard Satellite Intelligence & Development Risk Zoning (Section 23, 36)
  - Multi-API Key Pooling & Dynamic 429 Failover
  - Model M12 Compound Cascade & Landslide Dam Breach Simulation
  - ITU-T X.1303 / NDMA Sachet CAP v1.2 Early Warning Dispatch
  - Decision Intelligence Safe Evacuation Routing
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.errors import FloodyShieldException, floody_exception_handler
from backend.app.core.request_context import RequestContextMiddleware
from ml.security.api_key_manager import get_global_key_pool_manager

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production AI/ML and Satellite Geospatial Early Warning Microservice for Himalayan Flash Floods "
        "and Landslide Hazards (Upper Beas Catchment, Himachal Pradesh). SIH PS-26192."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach Request Context / Request ID Middleware
app.add_middleware(RequestContextMiddleware)

# Enable CORS for frontend / mobile clients (supports localhost & Vercel deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach Global Domain Exception Handler
app.add_exception_handler(FloodyShieldException, floody_exception_handler)

# Mount master API v1 router
app.include_router(api_router)

# Mount WebSocket real-time events router
from backend.app.websocket.endpoint import router as ws_router
app.include_router(ws_router)

@app.get("/metrics", summary="Prometheus metrics exporter")
def root_metrics() -> Any:
    from fastapi.responses import PlainTextResponse
    from backend.app.core.metrics import metrics
    return PlainTextResponse(metrics.export_text(), media_type="text/plain; version=0.0.4")


@app.get("/health", tags=["Health & System"], summary="Microservice liveness check")
def root_health(request: Request) -> Dict[str, Any]:
    from backend.app.api.v1.endpoints.health import get_health
    return get_health(request)


@app.get("/ready", tags=["Health & System"], summary="Microservice readiness check")
def root_ready(request: Request) -> Dict[str, Any]:
    from backend.app.api.v1.endpoints.health import get_readiness
    return get_readiness(request)

BASE_DIR = Path(__file__).resolve().parents[2]
SATELLITE_OUTPUT_DIR = BASE_DIR / "data" / "satellite_output"
EOC_HTML_PATH = Path(__file__).resolve().parent / "static" / "eoc" / "command_center.html"


@app.get("/eoc", response_class=HTMLResponse, summary="Emergency Operations Center Command Dashboard")
def eoc_dashboard() -> str:
    """Renders the full-screen FLOODY SHIELD Emergency Operations Center (EOC) Command Dashboard."""
    if EOC_HTML_PATH.exists():
        return EOC_HTML_PATH.read_text(encoding="utf-8")
    return """
    <html><body style="background:#0f172a;color:#f8fafc;font-family:sans-serif;padding:40px;">
    <h2>HILL-SAFE EOC Dashboard</h2>
    <p>Static dashboard asset is loading or not found.</p>
    </body></html>
    """


@app.get("/", response_class=HTMLResponse, summary="Root dashboard overview")
def root_endpoint() -> str:
    """Renders basic HTML landing page for HILL-SAFE microservice."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HILL-SAFE — Early Warning Microservice</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }
            .card { background: #1e293b; border-radius: 12px; padding: 24px; max-width: 800px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
            h1 { color: #38bdf8; margin-top: 0; }
            .tag { display: inline-block; background: #0369a1; color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; margin-right: 6px; }
            .btn-eoc { display: inline-block; background: #06b6d4; color: #0b0f19; padding: 10px 18px; border-radius: 8px; font-weight: bold; text-decoration: none; margin: 15px 0; }
            .btn-eoc:hover { background: #38bdf8; }
            a { color: #38bdf8; text-decoration: none; font-weight: 600; }
            a:hover { text-decoration: underline; }
            ul { line-height: 1.8; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>HILL-SAFE API <span class="tag">v4.0.0 PROD</span></h1>
            <p><strong>Predict • Protect • Preserve</strong> — Satellite Hazard Intelligence & Early Warning System for Hilly Regions.</p>
            <p><a class="btn-eoc" href="/eoc">🚀 Launch Emergency Operations Center (EOC) Console</a></p>
            <h3>Active API Services:</h3>
            <ul>
                <li><a href="/eoc">Full-Screen EOC Command Dashboard (/eoc)</a></li>
                <li><a href="/docs">Interactive OpenAPI Documentation (/docs)</a></li>
                <li><a href="/api/v1/health">System Health & Model Registry (/api/v1/health)</a></li>
                <li><a href="/api/v1/orchestrator/incidents">Active & Historical Incidents (/api/v1/orchestrator/incidents)</a></li>
                <li><a href="/api/v1/natural-dams">Natural River Dam Candidates (/api/v1/natural-dams)</a></li>
                <li><a href="/api/v1/damage/buildings">Copernicus EMS Building Damage (/api/v1/damage/buildings)</a></li>
                <li><a href="/api/v1/telemetry/stations">Real-Time IoT Ground Stations (/api/v1/telemetry/stations)</a></li>
                <li><a href="/api/v1/nowcast/latest">Atmospheric Nowcasting Trajectories (/api/v1/nowcast/latest)</a></li>
                <li><a href="/api/v1/satellite/layers">Satellite Hazard GIS Rasters (/api/v1/satellite/layers)</a></li>
                <li><a href="/api/v1/satellite/critical-zones">Section 36 Restricted Hazard Zones (/api/v1/satellite/critical-zones)</a></li>
                <li><a href="/api/v1/satellite/candidate-development-zones">Candidate Safe Development Zones (/api/v1/satellite/candidate-development-zones)</a></li>
                <li><a href="/api/v1/satellite/exposure">Critical Infrastructure Exposure (/api/v1/satellite/exposure)</a></li>
                <li><a href="/api/v1/cascade/historical-scenarios">Landslide Dam Breach Scenarios (/api/v1/cascade/historical-scenarios)</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
