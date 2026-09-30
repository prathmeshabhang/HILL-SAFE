# FLOODY SHIELD v3.7 — Real Telemetry Ingestion, Provenance & Quality Gating

**Target Basin:** Upper Beas River Basin, Himachal Pradesh  
**Data Protocol:** LoRaWAN 1.0.3 / Compact Binary Frames / REST Telemetry Packets  

---

## 1. Provenance & Environment Partitioning

To maintain scientific integrity and prevent test fixtures or synthetic simulators from corrupting baseline risk assessments, every telemetry packet records two immutable classification tags:

| Field | Allowed Values | Default | Semantics |
| :--- | :--- | :--- | :--- |
| `provenance` | `REAL`, `SIMULATED`, `REPLAY`, `TEST` | `REAL` | Origin of data: physical transducer vs simulated generator vs historical event replay |
| `environment` | `FIELD`, `TEST`, `LAB`, `STAGING` | `FIELD` | Deployment environment: physical station in Upper Beas vs bench test in laboratory |

### Database & Timeseries Query Isolation

Queries to `/api/v1/observations/timeseries` support strict filtering:
```http
GET /api/v1/observations/timeseries?station_id=STN_MANA_01&provenance=REAL&environment=FIELD
```
Observations generated during hardware validation or soak tests are tagged `SIMULATED` / `TEST` and automatically filtered from downstream decision intelligence dashboards unless explicitly requested.

---

## 2. Ingestion Quality Gates

Incoming telemetry passes through a 4-tier verification gate:

1. **Spatial Bounds Validation**: Ensures coordinates reside within the Upper Beas catchment envelope ($31.40^\circ\text{N} - 32.45^\circ\text{N}$, $76.80^\circ\text{E} - 77.45^\circ\text{E}$).
2. **Temporal Freshness & Skew Check**: Observations are timestamped in UTC. Future-dated observations $> 5\text{ minutes}$ are rejected as clock drift errors. Age $> 6\text{ hours}$ flags data as `STALE`; $> 24\text{ hours}$ flags `EXPIRED`.
3. **Physical Limits Validation**:
   - Rainfall: $0.0 - 500.0\text{ mm/h}$
   - River Stage: $0.0 - 50.0\text{ m}$
   - Pore Water Pressure: $-50.0 - 2000.0\text{ kPa}$
   - Displacement: $0.0 - 5000.0\text{ mm}$
4. **Stream Quality Control (QC)**:
   - **Flatline Detection (`QC_FLATLINE`)**: Detects stuck sensor if 5+ consecutive readings are identical non-zero values.
   - **Rate-of-Change Spike (`QC_SPIKE`)**: Flags sudden implausible surges (e.g., river stage $> 2\text{ m/min}$, rain $> 50\text{ mm/h/min}$).
   - Automatically downgrades observation quality state to `DEGRADED`.
