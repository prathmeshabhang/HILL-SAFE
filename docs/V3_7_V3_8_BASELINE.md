# FLOODY SHIELD v3.7–v3.8 — Baseline Audit & System Inventory

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Starting Baseline Version:** v3.6.0  
**Target Delivery:** v3.7 (Operational Pilot) + v3.8 (External Scientific Validation)  
**Baseline Test Execution:** `569 passed, 12 warnings in 72.22s`  
**Database Backend:** SQLite (`data/floody_shield.db`) with PostGIS compatibility emulation; PostgreSQL/PostGIS dialect verification harness  
**Alembic Head Revision:** `374d59487ca7 (head)`  
**Runtime Environment:** Python 3.11.9 on Windows NT 10.0 (AMD64)  
**System Classification:** **LEVEL 1 — PROTOTYPE / RESEARCH DECISION-SUPPORT** with verified, security-hardened physical-sensor and LoRa field-pilot backend.

---

## 1. System Inventory

| Component | State / Version | Verification Reference |
|:---|:---|:---|
| **Repository Baseline** | v3.6.0 | `backend/app/core/config.py` |
| **Test Suite Status** | 569 passed, 0 failures, 0 errors, 12 warnings | `pytest -q` |
| **Model Count** | Exactly 20 models (M1–M20) | Model registry & DAG |
| **Frozen Model Weights** | 4/4 models bit-identical SHA-256 | `tools/verify_model_hashes.py` |
| **Alembic Database Head** | `374d59487ca7` | `alembic current` |
| **LoRa LPWAN Stack** | Compact binary codec (36B/3-ch frame), CRC-16, IN865 band | `tools/lora/packet_codec.py` |
| **Hardware Abstraction** | HAL with physical bounds & single-sensor failure isolation | `hardware_abstraction.py` |
| **Life-Safety Gateway** | Human commander cryptographic sign-off over REST | REST authorization endpoint |
| **Station Lifecycle** | 8 states: `PLANNED` to `RETIRED` | Station schema & endpoints |
| **Pilot Station Profiles** | 5 stations in Upper Beas Basin (Manali, Kullu, Bhuntar, Aut, Larji) | `config/field_pilot/*.yaml` |

---

## 2. Frozen Scientific ML Models Status

The scientific models M1 through M20 remain strictly immutable. SHA-256 checksums verified bit-for-bit:

| Model ID | Relative File Path | Expected & Actual SHA-256 Hash | Immutability Status |
|:---:|:---|:---|:---:|
| **M2** | `ml/flood/m2_upper_beas_flood_model.joblib` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | **VERIFIED BIT-IDENTICAL** |
| **M4** | `data/satellite_output/flood_multimodal_unet.pt` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | **VERIFIED BIT-IDENTICAL** |
| **M6** | `ml/landslide/m6_beas_susceptibility_rf.joblib` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | **VERIFIED BIT-IDENTICAL** |
| **M7** | `ml/landslide/m7_beas_trigger_lgbm.joblib` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | **VERIFIED BIT-IDENTICAL** |

---

## 3. Current Scientific Evidence & Operational Readiness Assessment

| Area | Current Baseline Status | Planned v3.7–v3.8 Enhancement |
|:---|:---|:---|
| **Station Commissioning** | Basic status patch API exists | Formal commissioning workflow, field checklist, metadata tracking |
| **Telemetry Provenance** | JSON string in `provenance_json` | First-class `provenance` & `environment` attributes with strict separation |
| **Telemetry QC** | Range and timestamp checks | Rate-of-change spike checks, stuck flatline detection, battery anomaly checks |
| **Long-Run Reliability** | Single test cases | Multi-day simulation harness (24h, 72h, 7d) with loss & recovery metrics |
| **Validation Governance** | No central dataset registry | Formal dataset registry (`tools/validation/registry.py`) with SHA-256 hashes |
| **M6 Evidence** | Synthetic scarp training | 500+ GPS-verified stable-slope controls + independent landslide scarps |
| **M7 Evidence** | Synthetically perturbed events | 100+ independent storm-landslide episodes across Himachal Pradesh |
| **M10 Evidence** | Preliminary hydrograph fit | 2+ years continuous CWC Beas River gauge observations |
| **M11 Evidence** | SAR-HAND proxy evaluation | Independent satellite flood extents from Sentinel-1 / Copernicus |
| **M19 Evidence** | Theoretical arrival times | 50+ timestamped flash-flood propagation events |
| **M20 Evidence** | Prototype training weights | 500+ post-event damage survey ground-truth labeled examples |
| **Evidence Ledger** | Markdown summaries | Formal traceable claim-by-claim evidence ledger (`V3_8_EVIDENCE_LEDGER.md`) |
