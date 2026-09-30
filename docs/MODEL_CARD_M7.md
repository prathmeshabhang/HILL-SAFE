# Model Card: M7 Dynamic Landslide Trigger
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-lgbm350 | Framework: LightGBM 4.3 + scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M7 |
| **Model Full Name** | Dynamic Landslide Trigger Model |
| **Algorithm** | LightGBM Gradient Boosted Decision Trees (350 rounds, max leaves 31) |
| **Artifact Path** | `ml/landslide/m7_beas_trigger_lgbm.joblib` |
| **Artifact SHA-256** | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` (Strictly Frozen) |
| **Training Pipeline** | [`ml/landslide/train_m6_m7_upper_beas.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/landslide/train_m6_m7_upper_beas.py) |
| **External Validation Script** | [`ml/validation/external/evaluate_m7_strengthened.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/validation/external/evaluate_m7_strengthened.py) |
| **Validation Tier** | **`PRELIMINARY_EXTERNAL_EVIDENCE`** |
| **Benchmark Gap** | Minimum benchmark: 100+ independent storms. Current: N=7 storm episodes (5 trigger + 2 control); event specificity = 0% (false alarms on moderate storms); spatial ROC-AUC = 0.198 within storm. Training data is synthesised from IMD/ERA5 distributions. Research-grade validation requires 100+ real independently-sourced storm–landslide trigger pairs. |

---

## 2. Model Purpose & Semantic Definition

> **CRITICAL DISTINCTION from Model M6:**  
> - **M6 (Static Susceptibility)**: Asks *Where could a landslide occur, based on permanent terrain characteristics?* (DEM, slope, geology, LULC).  
> - **M7 (Dynamic Trigger)**: Asks *Given active hydrometeorological forcing (current rainfall, antecedent rain, soil moisture), is this slope failing RIGHT NOW?*

M7 predicts the conditional instantaneous trigger probability:
$$P(\text{Landslide Triggered} = 1 \mid \text{Rain}_{1\text{h}}, \text{Rain}_{3\text{d}}, \theta_{\text{soil}}, \text{Slope}, \text{SuscClass})$$

---

## 3. Training Data

| Field | Value |
|:------|:------|
| **Dataset File** | `data/processed/upper_beas/upper_beas_landslide_dataset.csv` |
| **Sample Size** | 10,000 samples |
| **Geographic AOI** | Upper Beas Catchment, Kullu–Manali, Himachal Pradesh, India ($76.80^\circ\text{E} - 77.45^\circ\text{E}, 31.40^\circ\text{N} - 32.45^\circ\text{N}$) |
| **Positive Class** | `landslide_triggered = 1` (active slope failure) |
| **Negative Class** | `landslide_triggered = 0` (stable slope) |
| **Data Nature** | **Calibrated synthetic simulation** grounded in regional GSI historical landslide statistics, Copernicus 30m DEM terrain, and IMD historical monsoonal rainfall distributions. |
| **Data Transparency** | All training distributions and synthetic generation parameters are formally documented in `docs/EXPERIMENTS.md`. |

---

## 4. Input Features

| # | Feature | Data Type | Physical Range | Source / Derivation |
|:--|:--------|:---------:|:--------------:|:--------------------|
| 1 | `susceptibility_class` | int (0, 1, 2) | [0=Low, 1=Mod, 2=High] | Model M6 output class |
| 2 | `slope_deg` | float32 | [3.0°, 65.0°] | Copernicus 30m DEM Horn's slope |
| 3 | `rainfall_1h` | float32 | [0.0, 105.0] mm/hr | IMD AWS / GPM IMERG 1-hour rainfall |
| 4 | `antecedent_rain_3d`| float32 | [0.0, 600.0] mm | 3-day cumulative precipitation |
| 5 | `soil_moisture_pct` | float32 | [15.0%, 98.0%] | In-situ probe / ERA5-Land volumetric moisture |

---

## 5. External Evaluation Data & Multi-Event Protocol

- **Dataset Source**: Historical Himalayan Storm Catalog (`data/external/events/himalayan_storm_landslide_catalog.csv`).
- **Data Provider**: Synthesized from IMD Automatic Weather Station telemetry, ERA5-Land reanalysis, and HPSDMA official post-disaster situation reports.
- **Event Scope**: $N = 7$ distinct multi-day storm episodes spanning 6 years (2018–2023):
  - **Disaster Trigger Storms ($N=5$)**:
    1. July 8–11, 2023 Extreme Monsoonal Cloudburst ($56.2\text{ mm/hr}, 278.4\text{ mm}$ 3d)
    2. August 12–15, 2023 Lesser Himalayas Surge ($42.8\text{ mm/hr}, 241.0\text{ mm}$ 3d)
    3. September 22–24, 2018 Unprecedented Snow-Rain Storm ($38.5\text{ mm/hr}, 210.5\text{ mm}$ 3d)
    4. July 12–13, 2021 Convective Cloudburst ($48.0\text{ mm/hr}, 182.0\text{ mm}$ 3d)
    5. August 17–19, 2019 Monsoonal Surge ($34.0\text{ mm/hr}, 195.0\text{ mm}$ 3d)
  - **Control Non-Trigger Storms ($N=2$)**:
    6. July 18–20, 2022 Moderate Monsoon Pulse ($12.5\text{ mm/hr}, 62.0\text{ mm}$ 3d)
    7. August 25–27, 2020 Moderate Monsoon Event ($10.0\text{ mm/hr}, 51.0\text{ mm}$ 3d)
- **Within-Storm Spatial Evaluation**: 22 spatial points (11 failure scarps, 11 stable control locations) evaluated under the single July 9–10, 2023 storm.

---

## 6. External Validation Performance

### 6.1 Multi-Event Storm Level Metrics ($N=7$ Events, $\tau = 0.50$)

| Metric | Point Estimate | Exact 95% Clopper-Pearson CI | Scientific Significance |
|:-------|:--------------:|:----------------------------:|:------------------------|
| **Event Recall** | **100.0%** (5/5) | **[47.82%, 100.00%]** | Perfect capture of all major historical disaster storms |
| **Event Specificity** | **0.0%** (0/2) | **[0.00%, 84.19%]** | Alarmed on moderate monsoon control events |
| **Event Accuracy** | **71.43%** (5/7) | **[29.04%, 96.33%]** | Overall storm classification rate |
| **Event ROC-AUC** | **1.0000** | — | Continuous probability perfectly separates disaster storms from controls |
| **Event Brier Score** | **0.2418** | — | Calibration loss across event spectrum |

### 6.2 Within-Storm Spatial Metrics ($N=22$ Points, July 2023 Storm)
- **Spatial Recall**: **100.0%** (11/11), 95% CI: $[71.5\%, 100.0\%]$
- **Spatial Specificity**: **0.0%** (0/11), 95% CI: $[0.0\%, 28.5\%]$
- **Spatial ROC-AUC**: **0.1983** (Under extreme uniform storm forcing, LightGBM trigger saturates on valley floor)

---

## 7. Calibration & Physical Interpretation

- **Monotonic Ranking**: All 5 disaster storms produced predicted probabilities $\ge 0.9998$, whereas the two non-trigger control storms produced lower probabilities ($0.9292$ and $0.9105$).
- **Threshold Saturation**: Because moderate Himalayan rainfall ($>10\text{ mm/hr}$) is interpreted by uncalibrated trees as high danger, the default $\tau = 0.50$ triggers false alarms.
- **Physical Integration**: This behavior directly motivated the development of the **Pore-Water Pressure (PWP) & Slope Stability Layer**, which computes transient effective stress reduction and an infinite-slope Factor of Safety ($FS$) to prevent false alarms on well-drained slopes.

---

## 8. Intended Use & Prohibited Misuse

- **Intended Use**: Regional monsoonal landslide warning trigger to flag high-risk atmospheric surges in the Upper Beas basin.
- **PROHIBITED Misuse**:
  - Do NOT use M7 without the downstream PWP Factor of Safety check to issue localized evacuation orders.
  - Do NOT assume M7 probabilities are well-calibrated absolute probabilities without the PWP safety layer.
  - Do NOT deploy in terrain outside the Indian Himalayan belt without regional re-benchmarking.
