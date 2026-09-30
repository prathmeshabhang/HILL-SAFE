# FLOODY SHIELD v3.7 — Operational Pilot & Basin Telemetry Architecture

**Target Geography:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**System Classification:** Level 1 — Prototype / Research Decision-Support System  
**System Version:** v3.7 / v3.8  
**Status:** Field Pilot Operational Architecture Active  

---

## 1. Executive Summary

FLOODY SHIELD v3.7 advances the physical-sensor and LoRa telemetry foundation into an operational field-pilot telemetry network deployed across the Upper Beas River Basin. The operational pilot couples ruggedized low-power LoRaWAN field telemetry nodes with multi-channel backhaul gateway ingestion, strict idempotency and cryptographic deduplication, rigorous stream quality control (flatline and surge detection), formal station commissioning workflows, and aggregated health diagnostic telemetry.

---

## 2. Basin Telemetry Architecture

```
                                  UPPER BEAS BASIN
                                  
  [Solang Valley Node]  [Kothi Geotechnical]  [Manali Gauge]  [Allain Barrage]  [Pandoh Dam]
      (Rain + PWP)          (Tilt + Disp)        (River Stage)    (Hydro Flow)    (Reservoir)
           │                      │                    │                │              │
           └──────────────┬───────┴────────────────────┴────────────────┴──────────────┘
                          │ LoRa RF 865-867 MHz (SF7-SF12, BW125kHz, CR4/5)
                          ▼
             [Rohtang & Kullu Gateways]
              - Packet forwarder + CRC-16 check
              - Offline buffer / flash FIFO
              - Cellular 4G / Satellite backhaul
                          │
                          ▼
            [FastAPI Ingestion Endpoint]
             (/api/v1/telemetry, /batch, /lora/frame)
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
   [Quality Gate]                 [Idempotency Engine]
   - Spatial AOI containment      - SHA-256 event ID
   - Temporal freshness & skew    - Conflict detection
   - Physical plausibility        - Tamper detection
   - Stream QC: Flatline & Spike
         │
         ▼
[PostgreSQL / PostGIS & Time-Series DB]
 (Provenanced: REAL, SIMULATED, REPLAY, TEST)
```

---

## 3. Physical Sensor Station Inventory

| Station Code | Location / Reach | Elevation (m) | Latitude | Longitude | Primary Sensor Instrumentation | Communication Channel |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `STN_SOAL_01` | Solang Valley Nallah | 2,480 | 32.3167°N | 77.1556°E | Dual Tipping Bucket + Vibrating Wire PWP | LoRaWAN + 4G Backhaul |
| `STN_KOTI_01` | Kothi / Gulaba Slope | 2,530 | 32.3214°N | 77.1989°E | MEMS Biaxial Tiltmeter + Crackmeter | LoRaWAN (Relayed via Rohtang) |
| `STN_MANA_01` | Manali Bridge (Beas) | 2,050 | 32.2396°N | 77.1887°E | FMCW Radar River Gauge + Ultrasonic Stage | LoRaWAN + Ethernet Backhaul |
| `STN_ALEN_01` | Allain Duhangan Intake | 1,920 | 32.2150°N | 77.2100°E | Hydrostatic Pressure Stage + Water Temp | LoRaWAN + Private Fiber |
| `STN_PAND_01` | Pandoh Dam Gorge | 900 | 31.6700°N | 77.0600°E | Continuous Acoustic Doppler Velocity Meter | 4G LTE + Satellite Backup |

---

## 4. Operational Invariants

1. **Zero Autonomous Dispatch**: Life-safety emergency alerts are never autonomously triggered by field telemetry spikes. A human-in-the-loop cryptographically signed authorization by a `SENIOR_INCIDENT_COMMANDER` is unconditionally required.
2. **Data Provenance Gating**: Every observation is explicitly tagged with `provenance` (`REAL`, `SIMULATED`, `REPLAY`, `TEST`) and `environment` (`FIELD`, `TEST`, `LAB`, `STAGING`), preventing simulated or bench-test data from contaminating operational field baselines.
3. **Hardware Degradation Isolation**: If a physical sensor suffers flatlining, drift, or excessive packet loss, the station is automatically downgraded to `DEGRADED` or `CRITICAL`, isolating its input from downstream scientific model pipelines.
