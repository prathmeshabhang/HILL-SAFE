# FLOODY SHIELD v3.4 — Failure Modes, Defense Mechanisms & Mitigation Runbook

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Scope**: Taxonomy of Operational, Environmental & Algorithmic Failure Modes  

---

## 1. Failure Taxonomy Matrix

| Failure Mode | Failure Severity | Root Cause | System Detection | Automatic Mitigation | Operator Action Required |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Field Node Power Depletion** | High | Prolonged monsoon overcast (> 5 days) depleting solar battery | Battery voltage $< 11.5\text{V}$ reported in heartbeat | Health transitions to `CRITICAL`; station marked `DEGRADED` | Dispatch field battery replacement team |
| **Wireless Telemetry Blackout** | High | Landslide severed cellular fiber; LoRa gateway RF shadowing | No heartbeat received for $> 24\text{ hours}$ | Device marked `OFFLINE`; risk engine switches to satellite/radar proxy | Check repeater links at Rohtang / Jalori Pass |
| **Sensor Physical Drifting** | Moderate | Silt sedimentation on radar reflector or diaphragm clogging | Quality gate spikes; physical range violation | Anomaly filter flags `SUSPECT`; calibration marked `DUE_SOON` | Schedule flushing and recalibration |
| **Replay Tampering Attack** | Critical | Malicious or corrupt proxy injecting conflicting values with valid sequence | SHA-256 hash collision with $|\Delta v| > 10^{-5}$ | HTTP 409 `TELEMETRY_INTEGRITY_VIOLATION`; audit alert logged | Inspect gateway authentication logs |
| **Sensor Clock Desynchronization** | Moderate | GPS lock failure or drift on remote edge MCU | Timestamp $> 120\text{ min}$ future skew | HTTP 422 `TELEMETRY_FUTURE_TIMESTAMP`; packet rejected | Resync NTP / RTC on gateway |
| **Upstream Radar/Satellite Outage** | Moderate | IMD radar maintenance or Copernicus pass delay | Data sources probe detects latency $> \text{threshold}$ | Risk engine enters `DEGRADED_MODE`; confidence lowered to `LOW_CONFIDENCE` | Monitor regional AWS radar backup |
| **Landslide Dam False Breach** | Critical | Spurious piezometer spike triggering breach model | Multi-evidence scorer checks geophone & water level before trigger | M12 breach suppressed if acoustic geophone does not confirm | Verify with aerial drone survey at Sainj |
| **Premature / Rogue Alert Dispatch** | Fatal (Life-Safety) | Algorithmic hallucination or unverified automated trigger | Human authorization gateway blocks autonomous dispatch | Alert held in `PENDING_APPROVAL`; requires Commander cryptographic key | Commander reviews evidence before sign-off |
| **WebSocket Stream Poisoning** | High | Unauthorized attempt to broadcast or authorize via open WS | WebSocket controller intercepts non-REST authorization frame | `WEBSOCKET_AUTHORIZATION_PROHIBITED` security frame emitted | Restrict commander credentials |
| **Database Storage Exhaustion** | High | Rapid raster accumulation from multi-temporal SAR scenes | Disk probe detects $< 10\%$ free space | Background job archives old scenes to cold storage; triggers alert | Run `scripts/backup_db.py` and purge cold data |

---

## 2. Emergency Operational Runbooks

### 2.1 Handling Degraded Mode in Multi-Hazard Risk Engine
When `confidence_state` transitions to `LOW_CONFIDENCE` or `UNAVAILABLE`:
1. Check `GET /api/v1/system/data-sources` to identify which upstream feed is disconnected.
2. In the Emergency Operations Center dashboard, visual indicators shift from green to amber.
3. The system automatically applies conservative fallback safety buffers:
   - Warning thresholds are lowered by $15\%$.
   - Evacuation corridor buffers along the Beas riverbed are widened by $100\text{ meters}$.

### 2.2 Alert Cancellation Procedure
If a flood or landslide advisory was drafted or authorized, but real-time telemetry indicates water levels have dropped below warning stage:
1. Incident Commander executes `POST /api/v1/alerts/{alert_id}/cancel`.
2. A cancellation notice (`msgType="Cancel"`) is rendered in OASIS CAP v1.2 format.
3. Notification dispatcher broadcasts cancellation notice across all channels to avoid public panic.
4. Tamper-evident audit log records cancellation reason, commander identity, and timestamp.
