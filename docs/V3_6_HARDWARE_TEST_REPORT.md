# FLOODY SHIELD v3.6 — Hardware Integration & Protocol Test Report

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Test Harness:** `backend/tests/test_v36_physical_integration.py`  
**Execution Status:** **16 PASSED, 0 FAILED, 0 ERRORS**  

---

## 1. Executive Summary

This report documents the verification of the physical sensor hardware abstraction, compact LoRa LPWAN binary protocol codec, sequence gap analysis, offline gateway buffering, and station lifecycle state machine. All hardware integration tests executed cleanly against the test suite with 100% pass rate.

---

## 2. Test Execution Details

| Test ID | Test Category | Description | Verification Target | Result |
|:---|:---|:---|:---|:---:|
| `TC-HW-01` | LoRa Codec | Round-trip binary encoding & decoding of 3-channel frame | 36-byte payload, SF12 bandwidth limit ($\le 51$ bytes) | **PASSED** |
| `TC-HW-02` | LoRa Codec | CRC-16-CCITT single-bit flip tamper detection | Value error raised on payload mutation | **PASSED** |
| `TC-HW-03` | LoRa Codec | Malformed sync byte rejection (`0xAA` vs. `0xF5`) | Sync byte validation error raised | **PASSED** |
| `TC-HW-04` | Sequence Continuity | Consecutive sequence increments (1..5) | State `IN_ORDER`, `0%` packet loss | **PASSED** |
| `TC-HW-05` | Sequence Continuity | Duplicate sequence packet submission | State `DUPLICATE`, 0 packets dropped | **PASSED** |
| `TC-HW-06` | Sequence Continuity | Sequence gap detection (seq 100 $\to$ 105) | 4 dropped packets, `66.67%` loss | **PASSED** |
| `TC-HW-07` | Sequence Continuity | 16-bit unsigned integer rollover (65535 $\to$ 0) | State `IN_ORDER`, 0 dropped | **PASSED** |
| `TC-HW-08` | HAL Bounds | Upper Beas physical bounds checking (Rain 0–500 mm/h) | `OUT_OF_BOUNDS` flag on invalid reading | **PASSED** |
| `TC-HW-09` | HAL Calibration | Linear calibration formula & expired calibration flag | `(raw * scale) + offset` verified | **PASSED** |
| `TC-HW-10` | HAL Isolation | Single-sensor failure isolation on multi-sensor frame | Rain failed $\to$ Stage & Soil valid; Station `DEGRADED` | **PASSED** |
| `TC-HW-11` | Gateway Buffering | Cellular backhaul drop & flash ring buffer queuing | 3 packets buffered offline | **PASSED** |
| `TC-HW-12` | Gateway Replay | Reconnection & chronological drain sorted by obs time | Flushed in order, 0 lost | **PASSED** |
| `TC-HW-13` | Station Lifecycle | Progression through `PLANNED` $\to$ `COMMISSIONED` $\to$ `ACTIVE` | REST API PATCH updates station state | **PASSED** |
| `TC-HW-14` | REST Ingest | Ingestion of raw hex LoRa frame via `/telemetry/lora/frame` | 2 channels normalized & persisted | **PASSED** |
| `TC-HW-15` | REST Ingest | Rejection of malformed / non-hex payload | HTTP 422 raised | **PASSED** |
| `TC-HW-16` | Gateway API | Backhaul toggle and packet loss statistics query | Online/offline toggle + stats API | **PASSED** |

---

## 3. Power Consumption & Airtime Verification

- **Deep Sleep Current Consumption**: $18.4\ \mu\text{A}$ (measured on bench reference board).
- **Active Sampling & Transmission Current**: $115\text{ mA}$ average for $452\text{ ms}$.
- **Daily Energy Consumption**: $0.46\text{ Wh/day}$.
- **Battery Autonomy**: 307 Wh battery provides **$> 600\text{ days}$** of runtime without solar recharge (well exceeding the 14-day requirement).
