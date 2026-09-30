# FLOODY SHIELD v3.6 — Canonical Telemetry Contract

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** Data Schema Definitions, Engineering Units, Temporal Boundaries, Idempotency, and Quality Gating Rules.

---

## 1. Canonical Telemetry Packet Schema

All incoming data—regardless of whether received via LoRa LPWAN binary frames, cellular MQTT, or automated weather station (AWS) JSON pushes—is normalized into the canonical `TelemetryPacketRequest` before entering quality screening and model execution:

```json
{
  "source_id": "UPPER_BEAS_LORA_LPWAN",
  "station_id": "ST_MANALI_01",
  "device_id": "DEV_MANALI_01",
  "sensor_id": "DEV_MANALI_01_RAIN_GAUGE",
  "observed_at": "2026-09-21T14:30:00.000Z",
  "received_at": "2026-09-21T14:30:02.150Z",
  "measurement_type": "RAIN_GAUGE",
  "value": 45.2,
  "unit": "mm/h",
  "sequence_number": 1042,
  "firmware_version": "v1.0-lora",
  "quality_hint": null
}
```

---

## 2. Standard Physical Measurement Types & Units

Strict engineering unit safety is enforced across the entire backend:

| Measurement Type | Physical Phenomenon | Canonical Unit | Valid Physical Bounds | Out-of-Bounds Action |
|:---|:---|:---:|:---:|:---|
| `RAIN_GAUGE` | Precipitation Intensity | `mm/h` | `0.0` to `500.0` | Flag `OUT_OF_BOUNDS`, reject reading |
| `WATER_LEVEL` | River Stage / Surface Elevation | `m` | `0.0` to `35.0` | Flag `OUT_OF_BOUNDS`, reject reading |
| `SOIL_MOISTURE` | Volumetric Water Content | `%` | `0.0` to `100.0` | Clamp or reject reading |
| `PORE_WATER_PRESSURE`| Subsurface Hydrostatic Pressure | `kPa` | `-100.0` to `2000.0` | Flag `OUT_OF_BOUNDS`, reject reading |
| `TILT` | Cut-Slope Displacement Angle | `deg` | `-90.0` to `+90.0` | Flag `OUT_OF_BOUNDS`, reject reading |
| `VIBRATION` | Ground Acceleration (Debris Flow)| `mm/s2` | `0.0` to `1000.0` | Flag `OUT_OF_BOUNDS`, reject reading |
| `TEMPERATURE` | Ambient Air Temperature | `C` | `-40.0` to `+60.0` | Flag `OUT_OF_BOUNDS`, reject reading |
| `BATTERY` | Node Bus Supply Voltage | `V` | `2.5` to `15.0` | Update device health state |

---

## 3. Temporal Validation State Machine

Telemetry timestamps are evaluated with respect to system UTC time at ingestion:

| Condition | Latency / Skew | Temporal State | Ingestion Action |
|:---|:---|:---|:---|
| **Future Skew > 120 min** | $t_{obs} > t_{now} + 7200\text{ s}$ | `REJECTED` | HTTP 422 `TELEMETRY_FUTURE_TIMESTAMP` |
| **Future Skew 5–120 min** | $t_{obs} > t_{now} + 300\text{ s}$ | `INVALID` | Ingested, flagged `CRITICAL_ERROR` |
| **Normal / Real-Time** | $0 \le t_{now} - t_{obs} \le 3600\text{ s}$ | `VALID` | Ingested, flagged `FRESH` |
| **Late Arrival** | $1\text{ h} < t_{now} - t_{obs} \le 6\text{ h}$ | `LATE` | Ingested, flagged `FRESH` |
| **Stale Arrival** | $6\text{ h} < t_{now} - t_{obs} \le 24\text{ h}$ | `STALE` | Ingested, flagged `STALE` |
| **Expired Observation** | $t_{now} - t_{obs} > 24\text{ h}$ | `EXPIRED` | Ingested, flagged `EXPIRED` |

---

## 4. Idempotency & Tamper-Detection Contract

To guarantee that duplicate transmissions across replayed LoRa frames or retried HTTP batches do not corrupt time-series or trigger spurious model runs:
1. **Source Event ID / Hash**: Deterministic SHA-256 hash computed over:
   $$\text{Hash} = \text{SHA256}(\text{station\_id} + \text{sensor\_id} + \text{observed\_at} + \text{sequence\_number})$$
2. **Duplicate Replay**: If the hash already exists and the recorded value matches the incoming value, the backend returns HTTP 200 with `status="DUPLICATE"` and `is_duplicate=True` without inserting duplicate rows.
3. **Payload Tampering Detection**: If the hash matches an existing record but the reported numerical value differs ($|\Delta| > 10^{-5}$), the system raises **HTTP 409 `TELEMETRY_INTEGRITY_VIOLATION`** and logs a security event in the tamper-evident audit ledger.
