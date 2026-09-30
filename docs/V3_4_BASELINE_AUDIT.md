# FLOODY SHIELD v3.4 — Baseline Audit & System Snapshot

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Audit Timestamp**: September 21, 2026, 17:52 IST  
**Environment**: Windows / Local Python Virtual Environment (`.venv`)  

---

## 1. Test Suite Baseline Execution

Command:
```bash
.\.venv\Scripts\python.exe -m pytest -q
```

### Execution Metrics
- **Total Tests**: **518**
- **Passed**: **518**
- **Failures**: **0**
- **Errors**: **0**
- **Warnings**: **12**
- **Runtime**: **48.03 seconds**

### Known Warnings
1. `fastapi/testclient.py:1`: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
2. `starlette/testclient.py:53`: `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.`
3. `test_database_layer.py:152`: `SAWarning: New instance <IncidentModel> with identity key conflicts with persistent instance` (expected intentionally simulated integrity rollback test).
4. `sklearn/utils/validation.py:2830`: `UserWarning: X does not have valid feature names, but RandomForestClassifier/LGBMClassifier/StandardScaler was fitted with feature names` (third-party scikit-learn/lightgbm feature name check during inference array passing).

---

## 2. Frozen Model Artifact SHA-256 Hashes

All 4 frozen machine learning model artifacts were verified bit-for-bit against the institutional registry:

| Model ID | Relative Artifact Path | SHA-256 Checksum | Verification Status |
| :--- | :--- | :--- | :---: |
| **M2** | `ml/flood/m2_upper_beas_flood_model.joblib` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | **VERIFIED BIT-IDENTICAL** |
| **M4** | `data/satellite_output/flood_multimodal_unet.pt` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | **VERIFIED BIT-IDENTICAL** |
| **M6** | `ml/landslide/m6_beas_susceptibility_rf.joblib` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | **VERIFIED BIT-IDENTICAL** |
| **M7** | `ml/landslide/m7_beas_trigger_lgbm.joblib` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | **VERIFIED BIT-IDENTICAL** |

---

## 3. Database Migration Revision

- **Alembic Head**: `6071286b9e46` (`v3_3_initial_schema`)
- **Tables Registered**: 16 tables
  - `users`, `sensor_stations`, `sensor_observations`, `data_ingestion_runs`, `data_quality_records`, `incidents`, `model_runs`, `risk_states`, `risk_zones`, `infrastructure_assets`, `population_zones`, `safe_zones`, `alert_dispatches`, `alert_acknowledgements`, `evacuation_routes`, `audit_logs`.
- **Spatial Extensions**: PostGIS Point and Polygon geometries supported via `geoalchemy2`.

---

## 4. Software & Dependency Versions

- **Python**: `3.11.9 (tags/v3.11.9:de54cf5, Apr 2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]`
- **FastAPI**: `0.141.1`
- **SQLAlchemy**: `2.0.54`
- **Alembic**: `1.20.0`
- **PyTorch**: `2.6.0+cpu`
- **Scikit-Learn**: `1.6.1`
- **LightGBM**: `4.6.0`
- **GeoAlchemy2**: `0.17.1`
- **PyJWT**: `2.10.1`
- **Bcrypt**: `4.3.0`
- **WebSockets**: `15.0.1`
- **Docker Base**: `python:3.11-slim`, `postgis/postgis:15-3.3-alpine`

---

## 5. API Route Count

- **Total OpenAPI Routes**: **67 distinct endpoint paths**
  - Core v3.3 Endpoints: `/api/v1/health/*`, `/api/v1/models/*`, `/api/v1/decision/pipeline/*`, `/api/v1/ingest/*`, `/api/v1/gis/*`, `/api/v1/dashboard/*`, `/api/v1/alerts/*`, `/api/v1/incidents/*`, `/api/v1/auth/*`, `/api/v1/audit/*`.
  - Domain Endpoints: `/api/v1/satellite/*`, `/api/v1/cascade/*`, `/api/v1/natural-dams/*`, `/api/v1/damage/*`, `/api/v1/nowcast/*`, `/api/v1/telemetry/*`, `/api/v1/orchestrator/*`.
  - Real-Time WebSocket: `/ws/v1/events`.

---

## 6. Git Status

- Git repository status: Workspace directory is standalone (no `.git` directory initialized in current tree). Commit tracking is maintained through versioned releases and institutional change logs.
