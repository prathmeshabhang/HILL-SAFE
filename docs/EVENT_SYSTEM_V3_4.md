# FLOODY SHIELD v3.4 — Event System & WebSocket Infrastructure

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Scope**: In-Memory Event Bus, Topic Taxonomy, WebSocket Stream Filtering, Resilience  

---

## 1. Asynchronous In-Memory Event Bus

FLOODY SHIELD v3.4 features an in-process, asynchronous Event Bus (`EventBus`) that decouples data ingestion, scientific inference, risk calculation, and real-time client broadcasting.

### 1.1 Architecture
- **Thread Safety**: Operates in Python's async event loop with asynchronous and synchronous subscriber support.
- **Ring Buffer**: Maintains a rolling historical buffer of the 1,000 most recent events for audit and diagnostic inspection.
- **Wildcard Subscriptions**: Handlers can subscribe to exact event types (e.g. `telemetry.accepted`) or hierarchical wildcards (`telemetry.*`, `alert.*`, `*`).

### 1.2 Event Data Structure (`SystemEvent`)
```json
{
  "event_id": "7b88ec7b-8fd1-4bc1-9bb4-71be84784a92",
  "event_type": "telemetry.accepted",
  "timestamp": "2026-09-21T12:00:00Z",
  "correlation_id": "corr-f92b7401-2026",
  "source": "INGESTION_SERVICE",
  "entity_id": "SNS_AUT_RAIN_01",
  "severity": "INFO",
  "payload": {
    "station_id": "ST_AUT_01",
    "measurement_type": "rainfall_rate_mmh",
    "value": 45.2,
    "quality_state": "FRESH"
  }
}
```

---

## 2. Topic Taxonomy

| Topic Pattern | Description | Originating Subsystem |
| :--- | :--- | :--- |
| `telemetry.accepted` | Valid telemetry packet ingested and stored | Ingestion Gateway |
| `telemetry.duplicate` | Duplicate packet rejected with existing ID | Ingestion Gateway |
| `telemetry.tampered` | Replay tampering detected and rejected | Ingestion Gateway |
| `station.heartbeat` | Diagnostic heartbeat ping from field device | Device Registry |
| `station.degraded` | Station battery low or packet loss high | Sensor Health Service |
| `model.started` | Scientific model execution initiated | Model Orchestrator |
| `model.completed` | Scientific model inference produced results | Model Orchestrator |
| `risk.updated` | Unified multi-hazard risk state synthesized | Risk Engine |
| `risk.critical` | Critical threshold breached in any hazard | Risk Engine |
| `alert.drafted` | New early warning alert draft created | Alert Lifecycle |
| `alert.authorized` | Statutory sign-off completed by Commander | Alert Lifecycle |
| `alert.dispatched` | Alert broadcast to sirens, SMS, NDMA | Notification Dispatcher |
| `alert.cancelled` | Alert cancelled by emergency authorities | Alert Lifecycle |
| `system.metric` | Background job execution or health event | Job Manager / Core |

---

## 3. Real-Time WebSockets (`/ws/v1/events` & `/ws/realtime`)

### 3.1 Connection Handshake
Clients connect to `/ws/v1/events` or `/ws/realtime` with an optional JWT token or role:
`ws://localhost:8000/ws/realtime?token=<JWT_TOKEN>&topics=risk,alerts`

Upon successful connection, the server sends an initial confirmation frame:
```json
{
  "type": "SUBSCRIPTION_CONFIRMED",
  "status": "CONNECTED",
  "role": "SENIOR_INCIDENT_COMMANDER",
  "topics": ["risk", "alerts"]
}
```

### 3.2 Client Control Actions
- **Subscribe to Topic**:
  ```json
  {"action": "subscribe", "topic": "telemetry"}
  ```
  Response: `{"type": "SUBSCRIPTION_CONFIRMED", "status": "SUBSCRIBED", "topic": "telemetry"}`
- **Unsubscribe**:
  ```json
  {"action": "unsubscribe", "topic": "telemetry"}
  ```
  Response: `{"type": "UNSUBSCRIBE_CONFIRMED", "status": "UNSUBSCRIBED", "topic": "telemetry"}`
- **Liveness Ping**: Client sends `"ping"`, server returns `"pong"`.

### 3.3 Security Boundary Enforcement
Any message attempting alert authorization over WebSocket is intercepted and rejected:
```json
{
  "type": "SECURITY_ERROR",
  "code": "WEBSOCKET_AUTHORIZATION_PROHIBITED",
  "error": "WEBSOCKET_AUTHORIZATION_PROHIBITED",
  "message": "Life-safety emergency alert authorization cannot be executed via WebSocket. The authenticated REST API gateway (POST /api/v1/alerts/{id}/authorize) is required."
}
```
