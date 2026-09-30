# Model Card — M18: Risk Calibration Engine

**Floody Shield — Predict • Protect • Preserve**
AOI: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India

---

## 1. Model Overview

| Field | Value |
|-------|-------|
| Model ID | M18 |
| Full Name | Risk Calibration Engine |
| Domain | Calibration |
| Version | 1.0.0 |
| Status | PROTOTYPE_SYNTHETIC_PIPELINE_ONLY |
| Benchmark Gap | Minimum benchmark: 100+ real independent prediction–outcome pairs. Current: 1,000 synthetic beta-distributed pairs (0 real event outcomes). Brier improvement (+34.6%) is on synthetic test data. Upgrade path: accumulate 100+ M2/M6/M7 predictions matched against real post-event outcomes. |
| Artifact | `ml/calibration/m18_calibration/m18_calibration.pkl` |

## 2. Purpose

M18 is a **probability calibration layer**, NOT a new hazard predictor.  It post-processes raw probabilities output by other Floody Shield models (M2, M6, M7, M1, M10, M11) to produce calibrated probabilities that better represent empirical event frequencies.

A model that outputs 0.80 should be correct ~80% of the time — M18 corrects systematic over- or under-confidence.

## 3. Calibration Methods

| Method | Description |
|--------|-------------|
| **Platt Scaling** | Logistic regression fitted to transform raw scores to calibrated probabilities |
| **Isotonic Regression** | Non-parametric monotone calibration (more flexible, requires more data) |
| **Selection** | The method with the lower Brier score on a stratified internal holdout is automatically selected |

## 4. Input / Output Contract

### Input
```python
M18CalibrationInput(
    source_model="M2_FLOOD_RISK",
    raw_probability=0.82,
    data_quality=0.9,
)
```

### Output
```python
M18CalibrationOutput(
    model="M18_RISK_CALIBRATION",
    source_model="M2_FLOOD_RISK",
    raw_probability=0.82,
    calibrated_probability=0.76,   # adjusted
    calibration_method="platt_scaling",
    confidence=0.84,
    data_quality=0.9,
    status="CALIBRATED",
    metrics={"platt_brier": 0.142, "iso_brier": 0.156},
    ...
)
```

When calibration data is insufficient (< 50 samples or < 5 positive events):
```
status = "INSUFFICIENT_EVIDENCE"
calibrated_probability = raw_probability  (passthrough)
```

## 5. Training / Calibration Split Architecture

```
Source model outputs  →  Calibration dataset (labelled 0/1)
                              │
                    ┌─────────┴─────────┐
                    │                   │
               Train split         Val split (30%)
              (Platt + Iso)        (Brier selection)
                                        │
                                  External validation
                                  (NEVER used for fitting)
```

> [!IMPORTANT]
> The external validation set is NEVER used for fitting or selecting the calibrator.

## 6. Metrics

| Metric | Definition | Interpretation |
|--------|-----------|----------------|
| **Brier Score** | Mean squared error between calibrated prob and binary label | Lower = better (0 = perfect) |
| **ECE** | Expected Calibration Error across 10 bins | Lower = better |
| **Calibration slope** | Logit-OLS slope of calibrated prob vs observed rate | Near 1.0 = well calibrated |
| **ROC-AUC** | Area under the receiver-operating-characteristic curve | Higher = better discrimination |
| **PR-AUC** | Area under precision-recall curve (for rare events) | More informative than ROC for imbalanced classes |

## 7. Validation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Platt calibrator | INTERNAL_VALIDATED | Verified on SYNTHETIC holdout |
| Isotonic calibrator | INTERNAL_VALIDATED | Verified on SYNTHETIC holdout |
| External validation | INSUFFICIENT_EVIDENCE | Real labelled calibration datasets not available for Upper Beas at this project stage |

> [!WARNING]
> Training data is **SYNTHETIC — PIPELINE TEST ONLY**.  Calibrators should be re-fitted on real event observations (labelled probability–outcome pairs) before operational use.

## 8. Limitations

- Calibration quality degrades with very small datasets (< 50 samples) or extreme class imbalance
- Isotonic regression can over-fit on small datasets; Platt scaling is more stable
- Calibration is only meaningful if the source model's scores have monotone discrimination power
- Upper Beas-specific calibration data (real flood/landslide event outcomes) is not yet available

## 9. Data Provenance

| Dataset | Type | Usage |
|---------|------|-------|
| Synthetic beta-distributed scores | SYNTHETIC — PIPELINE TEST ONLY | Unit tests and smoke tests |
| Real event outcomes (future) | REAL | Should replace synthetic when available |

## 10. Life-Safety Architecture

M18 is a **post-processing layer** only.  It does not issue alerts or trigger evacuations.  All calibrated probabilities must pass through M17 (Warning Gating) and authorized human decision workflows before any emergency action.

---
*Generated: 2026-09-20 | FLOODY SHIELD v3.0 | SIH-26192*
