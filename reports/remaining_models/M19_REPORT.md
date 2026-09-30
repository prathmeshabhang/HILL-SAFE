# M19 — Time-to-Impact Prediction Engine: Technical Report

**FLOODY SHIELD | SIH-26192 | Remaining Models Series**

---

## Summary

M19 estimates the time window until a hazard front (flood wave, debris flow, landslide runout, outburst flood) reaches a specified impact point.  Output is a P10/P50/P90 uncertainty quantile in minutes.  The primary prediction method is a kinematic physics baseline; an ML quantile regression layer is declared INSUFFICIENT_EVIDENCE pending real event timestamps.

---

## Architecture

### Kinematic Baseline (PRIMARY)

**Flood / Outburst events:**
```
Wave speed V = supplied (M12) → Manning proxy → M12 default 21 km/h
Saturation factor = 1 + max(0, (sat − 0.5)) × 1.0

t_P50 = distance / (V × sat_factor) [minutes]
t_P10 = distance / (V × sat_factor × 1.30)   ← +30% speed
t_P90 = distance / (V × sat_factor × 0.70)   ← −30% speed
```

**Landslide / Debris flow:**
```
H = distance × sin(slope_angle) [m vertical drop]
V = 2.7 × √H [m/s]  (Hungr 1995)
```

### ML Quantile Regression (INSUFFICIENT_EVIDENCE)

Full infrastructure implemented: `GradientBoostingRegressor(loss='quantile', alpha=0.10/0.50/0.90)` with **event-level GroupShuffleSplit** holdout.  Requires ≥ 10 distinct events and ≥ 30 samples.  No real Upper Beas event timestamps available.

---

## Physical Validation: Himalayan Benchmark Events

| Event | Dist (km) | Obs (h) | Pred P50 (h) | Error | In P10–P90 |
|-------|-----------|---------|-------------|-------|------------|
| Pareechu GLOF 2005 | 30.0 | 1.40 | 1.43 | 2.1% | ✓ |
| Sun Kosi 2014 | 22.0 | 1.20 | 1.20 | 0% | ✓ |
| Chamoli GLOF 2021 | 15.0 | 0.70 | 0.70 | 0% | ✓ |

All 3 benchmark events fall within the P10–P90 prediction interval.

---

## ML Validation Status

| Component | Status |
|-----------|--------|
| Physics baseline | PHYSICS_BENCHMARK_VALIDATED |
| ML quantile regression | **INSUFFICIENT_EVIDENCE** |
| Reason | No real event-level time-to-impact data for Upper Beas |

---

## Impact Types Supported

| Type | Speed Model |
|------|------------|
| FLOOD_INUNDATION | Manning / M12 wave speed |
| DAM_BREACH_OUTBURST | M12 Froehlich wave speed |
| LANDSLIDE_RUNOUT | Hungr (1995) empirical |
| DEBRIS_FLOW | Hungr (1995) empirical |
| COMBINED | Max(flood_speed, landslide_speed) → earliest arrival |

---

## Tests

`tests/test_m19_time_to_impact.py` — 11 tests (incl. 4 parametrize): **11 PASSED**

---
*Generated: 2026-09-20 | FLOODY SHIELD v3.0 | SIH-26192*
