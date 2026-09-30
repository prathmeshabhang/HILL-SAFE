# FLOODY SHIELD v3.6 — Failure Modes & Effects Analysis (FMEA)

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** Physical Hardware Failure Modes, Degraded States, Environmental Hazards, and Mitigation Architecture.

---

## 1. FMEA Risk Priority Matrix

| Failure Mode ID | Component | Cause / Hazard | Local Effect | System Effect | Detection | Mitigation / Defense |
|:---:|:---|:---|:---|:---|:---|:---|
| **FM-01** | Optical Rain Sensor | Pine needle / silt blockage in funnel | Fails to register tips during heavy rain | M1 nowcasting model underestimates precipitation rate | M9 anomaly screening detects flatline during satellite radar rain | Dual-sensor redundancy + automatic anomaly flagging (`SUSPECT`) |
| **FM-02** | Radar River Stage | Riverbank scour washes away mounting mast | Complete loss of river gauge signal | Loss of stage observation at key confluence | Station heartbeat timeout (>24h `OFFLINE`) | Cantilever set back on solid bedrock; upstream warning from tributary gauges |
| **FM-03** | Battery Power | 10 days continuous zero-solar monsoon fog | Battery voltage drops below 11.0V | Node power brownout and reboot loops | Hardware battery voltage telemetry in LoRa header | Low-power hibernation mode; dynamic sampling interval increase (60s $\to$ 300s) |
| **FM-04** | LoRa Transceiver | Direct or induced lightning EMP strike | RF front-end burnout; no packets transmitted | Station drops off radio network | Consecutive sequence number gap detected at gateway | Coaxial lightning surge arresters; 16mm copper ground rod with $<5\ \Omega$ resistance |
| **FM-05** | Cellular Backhaul | Fiber cut along NH-3 due to highway landslide | Gateway loses internet link to backend | Telemetry delayed to EOC decision dashboard | Gateway heartbeat failure; connection ping timeout | Flash ring-buffering (5,000 packets) + automatic chronological replay on reconnect |
| **FM-06** | Subsurface Piezometer | Shear rupture along active landslide slip plane | Cable sheared; sensor resistance open-circuit | Loss of pore pressure data on critical cut-slope | Electrical loop resistance test fails | Dual borehole instrumentation at staggered slope depths |
| **FM-07** | Clock Drift | Temperature variation in uncompensated crystal | Node timestamp drifts $\pm 15$ min | Incorrect temporal alignment in hydrologic models | Gateway compares node epoch vs. GPS gateway time | GPS time-sync pulse; backend latency correction |

---

## 2. Invariant: Single-Sensor Failure Isolation

A foundational reliability invariant of FLOODY SHIELD v3.6 is **Single-Sensor Failure Isolation**:
- If any individual physical sensor on a multi-sensor station suffers electrical failure, physical destruction, or out-of-bounds readings, the Hardware Abstraction Layer (HAL) MUST isolate that individual channel.
- The station health is marked as `DEGRADED` rather than failing the entire station or halting the backend ingestion pipeline.
- Healthy sibling sensors (e.g. river water level and soil moisture on the same station) continue to be ingested and fed into active scientific models without interruption.
