# FLOODY SHIELD v3.4 — Backend Architecture Specification

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Version**: v3.4 Operational Hardened Modular Monolith  
**Scientific Maturity**: Level 1 (Prototype / Research Decision-Support)  

---

## 1. Architectural Overview

FLOODY SHIELD v3.4 is a production-hardened, real-time disaster-risk and early warning decision-support system designed specifically for the complex mountainous terrain of the Upper Beas River Basin in Himachal Pradesh. The architecture is organized as a high-throughput, low-latency modular monolith built with Python 3.11, FastAPI, SQLAlchemy 2.x, PostgreSQL/PostGIS (with local SQLite fallback), Alembic, WebSockets, and a decoupled internal Event Bus.

```
+-----------------------------------------------------------------------------------+
|                                FLOODY SHIELD v3.4                                 |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +-----------------------+   +-----------------------+   +---------------------+  |
|  | Field Ground Sensors  |   | Satellite & Radars    |   | Hydrological Gauges |  |
|  | (Solang, Manali, etc) |   | (IMD AWS, GPM IMERG,  |   | (CWC Bhuntar,       |  |
|  | PWP, Rain, Acoustic   |   |  Sentinel-1/2 SAR)    |   |  Thalout, Pandoh)   |  |
|  +-----------+-----------+   +-----------+-----------+   +----------+----------+  |
|              |                           |                          |             |
|              v                           v                          v             |
|  +-----------------------------------------------------------------------------+  |
|  |                    INGESTION & FIELD TELEMETRY GATEWAY                      |  |
|  |  * UTC Normalization & Clock Skew Validation (<120m future tolerance)       |  |
|  |  * Temporal Classifier (VALID / LATE / STALE / EXPIRED / INVALID)           |  |
|  |  * Deterministic SHA-256 Idempotency & Tamper Detection (HTTP 409)          |  |
|  |  * Batch Ingestion (Up to 500 packets/batch)                                |  |
|  +---------------------------------------+-------------------------------------+  |
|                                          |                                        |
|                                          v                                        |
|  +-----------------------------------------------------------------------------+  |
|  |                       INTERNAL ASYNCHRONOUS EVENT BUS                       |  |
|  |  * Topic Hierarchy (telemetry.*, risk.*, alert.*, station.*, system.*)      |  |
|  |  * In-Memory Ring Buffer (1000 events) & Sub-millisecond Dispatch          |  |
|  +---------------------------------------+-------------------------------------+  |
|                                          |                                        |
|                                          v                                        |
|  +-----------------------------------------------------------------------------+  |
|  |                   SCIENTIFIC MODEL ORCHESTRATION (M1-M20)                   |  |
|  |  * M1-M3: Atmospheric Nowcast & Flood Susceptibility (HistGBM, UNet)        |  |
|  |  * M6-M9: Landslide Trigger (RF, LightGBM, InSAR, PWP-SSI, IsolationForest)|  |
|  |  * M10-M12: Hydrodynamic Inundation & Dam Breach (Froehlich/Costa)          |  |
|  |  * M13-M16: Impact Matrix, Safe Shelters (MCDA), Evacuation Routing         |  |
|  |  * M17-M20: Safety Gating, Conformal Calibration, Physics Proof, Damage SAR|  |
|  |  [STRICT INVARIANT: Exactly 20 models; Zero retraining; Frozen weights]    |  |
|  +---------------------------------------+-------------------------------------+  |
|                                          |                                        |
|                                          v                                        |
|  +-----------------------------------------------------------------------------+  |
|  |                      UNIFIED MULTI-HAZARD RISK ENGINE                       |  |
|  |  * Hazard Synthesis: Flood, Landslide, Cascade Breach                       |  |
|  |  * Composite Risk & Uncertainty Calibration (Conformal 90% / 95%)          |  |
|  |  * Degraded Mode Isolation (HIGH / MODERATE / LOW / UNAVAILABLE)            |  |
|  +---------------------------------------+-------------------------------------+  |
|                                          |                                        |
|                                          v                                        |
|  +-----------------------------------------------------------------------------+  |
|  |                  HUMAN-IN-THE-LOOP LIFE-SAFETY GATEWAY                      |  |
|  |  * Non-Negotiable: No AI Model Can Dispatch Public Alerts Directly         |  |
|  |  * All Generated Alerts Enter PENDING_APPROVAL Status                      |  |
|  |  * Senior Incident Commander Cryptographic Sign-Off via Secure REST Gateway|  |
|  |  * WebSocket Authorization Strictly Prohibited (Returns Security Error)     |  |
|  +---------------------------------------+-------------------------------------+  |
|                                          |                                        |
|                     +--------------------+--------------------+                   |
|                     |                                         |                   |
|                     v                                         v                   |
|  +------------------------------------+    +-----------------------------------+  |
|  |   TAMPER-EVIDENT AUDIT REGISTRY    |    | MULTI-CHANNEL DISPATCH SUBSYSTEM  |  |
|  |  * Cryptographic SHA-256 Hash Chain|    |  * OASIS CAP v1.2 / ITU-T X.1303  |  |
|  |  * Append-Only Immutability        |    |  * NDMA Sachet (mTLS HTTPS)       |  |
|  |  * Genesis Root Linking            |    |  * WebSockets, Sirens, SMS, Email |  |
|  |  * Verification Probes             |    |  * Honest NOT_CONFIGURED Reporting|  |
|  +------------------------------------+    +-----------------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### 2.1 Physical Station, Device & Sensor Registry
The database models establish a rigorous physical hierarchy:
- **Station (`sensor_stations`)**: Top-level geographical site (e.g. `ST_AUT_01`, `ST_MANALI_01`). Stores WGS-84 coordinates, river basin affiliation, and operational heartbeat.
- **Device (`devices`)**: Hardware telemetry node (cellular gateway, LoRaWAN concentrator, solar node) installed at a station. Tracks hardware version, firmware version, battery voltage, solar input, RSSI, and operational status.
- **Sensor (`sensors`)**: Specific transducer attached to a device (e.g. radar water level, acoustic geophone, tipping bucket rain gauge, vibrating wire piezometer). Tracks measurement units, physical calibration factors, and calibration expiration dates.
- **Calibration Records (`calibration_records`)**: Historical log of calibration events, zero offsets, multipliers, and technician sign-offs.
- **Device Heartbeats (`device_heartbeats`)**: Diagnostic pings tracking battery discharge curves, wireless signal-to-noise ratio, and hardware error bitmasks.

### 2.2 Ingestion Engine & Temporal State Machine
Telemetry packets are ingested via `POST /api/v1/telemetry` or high-throughput batch `POST /api/v1/telemetry/batch`. The pipeline enforces:
1. **UTC Normalization**: All timestamps are converted to offset-aware ISO-8601 UTC.
2. **Clock Skew Protection**: Incoming timestamps more than 120 minutes in the future are rejected with HTTP 422 (`TELEMETRY_FUTURE_TIMESTAMP`).
3. **Temporal States**:
   - `VALID`: Packet observed within standard polling window (latency $\le 1\text{ hour}$).
   - `LATE`: Packet delayed in transit ($1\text{ hour} < \text{latency} \le 6\text{ hours}$).
   - `STALE`: Packet significantly delayed ($6\text{ hours} < \text{latency} \le 24\text{ hours}$).
   - `EXPIRED`: Packet past analytical window ($\text{latency} > 24\text{ hours}$).
   - `INVALID`: Future clock skew exceeded.
4. **Deterministic Idempotency**:
   $$\text{EventID} = \text{SHA256}(\text{source} \parallel \text{station} \parallel \text{device} \parallel \text{sensor} \parallel \text{measurement\_type} \parallel \text{seq} \parallel \text{timestamp})$$
   - Exact duplicate returns HTTP 200 with `status="DUPLICATE"`.
   - Tampered replay (same event ID, conflicting observed value) returns HTTP 409 (`TELEMETRY_INTEGRITY_VIOLATION`).

### 2.3 Decoupled Event Bus & Real-Time WebSockets
- **Event Bus (`EventBus`)**: Decoupled in-memory publish-subscribe bus supporting pattern matching (e.g., `telemetry.*`, `alert.*`). Maintains a rolling buffer of 1,000 historical events.
- **WebSocket Endpoint (`/ws/v1/events` and `/ws/realtime`)**:
  - Requires JWT authentication token or role query parameter.
  - Supports client-driven topic subscription (`risk`, `telemetry`, `stations`, `alerts`, `system`).
  - **Life-Safety Invariant Enforced**: Any attempt to send authorization commands (`AUTHORIZE_ALERT`, `DISPATCH`) over a WebSocket stream is rejected immediately with code `WEBSOCKET_AUTHORIZATION_PROHIBITED`. Alert authorization is strictly restricted to the authenticated REST API.

### 2.4 Multi-Hazard Risk Engine & Degradation Isolation
The risk engine synthesizes hazard predictions across M1–M12, calculates composite risk, and estimates statistical uncertainty:
- **Confidence States**:
  - `HIGH_CONFIDENCE` ($\ge 0.80$): Complete data freshness across all input models.
  - `MODERATE_CONFIDENCE` ($0.50 \le \text{score} < 0.80$): Minor sensor latency or proxy inputs.
  - `LOW_CONFIDENCE` ($< 0.50$): Significant missing inputs, stale radar feeds, or model fallback.
  - `UNAVAILABLE`: Primary sensory arrays offline.
- When an upstream model fails, the system executes **Graceful Degradation**, isolating the failure, logging the degraded mode, and continuing multi-hazard synthesis without crashing the decision loop.

### 2.5 Alert Lifecycle & Multi-Channel Dispatch
1. **Creation**: Alert drafts are created via `POST /api/v1/alerts/draft` in `PENDING_APPROVAL` status.
2. **Cancellation**: Commanders or analysts can cancel pending drafts via `POST /api/v1/alerts/{id}/cancel`.
3. **Authorization**: Senior Incident Commanders authorize alerts via `POST /api/v1/alerts/{id}/authorize` supplying an authorized cryptographic token.
   - Enforces valid state machine: Only `PENDING_APPROVAL` can be authorized.
   - Cancelled alerts cannot be authorized.
   - Already dispatched alerts cannot be authorized twice.
4. **OASIS CAP v1.2 Validation**: Renders and validates standard Common Alerting Protocol XML before dispatch. XML characters are properly escaped.
5. **Multi-Channel Dispatcher**: Dispatches alert across active channels:
   - `WEBSOCKET`: Real-time streaming to EOC consoles.
   - `SIREN`: Acoustic sirens in corridor settlements (Solang, Manali, Pandoh).
   - `SMS` / `EMAIL`: Direct alerts to emergency responders.
   - `NDMA_SACHET`: National Disaster Management Authority Sachet gateway via Mutual TLS.
   - **Honest Status Guarantee**: If third-party credentials or certificates are not configured, providers report `status="NOT_CONFIGURED"`.

---

## 3. Database Architecture & Alembic Migrations

- **Revision**: `c4b1829e5a10` (`v3_4_device_sensor_schema`)
- **Tables**:
  1. `users`: Cryptographic identity & RBAC role storage.
  2. `sensor_stations`: Physical telemetry station metadata & coordinates.
  3. `devices`: Field hardware units, telemetry modems, battery/solar health.
  4. `sensors`: Transducer metadata, sampling intervals, calibration states.
  5. `calibration_records`: Traceable calibration history.
  6. `device_heartbeats`: Hardware diagnostic telemetry.
  7. `sensor_observations`: Timeseries measurements, deterministic event IDs, temporal states.
  8. `incidents`: Multi-hazard disaster incident entities.
  9. `model_runs`: Scientific execution provenance and run metrics.
  10. `risk_states`: Synthesized multi-hazard state, confidence metrics, and health.
  11. `risk_zones`: Spatial risk polygons.
  12. `infrastructure_assets`: Critical assets exposed to hazard.
  13. `population_zones`: Demographic vulnerability blocks.
  14. `safe_zones`: Verified candidate evacuation areas.
  15. `evacuation_routes`: Dijkstra/A* topological escape paths.
  16. `alert_dispatches`: Statutory CAP v1.2 warning records.
  17. `alert_acknowledgements`: Agency confirmation logs.
  18. `audit_logs`: SHA-256 hash-chained immutable audit log.
- **Migration Verification**: Bidirectional migration execution (`alembic upgrade head` $\to$ `alembic downgrade -1` $\to$ `alembic upgrade head`) verified clean.
