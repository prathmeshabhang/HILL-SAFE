# FLOODY SHIELD — Scientific Validation & Benchmark Audit Report
**Generated**: 2026-09-20T05:55:00.693732+00:00 | **Random Seed**: 42

## 1. Summary of Code-Measured Metrics

| Model ID | Task Name | Algorithm | Validation Holdout | Key Measured Metric | Calibration (ECE / Brier) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M2** | Catchment Flood Occurrence | Calibrated XGBoost | Spatial Holdout (20%) | ROC-AUC: 0.981, PR-AUC: 0.9521 | Brier: 0.0482, ECE: 0.0397 | **INTERNAL_SPATIAL_HOLDOUT** — metrics are on same-dataset spatial split; external evidence: N=6 strictly independent points (PRELIMINARY_EXTERNAL_EVIDENCE) |
| **M6** | Static Landslide Susceptibility | Random Forest (350 trees) | Spatial Holdout (20%) | Accuracy: 0.931, F1-Macro: 0.8918 | N/A (Multiclass) | **INTERNAL_SPATIAL_HOLDOUT** — metrics are on simulated training data spatial split; external evidence: Recall=16.67% on N=6 strictly independent scarps (INSUFFICIENT_EXTERNAL_EVIDENCE) |
| **M7** | Dynamic Landslide Trigger | LightGBM (350 rounds) | Spatial Holdout (20%) | ROC-AUC: 0.9305, Recall: 0.912 | ECE: 0.0432 | **INTERNAL_SPATIAL_HOLDOUT** — metrics are on simulated training data spatial split; external evidence: N=7 storms (PRELIMINARY_EXTERNAL_EVIDENCE) |
| **U-Net / M4** | Multimodal Flood Inundation | 9-Channel PyTorch U-Net | Satellite Granule | Probability bounds [0, 1] verified | N/A | **PROXY_VALIDATED_PROTOTYPE** — internal Dice=0.973 is against SAR-HAND proxy masks, NOT independent field ground truth (EXTERNAL FULL-SCENE GROUND TRUTH UNAVAILABLE) |

> [!CAUTION]
> **AUDIT NOTE (2026-09-21):** The original `VALIDATED` labels in this table referred to internal spatial holdout performance on simulated training data — not independent external validation. They have been replaced with accurate status descriptors. See `reports/DATASET_BENCHMARK_AUDIT.md` and `reports/remaining_models/FINAL_MODEL_VALIDATION_SUMMARY.md` for the authoritative validation status of all models.

## 2. Multi-Hazard Fusion Audit (60% U-Net / 40% M2)
- **Designation**: HEURISTIC ENSEMBLE WEIGHTING
- **Empirical Validation**: NOT experimentally fitted by holdout regression. Manually selected to balance fine-scale satellite radar/optical observations (60%) with regional hydrological gauge physics (40%).
- **Calibration Disclaimer**: The fused flood risk score is a composite index $[0, 1]$, NOT a calibrated probability.

## 3. Extreme M7 Output Investigation
- **Observation**: Real-scene pipeline logged 99.91% high trigger area under storm defaults.
- **Root Cause 1**: Saturated NDMI Proxy pushed summer canopy NDMI (~0.52) to 98% soil moisture across all pixels.
- **Root Cause 2**: Constant 25mm/1h rainfall applied uniformly across the entire grid simulated an omnipresent cloudburst.
- **Fix**: Re-calibrated un-saturated NDMI physical mapping ($18 + ((NDMI+0.35)/0.95)*70$) aligning with training distribution mean (55%).
