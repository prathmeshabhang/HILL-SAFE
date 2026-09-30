# Model Card: M11 Flood Propagation & Inundation Depth Forecast Engine
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-flooddepth-gbdt | Framework: LightGBM 4.0+ & scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M11 |
| **Model Full Name** | Flood Propagation & Inundation Depth Forecast Engine |
| **Algorithm** | Muskingum-Cunge Kinematic Wave Routing combined with 1D-HAND Manning Hydrodynamic Regressors |
| **Artifact Path** | `ml/flood/m11_flood_depth/m11_depth_gbdt.joblib` |
| **Artifact SHA-256** | `b93259c1fa7a9fbf450b9e4a129a62f1c78df68ff251f5c2b19ae7e1e3d138df` |
| **Training Pipeline** | [`ml/flood/m11_flood_depth/train.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/flood/m11_flood_depth/train.py) |
| **Inference Interface** | [`ml/flood/m11_flood_depth/infer.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/flood/m11_flood_depth/infer.py) |
| **Validation Script** | [`ml/flood/m11_flood_depth/validation.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/flood/m11_flood_depth/validation.py) |
| **Validation Status** | **`PROTOTYPE_SIMULATED_DATA`** |
| **Benchmark Gap** | Minimum benchmark: 50+ independent real flood events with gauge + satellite extent. Current: simulated multi-reach HEC-RAS/HAND calibrations (n=3,200 train, n=1,000 val); 1 disaster scenario cross-check (July 2023). No real Sentinel-1 flood extent scenes used. R²=0.999 is on simulated holdout. Research-grade validation requires 50+ real Beas flood events with observed extents. |

---

## 2. Model Purpose & Semantic Definition

Model M11 simulates downstream flood wave propagation along the 90-kilometer Upper Beas River corridor (Palchan $\to$ Manali $\to$ Patli Kuhal $\to$ Kullu $\to$ Bhuntar $\to$ Aut $\to$ Pandoh) and forecasts localized point and reach-scale inundation depths ($d_{\text{flood}}(x, y)$ in meters) conditioned on Copernicus DEM HAND (Height Above Nearest Drainage).

---

## 3. Training & Validation Datasets

| Field | Value |
|:------|:------|
| **Dataset ID** | `upper_beas_hecras_hand_floodplain_profiles` |
| **Data Nature** | Multi-reach hydrodynamic calibrations combining 1D/2D HEC-RAS profiles, Copernicus 30m DEM HAND layers, and surveyed Beas cross-sections. |
| **Split Strategy** | 80% train ($N=3200$), 20% validation ($N=800$). |
| **Evaluation Sample Size** | 1,000 holdout floodplain locations. |

---

## 4. Input Features (5 Hydro-Topographic Predictors)

1. `source_stage_m`: Upstream river stage (meters)
2. `source_discharge_m3s`: Upstream river discharge ($\text{m}^3/\text{s}$)
3. `hand_m`: Height Above Nearest Drainage from Copernicus DEM (meters)
4. `distance_to_river_m`: Euclidean distance to active river centerline (meters)
5. `slope_deg`: Local surface slope angle (degrees)

---

## 5. Benchmark Performance vs. Linear Clipping Baseline

Evaluated across 1,000 holdout floodplain locations:

| Metric | Model M11 | Linear Clipping Baseline | Relative Gain |
|:-------|:----------|:-------------------------|:--------------|
| **MAE (m)** | **0.061 m** | 0.128 m | **+52.3%** |
| **$R^2$ Score** | **0.9989** | 0.9951 | High fidelity |

### Disaster Scenario Verification (July 2023 Beas Surge)
- Inputs: Stage $= 8.5\text{m}$, Discharge $= 2400\text{ m}^3/\text{s}$, HAND $= 1.2\text{m}$.
- Result: Forecasted Depth $= 7.29\text{m}$, Severity $=$ `CATASTROPHIC_SUBMERGENCE`.
- Wave Arrival Time at Kullu: $128.8\text{ minutes}$ from Palchan.

---

## 6. Known Limitations

1. **Hydrostatic HAND Assumption**: Localized inundation depth assumes hydrostatic lateral connectivity; dynamic 2D momentum backwaters in narrow bridge throttles are approximated.
2. **Channel Morphology Shifts**: Severe geomorphic scour or gravel bed deposition during mega-floods shifts bankfull elevation.
