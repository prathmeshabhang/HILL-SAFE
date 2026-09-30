# FLOODY SHIELD v3.6 — Field Commissioning Runbook

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** Physical On-Site Installation, Structural Mounting, Antenna Alignment, Grounding, and System Sign-off.

---

## 1. Field Station Commissioning Workflow

Field installation progresses through 6 standardized phases in compliance with CWC (Central Water Commission) and IMD (India Meteorological Department) guidelines:

```
[ Phase 1: Site Survey & Foundation Inspection ]
                        |
                        v
[ Phase 2: Tower Erection & Sensor Mounting ]
                        |
                        v
[ Phase 3: Solar & Battery Power Hookup ]
                        |
                        v
[ Phase 4: Grounding & Lightning Protection ]
                        |
                        v
[ Phase 5: LoRa Link Margin & Radio Verification ]
                        |
                        v
[ Phase 6: Live Smoke Telemetry & Station Sign-off ]
```

---

## 2. Detailed Installation Standards

### 2.1 Sensor Mounting Standards
- **Radar River Gauge**:
  - Mounted on a 3.0 m galvanized cantilever steel arm projecting over the lowest dry-season river flow channel.
  - Must maintain vertical perpendicularity (plumb line $\le 1^\circ$ tilt) to avoid false echo degradation.
  - Zero datum must be surveyed using differential GPS (DGPS) or total station relative to the Survey of India (SOI) benchmark.
- **Tipping Bucket / Optical Rain Gauge**:
  - Mounted atop a rigid 1.5 m pedestal away from tree canopies and overhangs.
  - Horizon clearance angle: no obstruction exceeding $30^\circ$ from the horizontal plane.
  - Circular bullseye bubble level centered during bracket tightening.
- **Pore Water Pressure (PWP) Transducers**:
  - Lowered into 76 mm drilled exploratory boreholes on the scarp slip surface.
  - Packed in uniform clean silica sand filter pack (0.5–1.0 m thickness) and sealed above with bentonite clay pellets.

### 2.2 Electrical & Grounding Standards
- Dedicated grounding rod: 3.0 m long, 16 mm diameter copper-bonded steel rod driven into riverbed soil.
- Maximum allowable ground resistance: **$< 5\ \Omega$** (measured with 3-point earth ground tester).
- All antenna coax cables equipped with bulk-head N-type coaxial surge protectors connected directly to the master ground bus bar.

### 2.3 Antenna Alignment & RF Link Margin
- High-gain (5.8 dBi) fiberglass omnidirectional collinear antenna mounted atop mast.
- Minimum Receive Signal Strength Indicator (RSSI) at gateway: $\ge -110\text{ dBm}$.
- Minimum Signal-to-Noise Ratio (SNR): $\ge -5\text{ dB}$.

---

## 3. Commissioning API Transition & Handover

Once the station passes all physical checks, the field technician updates the lifecycle status via the REST API from `PLANNED` $\to$ `COMMISSIONED` $\to$ `ACTIVE`:

```bash
curl -X PATCH http://localhost:8000/api/v1/stations/ST_MANALI_01/status \
  -H "Authorization: Bearer $ANALYST_JWT" \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE"}'
```

The system automatically logs the commissioning timestamp in the tamper-evident audit ledger and begins incorporating the station's real-time observations into the M1–M20 multi-hazard risk engine.
