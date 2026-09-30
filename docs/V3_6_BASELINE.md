# FLOODY SHIELD v3.6 — Baseline Audit & System Inventory

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Starting Version:** v3.5.0  
**Target Version:** v3.6.0  
**Baseline Test Execution:** `547 passed, 12 warnings in 97.26s`  
**Database State:** SQLite (`data/floody_shield.db`), Alembic head revision `c4b1829e5a10`  
**Runtime Environment:** Python 3.11.9 on Windows NT (AMD64)  

---

## 1. Environment & Runtime Inventory

| Attribute | State / Value | Verification Method |
|:---|:---|:---|
| **Operating System** | Windows NT 10.0 (AMD64) | System telemetry / platform |
| **Python Runtime** | Python 3.11.9 (`.\.venv\Scripts\python.exe`) | `sys.version` |
| **Database Engine** | SQLite 3.x with PostGIS compatibility emulation | SQLAlchemy 2.0.44 |
| **FastAPI Version** | 0.115.0+ | Package metadata |
| **Alembic Revision** | `c4b1829e5a10 (head)` | `alembic current` |
| **Frozen Models** | 4 critical binary models verified bit-identical | SHA-256 hash checking |
| **Total Test Cases** | 547 passing tests | `pytest -q` |
| **Total Warnings** | 12 accepted third-party & test warnings | Warning audit |

---

## 2. Frozen Scientific ML Models (Zero-Change Invariant)

The scientific ML models M1 through M20 are completely frozen. The SHA-256 hashes of all binary weight artifacts have been verified bit-for-bit:

| Model ID | Relative Path | Expected SHA-256 | Actual SHA-256 | Status |
|:---|:---|:---|:---|:---|
| **M2** | `ml/flood/m2_upper_beas_flood_model.joblib` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | **VERIFIED BIT-IDENTICAL** |
| **M4** | `data/satellite_output/flood_multimodal_unet.pt` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | **VERIFIED BIT-IDENTICAL** |
| **M6** | `ml/landslide/m6_beas_susceptibility_rf.joblib` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | **VERIFIED BIT-IDENTICAL** |
| **M7** | `ml/landslide/m7_beas_trigger_lgbm.joblib` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | **VERIFIED BIT-IDENTICAL** |

No models have been retrained, modified, or altered in weight values.

---

## 3. Test Suite Starting Baseline

Test execution result:
```
547 passed, 12 warnings in 97.26s
```
- **Failures**: 0
- **Errors**: 0
- **Pass Rate**: 100.0%

---

## 4. Subsystem Status Audit

| Subsystem | Baseline State | Planned v3.6 Capability |
|:---|:---|:---|
| **Station Registry** | Schema defined; 5 pilot stations configured | Add full lifecycle state (`PLANNED` to `RETIRED`) & explicit metadata |
| **Physical Sensor HAL** | Basic models exist | Vendor-agnostic Hardware Abstraction Layer, engineering unit validation, range safety, single-sensor failure isolation |
| **LoRa Telemetry** | HTTP JSON ingestion only | Compact binary LPWAN protocol (51-222 byte bandwidth limit), CRC-16 integrity, packet codec |
| **Gateway Operations** | Generic REST endpoints | Gateway translation engine, sequence number gap analysis, offline chronological buffering & replay |
| **PostgreSQL / PostGIS** | SQLite dialect in dev environment | Dedicated dialect and spatial query verification harness (`test_postgres_postgis_verification.py`) |
| **Disaster Recovery** | Backup/restore script verified for SQLite | Full PostgreSQL production backup/restore and disaster recovery protocol documentation |
| **Firmware Reference** | None | Complete ESP32 + SX1262/SX1276 C++/Arduino firmware for field stations |
| **Life-Safety Gateway** | RBAC verified; commander authorization required | Maintained strictly: REST-only commander authorization; WebSockets prohibited |
