# FLOODY SHIELD v3.3 — Telemetry & Ingestion Architecture

**System**: FLOODY SHIELD  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Module**: `backend/app/services/ingestion/`  

---

## 1. Multi-Source Ingestion Architecture

Disaster risk forecasting in the Himalayas demands real-time fusion of multi-sensor telemetry across varying spatial resolutions, sampling frequencies, and latency profiles.

FLOODY SHIELD v3.3 introduces a modular ingestion framework with standardized data source adapters and centralized multi-stage quality gating.

```
[ IMD AWS ]       [ GPM IMERG ]     [ CWC River ]     [ Sentinel SAR ]   [ Upper Beas IoT ]
(Rainfall)        (Satellite Precip)(Stage/Discharge) (Backscatter/VV/VH)(PWP / Tilt / Raingauge)
     │                  │                 │                  │                   │
     ▼                  ▼                 ▼                  ▼                   ▼
  IMDAWSAdapter   GPMIMERGAdapter  CWCRiverAdapter  SentinelAdapter     IoTTelemetryAdapter
     └──────────────────┴─────────────────┬──────────────────┴───────────────────┘
                                          ▼
                             Normalized Observation Payload
                                          │
                                          ▼
                       TelemetryQualityGate.assess_quality()
                       ┌─────────────────────────────────────┐
                       │  1. Spatial Bounding Validation     │
                       │     (31.50 - 32.50 N, 76.80-77.60 E)│
                       │  2. Temporal Freshness & Clock Skew │
                       │     (No future >120m, stale >360m)  │
                       │  3. Physical Sensor Range Bounds    │
                       │     (Rain: 0-350 mm/h, Stage: 0-35m)│
                       │  4. M9 Anomaly Screening            │
                       │     (Multivariate Isolation Forest) │
                       └─────────────────────────────────────┘
                                          │
                        QualityState Assigned & Tagged:
                 [ FRESH | STALE | EXPIRED | DEGRADED | CRITICAL_ERROR ]
                                          │
                                          ▼
                            TelemetryIngestionService
                       ┌─────────────────────────────────────┐
                       │  - Idempotency Hash Deduplication   │
                       │    (SHA-256 over station/obs_time)  │
                       │  - DataIngestionRun Tracking        │
                       │  - DataQualityRecord Audit Logging  │
                       │  - SensorObservation Persistence    │
                       └─────────────────────────────────────┘
```

---

## 2. Ingestion Adapters

Every external source implements `DataSourceAdapter` (`backend/app/services/ingestion/adapters/base.py`):

| Adapter | Source ID | Typical Frequency | Measurement Variables | Physical Limits |
| :--- | :--- | :--- | :--- | :--- |
| **`IMDAWSAdapter`** | `IMD_AWS` | 15–60 min | Rain rate (mm/h), cumulative rain (mm), temperature, humidity | Rain: 0 – 350 mm/h |
| **`GPMIMERGAdapter`** | `GPM_IMERG` | 30 min | Half-hourly precipitation rate (mm/h), calibration flag | Precip: 0 – 300 mm/h |
| **`CWCRiverAdapter`** | `CWC_RIVER` | 15–60 min | River stage (m), discharge ($m^3/s$), warning level, danger mark | Stage: 0 – 35 m, Discharge: 0 – 15,000 $m^3/s$ |
| **`SentinelSceneAdapter`** | `SENTINEL_COPERNICUS`| 6–12 days | SAR backscatter (VV/VH dB), scene acquisition time, orbit pass | VV/VH: -40 to +10 dB |
| **`IoTTelemetryAdapter`** | `UPPER_BEAS_IOT` | 1–5 min | Pore-water pressure (kPa), tilt ($^\circ$), soil moisture (%), battery (V) | PWP: 0 – 1500 kPa, Battery: 2.0 – 5.0 V |

---

## 3. Telemetry Quality Gate Rules

The quality gate evaluates incoming telemetry before downstream model consumption:

1. **Spatial Bounds Enforcement**:
   Upper Beas geographic bounding box: $31.50^\circ\text{N} \le \text{Lat} \le 32.50^\circ\text{N}$ and $76.80^\circ\text{E} \le \text{Lon} \le 77.60^\circ\text{E}$. Observations falling outside this polygon are flagged with `CRITICAL_ERROR` and rejected from model ingestion.
2. **Temporal Freshness & Clock Skew**:
   - `Future timestamps` exceeding 120 minutes of clock skew are rejected as `CRITICAL_ERROR`.
   - Telemetry older than 360 minutes is accepted for historical records but tagged `STALE`.
   - Telemetry within standard latency is tagged `FRESH`.
3. **Physical Sensor Feasibility**:
   Rainfall rates $>350\text{ mm/h}$ (beyond cloudburst maximums) or river depths $<0\text{ m}$ / $>35\text{ m}$ trigger `CRITICAL_ERROR`.
4. **M9 Multivariate Anomaly Detection**:
   Uses an Isolation Forest trained on multivariate ground station features (rainfall, river stage, battery voltage). Anomalous sensor fluctuations are tagged `DEGRADED`, alerting operators to potential sensor drift or battery depletion.

---

## 4. Idempotency & Deduplication

To prevent double-counting of telemetry packets across network retries, an idempotency hash is computed:
$$\text{Hash} = \text{SHA-256}(\text{source\_id} \mathbin{\Vert} \text{station\_id} \mathbin{\Vert} \text{observed\_at})$$
Duplicate payloads are rejected safely with status `DUPLICATE` and zero database corruption.
