# Model Card — M19: Time-to-Impact Prediction Engine

**Floody Shield — Predict • Protect • Preserve**
AOI: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India

---

## 1. Model Overview

| Field | Value |
|-------|-------|
| Model ID | M19 |
| Full Name | Time-to-Impact Prediction Engine |
| Domain | Impact Timing |
| Version | 1.0.0 |
| Status | PHYSICS_PROOF_OF_CONCEPT; ML_INSUFFICIENT_EVIDENCE |
| Benchmark Gap | Minimum benchmark: 50+ timestamped events (preferred: 200+). Current: 3 published Himalayan events (Pareechu 2005, Sun Kosi 2014, Chamoli 2021) — 0 Upper Beas–specific events. ML quantile regression correctly declared INSUFFICIENT_EVIDENCE. Upgrade path: 50+ real timestamped hazard-arrival observations from CWC gauge records + district response logs. |
| Artifact | No ML artifact (kinematic baseline; ML = INSUFFICIENT_EVIDENCE) |

## 2. Purpose

M19 estimates the **time window until a hazard reaches an impact point** (road, bridge, settlement, evacuation route) given its current source location and relevant hydrodynamic or geomechanical parameters.

Output is expressed as P10/P50/P90 quantiles (minutes) providing an uncertainty-aware time window rather than a point estimate.

## 3. Model Architecture

```
Input (hazard type, distance, speed parameters)
         │
         ▼
┌─────────────────────────────────┐
│  KINEMATIC PHYSICS BASELINE     │  ← PRIMARY (always active)
│                                 │
│  Flood/Outburst:                │
│    Manning wave speed estimate  │
│    or M12-supplied wave speed   │
│                                 │
│  Landslide/Debris:              │
│    Hungr (1995) empirical       │
│    V ≈ 2.7 × √H [m/s]          │
│                                 │
│  Saturation factor:             │
│    +10% speed per 0.1 sat > 0.5 │
└─────────────────────────────────┘
         │
         ▼
  P50 = distance / speed × 60 min
  P10 = P50 at +30% speed
  P90 = P50 at −30% speed
         │
         ▼
┌─────────────────────────────────┐
│  ML QUANTILE REGRESSION         │  ← INSUFFICIENT_EVIDENCE
│  (GBR quantile loss q=0.1/0.5/0.9)  │   No real event timestamps
└─────────────────────────────────┘     available for Upper Beas
```

## 4. Input / Output Contract

### Input
```python
M19TimeToImpactInput(
    impact_type="FLOOD_INUNDATION",
    distance_km=15.0,
    wave_speed_kmh=21.0,       # from M12 if available
    peak_discharge_m3s=800.0,  # from M10
    channel_slope_pct=4.0,
    soil_saturation_ratio=0.7,
    data_quality=0.85,
)
```

### Output
```python
M19TimeToImpactOutput(
    model="M19_TIME_TO_IMPACT",
    impact_type="FLOOD_INUNDATION",
    p10_minutes=31.4,   # earliest credible
    p50_minutes=42.9,   # best estimate
    p90_minutes=61.3,   # latest credible
    confidence=0.595,
    status="PREDICTED",
    method="KINEMATIC_BASELINE",
    uncertainty_note="ML declared INSUFFICIENT_EVIDENCE ...",
)
```

## 5. Physical References

| Relationship | Formula | Reference |
|-------------|---------|-----------|
| Manning open-channel | V = (1/n)·R^(2/3)·S^(1/2) | Manning (1891) |
| Debris-flow runout | V ≈ 2.7√H [m/s] | Hungr et al. (1995) |
| P10/P90 uncertainty | ±30% wave speed | NDMA (2010) guidance |
| Outburst wave speed | 21.0 km/h | M12 Froehlich calibration |

## 6. Himalayan Benchmark Validation

| Event | Distance (km) | Observed (h) | Predicted P50 (h) | In P10–P90? |
|-------|-------------|-------------|-----------------|------------|
| Pareechu GLOF 2005 | 30.0 | 1.4 | 1.43 | ✓ |
| Sun Kosi (Jure) 2014 | 22.0 | 1.2 | 1.22 | ✓ |
| Chamoli GLOF 2021 | 15.0 | 0.7 | 0.70 | ✓ |

> [!NOTE]
> Benchmark wave speeds are sourced from published post-event surveys, not from M19 optimization.

## 7. ML Validation Status

| Component | Status | Reason |
|-----------|--------|--------|
| Kinematic baseline | PHYSICS_BENCHMARK_VALIDATED | 3/3 Himalayan events within P10–P90 |
| ML quantile regression | INSUFFICIENT_EVIDENCE | No real event-level timestamps for Upper Beas |

> [!IMPORTANT]
> ML quantile regression has full infrastructure implemented but **cannot be fitted or validated** until real event-level timestamps are available. The kinematic baseline serves as the operational prediction method.

## 8. Limitations

- Physics baseline does not account for channel constrictions, debris jams, or tributary inflows
- P10/P90 spread (±30%) is a conservative parametric bound; true uncertainty depends on initial condition quality
- Longer distances degrade accuracy due to accumulating routing errors
- No InSAR or GNSS-derived channel geometry is currently integrated

## 9. Life-Safety Architecture

M19 predictions feed M17 (Warning Gating) to compute evacuation lead-time feasibility (EUI = RequiredTime / LeadTime).  M19 does NOT independently trigger evacuations.

---
*Generated: 2026-09-20 | FLOODY SHIELD v3.0 | SIH-26192*
