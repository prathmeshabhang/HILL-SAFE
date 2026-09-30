# Model Card: M2 Calibrated XGBoost Flood Risk
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-xgb-calibrated | Framework: XGBoost 2.0+ & scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M2 |
| **Model Full Name** | Calibrated XGBoost Flood Occurrence / Risk Model |
| **Algorithm** | XGBoost Classifier with Platt / Isotonic Probability Calibration |
| **Artifact Path** | `ml/models/m2_flood_risk_calibrated.joblib` |
| **Artifact SHA-256** | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` (Strictly Frozen) |
| **Training Pipeline** | [`ml/training/train_m2_flood_risk.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/training/train_m2_flood_risk.py) |
| **Validation Script** | [`ml/validation/external/evaluate_m2_strengthened.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/validation/external/evaluate_m2_strengthened.py) |
| **Validation Status** | **`PRELIMINARY_EXTERNAL_EVIDENCE`** |
| **Benchmark Gap** | Minimum benchmark: 100+ real flood events. Current: N=6 strictly independent test points (wide Clopper-Pearson CIs; Recall 95% CI: [39.76%, 100%]). Training data is calibrated simulation (10,000 spatial points), not real event records. Evidence is directionally supportive but not statistically sufficient for full external validation. |

---

## 2. Model Purpose & Semantic Definition

Model M2 predicts the reach-level and point-scale occurrence probability of flash flooding given topographic vulnerability and upstream hydrological discharge:
$$P(\text{Flood Occurrence} = 1 \mid \text{HAND}, \text{Distance to River}, \text{Discharge}, \text{Rainfall}_{24\text{h}}, \text{Slope})$$

M2 serves as the regional reach-level early warning gate for the Beas River and its primary Himalayan tributaries (Parbati, Tirthan, Sainj).

---

## 3. Training Data

| Field | Value |
|:------|:------|
| **Dataset File** | `data/processed/flood/upper_beas_flood_training_dataset.csv` |
| **Total Samples** | 10,000 spatial reach points across Upper Beas Catchment |
| **Data Nature** | Calibrated hydro-physical simulation combining 1D/2D hydraulic hydrodynamic model outputs (HEC-RAS / HAND benchmarks) with historical CWC discharge records and IMD extreme rainfall surges. |
| **Target Label** | Binary flood occurrence (`flood_occurred = 1/0`). |

---

## 4. Input Features (6 Hydro-Topographic Predictors)

1. `hand_m`: Height Above Nearest Drainage (HAND) from 10m/30m DEM (meters)
2. `flow_accumulation`: Upstream catchment contributing area (number of cells)
3. `dist_river_m`: Euclidean distance to nearest primary Beas river channel (meters)
4. `slope_deg`: Local surface slope angle (degrees)
5. `rainfall_24h_mm`: 24-hour cumulative basin precipitation (mm)
6. `peak_discharge_m3s`: Estimated river discharge at the reach outlet ($\text{m}^3/\text{s}$)

---

## 5. External Evaluation Data & Spatial Independence

- **External Event**: July 8–11, 2023 Historic Beas River Flash Flood Disaster surge.
- **Observed Flood Damage Sites ($N=12$)**: Confirmed flood washouts, bridge breaches, and submerged infrastructure (Old Manali, Bahang, Aloo Ground, Kalath, 15 Mile, Raison, Akhara Bazar, Bhuntar Airport, Aut Tunnel, Thalout, Sainj Market, Palchan).
- **Control Benches ($N=12$)**: Audited into unverified valley margins vs. 4 verified operational relief headquarters and heritage mounds (Naggar Castle, Kullu DC Office, Bhuntar Upper Hill, Bajaura Temple).
- **Spatial Independence Audit (500m Rule)**:
  - Total samples: 24 points across 4 reach zones (Upper Manali, Mid-Valley, Confluence, Lower Gorge).
  - Spatially proximal ($<500\text{m}$ to training points): 18 points.
  - Strictly independent ($>500\text{m}$ to training points): **6 points** (4 flooded, 2 controls).

---

## 6. External Validation Performance

### 6.1 Strictly Independent Subset ($N=6$ Points, Locked $\tau = 0.50$)

| Metric | Sample Value | Exact 95% Clopper-Pearson CI | Scientific Significance |
|:-------|:------------:|:----------------------------:|:------------------------|
| **Recall** | **100.0%** (4/4) | **[39.76%, 100.00%]** | Captured 100% of independent disaster points |
| **Specificity** | **0.0%** (0/2) | **[0.00%, 84.19%]** | False alarms at default $\tau=0.50$ |
| **Accuracy** | **66.67%** (4/6) | **[22.28%, 95.67%]** | Overall classification concordance |
| **ROC-AUC** | **1.0000** | — | Continuous probability perfectly separates independent floods |
| **PR-AUC** | **1.0000** | — | High area under precision-recall curve |
| **Brier Score** | **0.2987** | — | Squared error probability loss |

### 6.2 Confirmed Valid Absence Cohort ($N=16$: 12 Floods vs. 4 Verified Safe Ridges)
- **Empirical ROC-AUC**: **0.8750** (Monotonic probability ranking reliably separates flooded disaster sites from safe relief ridges).
- **PR-AUC**: **0.9615**
- **Brier Score**: **0.2319**

---

## 7. Known Limitations & Calibration Behavior

- **Valley Floor Saturation**: Under basin-wide extreme discharge ($Q > 2,000\text{ m}^3/\text{s}$), M2 predicted probabilities along valley bottom terraces exceed $0.55$, causing false positives on dry terraces if evaluated at $\tau = 0.50$.
- **High Discrimination (AUC = 0.875)**: The continuous score correctly assigns higher probabilities to submerged sites ($0.85\text{–}0.99$) than to safe relief centers ($0.55\text{–}0.65$), confirming ranking efficacy.

---

## 8. Intended Operational Use & Prohibited Misuse

- **Intended Use**: Regional reach-level flood risk alerts, staging of relief assets, and triggering downstream Model M4 satellite segmentation passes.
- **PROHIBITED Misuse**:
  - Do NOT use M2 as a substitute for 2D hydraulic floodway delineation without checking Model M4.
  - Do NOT assume points with $\hat{p} \approx 0.55$ under extreme discharge are inevitably inundated to high depths.
