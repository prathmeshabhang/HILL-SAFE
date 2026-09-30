# FLOODY SHIELD v3.6 — Sensor Calibration & Drift Management

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** Sensor Calibration Protocols, Mathematical Adjustment Models, Re-Calibration Schedules, and Audit Trails.

---

## 1. Calibration Mathematics

FLOODY SHIELD applies a linear sensor transfer function in the Hardware Abstraction Layer (HAL):

$$\text{Value}_{\text{calibrated}} = \left(\text{Value}_{\text{raw}} \times \text{ScaleFactor}\right) + \text{ZeroOffset}$$

Where:
- $\text{Value}_{\text{raw}}$: Direct uncompensated physical transducer reading.
- $\text{ScaleFactor}$: Multiplicative gain correction factor (dimensionless, nominal $1.000$).
- $\text{ZeroOffset}$: Additive baseline shift compensation in native physical units.

---

## 2. Sensor-Specific Calibration Protocols

### 2.1 Optical / Tipping Bucket Rain Gauge
- **Field Reference**: Dynamic Field Calibrator with precision peristaltic pump / nozzle.
- **Test Points**:
  - Low Intensity: 20 mm/h
  - Moderate Intensity: 60 mm/h
  - Cloudburst Intensity: 120 mm/h
- **Tolerance**: $\pm 2.0\%$ volumetric volume.
- **Adjustment**: Fine-pitch mechanical calibration stop-screws beneath tipping bucket.

### 2.2 Radar River Stage Gauge
- **Field Reference**: Laser Distance Meter (Leica DISTO D810) or weighted sounding tape lowered to stilling basin.
- **Test Points**: Low-flow baseline, intermediate rock outcrop datum, bridge benchmark.
- **Tolerance**: $\pm 2\text{ mm}$ absolute distance.
- **Adjustment**: Digital offset calibration in radar sensor parameter memory.

### 2.3 Vibrating Wire Piezometer (PWP)
- **Field Reference**: Deadweight tester or calibrated pneumatic pressure comparator.
- **Polynomial Calibration**:
  $$P = G \times (R_0 - R_1) + K \times (T_1 - T_0) - (S_1 - S_0)$$
  Where $G$ is gauge factor (kPa/digit), $R$ is vibrating wire frequency reading, $K$ is thermal coefficient, and $S$ is barometric pressure correction.

---

## 3. Calibration Recording API & Auditability

Every field calibration event is permanently logged with technician identity, standard reference traceability, zero offset, scale factor, and notes:

```bash
curl -X POST http://localhost:8000/api/v1/sensors/DEV_MANALI_01_RAIN_GAUGE/calibrate \
  -H "Authorization: Bearer $ANALYST_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "calibrated_by": "Senior Hydrologist Er. Sharma (CWC)",
    "standard_reference": "NIST-Traceable Calibrator Drip-Kit SN-9042",
    "zero_offset": 0.0,
    "scale_factor": 1.024,
    "notes": "Pre-monsoon annual calibration check. 2.4% under-catch corrected."
  }'
```

### Expiration & Drift Enforcement
- Calibration interval: **180 days (6 months)** for hydrological instruments; **365 days** for geotechnical boreholes.
- When current time exceeds `next_calibration_at`:
  - `calibration_status` transitions to `EXPIRED`.
  - Ingested packets are flagged with `CALIBRATION_EXPIRED` quality codes.
  - Station health transitions to `CALIBRATION_REQUIRED` / `DEGRADED`.
