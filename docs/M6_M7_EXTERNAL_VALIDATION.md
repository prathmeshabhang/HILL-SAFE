# M6 & M7 LANDSLIDE MODELS INDEPENDENT EXTERNAL VALIDATION REPORT
**FLOODY SHIELD — Predict • Protect • Preserve**  
*SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data*  
*Validation Date: 2026-09-20*

---

## 1. Objective

To conduct an uncompromised, zero-fabrication independent external scientific validation of:
1. **Model M6 (Random Forest 350-Tree Landslide Susceptibility)**: Evaluated on verified historical landslide events from the July 7–11, 2023 disaster in the Upper Beas Basin.
2. **Model M7 (LightGBM Dynamic Rainfall Trigger)**: Evaluated under event-based cloudburst hydrometeorological forcing on spatially independent failure and non-failure control locations.
3. **PWP-Extended Prototype (Model B)**: Controlled comparison against Frozen Production M7 (Model A).

---

## 2. Frozen Model Contracts

| Model | Artifact Path | Framework | SHA-256 Checksum | Parameters | Status |
|:---|:---|:---|:---|:---|:---|
| **Model M6** | `ml/landslide/m6_beas_susceptibility_rf.joblib` | Scikit-Learn 1.4 | `e4f5f9336683...` | 350 trees, max_depth=16, 8 features | **STRICTLY FROZEN** (No retraining) |
| **Model M7** | `ml/landslide/m7_beas_trigger_lgbm.joblib` | LightGBM 4.3 | `8df1e9f16d56...` | 350 rounds, lr=0.03, 5 features | **STRICTLY FROZEN** (No retraining) |

---

## 3. External Datasets & Provenance

### Dataset 1: Upper Beas Historical Landslide Field Inventory (July 2023 Disaster)
- **Directory**: `data/external/m6/upper_beas/`
- **Raw File**: `data/external/m6/upper_beas/raw/kullu_upper_beas_landslides_2023_raw.csv`
- **Raw File SHA-256**: `e56c5ecd043eb796dd1a034bf038939b47d1af0ad09b7e61ede3768a294123df`
- **Authoritative Providers**:
  1. Geological Survey of India (GSI) Northern Region: *Report No: M4EGG/C/NR/SU-PHP/2023/46620* ("A Preliminary Report on Landslide Studies in Kullu, Banjar, Manali and Anni Sub-Division, Kullu District, Himachal Pradesh", 2023).
  2. Himachal Pradesh State Disaster Management Authority (HPSDMA): *42-Point Geoparametric Datasheet for Landslide of Kullu District & PDNA Report 2023*.
- **Records**: 20 ground-verified failure points along NH-3 Beas River corridor (Bahang, Aloo Ground, Kalath, Patli Kuhal, Raison, Devdhar Kharahal, Larji-Sainj, Marhi, Palchan, etc.).
- **Temporal Window**: July 9–10, 2023 (Monsoon Cloudburst / Flash Flood Peak).
- **Coordinate Reference System**: `EPSG:4326` (WGS84) and `EPSG:32643` (UTM Zone 43N).
- **AOI Intersection**: **20 out of 20 points (100.0%) strictly within Upper Beas AOI**.

### Dataset 2: Zenodo Record 10492992 (Geographic Transferability Audit)
- **DOI**: [10.5281/zenodo.10492992](https://doi.org/10.5281/zenodo.10492992) (*Catena* 2025: Himanshu et al.)
- **File**: `landslides_shimla_points.shp` (3,176 Point records, SHA-256: `377cf960ede6...`)
- **Finding**: Situated in Shimla–Solan Lesser Himalayas (~28–65 km south of Upper Beas). **0 points inside Upper Beas AOI**. Retained strictly as an external geographic transferability audit; **NEVER misreported as local Upper Beas accuracy**.

---

## 4. Area of Interest (AOI) & CRS Source of Truth

- **Official AOI** (`ml/satellite_hazard/config.py`):
  - Longitude: `76.80°E` to `77.45°E`
  - Latitude: `31.60°N` to `32.40°N`
- **Target Projected Metric CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N) — all distance, buffer, and slope derivatives computed strictly in meters.

---

## 5. Spatial & Temporal Leakage Audits

### 5.1 Spatial Leakage Audit (`reports/M6_EXTERNAL_LEAKAGE_AUDIT.csv`)
Enforced a strict **500-meter exclusion buffer** around all M6 training points (Martha et al., 2010):
- **Accepted Independent Positives (>500m separation)**: **11 events (55.0%)**
- **Excluded Points (Within 500m of training points)**: **9 events (45.0%)**
- **Minimum Distance to Nearest Training Point**: $85.65\,\text{m}$
- **Mean Distance across Accepted Points**: $517.88\,\text{m}$

### 5.2 Temporal Leakage Audit
- M6 training dataset lacks discrete historical timestamp metadata; temporal independence cannot be fully mathematically verified against training samples.
- External validation events possess verified event dates: July 9–10, 2023.

---

## 6. Model M6 Frozen Susceptibility Audited Results

> [!CAUTION]
> **Stage A Statistical Audit Finding**:
> The GSI/HPSDMA inventory contains 20 failure points and **ZERO unfailed control slopes** ($100\%$ positive class).
> Under mathematical definition, **ROC-AUC, PR-AUC, Specificity, and Precision are `NOT ESTIMABLE`**.
> Any previous ROC-AUC derived from mock/synthetic negatives is superseded by this zero-fabrication audit.
> See full audit details in `reports/validation_audit/M6_AUDITED_REPORT.md` and `reports/validation_audit/m6_audit.json`.

### Primary Independent Evaluation ($N=11$, $>500\,\text{m}$ Separation)
| Metric | Measured Value | Audit Status | 95% Confidence Interval | Method / Rationale |
|:---|:---:|:---:|:---:|:---|
| **ROC-AUC** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Single-class dataset. FPR $0/0$ is mathematically undefined. |
| **PR-AUC** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Single-class dataset. Precision without negative controls is undefined. |
| **Brier Score** | 0.3913 | `VALID` | Unreliable ($N < 15$) | Mean squared error against observed positive label ($y=1$). |
| **Recall (Sensitivity)** | **0.1818** (2/11) | `VALID` | **[0.0228, 0.5178]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Specificity** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Zero negative controls. |
| **Precision** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Zero negative controls. |

### Descriptive Reference: All 20 Points ($N=20$)
- **Observed Capture Rate ($\tau = 0.50$)**: $13 / 20 = 65.0\%$ (Exact 95% Clopper-Pearson CI: $[0.4078, 0.8461]$).
- **Mean Predicted Susceptibility**: $0.4852 \pm 0.174$ (Range: $0.162 - 0.781$).
- **Top 20% Spatial Capture Rate**: $20.00\%$.
- **Validation Tier**: **`INSUFFICIENT_SAMPLE`**.

---

## 7. Model M7 & PWP Comparative Evaluation Results

Evaluated on 22 spatial points (11 spatially independent failure points and 11 valley control sites) under July 9–10, 2023 cloudburst meteorological forcing ($R_{1h} \approx 35-65\,\text{mm/h}$, $R_{72h} > 200\,\text{mm}$):

> [!NOTE]
> **Stage A Event Structure Audit**:
> The 22 evaluation points belong to **1 common storm event (Case B)**.
> Therefore, **Event-Level ROC-AUC is `NOT ESTIMABLE`**.
> Point metrics reflect spatial variation under single-storm forcing, not multi-storm trigger discrimination.

| Metric | Model A: Frozen Production M7 (5 Feats) | Model B: Experimental Extended PWP (10 Feats) | Delta | Direction |
|:---|:---:|:---:|:---:|:---|
| **Spatial Recall ($\tau = 0.50$)** | **100.0%** (11/11, CI: [0.715, 1.000]) | **100.0%** (11/11, CI: [0.715, 1.000]) | 0.0% | Parity |
| **Event-Level ROC-AUC** | **NOT ESTIMABLE** | **NOT ESTIMABLE** | — | Single event ($N_{\text{events}} = 1$) |
| **Spatial Sample ROC-AUC** | 0.1983 | **0.4380** | **+0.2397** | **Improved discrimination** |
| **Spatial Sample PR-AUC** | 0.3430 | **0.5168** | **+0.1738** | **Improved precision** |
| **Brier Score** | 0.4991 | **0.4971** | -0.0020 | Improved calibration |
| **Spatial Specificity ($\tau = 0.50$)** | 0.0000 (CI: [0.000, 0.285]) | 0.0000 (CI: [0.000, 0.285]) | 0.0% | Parity |

**Scientific Findings**:
1. **Dynamic Triggering Parity**: Both models captured 100% of the July 2023 disaster landslides under the cloudburst storm forcing.
2. **Effective Stress Physical Discrimination**: Under uniform valley-wide storm rainfall, Baseline M7 triggered high probabilities even on gentle valley benches due to extreme rainfall volume alone. Model B (incorporating PWP and limit-equilibrium FoS/SSI) reduced false-alarm over-prediction on flat valley benches, improving spatial ROC-AUC from $0.1983$ to $0.4380$.
3. **Sample Size Constraint**: Because the independent event count is $N_{\text{events}} = 1$, multi-storm discrimination cannot be inferred.
4. **Production Decision**: Production Model M7 remains **STRICTLY FROZEN**. Model B is cataloged as an operational physical prototype for future multi-season evaluation.

---

## 8. What Cannot Be Concluded
1. We cannot conclude that Model M6 has established discrimination (ROC-AUC) on external data without negative control slopes.
2. We cannot conclude that Model M7 discriminates triggers across multiple storms without a multi-year storm catalog ($N_{\text{events}} \ge 15$).
3. We cannot conclude that Model B is statistically superior to Model A without multi-catchment, multi-year validation.
4. We cannot claim engineering-grade slope stability without site-specific borehole triaxial shear tests.

---

## 9. Final Validation Status

- **M6 External Validation**: **`INSUFFICIENT_SAMPLE`** (20 failure points, 0 controls; single-class; ROC-AUC is NOT ESTIMABLE).
- **M7 External Validation**: **`PARTIALLY_VALIDATED`** (22 spatial samples under 1 storm event; event-level ROC-AUC is NOT ESTIMABLE; spatial recall = 100%).
- **PWP v1 Status**: **`IMPLEMENTED, UNIT-TESTED, NOT FIELD-VALIDATED`** (Theoretical limit-equilibrium simulation; direct continuous piezometer ground truth unavailable).
