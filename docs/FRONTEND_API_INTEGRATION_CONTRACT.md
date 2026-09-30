# FLOODY SHIELD v4.0 — Master Frontend API & Integration Contract
> **System Version**: `4.0.0` (Production Hardened & Verified)  
> **Target Catchment**: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
> **Authority Invariant**: Life-safety alert broadcast strictly requires Senior Incident Commander cryptographic dual-authorization.  
> **Physical Network Maturity**: Physical IoT stations classified as `PROTOTYPE_STAGING` (0 active river water installations).  

---

## Table of Contents
1. [Frontend Environment Variables Specification](#1-frontend-environment-variables-specification)
2. [Authentication & RBAC Architecture](#2-authentication--rbac-architecture)
3. [Standard Error Response Specification](#3-standard-error-response-specification)
4. [Real-Time WebSocket Channels & Protocol](#4-real-time-websocket-channels--protocol)
5. [Exhaustive REST API Endpoints Specification](#5-exhaustive-rest-api-endpoints-specification)
   - [Module 1: Core System Health, Readiness & Observability](#module-1-core-system-health-readiness--observability)
   - [Module 2: Authentication & User RBAC](#module-2-authentication--user-rbac)
   - [Module 3: Unified Multi-Hazard Risk State & Spatial Corridors](#module-3-unified-multi-hazard-risk-state--spatial-corridors)
   - [Module 4: Incident Response & Multi-Hazard Orchestration](#module-4-incident-response--multi-hazard-orchestration)
   - [Module 5: Early Warning Alert Lifecycle & CAP v1.2 Dispatch](#module-5-early-warning-alert-lifecycle--cap-v12-dispatch)
   - [Module 6: Decision Intelligence, Evacuation & Routing](#module-6-decision-intelligence-evacuation--routing)
   - [Module 7: GIS Layers, Critical Infrastructure & Landslide Zoning](#module-7-gis-layers-critical-infrastructure--landslide-zoning)
   - [Module 8: ML Model Registry & Analytical Predictions (M1–M20)](#module-8-ml-model-registry--analytical-predictions-m1m20)
   - [Module 9: Physical Ground Stations, Devices & Hardware Lifecycle](#module-9-physical-ground-stations-devices--hardware-lifecycle)
   - [Module 10: Telemetry Ingestion, LoRa LPWAN Gateway & Time-Series QC](#module-10-telemetry-ingestion-lora-lpwan-gateway--time-series-qc)
   - [Module 11: Cryptographic Audit Trail & Tamper Evidence](#module-11-cryptographic-audit-trail--tamper-evidence)
   - [Module 12: High-Level EOC Dashboard Aggregations](#module-12-high-level-eoc-dashboard-aggregations)
6. [Endpoint Implementation Status Matrix](#6-endpoint-implementation-status-matrix)

---

## 1. Frontend Environment Variables Specification

For any modern frontend client (React, Vite, Next.js, or mobile Flutter app), configure the following environment variables in `.env`:

```ini
# FLOODY SHIELD Frontend Environment Variables
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000/ws/v1/events
VITE_APP_NAME="FLOODY SHIELD — Predict • Protect • Preserve"
VITE_APP_VERSION=4.0.0
VITE_ENVIRONMENT=development

# Geographic Focus (Upper Beas Catchment, Himachal Pradesh)
VITE_MAP_CENTER_LAT=32.2396
VITE_MAP_CENTER_LON=77.1887
VITE_MAP_DEFAULT_ZOOM=11
VITE_AOI_BBOX_SW_LAT=31.40
VITE_AOI_BBOX_SW_LON=76.80
VITE_AOI_BBOX_NE_LAT=32.45
VITE_AOI_BBOX_NE_LON=77.45

# Polling & Streaming Configuration
VITE_TELEMETRY_REFRESH_INTERVAL_MS=5000
VITE_WS_RECONNECT_BACKOFF_MS=3000
VITE_ALERT_POLL_INTERVAL_MS=10000

# External Map Tile Providers (Optional)
VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here
```

---

## 2. Authentication & RBAC Architecture

### Authentication Scheme
- **Protocol**: HTTP Bearer JWT (OAuth2 Password flow / JWT token).
- **Header**: `Authorization: Bearer <access_token>`
- **Token Lifespan**: Default 1440 minutes (24 hours).
- **Algorithm**: `HS256`.

### Role Hierarchy & Permissions
| Role | Level | Capabilities |
|---|:---:|---|
| `OBSERVER` | 1 | Read-only access to GIS layers, public telemetry, active incidents, and general system status. |
| `ANALYST` | 2 | Everything in `OBSERVER` plus: Run ML predictions, register stations, execute pipeline simulations, record field surveys, and create draft alerts. |
| `SENIOR_INCIDENT_COMMANDER` | 3 | Everything in `ANALYST` plus: **Cryptographic life-safety alert authorization**, station commissioning certification, and emergency escalation. |
| `ADMIN` | 4 | Full administrative access, device management, user administration, and system configuration. |

---

## 3. Standard Error Response Specification

All application exceptions follow the standardized domain error envelope:

```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Station 'STN_BEAS_99' not found",
  "details": {
    "resource_type": "Station",
    "resource_id": "STN_BEAS_99"
  },
  "timestamp": "2026-09-22T06:00:00Z",
  "request_id": "36094c79-4269-494e-9346-731ac387ee0e"
}
```

### Standard Error Codes
- `INVALID_CREDENTIALS` (401): Incorrect username or password.
- `AUTHORIZATION_ERROR` (403): Role privileges insufficient for requested action.
- `RESOURCE_NOT_FOUND` (404): Entity ID does not exist.
- `TELEMETRY_INTEGRITY_VIOLATION` (409): Duplicate event ID submitted with conflicting payload.
- `WEBSOCKET_AUTHORIZATION_PROHIBITED` (400): Life-safety emergency authorization attempted over WebSocket.
- `COMMISSIONING_VERIFICATION_FAILED` (400): Incomplete commissioning checklist gates.
- `VALIDATION_ERROR` (422): Malformed JSON schema or missing required attributes.

---

## 4. Real-Time WebSocket Channels & Protocol

### WebSocket Endpoints
- **Primary**: `ws://127.0.0.1:8000/ws/v1/events`
- **Alias**: `ws://127.0.0.1:8000/ws/realtime`

### Query Parameters
- `token` *(optional)*: JWT bearer token. Authorizes client role.
- `role` *(optional, default='OBSERVER')*: Unauthenticated role override.
- `topics` *(optional, default='all')*: Comma-separated list: `risk`, `telemetry`, `stations`, `alerts`, `system`, `all`.

### Client $\rightarrow$ Server Messages
```json
// Keepalive ping
"ping"

// Subscribe to topic
{"action": "subscribe", "topic": "alerts"}

// Unsubscribe from topic
{"action": "unsubscribe", "topic": "telemetry"}
```

### Server $\rightarrow$ Client Messages
```json
// Handshake Confirmation
{
  "type": "SUBSCRIPTION_CONFIRMED",
  "status": "CONNECTED",
  "role": "SENIOR_INCIDENT_COMMANDER",
  "topics": ["all"]
}

// Live Hazard Alert Broadcast
{
  "type": "ALERT_BROADCAST",
  "topic": "alerts",
  "timestamp": "2026-09-22T06:15:00Z",
  "data": {
    "alert_id": "ALERT-20260922-01",
    "cap_identifier": "CAP-HPSDMA-20260922-A41B",
    "headline": "FLASH FLOOD WARNING — UPPER BEAS BASIN",
    "severity": "Extreme",
    "urgency": "Immediate",
    "instruction": "Evacuate riverbank lowlands immediately to designated shelters."
  }
}
```

### Life-Safety Invariant
> [!IMPORTANT]
> WebSockets **CANNOT** authorize emergency alert dispatch. Attempting an authorization action over WebSocket immediately yields:
```json
{
  "type": "SECURITY_ERROR",
  "code": "WEBSOCKET_AUTHORIZATION_PROHIBITED",
  "message": "Life-safety emergency alert authorization cannot be executed via WebSocket. The authenticated REST API gateway (POST /api/v1/alerts/{id}/authorize) is required."
}
```

---

## 5. Exhaustive REST API Endpoints Specification

### Module 1: Core System Health, Readiness & Observability

#### `GET` /health
**Summary**: Microservice liveness check  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /ready
**Summary**: Microservice readiness check  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /metrics
**Summary**: Prometheus metrics exporter  
**Tags**: `` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/health
**Summary**: Check system health, model readiness, and API key pools  
**Description**: Returns comprehensive health check of all core models, satellite layers,
and external remote sensing API key rotation pools. Backward compatible with v2.1.0 contract.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/health/liveness
**Summary**: Lightweight liveness probe  
**Description**: Returns lightweight liveness status for container orchestration.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/health/ready
**Summary**: Readiness probe verifying dependencies  
**Description**: Checks database connectivity, model registry, and data lake catalog.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/system/status
**Summary**: Operational system status summary  
**Description**: Exposes high-level subsystem availability without revealing secrets or paths.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/system/data-sources
**Summary**: Telemetry & Earth Observation data source statuses  
**Description**: Returns operational availability, freshness, and sync state of external and ground telemetry sources.
Transparently reports whether each provider is LIVE, PROXY/SIMULATED, or OFFLINE.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/system/metrics
**Summary**: Prometheus metrics exposition endpoint  
**Description**: Returns Prometheus-formatted metrics.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/version
**Summary**: Application version metadata  
**Description**: Returns system version and scientific level declaration.  
**Tags**: `Health & System` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /eoc
**Summary**: Emergency Operations Center Command Dashboard  
**Description**: Renders the full-screen FLOODY SHIELD Emergency Operations Center (EOC) Command Dashboard.  
**Tags**: `` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /
**Summary**: Root dashboard overview  
**Description**: Renders basic HTML landing page for FLOODY SHIELD microservice.  
**Tags**: `` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

### Module 2: Authentication & User RBAC

#### `POST` /api/v1/auth/register
**Summary**: Register new operational user  
**Description**: Registers a new user account with hashed password and role assignment.  
**Tags**: `Authentication & Access Control` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "username": "username",
  "email": "User email address",
  "password": "password",
  "role": "OBSERVER",
  "full_name": "full_name",
  "agency": "HPSDMA / Civil Defense"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/auth/login
**Summary**: Authenticate user and obtain JWT token  
**Description**: Validates user credentials and returns signed JWT access token.  
**Tags**: `Authentication & Access Control` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "username": "username",
  "password": "password"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/auth/me
**Summary**: Get authenticated user identity  
**Description**: Returns profile of currently authenticated user.  
**Tags**: `Authentication & Access Control` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Bearer JWT (Any Authenticated User)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

### Module 3: Unified Multi-Hazard Risk State & Spatial Corridors

#### `GET` /api/v1/risk/current
**Summary**: Get authoritative current basin risk state  
**Tags**: `Unified Multi-Hazard Risk State` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `location_name` | `query` | `string` | No | Specific corridor/location filter |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/risk/history
**Summary**: Query historical risk state evaluations  
**Tags**: `Unified Multi-Hazard Risk State` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `query` | `string` | No | Filter by incident UUID |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/risk/zones
**Summary**: List spatial risk zone corridors  
**Tags**: `Unified Multi-Hazard Risk State` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `risk_state_id` | `query` | `string` | No | Filter by RiskState UUID |
| `risk_level` | `query` | `string` | No | Filter by risk tier (CRITICAL, HIGH, MODERATE, LOW) |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/risk/{incident_id}
**Summary**: Get consolidated risk state for a specific incident  
**Tags**: `Unified Multi-Hazard Risk State` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 4: Incident Response & Multi-Hazard Orchestration

#### `POST` /api/v1/incidents
**Summary**: Register or trigger new multi-hazard incident  
**Description**: Registers a new active civil defense incident.  
**Tags**: `Incident Management & Provenance History` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "incident_type": "e.g. NATURAL_DAM_BREACH, CLOUDBURST_FLASH_FLOOD, LANDSLIDE_DAM",
  "severity_level": "CRITICAL",
  "trigger_source": "SATELLITE_SYNTHESIS",
  "trigger_location": "e.g. Larji_Sainj_Confluence, Aut_Gorge",
  "latitude": "latitude",
  "longitude": "longitude",
  "dam_height_m": "dam_height_m",
  "impounded_volume_m3": "impounded_volume_m3",
  "rainfall_rate_mmh": "rainfall_rate_mmh",
  "summary": "summary"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/incidents
**Summary**: List incidents with pagination  
**Description**: Returns paginated list of operational incidents.  
**Tags**: `Incident Management & Provenance History` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `status` | `query` | `string` | No | Filter by status (ACTIVE, CONTAINED, RESOLVED, EXERCISE) |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/incidents/replay
**Summary**: Trigger historical disaster scenario replay (mode=REPLAY)  
**Description**: Executes a historical event reconstruction through the complete pipeline.
All outputs marked EXERCISE / REPLAY. Zero external alert broadcasts.  
**Tags**: `Incident Management & Provenance History` | **Status**: `IMPLEMENTED (SIMULATION)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "scenario_name": "July_2023_Upper_Beas_Compound_Flood",
  "rainfall_intensity_mmh": 85.0,
  "dam_height_m": 40.0,
  "impounded_volume_m3": 12000000.0,
  "river_water_level_m": 8.2
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/incidents/{incident_id}
**Summary**: Get full incident timeline, models, alerts, and audit provenance  
**Description**: Returns the complete end-to-end incident history:
Incident Details -> Associated Model Runs -> Synthesized Risk States -> Evacuation Routes -> Draft/Dispatched Alerts -> Audit Trail.  
**Tags**: `Incident Management & Provenance History` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/orchestrator/incidents
**Summary**: List all active and historical incidents  
**Tags**: `Incident Response & Orchestration` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/orchestrator/incidents/{incident_id}
**Summary**: Get comprehensive incident briefing  
**Tags**: `Incident Response & Orchestration` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/orchestrator/incidents/{incident_id}/cap-xml
**Summary**: Download official CAP v1.2 XML payload  
**Tags**: `Incident Response & Orchestration` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/orchestrator/incidents/{incident_id}/status
**Summary**: Update incident status and append audit note  
**Tags**: `Incident Response & Orchestration` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "new_status": "new_status",
  "notes": ""
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/orchestrator/trigger-incident
**Summary**: Trigger autonomous end-to-end incident response  
**Description**: Executes complete autonomous pipeline:
M12 Dam Breach Simulation -> Exposure Overlay -> M15/M16 Safe Route Solving ->
M20 Rescue Prioritization -> NDMA Sachet CAP v1.2 Bilingual Alert Generation.  
**Tags**: `Incident Response & Orchestration` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "incident_type": "NATURAL_DAM_BREACH",
  "severity_level": "CRITICAL",
  "trigger_source": "SATELLITE_SYNTHESIS",
  "trigger_location": "Larji_Sainj_Confluence",
  "dam_height_m": 35.0,
  "impounded_volume_m3": 8500000.0,
  "rainfall_rate_mmh": 65.0,
  "simulate_nh3_closure": true,
  "status": "ACTIVE",
  "custom_id": "Optional custom incident ID"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 5: Early Warning Alert Lifecycle & CAP v1.2 Dispatch

#### `GET` /api/v1/alerts
**Summary**: List alerts with filtering  
**Description**: Returns paginated list of alerts.  
**Tags**: `Early Warning & CAP Alerts` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `status` | `query` | `string` | No | Filter by status (e.g. PENDING_APPROVAL, DISPATCHED, RESOLVED) |
| `incident_id` | `query` | `string` | No | Filter by incident ID |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/alerts/draft
**Summary**: Create early warning alert draft (PENDING_APPROVAL)  
**Description**: Creates a new CAP alert record in PENDING_APPROVAL status.
Cannot be dispatched to the public without explicit Commander authorization.  
**Tags**: `Early Warning & CAP Alerts` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "incident_id": "Associated Incident UUID",
  "headline": "Alert headline in English",
  "description": "Full multi-hazard scenario narrative",
  "instruction": "Protective civil defense actions",
  "area_desc": "Target geographic corridor",
  "severity": "Extreme",
  "urgency": "Immediate",
  "certainty": "Observed",
  "polygon_geojson": "GeoJSON polygon string"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/alerts/hazard-zone
**Summary**: Generate targeted CAP v1.2 alert for critical hazard zone  
**Description**: Generates targeted Section 36 high-hazard warning for sirens and local geofenced push notifications.  
**Tags**: `Emergency Alerts & CAP` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "zone_name": "NH-3 Aut-Larji Riverbed Ribbon",
  "hazard_type": "Compound Flood & Debris Flow",
  "coordinates_polygon": [
    [
      31.715,
      77.145
    ],
    [
      31.76,
      77.17
    ],
    [
      31.75,
      77.195
    ],
    [
      31.715,
      77.145
    ]
  ],
  "format": "json"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/alerts/cascade-breach
**Summary**: Generate bilingual CAP v1.2 alert for landslide dam breach  
**Description**: Simulates dam breach hydrograph and produces an ITU-T X.1303 / NDMA Sachet
bilingual CAP v1.2 alert payload (English and Hindi).  
**Tags**: `Emergency Alerts & CAP` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "dam_location": "Larji_Sainj_Confluence",
  "dam_height_m": 35.0,
  "impounded_volume_m3": 8500000.0,
  "status": "Actual",
  "format": "json"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/alerts/{alert_id}
**Summary**: Get alert details and CAP v1.2 XML  
**Description**: Returns alert record details or raw OASIS CAP v1.2 XML document.  
**Tags**: `Early Warning & CAP Alerts` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `alert_id` | `path` | `string` | Yes |  |
| `format` | `query` | `string` | No | Output format: json or xml |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/alerts/{alert_id}/authorize
**Summary**: Commander authorization and CAP dispatch  
**Description**: Statutory Commander Sign-off:
Validates Senior Incident Commander authority and approval token,
transitions status to DISPATCHED, renders OASIS CAP v1.2 XML, and logs to tamper-evident audit.  
**Tags**: `Early Warning & CAP Alerts` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Cryptographic Approval Token + `SENIOR_INCIDENT_COMMANDER``  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `alert_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "actor_id": "Incident Commander identifier",
  "actor_role": "SENIOR_INCIDENT_COMMANDER",
  "approval_token": "Cryptographic authorization token"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/alerts/{alert_id}/acknowledge
**Summary**: Acknowledge alert reception  
**Description**: Records emergency agency reception acknowledgement.  
**Tags**: `Early Warning & CAP Alerts` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `alert_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "recipient_id": "Agency or operator identifier",
  "channel": "EOC_DASHBOARD",
  "notes": "Field action notes"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/alerts/{alert_id}/cancel
**Summary**: Commander cancellation / all-clear  
**Description**: Cancels an active alert. Strictly restricted to SENIOR_INCIDENT_COMMANDER or ADMIN.  
**Tags**: `Early Warning & CAP Alerts` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `alert_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "actor_id": "Commander identifier",
  "actor_role": "SENIOR_INCIDENT_COMMANDER",
  "reason": "Threat abated / All-clear issued"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/decision/pipeline/alerts/{alert_id}/authorize
**Summary**: Senior Incident Commander CAP Alert Authorization  
**Description**: Cryptographically authorizes and transitions a CAP v1.2 emergency alert from
PENDING_APPROVAL to DISPATCHED. Generates an immutable audit log entry.  
**Tags**: `Hazard Decision Pipeline` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Cryptographic Approval Token + `SENIOR_INCIDENT_COMMANDER``  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `alert_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "actor_id": "ID of authorizing official",
  "actor_role": "Role must be SENIOR_INCIDENT_COMMANDER",
  "approval_token": "Cryptographic commander sign-off token"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 6: Decision Intelligence, Evacuation & Routing

#### `POST` /api/v1/decision/evacuation-route
**Summary**: Find safest risk-weighted evacuation path  
**Description**: Computes safest evacuation corridor around active flood and landslide hazards using Model M16.
If NH-3 is flooded/blocked, calculates bypass route via safer higher-elevation alignments.  
**Tags**: `Decision Intelligence & Evacuation` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "origin_node": "V_BHUNTAR",
  "destination_node": "S_KULLU_COLLEGE",
  "simulate_nh3_closure": true
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/decision/infrastructure-graph
**Summary**: Get Beas corridor infrastructure network summary  
**Description**: Returns summary of graph nodes, monitored bridges, roads, and designated shelters.  
**Tags**: `Decision Intelligence & Evacuation` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `POST` /api/v1/decision/pipeline/execute
**Summary**: Execute end-to-end multi-hazard decision pipeline  
**Description**: Executes full hazard chain (M1-M20), produces decision briefing,
and drafts CAP v1.2 alert in PENDING_APPROVAL status.  
**Tags**: `Hazard Decision Pipeline` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "incident_id": "Optional incident ID",
  "location_name": "Larji_Sainj_Confluence",
  "rainfall_intensity_mmh": 65.0,
  "dam_height_m": 35.0,
  "impounded_volume_m3": 8500000.0,
  "simulate_nh3_closure": true
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/gis/routes
**Summary**: Get evacuation corridors GeoJSON  
**Description**: Returns Model M16 hazard-weighted dynamic evacuation paths.  
**Tags**: `GIS & Spatial Intelligence` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `incident_id` | `query` | `string` | No | Optional incident filter |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/gis/safe-zones
**Summary**: Get designated safe shelters GeoJSON  
**Description**: Returns high-elevation emergency assembly shelters and relief grounds.  
**Tags**: `GIS & Spatial Intelligence` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `min_elevation_m` | `query` | `number` | No | Minimum shelter elevation above MSL |
| `min_capacity` | `query` | `integer` | No | Minimum headcount capacity |
| `bbox` | `query` | `string` | No | Optional bounding box filter minx,miny,maxx,maxy |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 7: GIS Layers, Critical Infrastructure & Landslide Zoning

#### `GET` /api/v1/gis/hazards
**Summary**: Get multi-hazard risk zones GeoJSON  
**Description**: Returns spatial hazard boundary polygons formatted as GeoJSON FeatureCollection.  
**Tags**: `GIS & Spatial Intelligence` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `zone_type` | `query` | `string` | No | Filter by zone type (e.g. INUNDATION_ZONE, LANDSLIDE_RUNOUT) |
| `bbox` | `query` | `string` | No | Optional bounding box filter minx,miny,maxx,maxy |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/gis/infrastructure
**Summary**: Get critical infrastructure assets GeoJSON  
**Description**: Returns NH-3 highway corridors, tunnels, bridges, and hydropower facilities.  
**Tags**: `GIS & Spatial Intelligence` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `bbox` | `query` | `string` | No | Optional bounding box filter minx,miny,maxx,maxy |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/satellite/layers
**Summary**: List generated GIS satellite hazard rasters  
**Description**: Returns inventory of all available GeoTIFF rasters and GIS layers.  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/satellite/critical-zones
**Summary**: Get Section 36 high-hazard restricted development zones  
**Description**: Returns GeoJSON feature collection of high-hazard zones where development
must be prohibited under Section 36 of Disaster Management Act 2005.  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/satellite/candidate-development-zones
**Summary**: Get candidate safe development zones with statutory disclaimer  
**Description**: Returns candidate safe development zones filtered by multi-hazard risk,
gentle slope, safe distance from active flood channels, and stable lithology.
Includes legally mandatory planning disclaimer.  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/satellite/risk-map
**Summary**: Get multi-hazard risk map metadata and bounds  
**Description**: Retrieves spatial extent and statistics for the compound multi-hazard risk map.  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/satellite/exposure
**Summary**: Get critical infrastructure and population exposure summary  
**Description**: Returns infrastructure exposure analysis calculated by Model M13/M14.  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

### Module 8: ML Model Registry & Analytical Predictions (M1–M20)

#### `GET` /api/v1/models
**Summary**: List all registered models in the 20-model ecosystem  
**Description**: Returns catalog of models with their authoritative evidence status and version.  
**Tags**: `Model Registry & Inference (M1-M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/models/{model_id}
**Summary**: Get full model card and provenance metadata  
**Description**: Retrieves full specification, training period, validation evidence, and known limitations.  
**Tags**: `Model Registry & Inference (M1-M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `model_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/models/{model_id}/predict
**Summary**: Run inference on an analytical model via its adapter  
**Description**: Invokes the model adapter for the specified model ID.  
**Tags**: `Model Registry & Inference (M1-M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `model_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "features": null
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/nowcast/forecast
**Summary**: Generate Lagrangian short-term precipitation nowcast  
**Description**: Generates 15-minute to 120-minute lead time spatial precipitation nowcast.  
**Tags**: `Atmospheric Nowcasting (M1)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "catchment_name": "Upper_Beas_Catchment",
  "current_max_rain_mmh": 78.5,
  "storm_motion_dx_kmh": 14.0,
  "storm_motion_dy_kmh": -8.0
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/nowcast/latest
**Summary**: Get latest active atmospheric cloudburst forecast  
**Description**: Returns the most recent nowcast cycle for the Upper Beas mountain basin.  
**Tags**: `Atmospheric Nowcasting (M1)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `POST` /api/v1/cascade/simulate
**Summary**: Simulate landslide dam overtopping breach and downstream wave arrival  
**Description**: Computes breach outflow hydrograph (peak discharge Q_p and breach formation time t_f)
and downstream attenuation along Beas River corridor reaches (Aut, Thalout, Pandoh Dam, Mandi).  
**Tags**: `Cascade & Dam Breach` | **Status**: `IMPLEMENTED (SIMULATION)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "dam_location": "Larji_Sainj_Confluence",
  "dam_height_m": 35.0,
  "impounded_volume_m3": 8500000.0,
  "normal_river_discharge_m3s": 450.0
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/cascade/historical-scenarios
**Summary**: List historical Himalayan dam breach benchmarks  
**Description**: Returns historical benchmarks for validation (e.g. Pareechu 2005, Rishiganga 2021).  
**Tags**: `Cascade & Dam Breach` | **Status**: `IMPLEMENTED (SIMULATION)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/natural-dams
**Summary**: Get all detected natural dam candidates as GeoJSON  
**Description**: Returns OGC GeoJSON FeatureCollection of all candidate points and properties.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `POST` /api/v1/natural-dams/analyze
**Summary**: Trigger multi-temporal natural dam detection across river network  
**Description**: Runs end-to-end multi-evidence detection over satellite passes and river network.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "corridor_name": "Upper_Beas_Basin",
  "include_sar_radar": true,
  "forecast_rain_24h_mm": 80.0
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/natural-dams/{dam_id}
**Summary**: Get detailed profile, multi-evidence indicators, and explainability  
**Description**: Returns exhaustive diagnostic profile and 8-point evidence audit trail for a candidate.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `dam_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/natural-dams/{dam_id}/downstream-risk
**Summary**: Get outburst failure potential and wave arrival times  
**Description**: Returns geotechnical breach risk tier and hydraulic surge estimates.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `dam_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/natural-dams/{dam_id}/exposure
**Summary**: Get downstream population and infrastructure exposure  
**Description**: Returns exposed settlements, population count, roads, bridges, and institutions.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `dam_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/natural-dams/{dam_id}/history
**Summary**: Get multi-temporal evolution timeline  
**Description**: Returns observation timeline tracking candidate emergence, impoundment growth, and stability.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `dam_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/natural-dams/{dam_id}/impoundment
**Summary**: Get upstream impounded water extent and reservoir metrics  
**Description**: Returns upstream reservoir geometry polygon, surface area, and estimated volume.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `dam_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/natural-dams/{dam_id}/validate
**Summary**: Submit authority or field validation for candidate  
**Description**: Submits ground-truth validation (Confirmed, False Detection, etc.)
and updates candidate state in the registry.  
**Tags**: `Natural River Dam Detection` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `dam_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "status": "Authority validation classification",
  "validator_role": "HPSDMA_District_Emergency_Officer",
  "notes": "Field inspection or aerial drone observation notes",
  "evidence_type": "GROUND_INSPECTION",
  "photo_url": "URL or URI to georeferenced evidence photo"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/damage/analyze
**Summary**: Trigger satellite damage proxy mapping over affected corridor  
**Description**: Runs Model M20 damage proxy mapping combining SAR coherence loss and optical NDBI change.  
**Tags**: `Post-Disaster Damage Assessment (M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "catchment_name": "Upper_Beas_Basin",
  "event_timestamp_utc": "2026-09-20T08:00:00Z",
  "include_sar_coherence": true
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/damage/buildings
**Summary**: Get Copernicus EMS assessed building footprints as GeoJSON  
**Description**: Returns GeoJSON FeatureCollection of all classified buildings with damage grades.  
**Tags**: `Post-Disaster Damage Assessment (M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/damage/lifelines
**Summary**: Get compromised road networks and severed bridges  
**Description**: Returns assessment of severed highway segments (NH-3), overtopped bridges, and cut-off towns.  
**Tags**: `Post-Disaster Damage Assessment (M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/damage/rescue-priority
**Summary**: Get ranked NDRF/SDRF Rescue Prioritization Index list  
**Description**: Returns prioritized rescue target list based on structural damage, population, and isolation.  
**Tags**: `Post-Disaster Damage Assessment (M20)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `POST` /api/v1/satellite/analyze
**Summary**: Run multi-sensor hazard inference on satellite scene  
**Description**: Performs multi-sensor satellite hazard inference fusing Sentinel-2 MSI,
Sentinel-1 SAR C-Band radar, and Copernicus GLO-30 DEM.  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "scene_id": "S2_L2A_UPPER_BEAS_20230710",
  "bbox": [
    77.05,
    31.65,
    77.3,
    32.05
  ],
  "include_sar_radar": true,
  "uncertainty_level": 0.95
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/satellite/process-real-scene
**Summary**: Execute end-to-end disaster intelligence pipeline on real satellite scenes  
**Description**: Executes the unified end-to-end geospatial disaster intelligence pipeline:
  REAL SENTINEL-1/2 SCENE -> Quality/Cloud Audit -> Preprocessing & DEM Alignment
  -> 9-Channel Feature Stack -> Parallel 4-Branch Extraction (Flood, Landslide, River Change, Development)
  -> Natural Dam Detection -> Multi-Hazard Fusion -> GeoTIFF + GeoJSON -> PostGIS Sync -> Live Leaflet Map  
**Tags**: `Satellite Intelligence & Zoning` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 9: Physical Ground Stations, Devices & Hardware Lifecycle

#### `GET` /api/v1/stations
**Summary**: List physical telemetry stations  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_type` | `query` | `string` | No |  |
| `is_active` | `query` | `string` | No |  |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/stations
**Summary**: Register a physical station (Admin/Analyst)  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "station_id": "Unique Station Code, e.g. STN_KULLU_01",
  "name": "Descriptive station name",
  "station_type": "MET_HYDRO_IOT",
  "latitude": 42.5,
  "longitude": 42.5,
  "elevation_m": "Station elevation in meters",
  "river_basin": "Upper Beas Basin",
  "status": "PLANNED"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/stations/{station_id}/survey
**Summary**: Record station field survey (Analyst/Admin)  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "surveyor_name": "Name or identifier of field surveyor",
  "survey_notes": "Observations regarding terrain, line of sight, power",
  "coordinates_verified": true,
  "elevation_m": "Measured altitude in meters",
  "site_suitability_score": "Suitability score 0-100",
  "photos_metadata": "Metadata of survey site photographs"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/stations/{station_id}/install
**Summary**: Record station physical installation (Analyst/Admin)  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "installer_name": "Field technician / installation contractor",
  "hardware_manifest": "Hardware manifest (sensors, solar panel, mast)",
  "firmware_version": "Initial node firmware version",
  "notes": "Installation notes"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/stations/{station_id}/commission
**Summary**: Verify checklist and commission station (Senior Commander/Admin)  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "commissioner_name": "Senior Engineer / Commissioning Authority",
  "sensor_check": true,
  "calibration_check": true,
  "lora_check": true,
  "battery_check": true,
  "timestamp_check": true,
  "remarks": "Commissioning authority sign-off remarks"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/stations/{station_id}/commissioning
**Summary**: Get station commissioning status and record  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/stations/{station_id}/health
**Summary**: Evaluate station operational health  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `PATCH` /api/v1/stations/{station_id}/status
**Summary**: Update station lifecycle status  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "status": "New station lifecycle status (PLANNED, SURVEYED, INSTALLED, COMMISSIONED, ACTIVE, DEGRADED, OFFLINE, RETIRED)"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/devices
**Summary**: List field IoT devices  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `query` | `string` | No |  |
| `status` | `query` | `string` | No |  |
| `device_type` | `query` | `string` | No |  |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/devices
**Summary**: Register a field device (Admin/Analyst)  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "device_id": "Unique device ID, e.g. DEV_AUT_PWP_01",
  "station_id": "Associated station ID",
  "serial_number": "Hardware serial number / IMEI",
  "device_type": "Device classification (LORA_NODE, CELLULAR_GATEWAY)",
  "manufacturer": "FloodyShield-Hardware",
  "firmware_version": "1.0.0",
  "protocol": "LORAWAN",
  "status": "PLANNED",
  "latitude": "latitude",
  "longitude": "longitude",
  "elevation": "elevation"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/devices/{device_id}
**Summary**: Get device detail  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `device_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/devices/{device_id}/health
**Summary**: Evaluate device operational health  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `device_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/devices/{device_id}/heartbeat
**Summary**: Record device heartbeat and radio telemetry  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `device_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "battery_voltage": "Voltage in Volts",
  "battery_percentage": "Battery percentage (0-100)",
  "rssi_dbm": "Received Signal Strength in dBm",
  "snr_db": "Signal-to-Noise Ratio in dB",
  "firmware_version": "firmware_version",
  "error_flags": 0
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `PATCH` /api/v1/devices/{device_id}/status
**Summary**: Update device lifecycle status  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `device_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "status": "New lifecycle status (PLANNED, INSTALLED, ACTIVE, DEGRADED, OFFLINE, RETIRED)"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/sensors
**Summary**: List sensors  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `device_id` | `query` | `string` | No |  |
| `sensor_type` | `query` | `string` | No |  |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/sensors
**Summary**: Register a sensor attached to a device  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Body (application/json)**:

```json
{
  "sensor_id": "Unique sensor ID, e.g. SNS_AUT_RAIN_01",
  "device_id": "Parent device ID",
  "sensor_type": "RAIN_GAUGE, WATER_LEVEL, WATER_FLOW, SOIL_MOISTURE, PORE_WATER_PRESSURE, TILT, VIBRATION, TEMPERATURE, HUMIDITY, BATTERY",
  "unit": "Unit of measurement (mm/h, m, m3/s, %, kPa, deg, mm/s2, C, V)",
  "measurement_range_min": "measurement_range_min",
  "measurement_range_max": "measurement_range_max",
  "sampling_interval_sec": 60
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/sensors/{sensor_id}/calibrate
**Summary**: Add calibration record for a sensor  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `sensor_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "calibrated_by": "Name or ID of calibration technician/authority",
  "standard_reference": "Calibration reference instrument/traceability ID",
  "zero_offset": 0.0,
  "scale_factor": 1.0,
  "notes": "Technician notes"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/sensors/{sensor_id}/calibrations
**Summary**: Add calibration record for a sensor (alias)  
**Tags**: `Physical Stations, Devices & Sensors` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Bearer JWT (`ANALYST`, `SENIOR_INCIDENT_COMMANDER`, `ADMIN`)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `sensor_id` | `path` | `string` | Yes |  |

**Request Body (application/json)**:

```json
{
  "calibrated_by": "Name or ID of calibration technician/authority",
  "standard_reference": "Calibration reference instrument/traceability ID",
  "zero_offset": 0.0,
  "scale_factor": 1.0,
  "notes": "Technician notes"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 10: Telemetry Ingestion, LoRa LPWAN Gateway & Time-Series QC

#### `POST` /api/v1/telemetry
**Summary**: Ingest single field telemetry packet with strict idempotency  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "source_id": "UPPER_BEAS_IOT",
  "station_id": "Unique station ID",
  "device_id": "Physical device ID",
  "sensor_id": "Physical sensor ID",
  "observed_at": "ISO-8601 observation timestamp",
  "received_at": "ISO-8601 gateway reception timestamp",
  "measurement_type": "RAINFALL, WATER_LEVEL, PORE_WATER_PRESSURE, TILT, DISPLACEMENT, etc.",
  "value": 42.5,
  "unit": "Measurement unit (mm/h, m, kPa, deg, etc.)",
  "sequence_number": "Device packet increment counter",
  "firmware_version": "Device firmware version",
  "quality_hint": "Optional raw sensor quality code",
  "provenance": "REAL",
  "environment": "FIELD",
  "qc_flags": "Initial QC flags or error tags"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/telemetry/batch
**Summary**: Ingest a batch of field telemetry packets  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "packets": [
    {
      "source_id": "UPPER_BEAS_IOT",
      "station_id": "Unique station ID",
      "device_id": "Physical device ID",
      "sensor_id": "Physical sensor ID",
      "observed_at": "ISO-8601 observation timestamp",
      "received_at": "ISO-8601 gateway reception timestamp",
      "measurement_type": "RAINFALL, WATER_LEVEL, PORE_WATER_PRESSURE, TILT, DISPLACEMENT, etc.",
      "value": 42.5,
      "unit": "Measurement unit (mm/h, m, kPa, deg, etc.)",
      "sequence_number": "Device packet increment counter",
      "firmware_version": "Device firmware version",
      "quality_hint": "Optional raw sensor quality code",
      "provenance": "REAL",
      "environment": "FIELD",
      "qc_flags": "Initial QC flags or error tags"
    }
  ]
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/telemetry/ingest
**Summary**: Ingest and quality-audit real-time ground sensor reading  
**Description**: Ingests sensor reading, verifies physical plausibility, and flags telemetry anomalies.  
**Tags**: `IoT Telemetry & Quality Gating (M9)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "station_id": "Unique station identifier (e.g., ST_AUT_01)",
  "sensor_type": "Sensor type",
  "value": 42.5,
  "timestamp_utc": "ISO-8601 observation timestamp"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/telemetry/recent
**Summary**: Get recent verified telemetry readings  
**Description**: Retrieves recent stream of telemetry readings with quality scores.  
**Tags**: `IoT Telemetry & Quality Gating (M9)` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `limit` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/telemetry/stations
**Summary**: List all registered IoT ground telemetry stations  
**Description**: Returns active hydrological, meteorological, and geotechnical monitoring stations.  
**Tags**: `IoT Telemetry & Quality Gating (M9)` | **Status**: `PROTOTYPE_STAGING` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

#### `GET` /api/v1/telemetry/health/summary
**Summary**: Get aggregated field telemetry and hardware health summary  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `window` | `query` | `string` | No | Aggregation time window |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/observations/timeseries
**Summary**: Query aggregated time-series telemetry  
**Description**: Returns time-series observations with unit safety, filtering, and optional statistical aggregation.  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `station_id` | `query` | `string` | No |  |
| `device_id` | `query` | `string` | No |  |
| `sensor_id` | `query` | `string` | No |  |
| `measurement_type` | `query` | `string` | No |  |
| `quality` | `query` | `string` | No |  |
| `provenance` | `query` | `string` | No |  |
| `environment` | `query` | `string` | No |  |
| `start` | `query` | `string` | No |  |
| `end` | `query` | `string` | No |  |
| `aggregation` | `query` | `string` | No |  |
| `interval` | `query` | `string` | No |  |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/ingest/rain-gauge
**Summary**: Ingest rainfall telemetry with M9 quality gating  
**Description**: Ingests AWS/IMD rain gauge telemetry, runs quality checks, and saves to database.  
**Tags**: `Telemetry Ingestion & Quality Gating` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "station_id": "Unique sensor station identifier, e.g. STN_KULLU_01",
  "timestamp": "2026-09-22T06:00:00Z",
  "rainfall_rate_mmh": 42.5,
  "accumulated_24h_mm": "24h cumulative rainfall"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/ingest/river-stage
**Summary**: Ingest CWC river stage telemetry with M9 quality gating  
**Description**: Ingests CWC river gauge telemetry, runs quality checks, and saves to database.  
**Tags**: `Telemetry Ingestion & Quality Gating` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "station_id": "Unique sensor station identifier, e.g. STN_KULLU_01",
  "timestamp": "2026-09-22T06:00:00Z",
  "water_level_m": 42.5,
  "discharge_m3s": "Estimated instantaneous discharge",
  "danger_level_m": "CWC danger mark threshold"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/telemetry/lora/frame
**Summary**: Ingest raw binary LoRa frame with CRC-16 check and sequence tracking  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (HARDWARE_SIMULATION)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "hex_payload": "Hexadecimal-encoded compact binary LoRa frame",
  "gateway_id": "GW_ROHTANG_01"
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/telemetry/lora/gateway/backhaul
**Summary**: Set gateway backhaul online/offline status  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (HARDWARE_SIMULATION)` | **Auth**: `Public (None required)`  

**Request Body (application/json)**:

```json
{
  "gateway_id": "GW_ROHTANG_01",
  "online": true
}
```

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `POST` /api/v1/telemetry/lora/gateway/flush
**Summary**: Flush offline buffered LoRa packets chronologically  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (HARDWARE_SIMULATION)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `gateway_id` | `query` | `string` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/telemetry/lora/device/{device_id}/stats
**Summary**: Get sequence continuity and packet loss stats  
**Tags**: `Field Telemetry & Time-Series` | **Status**: `IMPLEMENTED (HARDWARE_SIMULATION)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `device_id` | `path` | `string` | Yes |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

### Module 11: Cryptographic Audit Trail & Tamper Evidence

#### `GET` /api/v1/audit/logs
**Summary**: List audit logs with filtering and pagination  
**Description**: Returns paginated audit trail records.  
**Tags**: `Audit & Tamper-Evidence` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Request Parameters**:

| Name | In | Type | Required | Description |
|---|:---:|:---:|:---:|---|
| `action` | `query` | `string` | No | Filter by action type (e.g. ALERT_AUTHORIZED_AND_DISPATCHED) |
| `actor_id` | `query` | `string` | No | Filter by actor ID |
| `target_entity_type` | `query` | `string` | No | Filter by entity type (e.g. AlertDispatch, Incident) |
| `limit` | `query` | `integer` | No |  |
| `offset` | `query` | `integer` | No |  |

**Responses**:

- **`HTTP 200`**: Successful Response
- **`HTTP 422`**: Validation Error
  ```json
  {
    "detail": [
      {
        "loc": [
          {}
        ],
        "msg": "msg",
        "type": "type",
        "input": "input",
        "ctx": null
      }
    ]
  }
  ```

---

#### `GET` /api/v1/audit/verify-chain
**Summary**: Cryptographically verify tamper-evident hash chain integrity  
**Description**: Traverses the chronological audit log entries and verifies SHA-256 hash chaining.
Proves whether the audit trail has been tampered with or modified.  
**Tags**: `Audit & Tamper-Evidence` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

### Module 12: High-Level EOC Dashboard Aggregations

#### `GET` /api/v1/dashboard/summary
**Summary**: Get comprehensive EOC operational briefing  
**Description**: Returns aggregated real-time operational status:
- Ingestion freshness across IMD, CWC, GPM, Sentinel
- Active multi-hazard incidents
- Pending and dispatched alerts
- Most recent basin risk state
- Model registry health  
**Tags**: `EOC Executive Dashboard` | **Status**: `IMPLEMENTED (OPERATIONAL)` | **Auth**: `Public (None required)`  

**Responses**:

- **`HTTP 200`**: Successful Response

---

## 6. Endpoint Implementation Status Matrix

| Method | Endpoint URL | Summary | Classification Status |
|:---:|---|---|:---:|
| `GET` | `/health` | Microservice liveness check | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/ready` | Microservice readiness check | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/metrics` | Prometheus metrics exporter | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/health` | Check system health, model readiness, and API key pools | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/health/liveness` | Lightweight liveness probe | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/health/ready` | Readiness probe verifying dependencies | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/system/status` | Operational system status summary | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/system/data-sources` | Telemetry & Earth Observation data source statuses | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/system/metrics` | Prometheus metrics exposition endpoint | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/version` | Application version metadata | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/eoc` | Emergency Operations Center Command Dashboard | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/` | Root dashboard overview | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/auth/register` | Register new operational user | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/auth/login` | Authenticate user and obtain JWT token | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/auth/me` | Get authenticated user identity | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/risk/current` | Get authoritative current basin risk state | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/risk/history` | Query historical risk state evaluations | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/risk/zones` | List spatial risk zone corridors | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/risk/{incident_id}` | Get consolidated risk state for a specific incident | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/incidents` | Register or trigger new multi-hazard incident | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/incidents` | List incidents with pagination | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/incidents/replay` | Trigger historical disaster scenario replay (mode=REPLAY) | `IMPLEMENTED (SIMULATION)` |
| `GET` | `/api/v1/incidents/{incident_id}` | Get full incident timeline, models, alerts, and audit provenance | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/orchestrator/incidents` | List all active and historical incidents | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/orchestrator/incidents/{incident_id}` | Get comprehensive incident briefing | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/orchestrator/incidents/{incident_id}/cap-xml` | Download official CAP v1.2 XML payload | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/orchestrator/incidents/{incident_id}/status` | Update incident status and append audit note | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/orchestrator/trigger-incident` | Trigger autonomous end-to-end incident response | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/alerts` | List alerts with filtering | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/alerts/draft` | Create early warning alert draft (PENDING_APPROVAL) | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/alerts/hazard-zone` | Generate targeted CAP v1.2 alert for critical hazard zone | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/alerts/cascade-breach` | Generate bilingual CAP v1.2 alert for landslide dam breach | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/alerts/{alert_id}` | Get alert details and CAP v1.2 XML | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/alerts/{alert_id}/authorize` | Commander authorization and CAP dispatch | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/alerts/{alert_id}/acknowledge` | Acknowledge alert reception | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/alerts/{alert_id}/cancel` | Commander cancellation / all-clear | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/decision/pipeline/alerts/{alert_id}/authorize` | Senior Incident Commander CAP Alert Authorization | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/decision/evacuation-route` | Find safest risk-weighted evacuation path | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/decision/infrastructure-graph` | Get Beas corridor infrastructure network summary | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/decision/pipeline/execute` | Execute end-to-end multi-hazard decision pipeline | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/gis/routes` | Get evacuation corridors GeoJSON | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/gis/safe-zones` | Get designated safe shelters GeoJSON | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/gis/hazards` | Get multi-hazard risk zones GeoJSON | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/gis/infrastructure` | Get critical infrastructure assets GeoJSON | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/satellite/layers` | List generated GIS satellite hazard rasters | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/satellite/critical-zones` | Get Section 36 high-hazard restricted development zones | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/satellite/candidate-development-zones` | Get candidate safe development zones with statutory disclaimer | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/satellite/risk-map` | Get multi-hazard risk map metadata and bounds | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/satellite/exposure` | Get critical infrastructure and population exposure summary | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/models` | List all registered models in the 20-model ecosystem | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/models/{model_id}` | Get full model card and provenance metadata | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/models/{model_id}/predict` | Run inference on an analytical model via its adapter | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/nowcast/forecast` | Generate Lagrangian short-term precipitation nowcast | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/nowcast/latest` | Get latest active atmospheric cloudburst forecast | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/cascade/simulate` | Simulate landslide dam overtopping breach and downstream wave arrival | `IMPLEMENTED (SIMULATION)` |
| `GET` | `/api/v1/cascade/historical-scenarios` | List historical Himalayan dam breach benchmarks | `IMPLEMENTED (SIMULATION)` |
| `GET` | `/api/v1/natural-dams` | Get all detected natural dam candidates as GeoJSON | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/natural-dams/analyze` | Trigger multi-temporal natural dam detection across river network | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/natural-dams/{dam_id}` | Get detailed profile, multi-evidence indicators, and explainability | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/natural-dams/{dam_id}/downstream-risk` | Get outburst failure potential and wave arrival times | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/natural-dams/{dam_id}/exposure` | Get downstream population and infrastructure exposure | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/natural-dams/{dam_id}/history` | Get multi-temporal evolution timeline | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/natural-dams/{dam_id}/impoundment` | Get upstream impounded water extent and reservoir metrics | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/natural-dams/{dam_id}/validate` | Submit authority or field validation for candidate | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/damage/analyze` | Trigger satellite damage proxy mapping over affected corridor | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/damage/buildings` | Get Copernicus EMS assessed building footprints as GeoJSON | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/damage/lifelines` | Get compromised road networks and severed bridges | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/damage/rescue-priority` | Get ranked NDRF/SDRF Rescue Prioritization Index list | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/satellite/analyze` | Run multi-sensor hazard inference on satellite scene | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/satellite/process-real-scene` | Execute end-to-end disaster intelligence pipeline on real satellite scenes | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/stations` | List physical telemetry stations | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/stations` | Register a physical station (Admin/Analyst) | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/stations/{station_id}/survey` | Record station field survey (Analyst/Admin) | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/stations/{station_id}/install` | Record station physical installation (Analyst/Admin) | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/stations/{station_id}/commission` | Verify checklist and commission station (Senior Commander/Admin) | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/stations/{station_id}/commissioning` | Get station commissioning status and record | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/stations/{station_id}/health` | Evaluate station operational health | `PROTOTYPE_STAGING` |
| `PATCH` | `/api/v1/stations/{station_id}/status` | Update station lifecycle status | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/devices` | List field IoT devices | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/devices` | Register a field device (Admin/Analyst) | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/devices/{device_id}` | Get device detail | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/devices/{device_id}/health` | Evaluate device operational health | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/devices/{device_id}/heartbeat` | Record device heartbeat and radio telemetry | `PROTOTYPE_STAGING` |
| `PATCH` | `/api/v1/devices/{device_id}/status` | Update device lifecycle status | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/sensors` | List sensors | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/sensors` | Register a sensor attached to a device | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/sensors/{sensor_id}/calibrate` | Add calibration record for a sensor | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/sensors/{sensor_id}/calibrations` | Add calibration record for a sensor (alias) | `PROTOTYPE_STAGING` |
| `POST` | `/api/v1/telemetry` | Ingest single field telemetry packet with strict idempotency | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/telemetry/batch` | Ingest a batch of field telemetry packets | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/telemetry/ingest` | Ingest and quality-audit real-time ground sensor reading | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/telemetry/recent` | Get recent verified telemetry readings | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/telemetry/stations` | List all registered IoT ground telemetry stations | `PROTOTYPE_STAGING` |
| `GET` | `/api/v1/telemetry/health/summary` | Get aggregated field telemetry and hardware health summary | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/observations/timeseries` | Query aggregated time-series telemetry | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/ingest/rain-gauge` | Ingest rainfall telemetry with M9 quality gating | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/ingest/river-stage` | Ingest CWC river stage telemetry with M9 quality gating | `IMPLEMENTED (OPERATIONAL)` |
| `POST` | `/api/v1/telemetry/lora/frame` | Ingest raw binary LoRa frame with CRC-16 check and sequence tracking | `IMPLEMENTED (HARDWARE_SIMULATION)` |
| `POST` | `/api/v1/telemetry/lora/gateway/backhaul` | Set gateway backhaul online/offline status | `IMPLEMENTED (HARDWARE_SIMULATION)` |
| `POST` | `/api/v1/telemetry/lora/gateway/flush` | Flush offline buffered LoRa packets chronologically | `IMPLEMENTED (HARDWARE_SIMULATION)` |
| `GET` | `/api/v1/telemetry/lora/device/{device_id}/stats` | Get sequence continuity and packet loss stats | `IMPLEMENTED (HARDWARE_SIMULATION)` |
| `GET` | `/api/v1/audit/logs` | List audit logs with filtering and pagination | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/audit/verify-chain` | Cryptographically verify tamper-evident hash chain integrity | `IMPLEMENTED (OPERATIONAL)` |
| `GET` | `/api/v1/dashboard/summary` | Get comprehensive EOC operational briefing | `IMPLEMENTED (OPERATIONAL)` |

### Scientific & Hardware Classification Notes
1. **`IMPLEMENTED (OPERATIONAL)`**: Fully backed by SQLite/PostgreSQL databases, active mathematical/ML logic, GIS asset loaders, and live business logic.
2. **`IMPLEMENTED (SIMULATION)`**: Validated numerical simulations and scenario replays (e.g. Costa-Froehlich breach hydrodynamics, synthetic cloudburst cascades, July 2023 flood replay).
3. **`PROTOTYPE_STAGING`**: Sensor and station registry endpoints manage hardware inventories staged in prototype/bench testing. As qualified under v3.9–v4.0 scientific closure, **0 physical sensor stations are deployed in active river water**.
4. **`IMPLEMENTED (HARDWARE_SIMULATION)`**: LoRa LPWAN gateways and binary packet ingestion verify CRC-16, SNR, and buffer flushes using bench-staged transceivers and simulated hardware vectors.
