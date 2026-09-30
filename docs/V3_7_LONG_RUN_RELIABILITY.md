# FLOODY SHIELD v3.7 — Long-Run Reliability & Soak Testing Report

**Test Harness:** `tools/reliability/long_run_harness.py`  
**Evaluation Scope:** 24h, 72h, and 7d continuous multi-station telemetry simulation  
**Target Basin:** Upper Beas River Basin (5 monitoring stations)  

---

## 1. Objectives & Metrics

The long-run reliability test evaluates system persistence stability under continuous telemetry loads, high packet delivery ratio (PDR), duplicate packet quarantine, real-time QC flag detection, and memory leak absence.

### Key Performance Indicators (KPIs)
- **Packet Delivery Ratio (PDR):** Target $\ge 98.0\%$
- **Duplicate Isolation:** $100\%$ duplicate detection without database integrity errors
- **Throughput:** $\ge 50\text{ packets/sec}$ sustained ingestion rate
- **Failure Gating:** Complete isolation of corrupted or uncommissioned sensor packets

---

## 2. 24-Hour Soak Test Benchmark Results

| Parameter | Observed Benchmark | Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Simulated Duration** | 24 Hours (96 cycles/station) | 24 Hours | **PASS** |
| **Monitored Stations** | 5 Basin Stations | 5 Stations | **PASS** |
| **Transmitted Packets** | 493 | - | - |
| **Accepted Observations** | 480 | - | - |
| **Quarantined Duplicates** | 13 | All duplicates quarantined | **PASS** |
| **Packet Delivery Ratio (PDR)** | **100.00%** | $\ge 98.0\%$ | **PASS** |
| **Ingestion Throughput** | **77.99 pkts/sec** | $\ge 50.0\text{ pkts/sec}$ | **PASS** |
| **QC Flatlines Flagged** | 6 | Automatic flagging | **PASS** |
| **Elapsed Execution Time** | 6.32 seconds | - | - |
| **Overall Verdict** | **PASS** | - | **PASS** |

Detailed machine-readable metrics are persisted at: `reports/reliability/long_run_summary.json`.
