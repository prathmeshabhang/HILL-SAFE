# FLOODY SHIELD v3.3 — Real-Time Events & GIS API Specification

**System**: FLOODY SHIELD  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Modules**: `backend/app/websocket/`, `backend/app/api/v1/endpoints/gis.py`  

---

## 1. WebSocket Streaming Endpoint (`/ws/v1/events`)

Real-time situational awareness across EOC command consoles, field devices, and emergency sirens is delivered via a persistent WebSocket stream:

- **URL**: `ws://<host>:8000/ws/v1/events` (or `wss://` in TLS-terminated production environments)
- **Authentication**: Optional query token `?token=<jwt>` or WebSocket handshake header `Authorization: Bearer <jwt>`.
- **Role Scoping**: Unauthenticated or `OBSERVER` connections receive public advisories and telemetry. `ANALYST` and `SENIOR_INCIDENT_COMMANDER` connections receive internal alerts (`ALERT_DRAFT_CREATED`), model run telemetry, and quality degradation warnings.

```
CLIENT (EOC / Field App)                              FASTAPI WEBSOCKET MANAGER
         │                                                      │
         ├──────────────── WebSocket Connect ──────────────────►│ Authenticate & Bind Client ID
         │                                                      │
         │◄────────────── EVENT: CONNECTION_READY ──────────────┤ Initial connection confirmation
         │                                                      │
         │                  [When Ingestion Occurs]             │
         │◄────────────── EVENT: TELEMETRY_INGESTED ────────────┤ New sensor observation
         │                                                      │
         │                  [When Threshold Exceeded]           │
         │◄────────────── EVENT: ALERT_DRAFT_CREATED ───────────┤ New draft awaiting sign-off
         │                                                      │
         │                  [When Commander Signs Off]          │
         │◄────────────── EVENT: ALERT_DISPATCHED ──────────────┤ Official CAP v1.2 broadcast
         │                                                      │
         │                  [Downstream Unit Acks]              │
         │◄────────────── EVENT: ALERT_ACKNOWLEDGED ────────────┤ Delivery confirmation
         │                                                      │
```

---

## 2. Event Types & JSON Schemas

Every frame broadcast by `ConnectionManager` adheres to the typed `RealTimeEvent` schema:

```json
{
  "event_id": "9a42f53c-1b77-49d9-bb43-b91c8900fe12",
  "event_type": "ALERT_DISPATCHED",
  "timestamp": "2026-09-21T12:00:00.000Z",
  "source": "FLOODY_SHIELD_EOC_ORCHESTRATOR",
  "data": {
    "alert_id": "c2da8b01-527e-40ef-862a-191024bd21a9",
    "identifier": "CAP-HPSDMA-20260921-C2DA8B",
    "headline": "FLASH FLOOD EMERGENCY — UPPER BEAS CORRIDOR",
    "severity": "Extreme",
    "urgency": "Immediate",
    "status": "DISPATCHED",
    "authorized_by": "SENIOR_COMMANDER_KULLU_01"
  }
}
```

### Supported Event Types (`RealTimeEventType`):
- `TELEMETRY_INGESTED`: New weather, river, or IoT ground observation recorded.
- `QUALITY_DEGRADATION`: Quality gate flagged anomalous or stale sensor data.
- `RISK_STATE_UPDATED`: Authoritative composite basin risk recalculated.
- `ALERT_DRAFT_CREATED`: High-hazard threshold crossed; draft alert awaits authorization.
- `ALERT_DISPATCHED`: Incident commander authorized emergency alert dispatch.
- `ALERT_ACKNOWLEDGED`: Field civil defense unit confirmed siren sounding or siren activation.
- `ALERT_CANCELLED`: Commander cancelled or cleared an active alert.
- `MODEL_EXECUTION_COMPLETED`: Individual model execution node finished.

---

## 3. PostGIS GIS Spatial Endpoints

All GIS endpoints return RFC 7946 compliant GeoJSON FeatureCollections:

### 3.1 `GET /api/v1/gis/hazards`
Returns active multi-hazard risk zones with properties:
- `zone_name` (e.g. `NH-3 Aut-Larji Riverbed Ribbon`)
- `hazard_type` (`Compound Flood & Debris Flow`)
- `risk_level` (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`)
- `peak_depth_m`, `time_to_impact_sec`

### 3.2 `GET /api/v1/gis/safe-zones`
Returns designated emergency refuge centers filtered by criteria:
- Query parameters: `min_elevation_m`, `accessible_only=true`
- Properties: `name`, `zone_type`, `capacity`, `elevation_m`, `slope_degrees`, `is_accessible`

### 3.3 `GET /api/v1/gis/infrastructure`
Returns exposed critical infrastructure:
- Filter: `asset_type` (`BRIDGE`, `ROAD_SEGMENT`, `POWER_SUBSTATION`, `HOSPITAL`)
- Properties: `name`, `asset_type`, `criticality_score`, `elevation_m`

### 3.4 `GET /api/v1/gis/routes`
Returns dynamic evacuation routing polylines avoiding active flood and landslide hazards:
- Filter: `origin_id`, `destination_id`, `incident_id`
- Properties: `route_id`, `source`, `destination`, `risk_cost`, `eta_minutes`, `status`
