# FLOODY SHIELD v3.4 — Authoritative API Contract

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Base URL**: `http://localhost:8000` (or `https://eoc.hpsdma.nic.in`)  
**Specification**: OpenAPI 3.0 / FastAPI  

---

## 1. Physical Stations, Devices & Sensors

### 1.1 `POST /api/v1/stations`
- **Role**: `ANALYST`, `SENIOR_INCIDENT_COMMANDER`
- **Request**:
  ```json
  {
    "station_id": "ST_AUT_01",
    "name": "Aut Hydro-Meteorological Station",
    "station_type": "MET_HYDRO_IOT",
    "latitude": 31.7483,
    "longitude": 77.2081,
    "elevation_m": 1050.0,
    "river_basin": "Upper Beas Basin"
  }
  ```
- **Response**: `200 OK` with registered station object.

### 1.2 `GET /api/v1/stations/{station_id}/health`
- **Role**: Any
- **Response**: `200 OK`
  ```json
  {
    "station_id": "ST_AUT_01",
    "status": "OPERATIONAL",
    "operational_state": "OPERATIONAL",
    "total_devices": 2,
    "total_sensors": 4,
    "devices": [...]
  }
  ```

### 1.3 `POST /api/v1/devices`
- **Role**: `ANALYST`, `SENIOR_INCIDENT_COMMANDER`
- **Request**:
  ```json
  {
    "device_id": "DEV_AUT_01",
    "station_id": "ST_AUT_01",
    "serial_number": "SN-2026-AUT-99",
    "device_type": "LORA_NODE",
    "protocol": "LORAWAN",
    "status": "ACTIVE"
  }
  ```

### 1.4 `POST /api/v1/devices/{device_id}/heartbeat`
- **Role**: Unauthenticated (Device API key or open telemetry port)
- **Request**:
  ```json
  {
    "battery_percentage": 94.2,
    "battery_voltage": 13.6,
    "rssi_dbm": -68.0,
    "firmware_version": "1.0.4",
    "error_flags": 0
  }
  ```

### 1.5 `POST /api/v1/sensors/{sensor_id}/calibrate` (and `/calibrations`)
- **Role**: `ANALYST`, `SENIOR_INCIDENT_COMMANDER`
- **Request**:
  ```json
  {
    "calibrated_by": "Field Engineer Sharma",
    "standard_reference": "REF-OTT-2026",
    "zero_offset": 0.02,
    "scale_factor": 1.001,
    "notes": "Pre-monsoon calibration"
  }
  ```

---

## 2. Field Telemetry Ingestion & Timeseries

### 2.1 `POST /api/v1/telemetry`
- **Request**:
  ```json
  {
    "source": "FIELD_NODE",
    "station_id": "ST_AUT_01",
    "device_id": "DEV_AUT_01",
    "sensor_id": "SNS_AUT_RAIN_01",
    "measurement_type": "rainfall_rate_mmh",
    "value": 45.2,
    "unit": "mm/h",
    "sequence_number": 1205,
    "observed_at": "2026-09-21T12:00:00Z"
  }
  ```
- **Responses**:
  - `200 OK`: `{"status": "INGESTED", "temporal_state": "VALID", "source_event_id": "..."}`
  - `200 OK`: `{"status": "DUPLICATE", "source_event_id": "..."}` (benign retransmission)
  - `409 Conflict`: `{"error": {"code": "TELEMETRY_INTEGRITY_VIOLATION", ...}}` (tampered value)
  - `422 Unprocessable Entity`: `{"error": {"code": "TELEMETRY_FUTURE_TIMESTAMP", ...}}`

### 2.2 `POST /api/v1/telemetry/batch`
- Ingests up to 500 packets in a single payload.

### 2.3 `GET /api/v1/observations/timeseries`
- **Query Params**: `sensor_id`, `station_id`, `measurement_type`, `aggregation` (`raw`, `latest`, `min`, `max`, `mean`, `sum`, `count`), `start`, `end`.

---

## 3. Multi-Hazard Risk & Early Warning Alerts

### 3.1 `GET /api/v1/risk/current`
- **Response**:
  ```json
  {
    "overall_risk_level": "CRITICAL",
    "composite_risk_score": 0.88,
    "confidence_score": 0.85,
    "confidence_state": "HIGH_CONFIDENCE",
    "model_health_state": "HEALTHY",
    "flood_hazard": {...},
    "landslide_hazard": {...},
    "cascade_hazard": {...}
  }
  ```

### 3.2 `POST /api/v1/alerts/draft`
- Creates an alert draft in `PENDING_APPROVAL` status.

### 3.3 `POST /api/v1/alerts/{alert_id}/authorize`
- **Role**: `SENIOR_INCIDENT_COMMANDER`
- **Request**:
  ```json
  {
    "actor_id": "SENIOR_COMMANDER_VERMA",
    "actor_role": "SENIOR_INCIDENT_COMMANDER",
    "approval_token": "CRYPTO_APPROVED_2026_KULLU"
  }
  ```
- **Response**: `200 OK` (`status="DISPATCHED"`).

### 3.4 `POST /api/v1/alerts/{alert_id}/cancel`
- **Role**: `ANALYST`, `SENIOR_INCIDENT_COMMANDER`
- **Request**: `{"reason": "Threat subsided"}`
- **Response**: `200 OK` (`status="CANCELLED"`).

---

## 4. Observability & Real-Time WebSockets

- `GET /metrics`: Prometheus plain-text exposition.
- `GET /api/v1/system/status`: Overall system status.
- `GET /api/v1/system/data-sources`: Upstream data source freshness.
- `WS /ws/v1/events` (and `/ws/realtime`): Real-time streaming WebSocket.
