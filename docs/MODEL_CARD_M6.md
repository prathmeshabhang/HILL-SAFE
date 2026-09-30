# Model Card: M6 Landslide Susceptibility (Random Forest)
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-rf350 | Framework: scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M6 |
| **Model Full Name** | Random Forest Landslide Susceptibility Model |
| **Algorithm** | Random Forest Classifier (350 estimators, max depth 9, min samples split 4) |
| **Artifact Path** | `ml/landslide/m6_beas_susceptibility_rf.joblib` |
| **Artifact SHA-256** | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` (Strictly Frozen) |
| **Training Pipeline** | [`ml/landslide/train_m6_m7_upper_beas.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/landslide/train_m6_m7_upper_beas.py) |
| **Validation Script** | [`ml/validation/external/evaluate_m6_strengthened.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/validation/external/evaluate_m6_strengthened.py) |
| **Validation Status** | **`INSUFFICIENT_EXTERNAL_EVIDENCE`** |

---

## 2. Model Purpose & Semantic Definition

Model M6 estimates the **spatial static susceptibility** of terrain to landslide failure:
$$P(\text{Susceptible} = 1 \mid \text{Geomorphology}, \text{Topography}, \text{Infrastructure}, \text{LULC})$$

> **CRITICAL DISTINCTION from Dynamic Trigger M7:**  
> M6 measures *where* slopes are fundamentally weak based on permanent geology, slope angle, and drainage distance. It does NOT incorporate real-time rainfall or pore-water pressure and CANNOT predict *when* a failure will occur.

---

## 3. Training Data

| Field | Value |
|:------|:------|
| **Dataset File** | `data/processed/upper_beas/upper_beas_landslide_dataset.csv` |
| **Total Samples** | 10,000 spatial points across Upper Beas Catchment ($76.80^\circ\text{E} - 77.45^\circ\text{E}, 31.40^\circ\text{N} - 32.45^\circ\text{N}$) |
| **Data Nature** | Calibrated synthetic simulation generated from Copernicus 30m DEM terrain attributes, regional GSI landslide susceptibility maps, and OpenStreetMap road vectors. |
| **Labels** | Binary susceptibility classes and multi-tier classes (0=Low, 1=Moderate, 2=High). |

---

## 4. Input Features (10 Static Factors)

1. `slope_deg` (Copernicus 30m DEM slope)
2. `aspect_deg` (Slope aspect angle)
3. `elevation_m` (Orthometric elevation)
4. `plan_curvature` (Horizontal slope divergence)
5. `profile_curvature` (Vertical slope acceleration)
6. `tpi` (Topographic Position Index)
7. `tri` (Terrain Ruggedness Index)
8. `dist_drainage_m` (Euclidean distance to Beas stream network)
9. `dist_roads_m` (Euclidean distance to NH-3 / NH-305 corridors)
10. `lulc_code` (ESA WorldCover 10m LULC class)

---

## 5. External Evaluation Data & Spatial Independence

- **External Failure Observations**: 20 documented disaster landslide scarps from the July/August 2023 disaster events in Kullu Valley (GSI field reconnaissance / HPSDMA reports).
- **Authoritative Negative Controls**: 12 verified stable bedrock spurs, ancient architectural monuments (e.g. Naggar Castle, Bajaura Temple), and civil administration benches.
- **Total Points Evaluated**: $N = 32$ (20 positives, 12 controls).
- **Spatial Independence Audit (500m Exclusion Rule)**:
  - Proximal points ($<500\text{m}$ to training data): 24 points (mean distance: $376.18\text{ m}$).
  - Strictly independent points ($>500\text{m}$ to training data): **8 points** (6 failure scarps, 2 stable control benches).
  - Spatial groups: Upper Manali–Rohtang, Mid-Beas Valley, Lower Gorge–Tirthan.

---

## 6. External Validation Performance

### 6.1 Strictly Independent Subset ($N=8$ Points, Locked $\tau = 0.50$)

| Metric | Sample Estimate | Exact 95% Clopper-Pearson CI | Scientific Commentary |
|:-------|:---------------:|:----------------------------:|:----------------------|
| **Recall (Sensitivity)** | **16.67%** (1/6) | **[0.44%, 64.12%]** | 5 of 6 real failure scarps under-predicted |
| **Specificity** | **100.00%** (2/2) | **[15.81%, 100.00%]** | Both independent bedrock benches correctly classified |
| **Precision** | **100.00%** (1/1) | **[2.53%, 100.00%]** | No false positives on independent benches |
| **Accuracy** | **37.50%** (3/8) | **[8.52%, 75.51%]** | Low point accuracy caused by false negatives |
| **ROC-AUC** | **0.3333** | — | Inverted ranking on small independent sample |
| **PR-AUC** | **0.7246** | — | Base rate = 0.750 |
| **Brier Score** | **0.3488** | — | Mean squared calibration error |

### 6.2 All 32 Points (Descriptive Context)
- **Observed Failures**: 20 | **Observed Controls**: 12
- **Recall**: **15.0%** (3/20), 95% CI: $[3.2\%, 37.9\%]$
- **Specificity**: **83.3%** (10/12), 95% CI: $[51.6\%, 97.9\%]$
- **ROC-AUC**: **0.4000** | **PR-AUC**: **0.6125** | **Brier**: **0.3500**

---

## 7. Known Limitations & Root Cause of Low Sensitivity

1. **Topographic Smoothing in 30m DEM**: 30m grid cells flatten micro-cliffs and steep road cuts ($10\text{–}15\text{m}$ tall) along NH-3 down to moderate slopes ($20^\circ\text{–}25^\circ$), lowering predicted susceptibility.
2. **Omission of Hydro-Mechanical Forcing**: Many 2023 failures occurred on moderately sloped terrain because extreme cloudbursts ($>50\text{mm/hr}$) saturated the soil column. Static M6 cannot account for pore-water pressure spikes.
3. **Engineering Confirmation**: This empirical limitation confirms why Model M7 (Dynamic Rainfall Trigger) and the physical PWP/Slope Stability Layer were designed as mandatory downstream components.

---

## 8. Intended Operational Use & Prohibited Misuse

- **Intended Use**: Long-term land-use planning, spatial zoning, and providing the baseline static susceptibility prior for Model M7.
- **PROHIBITED Misuse**:
  - Do NOT use M6 as a real-time warning trigger.
  - Do NOT use M6 in isolation for life-safety evacuation decisions.
  - Do NOT assume slopes with M6 score $<0.50$ are safe during monsoonal cloudburst events.
