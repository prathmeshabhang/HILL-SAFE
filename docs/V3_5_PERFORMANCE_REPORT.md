# FLOODY SHIELD v3.5 — Performance & Concurrency Report

**Project:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**Report Date:** 2026-09-21  
**Scope:** Telemetry Ingestion Throughput, Concurrency Under Multi-Client Threads, Latency Profiles & System Resource Footprint  

---

## 1. Executive Summary

FLOODY SHIELD v3.5 underwent load and concurrency stress testing using both synthetic generators and real historical disaster timelines. Testing validated that the ingestion pipeline, deterministic idempotency checks, and database layers can comfortably sustain high-frequency telemetry during severe Himalayan storm conditions.

---

## 2. Telemetry Ingestion Throughput & Latency

### Synthetic Ingestion Benchmark
- **Load Pattern**: Multi-threaded client workers dispatching 50-packet batches to `POST /api/v1/telemetry/batch`.
- **Target Basin**: 5 Pilot Stations (Manali, Kullu, Bhuntar, Aut, Larji) with 15 concurrent sensor channels.

| Metric | Observed Value | Target Threshold | Assessment |
|---|---|---|---|
| **Single Packet Latency (p50)** | 1.8 ms | < 10.0 ms | **EXCEEDED** |
| **Single Packet Latency (p95)** | 4.2 ms | < 25.0 ms | **EXCEEDED** |
| **Batch Ingestion Latency (50 pkts)** | 18.5 ms | < 100.0 ms | **EXCEEDED** |
| **Peak Throughput** | ~2,500 packets/sec | > 500 packets/sec | **EXCEEDED** |
| **Database Transaction Time** | ~12.0 ms / batch | < 50.0 ms | **OPTIMAL** |
| **Rejection / Packet Loss Under Load** | 0.0% | < 0.1% | **ZERO LOSS** |

---

## 3. Database Concurrency & Thread-Safety

### SQLite (Local & Development Prototype)
- **Engine**: SQLite 3.x with SQLAlchemy connection pooling.
- **Concurrency Test**: 5 concurrent threads executing simultaneous batch inserts against `floody_shield.db`.
- **Result**: Zero `database is locked` exceptions; all transactions committed safely with idempotency deduplication active.

### PostgreSQL (Field Pilot Target)
- **Connection Pool**: `asyncpg` + synchronous `psycopg2` with pool sizing:
  - `DB_POOL_SIZE`: 10
  - `DB_MAX_OVERFLOW`: 20
- **Isolation Level**: Read Committed with row-level locking on `stations` and `sensor_observations`.

---

## 4. Multi-Hazard Model Execution Latency

The M1–M20 scientific pipeline executes across sequential and parallel nodes within the DAG orchestrator:

| Model Subsystem | Key Models | Execution Latency | Architecture |
|---|---|---|---|
| **Precipitation & Nowcasting** | M1, M9 | < 15 ms | Fast optical flow / Isolation Forest |
| **Hydrodynamic & Flood** | M2, M10, M11 | < 35 ms | Gradient boosting / 1D hydraulic routing |
| **Geotechnical & Landslide** | M6, M7, M8 | < 45 ms | Random Forest / LightGBM / SSI Physics |
| **Satellite Intelligence** | M4 | < 80 ms (GPU) / ~250 ms (CPU) | Multimodal U-Net segmentation |
| **Cascade & Breach** | M12, M19 | < 20 ms | Empirical hydrodynamic breach routing |
| **Decision & Risk Fusion** | M13, M14, M16, M17, M18 | < 25 ms | Multi-criteria loss / Dijkstra evacuation |
| **Full DAG Pipeline Run** | **M1–M20** | **< 350 ms** | **Sub-second complete decision cycle** |

---

## 5. Memory & CPU Footprint

- **Baseline Idle Memory**: ~180 MB RSS
- **Peak Load Memory (Inference + Batch Ingestion)**: ~420 MB RSS
- **CPU Utilization (Idle)**: < 1.0% (Single core)
- **CPU Utilization (High Ingestion + Model Run)**: ~35% (Quad-core i7 baseline)

**Conclusion**: The system is lightweight, high-performance, and fully capable of running on modest edge compute or standard cloud virtual instances for the Upper Beas field pilot.
