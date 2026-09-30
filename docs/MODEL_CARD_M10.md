# Model Card: M10 River Water-Level & Stage Forecast Engine
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-waterlevel-gbdt | Framework: LightGBM 4.0+ & scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M10 |
| **Model Full Name** | River Water-Level & Stage Forecast Engine |
| **Algorithm** | Kinematic Momentum Extrapolation combined with Catchment Runoff LightGBM Multi-Horizon Regressors |
| **Artifact Path** | `ml/flood/m10_water_level/m10_water_level_gbdt.joblib` |
| **Artifact SHA-256** | `ed8f6091301f61335767a37997fe91ae7bddb3c44b295227e43a69c953213000` |
| **Training Pipeline** | [`ml/flood/m10_water_level/train.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/flood/m10_water_level/train.py) |
| **Inference Interface** | [`ml/flood/m10_water_level/infer.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/flood/m10_water_level/infer.py) |
| **Validation Script** | [`ml/flood/m10_water_level/validation.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/flood/m10_water_level/validation.py) |
| **Validation Status** | **`PROTOTYPE_SIMULATED_DATA`** |
| **Benchmark Gap** | Minimum benchmark: 2–5 yr real continuous gauge records (preferred: 10+ yr). Current: simulated Beas hydrographs grounded in seasonal patterns (n=3,600 train, n=1,000 val); no real CWC gauge telemetry used. R² metrics are on simulated holdout. Research-grade validation requires real CWC/HP continuous stage readings at Manali, Kullu, Bhuntar, Pandoh gauges. |

---

## 2. Model Purpose & Semantic Definition

Model M10 delivers tactical river stage forecasts $h(t)$ in meters across 4 operational horizons:
$$\{+30\text{m}, +1\text{h}, +3\text{h}, +6\text{h}\}$$
at critical gauge points along the Beas River network (Manali, Patli Kuhal, Kullu, Bhuntar Confluence, Thalout, Pandoh) and evaluates exceedance against Central Water Commission (CWC) warning, danger, and high flood level (HFL) marks.

---

## 3. Training & Validation Datasets

| Field | Value |
|:------|:------|
| **Dataset ID** | `upper_beas_cwc_hydrographic_telemetry` |
| **Data Nature** | Multi-year hydrographic series grounded in Beas River seasonal hydrographs, rainfall-runoff response lags, and high-flood monsoon surges. |
| **Split Strategy** | 80% train ($N=3600$), 20% validation ($N=900$). |
| **Evaluation Sample Size** | 1,000 holdout hydrograph sequences. |

---

## 4. Input Features (7 Hydrological & Meteorological Predictors)

1. `current_stage_m`: Active stream gauge water level (meters)
2. `rate_of_rise_m_hr`: First derivative of stage $dh/dt$ ($\text{m}/\text{hr}$)
3. `rainfall_1h_mm`: 1-hour upstream basin rainfall accumulation (mm)
4. `rainfall_3h_mm`: 3-hour upstream basin rainfall accumulation (mm)
5. `rainfall_6h_mm`: 6-hour upstream basin rainfall accumulation (mm)
6. `soil_moisture_pct`: Basin volumetric soil moisture saturation (%)
7. `effective_runoff_index`: Saturation-weighted runoff proxy $(R_{1\text{h}} + 0.6 R_{3\text{h}} + 0.3 R_{6\text{h}}) \cdot (\text{SM}_{\text{pct}}/100)$

---

## 5. Benchmark Performance vs. Static Persistence Baseline

Evaluated across 1,000 holdout hydrographs against static persistence ($h(t) = h_0$):

| Horizon | M10 MAE (m) | M10 $R^2$ | Static Baseline MAE (m) | MAE Gain over Baseline |
|:--------|:------------|:----------|:------------------------|:-----------------------|
| **30m** | 0.082 m | 0.9412 | 0.165 m | **+50.3%** |
| **1h** | 0.141 m | 0.9628 | 0.312 m | **+54.8%** |
| **3h** | 0.284 m | 0.9715 | 0.745 m | **+61.9%** |
| **6h** | 0.428 m | 0.9782 | 1.280 m | **+66.6%** |

---

## 6. Known Limitations

1. **Sub-Catchment Cloudburst Shift**: Extrapolation beyond $+3\text{h}$ assumes stationary convective center over contributing catchments.
2. **Artificial Flow Interventions**: Model reflects natural riverbed hydraulics; unscheduled barrage gate openings (e.g. Larji/Pandoh dam spillways) require upstream SCADA integration.
