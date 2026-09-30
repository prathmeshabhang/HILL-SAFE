# FLOODY SHIELD v3.4 — Observability, Health Probes & Metrics Specification

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Scope**: Liveness, Readiness, Data Sources Status, Prometheus Text Exposition  

---

## 1. Observability Endpoints

FLOODY SHIELD v3.4 implements enterprise-grade observability conforming to cloud-native monitoring standards and ITU-T disaster management reliability recommendations.

| Endpoint | Method | Purpose | Authentication |
| :--- | :---: | :--- | :---: |
| `/api/v1/health` | `GET` | Comprehensive system health & model catalog status | None |
| `/api/v1/health/liveness` | `GET` | Lightweight container orchestrator liveness probe | None |
| `/api/v1/health/ready` | `GET` | Dependency readiness probe (DB, data catalogs, models) | None |
| `/api/v1/version` | `GET` | Exact application version, environment, scientific level | None |
| `/api/v1/system/status` | `GET` | Subsystem operational summary without leaking secrets | None |
| `/api/v1/system/data-sources` | `GET` | External & ground observation telemetry sync monitor | None |
| `/metrics` | `GET` | Prometheus text exposition format (`text/plain; version=0.0.4`) | None |
| `/api/v1/system/metrics` | `GET` | Alias for Prometheus metrics exposition | None |

---

## 2. Health & Readiness Probes

### 2.1 Liveness Probe (`GET /api/v1/health/liveness`)
Used by Kubernetes or container runtimes to detect process hangs:
```json
{
  "status": "HEALTHY",
  "service": "floody-shield-backend",
  "timestamp": "2026-09-21T12:00:00Z",
  "request_id": "REQ-7b88ec7b"
}
```

### 2.2 Readiness Probe (`GET /api/v1/health/ready`)
Verifies that all required local data catalogs and model registry definitions exist on disk before routing traffic:
```json
{
  "ready": true,
  "service": "floody-shield-backend",
  "checks": {
    "model_registry": true,
    "data_root": true,
    "data_catalog": true
  },
  "timestamp": "2026-09-21T12:00:00Z",
  "request_id": "REQ-7b88ec7b"
}
```

---

## 3. Data Sources Status Monitor (`GET /api/v1/system/data-sources`)

Transparently tracks the real-time availability, sync cadence, and freshness tolerances of all upstream and in-situ feeds:

```json
{
  "status": "OPERATIONAL",
  "timestamp": "2026-09-21T12:00:00Z",
  "sources": {
    "IMD": {
      "name": "India Meteorological Department (IMD)",
      "type": "RADAR_WEATHER_STATION",
      "coverage": "Himachal Pradesh (Shimla / Kullu Doppler Radars)",
      "status": "OPERATIONAL",
      "integration_mode": "REAL_TIME_PROXY",
      "freshness_tolerance_seconds": 900,
      "failover_configured": true
    },
    "GPM": {
      "name": "NASA Global Precipitation Measurement (IMERG)",
      "type": "SATELLITE_PRECIPITATION",
      "coverage": "Global / Upper Beas Basin (31.5N-32.5N, 76.8E-77.5E)",
      "status": "OPERATIONAL",
      "integration_mode": "HOURLY_API_SYNC",
      "freshness_tolerance_seconds": 7200,
      "failover_configured": true
    },
    "CWC": {
      "name": "Central Water Commission (CWC)",
      "type": "HYDROLOGICAL_RIVER_GAUGE",
      "coverage": "Beas River Gauges (Thalout, Bhuntar, Pandoh)",
      "status": "OPERATIONAL",
      "integration_mode": "HOURLY_DISCHARGE_INGEST",
      "freshness_tolerance_seconds": 3600,
      "failover_configured": true
    },
    "Sentinel": {
      "name": "Copernicus Sentinel-1 & Sentinel-2",
      "type": "EARTH_OBSERVATION_SAR_OPTICAL",
      "coverage": "Upper Beas Catchment (10m Resolution)",
      "status": "OPERATIONAL",
      "integration_mode": "ORBITAL_PASS_CATALOG",
      "freshness_tolerance_seconds": 432000,
      "failover_configured": true
    },
    "IoT_Ground_Network": {
      "name": "FLOODY SHIELD Upper Beas Sensor Network",
      "type": "IN_SITU_TELEMETRY",
      "coverage": "Solang, Manali, Naggar, Kullu, Bhuntar, Larji",
      "status": "OPERATIONAL",
      "integration_mode": "STREAMING_REST_MQTT",
      "freshness_tolerance_seconds": 300,
      "failover_configured": true
    }
  }
}
```

---

## 4. Prometheus Metrics Exporter (`/metrics`)

FLOODY SHIELD includes a native, thread-safe Prometheus text exporter (`MetricRegistry`) that requires zero external runtime dependencies and exports OpenMetrics standard text.

### Metric Definitions
- `floody_uptime_seconds` (gauge): Total service uptime in seconds.
- `floody_http_requests_total{endpoint, method, status}` (counter): HTTP request counter.
- `floody_telemetry_packets_total{status}` (counter): Processed telemetry packets classified by ingestion state (`VALID`, `DUPLICATE`, `TAMPERED`, `INVALID`, `LATE`, `STALE`, `EXPIRED`).
- `floody_model_inferences_total{model_id}` (counter): Inferences per model (M1–M20).
- `floody_alerts_total{status}` (counter): Alerts classified by lifecycle state (`PENDING`, `AUTHORIZED`, `DISPATCHED`, `CANCELLED`).
- `floody_jobs_total{status}` (counter): Background job runs (`SUCCESS`, `FAILED`, `RETRY`).
- `floody_active_stations` (gauge): Number of active physical ground stations.
- `floody_active_devices` (gauge): Number of active IoT devices.
- `floody_current_risk_index` (gauge): Integrated multi-hazard risk index (0.0–1.0).

Sample Exposition:
```
# HELP floody_uptime_seconds Total uptime of the Floody Shield service in seconds.
# TYPE floody_uptime_seconds gauge
floody_uptime_seconds 4821.3

# HELP floody_telemetry_packets_total Total telemetry packets processed by ingestion status.
# TYPE floody_telemetry_packets_total counter
floody_telemetry_packets_total{status="VALID"} 1420
floody_telemetry_packets_total{status="DUPLICATE"} 45
floody_telemetry_packets_total{status="LATE"} 12
```
