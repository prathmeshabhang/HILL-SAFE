# FLOODY SHIELD v3.7 — Station Commissioning Protocol & Hardware Lifecycle

**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh  
**Standard:** CWC / IMD Automated Hydrometeorological Station Guidelines  
**Version:** v3.7.0  

---

## 1. Lifecycle State Machine

Each physical monitoring station progresses through a deterministic, auditable 5-stage lifecycle state machine:

```
┌───────────┐      Field Survey      ┌────────────┐     Hardware Mount     ┌─────────────┐
│  PLANNED  │ ─────────────────────> │  SURVEYED  │ ─────────────────────> │  INSTALLED  │
└───────────┘                        └────────────┘                        └─────────────┘
                                                                                  │
                                                                 5/5 Checks Passed│ (Senior Commander)
                                                                                  ▼
┌───────────┐      Decommission      ┌────────────┐   Automatic Failover   ┌─────────────┐
│  RETIRED  │ <───────────────────── │  OFFLINE   │ <───────────────────── │   ACTIVE    │
└───────────┘                        └────────────┘   (or DEGRADED)        └─────────────┘
```

---

## 2. Commissioning Verification Gates

A station CANNOT transition to `ACTIVE` until all five verification checks are certified by a `SENIOR_INCIDENT_COMMANDER` or `ADMIN`:

1. **`sensor_check`**: All connected physical transducers (rain gauge, radar stage, pore pressure, tilt) are actively transmitting plausible non-null data within calibrated physical bounds.
2. **`calibration_check`**: Zero-offset calibration and scale factor verification against traceable standards has been performed within the last 30 days.
3. **`lora_check`**: Reliable radio link verified with Received Signal Strength Indicator (RSSI) $\ge -115\text{ dBm}$ and Signal-to-Noise Ratio (SNR) $\ge -5\text{ dB}$.
4. **`battery_check`**: Power subsystem verified; solar charge controller operating and battery terminal voltage $\ge 12.2\text{ V}$ (or state-of-charge $\ge 70\%$).
5. **`timestamp_check`**: Real-Time Clock (RTC) and gateway NTP timestamp synchronization verified within $\pm 60\text{ seconds}$ of True UTC.

---

## 3. Commissioning REST API Endpoints

- **`POST /api/v1/stations`**: Register initial station in `PLANNED` state.
- **`POST /api/v1/stations/{id}/survey`**: Record field topography, GPS ground-truthing, and line-of-sight analysis.
- **`POST /api/v1/stations/{id}/install`**: Record hardware manifest, mast assembly, solar setup, and firmware revision.
- **`POST /api/v1/stations/{id}/commission`**: Enforce 5/5 gate verification. Sets status to `ACTIVE`, stamps `commissioned_at`, and logs `commissioned_by`.
- **`GET /api/v1/stations/{id}/commissioning`**: Retrieve complete, tamper-evident commissioning dossier.
