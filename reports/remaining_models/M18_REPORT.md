# M18 — Risk Calibration Engine: Technical Report

**FLOODY SHIELD | SIH-26192 | Remaining Models Series**

---

## Summary

M18 is the probability calibration layer for the Floody Shield hazard model ensemble.  It applies Platt scaling and isotonic regression to post-process raw output probabilities from M2, M6, M7, M1, M10, and M11, correcting systematic over- or under-confidence without modifying the underlying production models.

---

## Architecture

```
Source model (M2 / M6 / M7 / M1 / M10 / M11)
              │
              ▼
       raw_probability ∈ [0, 1]
              │
    ┌─────────┴──────────┐
    │                    │
  Platt              Isotonic
  Scaling           Regression
    │                    │
    └─────────┬──────────┘
              │
         Brier-score
         comparison
         on val split
              │
       best_method selected
              │
     calibrated_probability
```

---

## Data Provenance

| Dataset | Type | Usage |
|---------|------|-------|
| Beta-distributed synthetic scores | **SYNTHETIC — PIPELINE TEST ONLY** | Model fit, unit tests |
| Real hazard event labels (future) | REAL | Required for operational calibration |

---

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Calibration algorithm | Platt (LogisticRegression, C=1e6) + Isotonic |
| Val split fraction | 30% (stratified by label) |
| Min samples for fitting | 50 |
| Min positive samples | 5 |
| Best method selection | Lower Brier score on val split |

---

## Results (SYNTHETIC Pipeline Test)

| Metric | Uncalibrated | Platt | Isotonic |
|--------|-------------|-------|----------|
| Brier score (val) | 0.1144 | **0.0748** | 0.0765 |
| Best method | — | ✓ Selected | — |

Brier improvement: **+34.6%** (on synthetic test data — not externally validated).

---

## Inference Contract

| Status | Condition | Action |
|--------|-----------|--------|
| `CALIBRATED` | Model fitted, data_quality ≥ 0.3 | Returns calibrated_probability |
| `INSUFFICIENT_EVIDENCE` | < 50 samples or < 5 positives | Returns raw_probability (passthrough) |
| `DEGRADED_INPUT` | data_quality < 0.3 | Returns raw_probability (passthrough) |

---

## Validation

External validation status: **INSUFFICIENT_EVIDENCE**

Real labelled calibration datasets (probability-outcome pairs per event) are not available for Upper Beas at this project stage.  Once real event outcomes are available, calibrators should be refitted and evaluated on independent external holdout.

---

## Artifact

```
ml/calibration/m18_calibration/m18_calibration.pkl
SHA-256: abd57eebf06c4b36b512d8516b24bf328b07a9ced530a6e2b0ace79003d1d726
```

---

## Tests

`tests/test_m18_calibration.py` — 10 tests (incl. parametrize): **10 PASSED**

---
*Generated: 2026-09-20 | FLOODY SHIELD v3.0 | SIH-26192*
