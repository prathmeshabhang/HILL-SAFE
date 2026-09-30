# Model Card: M1 Multi-Horizon Extreme Rainfall Nowcasting Engine
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-nowcast-lgbm | Framework: LightGBM 4.0+ & scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M1 |
| **Model Full Name** | Multi-Horizon Extreme Rainfall Nowcasting & Cloudburst Detection Engine |
| **Algorithm** | Kinematic Persistence Baselines combined with Multi-Horizon LightGBM Quantile Regressors |
| **Artifact Path** | `ml/rainfall/m1_nowcast/m1_nowcast_lgbm.joblib` |
| **Artifact SHA-256** | `4065c7c7ef4dc9147d452dd3cedc6ddf454a3c11218091e6d3bcf72d10d7467d` |
| **Training Pipeline** | [`ml/rainfall/m1_nowcast/train.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/rainfall/m1_nowcast/train.py) |
| **Inference Interface** | [`ml/rainfall/m1_nowcast/infer.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/rainfall/m1_nowcast/infer.py) |
| **Validation Script** | [`ml/rainfall/m1_nowcast/validation.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/rainfall/m1_nowcast/validation.py) |
| **Validation Status** | **`PROTOTYPE_SIMULATED_DATA`** |
| **Benchmark Gap** | Training data is physics-calibrated simulation, not raw IMD/GPM records. Minimum benchmark: 2–3 yr real hourly (preferred: 5–10 yr). Current: simulated 5-yr series. Real IMD AWS + GPM IMERG records required for research-grade validation. |

---

## 2. Model Purpose & Semantic Definition

Model M1 forecasts localized precipitation accumulation across 6 tactical horizons:
$$\{15\text{m}, 30\text{m}, 1\text{h}, 3\text{h}, 6\text{h}, 24\text{h}\}$$
and computes the exceedance probability of localized convective cloudbursts ($P(\text{Rate} \ge 60\text{ mm/h})$ or catastrophic short-duration accumulations) in the steep complex orography of the Upper Beas Basin.

---

## 3. Training & Validation Datasets

| Field | Value |
|:------|:------|
| **Dataset ID** | `upper_beas_monsoon_aws_timeseries` |
| **Data Nature** | Multi-year convective storm telemetry calibrated with IMD AWS precipitation profiles, orographic enhancement proxies, and synthetic convective cloudburst sequences. |
| **Split Strategy** | Strict chronological holdout (past 80% train, subsequent 20% holdout). |
| **Evaluation Sample Size** | 600 contiguous 15-minute time steps. |

---

## 4. Input Features (14 Hydro-Meteorological & Topographic Predictors)

1. `r_15m`: 15-minute antecedent accumulation (mm)
2. `r_30m`: 30-minute antecedent accumulation (mm)
3. `r_1h`: 1-hour antecedent accumulation (mm)
4. `r_3h`: 3-hour antecedent accumulation (mm)
5. `r_6h`: 6-hour antecedent accumulation (mm)
6. `r_12h`: 12-hour antecedent accumulation (mm)
7. `r_24h`: 24-hour antecedent accumulation (mm)
8. `r_72h`: 72-hour antecedent accumulation (mm)
9. `rolling_intensity_mmh`: Current instantaneous rainfall rate (mm/h)
10. `rainfall_acceleration`: Second derivative of rainfall rate ($d^2R/dt^2$, $\text{mm}/\text{h}^2$)
11. `elevation_m`: Station terrain elevation from DEM (meters)
12. `slope_deg`: Local slope inclination (degrees)
13. `orographic_factor`: Updraft precipitation amplification factor ($1.0 + 0.6 \cdot \text{elev}_{\text{norm}} \cdot \sin(\theta)$)
14. `storm_motion_dx`: Semi-Lagrangian cell tracking advection velocity proxy

---

## 5. Benchmark Performance vs. Baselines

Evaluated against standard operational benchmarks (Lagrangian/Eulerian Persistence and Climatology):

| Horizon | M1 MAE (mm) | M1 RMSE (mm) | Persistence MAE (mm) | MAE Gain over Baseline | Brier Score (Extreme) |
|:--------|:------------|:-------------|:---------------------|:-----------------------|:----------------------|
| **15m** | 0.435 mm | 0.966 mm | 0.439 mm | +0.8% | 0.050 |
| **1h** | 2.120 mm | 3.926 mm | 1.939 mm | Baseline competitive | 0.050 |
| **3h** | 7.117 mm | 10.281 mm | 7.778 mm | +8.5% | 0.108 |
| **6h** | 11.420 mm | 14.826 mm | 19.371 mm | **+41.0%** | 0.286 |
| **24h** | 20.390 mm | 25.664 mm | 80.849 mm | **+74.8%** | 0.015 |

---

## 6. Uncertainty & Data Quality Guarantees

- **Uncertainty Bounds**: Calibrated 80% quantile prediction intervals (`[uncertainty_lower_mm, uncertainty_upper_mm]`).
- **Data Quality Integration**: Audited directly via `DataQualityValidator`. Unphysical rates ($>300\text{ mm/h}$) or out-of-basin coordinates automatically penalize `data_quality` and flag anomalies.
- **Fail-Safe Mode**: If GBDT inference fails, model automatically falls back to kinematic exponential decay persistence.

---

## 7. Known Limitations

1. **Doppler Radar Absence**: Pure point AWS extrapolation decays beyond $+3\text{h}$ without active C/X-band Doppler radar reflectivity assimilation.
2. **Orographic Proxy**: Orography currently approximates lift via DEM slope and elevation without dynamic 3D wind velocity field assimilation.
