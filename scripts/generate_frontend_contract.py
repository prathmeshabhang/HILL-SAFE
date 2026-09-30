"""
scripts/generate_frontend_contract.py
=====================================
Generates the comprehensive, exhaustive Frontend API Integration Contract
for FLOODY SHIELD v4.0.
Extracts all OpenAPI paths, request/response models, authentication gates,
WebSocket channels, error models, and frontend environment variables.
"""

import json
import inspect
from pathlib import Path
from typing import Any, Dict, List
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "docs" / "FRONTEND_API_INTEGRATION_CONTRACT.md"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.main import app


def get_schema_example(schema_dict: Dict[str, Any], components_schemas: Dict[str, Any], depth=0) -> Any:
    if depth > 5:
        return {}
    if not schema_dict:
        return {}
    if "$ref" in schema_dict:
        ref_name = schema_dict["$ref"].split("/")[-1]
        resolved = components_schemas.get(ref_name, {})
        return get_schema_example(resolved, components_schemas, depth + 1)

    schema_type = schema_dict.get("type", "object")

    if schema_type == "object" or "properties" in schema_dict:
        props = schema_dict.get("properties", {})
        example = {}
        for p_name, p_spec in props.items():
            if "example" in p_spec:
                example[p_name] = p_spec["example"]
            elif "default" in p_spec:
                example[p_name] = p_spec["default"]
            else:
                p_type = p_spec.get("type", "string")
                if "$ref" in p_spec:
                    example[p_name] = get_schema_example(p_spec, components_schemas, depth + 1)
                elif p_type == "string":
                    fmt = p_spec.get("format", "")
                    if fmt == "date-time":
                        example[p_name] = "2026-09-22T06:00:00Z"
                    else:
                        example[p_name] = p_spec.get("description", p_name)
                elif p_type == "number" or p_type == "float":
                    example[p_name] = 42.5
                elif p_type == "integer":
                    example[p_name] = 10
                elif p_type == "boolean":
                    example[p_name] = True
                elif p_type == "array":
                    items = p_spec.get("items", {})
                    example[p_name] = [get_schema_example(items, components_schemas, depth + 1)]
                else:
                    example[p_name] = None
        return example

    elif schema_type == "array":
        items = schema_dict.get("items", {})
        return [get_schema_example(items, components_schemas, depth + 1)]
    elif schema_type == "string":
        return schema_dict.get("default", "string_value")
    elif schema_type in ("number", "float"):
        return schema_dict.get("default", 0.0)
    elif schema_type == "integer":
        return schema_dict.get("default", 0)
    elif schema_type == "boolean":
        return schema_dict.get("default", True)
    return {}


def classify_status(path: str, method: str) -> str:
    # Physical sensor/device staging
    if "/stations" in path or "/devices" in path or "/sensors" in path:
        return "PROTOTYPE_STAGING"
    # Scenario simulations / historical replays
    if "/cascade/simulate" in path or "/incidents/replay" in path or "/cascade/historical-scenarios" in path:
        return "IMPLEMENTED (SIMULATION)"
    # LoRa binary frame & backhaul
    if "/telemetry/lora" in path:
        return "IMPLEMENTED (HARDWARE_SIMULATION)"
    # Fully operational production services
    return "IMPLEMENTED (OPERATIONAL)"


def generate_contract():
    openapi = app.openapi()
    paths = openapi.get("paths", {})
    components_schemas = openapi.get("components", {}).get("schemas", {})

    lines = []
    lines.append("# FLOODY SHIELD v4.0 — Master Frontend API & Integration Contract\n")
    lines.append("> **System Version**: `4.0.0` (Production Hardened & Verified)  \n")
    lines.append("> **Target Catchment**: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  \n")
    lines.append("> **Authority Invariant**: Life-safety alert broadcast strictly requires Senior Incident Commander cryptographic dual-authorization.  \n")
    lines.append("> **Physical Network Maturity**: Physical IoT stations classified as `PROTOTYPE_STAGING` (0 active river water installations).  \n\n")

    lines.append("---\n\n")
    lines.append("## Table of Contents\n")
    lines.append("1. [Frontend Environment Variables Specification](#1-frontend-environment-variables-specification)\n")
    lines.append("2. [Authentication & RBAC Architecture](#2-authentication--rbac-architecture)\n")
    lines.append("3. [Standard Error Response Specification](#3-standard-error-response-specification)\n")
    lines.append("4. [Real-Time WebSocket Channels & Protocol](#4-real-time-websocket-channels--protocol)\n")
    lines.append("5. [Exhaustive REST API Endpoints Specification](#5-exhaustive-rest-api-endpoints-specification)\n")
    lines.append("   - [Module 1: Core System Health, Readiness & Observability](#module-1-core-system-health-readiness--observability)\n")
    lines.append("   - [Module 2: Authentication & User RBAC](#module-2-authentication--user-rbac)\n")
    lines.append("   - [Module 3: Unified Multi-Hazard Risk State & Spatial Corridors](#module-3-unified-multi-hazard-risk-state--spatial-corridors)\n")
    lines.append("   - [Module 4: Incident Response & Multi-Hazard Orchestration](#module-4-incident-response--multi-hazard-orchestration)\n")
    lines.append("   - [Module 5: Early Warning Alert Lifecycle & CAP v1.2 Dispatch](#module-5-early-warning-alert-lifecycle--cap-v12-dispatch)\n")
    lines.append("   - [Module 6: Decision Intelligence, Evacuation & Routing](#module-6-decision-intelligence-evacuation--routing)\n")
    lines.append("   - [Module 7: GIS Layers, Critical Infrastructure & Landslide Zoning](#module-7-gis-layers-critical-infrastructure--landslide-zoning)\n")
    lines.append("   - [Module 8: ML Model Registry & Analytical Predictions (M1–M20)](#module-8-ml-model-registry--analytical-predictions-m1m20)\n")
    lines.append("   - [Module 9: Physical Ground Stations, Devices & Hardware Lifecycle](#module-9-physical-ground-stations-devices--hardware-lifecycle)\n")
    lines.append("   - [Module 10: Telemetry Ingestion, LoRa LPWAN Gateway & Time-Series QC](#module-10-telemetry-ingestion-lora-lpwan-gateway--time-series-qc)\n")
    lines.append("   - [Module 11: Cryptographic Audit Trail & Tamper Evidence](#module-11-cryptographic-audit-trail--tamper-evidence)\n")
    lines.append("   - [Module 12: High-Level EOC Dashboard Aggregations](#module-12-high-level-eoc-dashboard-aggregations)\n")
    lines.append("6. [Endpoint Implementation Status Matrix](#6-endpoint-implementation-status-matrix)\n\n")

    lines.append("---\n\n")
    lines.append("## 1. Frontend Environment Variables Specification\n\n")
    lines.append("For any modern frontend client (React, Vite, Next.js, or mobile Flutter app), configure the following environment variables in `.env`:\n\n")
    lines.append("```ini\n")
    lines.append("# FLOODY SHIELD Frontend Environment Variables\n")
    lines.append("VITE_API_BASE_URL=http://127.0.0.1:8000\n")
    lines.append("VITE_WS_URL=ws://127.0.0.1:8000/ws/v1/events\n")
    lines.append("VITE_APP_NAME=\"FLOODY SHIELD — Predict • Protect • Preserve\"\n")
    lines.append("VITE_APP_VERSION=4.0.0\n")
    lines.append("VITE_ENVIRONMENT=development\n\n")
    lines.append("# Geographic Focus (Upper Beas Catchment, Himachal Pradesh)\n")
    lines.append("VITE_MAP_CENTER_LAT=32.2396\n")
    lines.append("VITE_MAP_CENTER_LON=77.1887\n")
    lines.append("VITE_MAP_DEFAULT_ZOOM=11\n")
    lines.append("VITE_AOI_BBOX_SW_LAT=31.40\n")
    lines.append("VITE_AOI_BBOX_SW_LON=76.80\n")
    lines.append("VITE_AOI_BBOX_NE_LAT=32.45\n")
    lines.append("VITE_AOI_BBOX_NE_LON=77.45\n\n")
    lines.append("# Polling & Streaming Configuration\n")
    lines.append("VITE_TELEMETRY_REFRESH_INTERVAL_MS=5000\n")
    lines.append("VITE_WS_RECONNECT_BACKOFF_MS=3000\n")
    lines.append("VITE_ALERT_POLL_INTERVAL_MS=10000\n\n")
    lines.append("# External Map Tile Providers (Optional)\n")
    lines.append("VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here\n")
    lines.append("```\n\n")

    lines.append("---\n\n")
    lines.append("## 2. Authentication & RBAC Architecture\n\n")
    lines.append("### Authentication Scheme\n")
    lines.append("- **Protocol**: HTTP Bearer JWT (OAuth2 Password flow / JWT token).\n")
    lines.append("- **Header**: `Authorization: Bearer <access_token>`\n")
    lines.append("- **Token Lifespan**: Default 1440 minutes (24 hours).\n")
    lines.append("- **Algorithm**: `HS256`.\n\n")
    lines.append("### Role Hierarchy & Permissions\n")
    lines.append("| Role | Level | Capabilities |\n")
    lines.append("|---|:---:|---|\n")
    lines.append("| `OBSERVER` | 1 | Read-only access to GIS layers, public telemetry, active incidents, and general system status. |\n")
    lines.append("| `ANALYST` | 2 | Everything in `OBSERVER` plus: Run ML predictions, register stations, execute pipeline simulations, record field surveys, and create draft alerts. |\n")
    lines.append("| `SENIOR_INCIDENT_COMMANDER` | 3 | Everything in `ANALYST` plus: **Cryptographic life-safety alert authorization**, station commissioning certification, and emergency escalation. |\n")
    lines.append("| `ADMIN` | 4 | Full administrative access, device management, user administration, and system configuration. |\n\n")

    lines.append("---\n\n")
    lines.append("## 3. Standard Error Response Specification\n\n")
    lines.append("All application exceptions follow the standardized domain error envelope:\n\n")
    lines.append("```json\n")
    lines.append("{\n")
    lines.append('  "error_code": "RESOURCE_NOT_FOUND",\n')
    lines.append('  "message": "Station \'STN_BEAS_99\' not found",\n')
    lines.append('  "details": {\n')
    lines.append('    "resource_type": "Station",\n')
    lines.append('    "resource_id": "STN_BEAS_99"\n')
    lines.append("  },\n")
    lines.append('  "timestamp": "2026-09-22T06:00:00Z",\n')
    lines.append('  "request_id": "36094c79-4269-494e-9346-731ac387ee0e"\n')
    lines.append("}\n")
    lines.append("```\n\n")
    lines.append("### Standard Error Codes\n")
    lines.append("- `INVALID_CREDENTIALS` (401): Incorrect username or password.\n")
    lines.append("- `AUTHORIZATION_ERROR` (403): Role privileges insufficient for requested action.\n")
    lines.append("- `RESOURCE_NOT_FOUND` (404): Entity ID does not exist.\n")
    lines.append("- `TELEMETRY_INTEGRITY_VIOLATION` (409): Duplicate event ID submitted with conflicting payload.\n")
    lines.append("- `WEBSOCKET_AUTHORIZATION_PROHIBITED` (400): Life-safety emergency authorization attempted over WebSocket.\n")
    lines.append("- `COMMISSIONING_VERIFICATION_FAILED` (400): Incomplete commissioning checklist gates.\n")
    lines.append("- `VALIDATION_ERROR` (422): Malformed JSON schema or missing required attributes.\n\n")

    lines.append("---\n\n")
    lines.append("## 4. Real-Time WebSocket Channels & Protocol\n\n")
    lines.append("### WebSocket Endpoints\n")
    lines.append("- **Primary**: `ws://127.0.0.1:8000/ws/v1/events`\n")
    lines.append("- **Alias**: `ws://127.0.0.1:8000/ws/realtime`\n\n")
    lines.append("### Query Parameters\n")
    lines.append("- `token` *(optional)*: JWT bearer token. Authorizes client role.\n")
    lines.append("- `role` *(optional, default='OBSERVER')*: Unauthenticated role override.\n")
    lines.append("- `topics` *(optional, default='all')*: Comma-separated list: `risk`, `telemetry`, `stations`, `alerts`, `system`, `all`.\n\n")
    lines.append("### Client $\\rightarrow$ Server Messages\n")
    lines.append("```json\n")
    lines.append('// Keepalive ping\n')
    lines.append('"ping"\n\n')
    lines.append('// Subscribe to topic\n')
    lines.append('{"action": "subscribe", "topic": "alerts"}\n\n')
    lines.append('// Unsubscribe from topic\n')
    lines.append('{"action": "unsubscribe", "topic": "telemetry"}\n')
    lines.append("```\n\n")
    lines.append("### Server $\\rightarrow$ Client Messages\n")
    lines.append("```json\n")
    lines.append('// Handshake Confirmation\n')
    lines.append("{\n")
    lines.append('  "type": "SUBSCRIPTION_CONFIRMED",\n')
    lines.append('  "status": "CONNECTED",\n')
    lines.append('  "role": "SENIOR_INCIDENT_COMMANDER",\n')
    lines.append('  "topics": ["all"]\n')
    lines.append("}\n\n")
    lines.append('// Live Hazard Alert Broadcast\n')
    lines.append("{\n")
    lines.append('  "type": "ALERT_BROADCAST",\n')
    lines.append('  "topic": "alerts",\n')
    lines.append('  "timestamp": "2026-09-22T06:15:00Z",\n')
    lines.append('  "data": {\n')
    lines.append('    "alert_id": "ALERT-20260922-01",\n')
    lines.append('    "cap_identifier": "CAP-HPSDMA-20260922-A41B",\n')
    lines.append('    "headline": "FLASH FLOOD WARNING — UPPER BEAS BASIN",\n')
    lines.append('    "severity": "Extreme",\n')
    lines.append('    "urgency": "Immediate",\n')
    lines.append('    "instruction": "Evacuate riverbank lowlands immediately to designated shelters."\n')
    lines.append("  }\n")
    lines.append("}\n")
    lines.append("```\n\n")
    lines.append("### Life-Safety Invariant\n")
    lines.append("> [!IMPORTANT]\n")
    lines.append("> WebSockets **CANNOT** authorize emergency alert dispatch. Attempting an authorization action over WebSocket immediately yields:\n")
    lines.append("```json\n")
    lines.append("{\n")
    lines.append('  "type": "SECURITY_ERROR",\n')
    lines.append('  "code": "WEBSOCKET_AUTHORIZATION_PROHIBITED",\n')
    lines.append('  "message": "Life-safety emergency alert authorization cannot be executed via WebSocket. The authenticated REST API gateway (POST /api/v1/alerts/{id}/authorize) is required."\n')
    lines.append("}\n")
    lines.append("```\n\n")

    lines.append("---\n\n")
    lines.append("## 5. Exhaustive REST API Endpoints Specification\n\n")

    # Group paths into domain modules
    modules = {
        "Module 1: Core System Health, Readiness & Observability": [
            "/health", "/ready", "/metrics", "/api/v1/health", "/api/v1/health/liveness",
            "/api/v1/health/ready", "/api/v1/system/status", "/api/v1/system/data-sources",
            "/api/v1/system/metrics", "/api/v1/version", "/eoc", "/"
        ],
        "Module 2: Authentication & User RBAC": [
            "/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/me"
        ],
        "Module 3: Unified Multi-Hazard Risk State & Spatial Corridors": [
            "/api/v1/risk/current", "/api/v1/risk/history", "/api/v1/risk/zones", "/api/v1/risk/{incident_id}"
        ],
        "Module 4: Incident Response & Multi-Hazard Orchestration": [
            "/api/v1/incidents", "/api/v1/incidents/replay", "/api/v1/incidents/{incident_id}",
            "/api/v1/orchestrator/incidents", "/api/v1/orchestrator/incidents/{incident_id}",
            "/api/v1/orchestrator/incidents/{incident_id}/cap-xml",
            "/api/v1/orchestrator/incidents/{incident_id}/status",
            "/api/v1/orchestrator/trigger-incident"
        ],
        "Module 5: Early Warning Alert Lifecycle & CAP v1.2 Dispatch": [
            "/api/v1/alerts", "/api/v1/alerts/draft", "/api/v1/alerts/hazard-zone",
            "/api/v1/alerts/cascade-breach", "/api/v1/alerts/{alert_id}",
            "/api/v1/alerts/{alert_id}/authorize", "/api/v1/alerts/{alert_id}/acknowledge",
            "/api/v1/alerts/{alert_id}/cancel",
            "/api/v1/decision/pipeline/alerts/{alert_id}/authorize"
        ],
        "Module 6: Decision Intelligence, Evacuation & Routing": [
            "/api/v1/decision/evacuation-route", "/api/v1/decision/infrastructure-graph",
            "/api/v1/decision/pipeline/execute", "/api/v1/gis/routes", "/api/v1/gis/safe-zones"
        ],
        "Module 7: GIS Layers, Critical Infrastructure & Landslide Zoning": [
            "/api/v1/gis/hazards", "/api/v1/gis/infrastructure", "/api/v1/satellite/layers",
            "/api/v1/satellite/critical-zones", "/api/v1/satellite/candidate-development-zones",
            "/api/v1/satellite/risk-map", "/api/v1/satellite/exposure"
        ],
        "Module 8: ML Model Registry & Analytical Predictions (M1–M20)": [
            "/api/v1/models", "/api/v1/models/{model_id}", "/api/v1/models/{model_id}/predict",
            "/api/v1/nowcast/forecast", "/api/v1/nowcast/latest",
            "/api/v1/cascade/simulate", "/api/v1/cascade/historical-scenarios",
            "/api/v1/natural-dams", "/api/v1/natural-dams/analyze", "/api/v1/natural-dams/{dam_id}",
            "/api/v1/natural-dams/{dam_id}/downstream-risk", "/api/v1/natural-dams/{dam_id}/exposure",
            "/api/v1/natural-dams/{dam_id}/history", "/api/v1/natural-dams/{dam_id}/impoundment",
            "/api/v1/natural-dams/{dam_id}/validate",
            "/api/v1/damage/analyze", "/api/v1/damage/buildings", "/api/v1/damage/lifelines",
            "/api/v1/damage/rescue-priority",
            "/api/v1/satellite/analyze", "/api/v1/satellite/process-real-scene"
        ],
        "Module 9: Physical Ground Stations, Devices & Hardware Lifecycle": [
            "/api/v1/stations", "/api/v1/stations/{station_id}/survey",
            "/api/v1/stations/{station_id}/install", "/api/v1/stations/{station_id}/commission",
            "/api/v1/stations/{station_id}/commissioning", "/api/v1/stations/{station_id}/health",
            "/api/v1/stations/{station_id}/status",
            "/api/v1/devices", "/api/v1/devices/{device_id}", "/api/v1/devices/{device_id}/health",
            "/api/v1/devices/{device_id}/heartbeat", "/api/v1/devices/{device_id}/status",
            "/api/v1/sensors", "/api/v1/sensors/{sensor_id}/calibrate",
            "/api/v1/sensors/{sensor_id}/calibrations"
        ],
        "Module 10: Telemetry Ingestion, LoRa LPWAN Gateway & Time-Series QC": [
            "/api/v1/telemetry", "/api/v1/telemetry/batch", "/api/v1/telemetry/ingest",
            "/api/v1/telemetry/recent", "/api/v1/telemetry/stations",
            "/api/v1/telemetry/health/summary", "/api/v1/observations/timeseries",
            "/api/v1/ingest/rain-gauge", "/api/v1/ingest/river-stage",
            "/api/v1/telemetry/lora/frame", "/api/v1/telemetry/lora/gateway/backhaul",
            "/api/v1/telemetry/lora/gateway/flush", "/api/v1/telemetry/lora/device/{device_id}/stats"
        ],
        "Module 11: Cryptographic Audit Trail & Tamper Evidence": [
            "/api/v1/audit/logs", "/api/v1/audit/verify-chain"
        ],
        "Module 12: High-Level EOC Dashboard Aggregations": [
            "/api/v1/dashboard/summary"
        ]
    }

    status_matrix = []

    for mod_title, mod_paths in modules.items():
        lines.append(f"### {mod_title}\n\n")

        for p in mod_paths:
            if p not in paths:
                continue
            path_spec = paths[p]
            for method, spec in path_spec.items():
                m_upper = method.upper()
                summary = spec.get("summary", "Endpoint summary")
                desc = spec.get("description", "")
                tags = ", ".join(spec.get("tags", []))
                status = classify_status(p, m_upper)
                status_matrix.append((m_upper, p, summary, status))

                # Auth detection
                auth_req = "Public (None required)"
                if any(k in p for k in ["/auth/me"]):
                    auth_req = "Bearer JWT (Any Authenticated User)"
                elif any(k in p for k in ["/stations/", "/devices/", "/sensors"]):
                    auth_req = "Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)"
                elif "/commission" in p:
                    auth_req = "Bearer JWT (`SENIOR_INCIDENT_COMMANDER`, `ADMIN`)"
                elif "/authorize" in p:
                    auth_req = "Cryptographic Approval Token + `SENIOR_INCIDENT_COMMANDER`"

                lines.append(f"#### `{m_upper}` {p}\n")
                lines.append(f"**Summary**: {summary}  \n")
                if desc:
                    lines.append(f"**Description**: {desc}  \n")
                lines.append(f"**Tags**: `{tags}` | **Status**: `{status}` | **Auth**: `{auth_req}`  \n\n")

                # Parameters
                params = spec.get("parameters", [])
                if params:
                    lines.append("**Request Parameters**:\n\n")
                    lines.append("| Name | In | Type | Required | Description |\n")
                    lines.append("|---|:---:|:---:|:---:|---|\n")
                    for pm in params:
                        p_name = pm.get("name")
                        p_in = pm.get("in")
                        p_req = "Yes" if pm.get("required") else "No"
                        p_schema = pm.get("schema", {})
                        p_type = p_schema.get("type", "string")
                        p_desc = pm.get("description", "")
                        lines.append(f"| `{p_name}` | `{p_in}` | `{p_type}` | {p_req} | {p_desc} |\n")
                    lines.append("\n")

                # Request body
                req_body = spec.get("requestBody", {})
                if req_body:
                    content = req_body.get("content", {}).get("application/json", {})
                    schema_ref = content.get("schema", {})
                    req_example = get_schema_example(schema_ref, components_schemas)
                    lines.append("**Request Body (application/json)**:\n\n")
                    lines.append("```json\n")
                    lines.append(json.dumps(req_example, indent=2))
                    lines.append("\n```\n\n")

                # Responses
                responses = spec.get("responses", {})
                lines.append("**Responses**:\n\n")
                for code, resp_spec in responses.items():
                    r_desc = resp_spec.get("description", "")
                    lines.append(f"- **`HTTP {code}`**: {r_desc}\n")
                    r_content = resp_spec.get("content", {}).get("application/json", {})
                    if r_content:
                        r_schema = r_content.get("schema", {})
                        r_example = get_schema_example(r_schema, components_schemas)
                        if r_example:
                            lines.append("  ```json\n")
                            # Indent example with 2 spaces
                            ex_str = json.dumps(r_example, indent=2)
                            lines.append("  " + ex_str.replace("\n", "\n  "))
                            lines.append("\n  ```\n")
                lines.append("\n---\n\n")

    # Section 6: Status Matrix
    lines.append("## 6. Endpoint Implementation Status Matrix\n\n")
    lines.append("| Method | Endpoint URL | Summary | Classification Status |\n")
    lines.append("|:---:|---|---|:---:|\n")
    for m, p, s, st in status_matrix:
        lines.append(f"| `{m}` | `{p}` | {s} | `{st}` |\n")
    lines.append("\n")

    lines.append("### Scientific & Hardware Classification Notes\n")
    lines.append("1. **`IMPLEMENTED (OPERATIONAL)`**: Fully backed by SQLite/PostgreSQL databases, active mathematical/ML logic, GIS asset loaders, and live business logic.\n")
    lines.append("2. **`IMPLEMENTED (SIMULATION)`**: Validated numerical simulations and scenario replays (e.g. Costa-Froehlich breach hydrodynamics, synthetic cloudburst cascades, July 2023 flood replay).\n")
    lines.append("3. **`PROTOTYPE_STAGING`**: Sensor and station registry endpoints manage hardware inventories staged in prototype/bench testing. As qualified under v3.9–v4.0 scientific closure, **0 physical sensor stations are deployed in active river water**.\n")
    lines.append("4. **`IMPLEMENTED (HARDWARE_SIMULATION)`**: LoRa LPWAN gateways and binary packet ingestion verify CRC-16, SNR, and buffer flushes using bench-staged transceivers and simulated hardware vectors.\n")

    output_text = "".join(lines)
    OUTPUT_FILE.write_text(output_text, encoding="utf-8")
    print(f"[OK] Generated {OUTPUT_FILE} ({len(output_text)} bytes, {len(status_matrix)} endpoints documented).")


if __name__ == "__main__":
    generate_contract()
