# FLOODY SHIELD v3.5 — Baseline System Audit

**Project:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**Audit Date:** 2026-09-21  
**Audit Scope:** Verification, Reliability, Security, Real-Deployment Testing & Field-Pilot Readiness  
**Current Baseline Version:** v3.4.0 $\to$ **Target Version:** v3.5.0  
**Overall Readiness Classification:** LEVEL 1 — PROTOTYPE / RESEARCH DECISION-SUPPORT  

---

## 1. Executive Summary

An independent baseline audit was conducted prior to executing the v3.5 hardening and verification phase. The system baseline consists of 530 tests passing with 0 failures and 0 errors across both the core scientific ML layer (M1–M20) and the v3.4 operational platform (device registry, telemetry ingestion gateway, risk engine, life-safety authorization gateway, CAP v1.2 alert pipeline, and Prometheus observability).

All 4 frozen model weight artifacts were re-verified bit-for-bit against their authoritative SHA-256 hashes. No model retraining, re-weighting, or scientific logic alteration has occurred.

---

## 2. Environment & Dependency Inventory

| Component | Specification / Version | Status / Notes |
|---|---|---|
| **Operating System** | Microsoft Windows 11 / Windows Server | Native execution environment (PowerShell) |
| **Python Runtime** | Python 3.11.9 (`.\.venv\Scripts\python.exe`) | Validated virtualenv |
| **FastAPI** | 0.115.6 | Core ASGI application framework |
| **Uvicorn** | 0.34.0 | ASGI web server |
| **SQLAlchemy** | 2.0.36 | Modern 2.x declarative ORM |
| **Alembic** | 1.14.0 | Schema migration manager |
| **GeoAlchemy2 / Shapely** | 0.17.1 / 2.0.6 | Geospatial geometries & PostGIS support |
| **Pydantic** | 2.10.4 | Data validation & settings |
| **PyJWT & Passlib / Bcrypt** | 2.10.1 / 1.7.4 / 4.2.1 | Authentication & cryptographic hashing |
| **Pytest** | 8.3.4 | Test harness (530 tests passed) |

---

## 3. Scientific Layer & Frozen Model Hash Audit

The FLOODY SHIELD architecture comprises exactly 20 distinct model components (M1–M20). Four frozen model artifacts were audited bit-for-bit:

| Model ID | Target Path | Expected SHA-256 Hash | Observed SHA-256 Hash | Verification Status |
|---|---|---|---|---|
| **M2** | `ml/flood/m2_upper_beas_flood_model.joblib` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | **VERIFIED (Bit-Identical)** |
| **M4** | `data/satellite_output/flood_multimodal_unet.pt` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | **VERIFIED (Bit-Identical)** |
| **M6** | `ml/landslide/m6_beas_susceptibility_rf.joblib` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | **VERIFIED (Bit-Identical)** |
| **M7** | `ml/landslide/m7_beas_trigger_lgbm.joblib` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | **VERIFIED (Bit-Identical)** |

Scientific constraint compliance:
- Zero retraining performed.
- Zero model weight modifications.
- Explicit provenance separation maintained across all endpoints (`OBSERVED`, `PREDICTED`, `MODELLED`, `DERIVED`, `SIMULATED`).

---

## 4. Database Schema & Migration Status

- **Migration Tool**: Alembic 1.14.0
- **Current Head**: `c4b1829e5a10` (`v3_4_device_sensor_schema`)
- **Migration History**:
  1. `6071286b9e46` (`v3_3_initial_schema`)
  2. `c4b1829e5a10` (`v3_4_device_sensor_schema`)
- **Active Tables (13)**:
  - `users`
  - `incidents`
  - `telemetry`
  - `model_runs`
  - `risk_assessments`
  - `alerts`
  - `audit_logs`
  - `stations`
  - `devices`
  - `sensors`
  - `calibration_records`
  - `device_heartbeats`
  - `sensor_observations`
- **Spatial Geometry Support**:
  - Production engine: PostgreSQL with PostGIS extension (`geometry(Geometry, 4326)`).
  - Development / Local fallback: SQLite with serialized GeoJSON/WKT fallback and Shapely geometry validation.

---

## 5. Test Suite Baseline Audit

A full test suite run executed 530 tests:
```text
530 passed, 0 failures, 0 errors, 12 warnings in 60.69s
```

### Warning Baseline Breakdown
A total of 12 non-fatal warnings were detected during test execution:
1. **StarletteDeprecationWarning (1)**: `fastapi/testclient.py:1` — `Using httpx with starlette.testclient is deprecated; install httpx2 instead.` (Harmless upstream Starlette/FastAPI deprecation warning).
2. **DeprecationWarning (1)**: `starlette/testclient.py:53` — `The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.` (Upstream AnyIO/Starlette internal alias).
3. **SAWarning (1)**: `backend/tests/test_database_layer.py:152` — `New instance <IncidentModel> conflicts with persistent instance` (Intentional test asserting rollback behavior on primary key collision).
4. **UserWarning (8)**: `sklearn/utils/validation.py:2830` — `X does not have valid feature names, but RandomForestClassifier/LGBMClassifier/StandardScaler was fitted with feature names` (Scikit-learn / LightGBM feature name checking when passing raw NumPy arrays during M6/M7 inference).
5. **UserWarning (1)**: `tests/test_upper_beas_benchmarks.py` — StandardScaler feature names warning.

All 12 warnings are classified as non-blocking and do not compromise system correctness or life-safety invariants.

---

## 6. Subsystem Verification Status

| Subsystem | Audit Status | Key Invariant / Verification |
|---|---|---|
| **Life-Safety Authorization Gateway** | VERIFIED | REST `POST /api/v1/alerts/{id}/authorize` strictly requires `SENIOR_INCIDENT_COMMANDER`. WebSocket authorization rejected (`WEBSOCKET_AUTHORIZATION_PROHIBITED`). |
| **Telemetry Ingestion & Idempotency** | VERIFIED | Deterministic SHA-256 event ID prevents duplicate processing; modified payloads with existing event ID trigger `TELEMETRY_INTEGRITY_VIOLATION` (409). |
| **Temporal Correctness Engine** | VERIFIED | Packets classified into `VALID`, `LATE`, `STALE`, `EXPIRED`, `INVALID`. Future clock skew > 120m rejected. |
| **Multi-Hazard Risk Engine** | VERIFIED | Probabilities bounded in $[0.0, 1.0]$. Failed models return `MODEL_UNAVAILABLE` rather than faking 0.0 or 0.5. |
| **CAP v1.2 Alerts** | VERIFIED | OASIS CAP v1.2 XML with character escaping and bilingual templates. |
| **Notification Engine** | VERIFIED | Missing external providers (NDMA Sachet, SMS, Sirens) report `NOT_CONFIGURED` without mock success faking. |
| **Event Bus & WebSockets** | AUDITED (SINGLE-WORKER) | In-process asyncio event bus is functional for single worker; requires distributed pub/sub documentation and boundary for multi-worker setups. |
| **Prometheus Metrics** | VERIFIED | `/metrics` operational; tracking request counts, latencies, telemetry volume, and model execution time. |
| **Database Backup & Recovery** | VERIFIED | `scripts/backup_db.py` and `scripts/restore_db.py` validated with SQLite and PostgreSQL compatibility. |

---

## 7. Baseline Maturity Classification

- **Scientific Layer**: LEVEL 1 (Research Prototype / Decision-Support)
- **Backend Architecture**: LEVEL 3 (Hardened Modular Monolith / Field-Pilot Candidate)
- **Operational Procedures**: LEVEL 2 (Runbook Defined / Supervised Pilot Ready)
- **External Public Alerts**: LEVEL 0 (Simulation / Gated / Non-Autonomous)

The baseline is verified and ready for v3.5 stress testing, failure injection, synthetic telemetry generation, and pilot deployment packaging.
