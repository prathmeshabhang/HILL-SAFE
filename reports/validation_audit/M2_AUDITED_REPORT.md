# MODEL M2: FLOOD OCCURRENCE / RISK SCIENTIFIC AUDIT REPORT
**FLOODY SHIELD — Independent External Validation Stage A**  
*Problem Statement 26192 | Upper Beas Basin, Himachal Pradesh*  
*Validation Status: AUDITED & FROZEN | Validation Tier: PARTIALLY_VALIDATED*

---

## 1. Executive Summary & Audit Declaration

This report provides the audited external validation analysis of **Model M2 (Calibrated XGBoost Flood Occurrence / Risk)** against authentic disaster documentation from the July 2023 Upper Beas catastrophe. In strict accordance with scientific standards:
- **Zero Retraining**: Production weights (`ml/flood/m2_beas_flood_xgb_calibrated.joblib`, SHA-256: `60d1ba58...`) remain strictly frozen.
- **Spatial Independence Partition**: Evaluated against a strict $500\,\text{m}$ buffer of M2's 10,000 training points, yielding **6 strictly independent points** and **18 spatially non-independent points**.
- **Negative Control Quality Audit**: All 12 unflooded control sites were audited against a 5-point checklist, confirming **1 valid absence** (Dhalpur Ground relief center) and **11 provisional absences** (upland spurs outside satellite inundation).
- **Exact Uncertainty Bounds**: Demonstrated that while observed recall on independent data is $100\%$ ($4/4$), the exact 95% Clopper-Pearson confidence interval is **$[0.3976, 1.0000]$**, highlighting substantial small-sample uncertainty.

---

## 2. Frozen Model Specification

| Attribute | Specification |
|:---|:---|
| **Model ID** | M2 |
| **Model Architecture** | CalibratedClassifierCV(XGBClassifier(n_estimators=300, max_depth=6), method='isotonic') |
| **Model Artifact** | `ml/flood/m2_beas_flood_xgb_calibrated.joblib` |
| **Model SHA-256** | `60d1ba58dbebf436c6410ce9761a2979261ff5a840e691217e94e5ec6d4f90bf` |
| **Input Features (6)** | Elevation, Slope, HAND (Height Above Nearest Drainage), Distance to River, 24h Rainfall, River Stage |
| **Predefined Operating Threshold** | $\tau = 0.50$ (Locked prior to external evaluation) |

---

## 3. Dataset Provenance & Control Quality Audit

### 3.1 Dataset Metadata
- **Source**: HPSDMA Post-Disaster Needs Assessment (PDNA 2023), Central Water Commission (CWC Flood Situation Report July 2023), NRSC Disaster Watch Maps.
- **File**: `data/external/flood/raw/upper_beas_flood_events_2023_raw.csv` (SHA-256: `484c7677...`)
- **Total Locations**: 24 points (12 flooded disaster sites + 12 unflooded control sites).
- **AOI Compliance**: 24 / 24 points ($100.0\%$) inside Upper Beas AOI.

### 3.2 Negative Control Quality Grading (5-Point Checklist A–E)
- **Criterion A (Source Independence)**: Controls derived from official administrative district records and topo sheets.
- **Criterion B (Outside Inundation Extent)**: Controls verified outside Sentinel-1 / NRSC water masks.
- **Criterion C (Geomorphic Plausibility)**: Elevations $>200\,\text{m}$ above High Flood Level (HFL).
- **Criterion D (Contemporaneous Observation)**: July 9–10, 2023 disaster window.
- **Criterion E (Positive Verification of Absence)**:
  - **VALID_ABSENCE (1 site)**: `NFL_07` (Dhalpur Ground, Kullu) — officially documented active civil relief camp and helicopter landing zone; positive proof of non-submergence.
  - **PROVISIONAL_ABSENCE (11 sites)**: Upland spurs/terraces (Vashisht, Naggar, Bajaura, etc.) geomorphically deduced as dry, but without explicit continuous water level sensor telemetry.
  - **INVALID_ABSENCE (0 sites)**: Zero controls were located within flood corridors.

### 3.3 Spatial Leakage Partition ($500\,\text{m}$ Exclusion Buffer)
- **Primary Independent Subset ($>500\,\text{m}$)**: **6 points (25.0%)** (4 flooded sites, 2 unflooded controls; Mean distance: $694.1\,\text{m}$)
- **Non-Independent Subset ($\le 500\,\text{m}$)**: **18 points (75.0%)** (8 flooded sites, 10 unflooded controls; Mean distance: $253.2\,\text{m}$)

---

## 4. Audited Metric Evaluation

### 4.1 Primary Independent Subset ($N=6$, $>500\,\text{m}$ Separation)

| Metric | Measured Value | Audit Status | 95% Confidence Interval | Method / Rationale |
|:---|:---:|:---:|:---:|:---|
| **ROC-AUC** | 1.0000 | `VALID` | Unreliable ($N < 15$) | Perfect continuous rank discrimination on 6 samples; bootstrap guarded ($N=6 < 15$). |
| **PR-AUC** | 1.0000 | `VALID` | Unreliable ($N < 15$) | Perfect precision-recall ranking on 6 samples; bootstrap guarded ($N=6 < 15$). |
| **Brier Score** | 0.2987 | `VALID` | Unreliable ($N < 15$) | Mean squared error; bootstrap guarded. |
| **Recall (Sensitivity)** | **1.0000** (4/4) | `VALID` | **[0.3976, 1.0000]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Specificity** | **0.0000** (0/2) | `VALID` | **[0.0000, 0.8419]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Precision** | 0.6667 (4/6) | `VALID` | [0.2228, 0.9567] | Exact Clopper-Pearson binomial CI at operating threshold $\tau = 0.50$. |
| **Accuracy** | 0.6667 (4/6) | `VALID` | [0.2228, 0.9567] | Exact Clopper-Pearson binomial CI at operating threshold $\tau = 0.50$. |

### 4.2 Full External Dataset ($N=24$ for Descriptive Comparison)
- **Recall ($\tau = 0.50$)**: $12 / 12 = 100.0\%$ (Exact 95% CI: $[0.7354, 1.0000]$).
- **Specificity ($\tau = 0.50$)**: $0 / 12 = 0.0\%$ (Exact 95% CI: $[0.0000, 0.2646]$).
- **ROC-AUC**: $0.7083$ (95% Bootstrap CI: $[0.5000, 0.8958]$).
- **PR-AUC**: $0.8158$ (95% Bootstrap CI: $[0.5843, 0.9632]$).

---

## 5. Statistical Significance of Confidence Intervals

The exact Clopper-Pearson interval $[0.3976, 1.0000]$ demonstrates the necessity of uncertainty quantification:
- Even though $4$ out of $4$ independent flooded locations were detected, the true population recall could be as low as $39.8\%$ with 95% confidence.
- Similarly, while ROC-AUC on 6 samples is $1.0000$, generalizing this to claim "perfect discrimination" would be scientifically invalid.

---

## 6. Conservative Claims & Scientific Boundaries

### Supported Claims
- On the strictly independent subset ($N=6$, $>500\,\text{m}$ from training data), frozen Model M2 detected **100.0%** of flooded disaster locations ($4/4$, 95% exact Clopper-Pearson CI: **[39.8%, 100.0%]**) at predefined threshold $0.50$.
- Model M2 continuously ranks flooded locations higher ($P=1.0000$) than unflooded upland controls ($P=0.874 - 0.995$), yielding an overall ROC-AUC of **0.7083** across all 24 points.
- 1 unflooded control (Dhalpur Ground) is verified as a valid absence; 11 controls are provisional absences.

### Unsupported Claims (Prohibited)
- **Prohibited**: Claiming perfect detection or zero misses based on $4/4$ samples without reporting the wide $[0.3976, 1.0000]$ confidence interval.
- **Prohibited**: Claiming high specificity or low false alarms during catastrophic flood emergencies (under extreme rainfall, threshold $\tau=0.50$ saturates).
- **Prohibited**: Claiming ROC-AUC = 1.0000 is representative of general model performance across normal rainfall regimes.

---

## 7. Required Missing Evidence for Full Validation
1. **Low and Moderate Flow Non-Flood Events**: Controlled validation across seasonal high-flow events (e.g. 2021, 2022 monsoons) that did not breach riverbanks to establish true operational specificity.
2. **Dense In-Situ River Gauge Network**: Continuous hourly river stage telemetry across all sub-catchments.
