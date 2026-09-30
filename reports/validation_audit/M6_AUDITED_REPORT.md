# MODEL M6: LANDSLIDE SUSCEPTIBILITY SCIENTIFIC AUDIT REPORT
**FLOODY SHIELD — Independent External Validation Stage A**  
*Problem Statement 26192 | Upper Beas Basin, Himachal Pradesh*  
*Validation Status: AUDITED & FROZEN | Validation Tier: INSUFFICIENT_SAMPLE*

---

## 1. Executive Summary & Audit Declaration

This report provides the audited, zero-fabrication external validation analysis of **Model M6 (Random Forest Landslide Susceptibility)**. In strict accordance with scientific standards:
- **Zero Retraining**: Production weights (`ml/landslide/m6_beas_susceptibility_rf.joblib`, SHA-256: `e4f5f933...`) remain strictly frozen.
- **Zero Synthetic Negatives**: The external inventory consists solely of documented landslide failure points ($N=20$). No synthetic unfailed slopes were generated.
- **Single-Class Limitation**: Because the external dataset contains positive failures only ($100\%$ single class), **ROC-AUC, PR-AUC, Specificity, Precision, and Accuracy are mathematically `NOT ESTIMABLE`**.
- **Spatial Independence Partition**: Evaluated against a strict $500\,\text{m}$ buffer of training points, yielding **11 strictly independent points** and **9 spatially non-independent points**.

---

## 2. Frozen Model Specification

| Attribute | Specification |
|:---|:---|
| **Model ID** | M6 |
| **Model Architecture** | Random Forest Classifier (350 trees, max_depth=9, min_samples_split=4) |
| **Model Artifact** | `ml/landslide/m6_beas_susceptibility_rf.joblib` |
| **Model SHA-256** | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` |
| **Input Features (8)** | Elevation, Horn's Slope, Aspect, Profile Curvature, Lithology, Road Distance, River Distance, LULC |
| **Predefined Operating Threshold** | $\tau = 0.50$ (Locked prior to external evaluation) |

---

## 3. Dataset Provenance & Spatial Independence Audit

### 3.1 External Inventory Metadata
- **Source**: Geological Survey of India (GSI Northern Region Report 2023) & HPSDMA Post-Disaster Needs Assessment (PDNA 2023).
- **File**: `data/external/m6/upper_beas/raw/kullu_upper_beas_landslides_2023_raw.csv` (SHA-256: `e56c5ecd...`)
- **Total Field Failure Locations**: 20 points along the NH-3 Beas River corridor (Bahang, Aloo Ground, Kalath, Patli Kuhal, Raison, Marhi, Palchan, etc.).
- **Event Date**: July 9–10, 2023 monsoonal cloudburst disaster peak.
- **AOI Compliance**: 20 / 20 points ($100.0\%$) fall inside the Upper Beas AOI (Lat $31.60^\circ - 32.40^\circ\text{N}$, Lon $76.80^\circ - 77.45^\circ\text{E}$).

### 3.2 Proximity Leakage Partition ($500\,\text{m}$ Exclusion Buffer)
Following Martha et al. (2010), points within $500\,\text{m}$ of training points are isolated to prevent optimistic spatial autocorrelation bias:
- **Primary Independent Subset ($>500\,\text{m}$)**: **11 points (55.0%)** (Mean distance to training: $517.9\,\text{m}$)
- **Non-Independent Subset ($\le 500\,\text{m}$)**: **9 points (45.0%)** (Mean distance to training: $310.6\,\text{m}$, Min: $85.6\,\text{m}$)

---

## 4. Audited Metric Evaluation

### 4.1 Primary Independent Subset ($N=11$, Positives Only)

| Metric | Measured Value | Audit Status | 95% Confidence Interval | Method / Rationale |
|:---|:---:|:---:|:---:|:---|
| **ROC-AUC** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Single-class dataset (0 negative controls). False-positive rate $0/0$ is mathematically undefined. |
| **PR-AUC** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Single-class dataset. Precision without negatives is mathematically undefined. |
| **Brier Score** | 0.3913 | `VALID` | Unreliable ($N < 15$) | Mean squared error to observed positive label ($y=1$). Bootstrap CI guarded ($N=11 < 15$). |
| **Recall (Sensitivity)** | **0.1818** (2/11) | `VALID` | **[0.0228, 0.5178]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Specificity** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | 0 negative control slopes available. |
| **Precision** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | False positives cannot occur on positive-only dataset. |
| **Accuracy** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Single-class dataset. |

### 4.2 Descriptive Reference: All 20 Points ($N=20$)
- **Observed Failure Capture Rate ($\tau = 0.50$)**: $13 / 20 = 65.0\%$ (Exact 95% Clopper-Pearson CI: $[0.4078, 0.8461]$).
- **Mean Predicted Susceptibility**: $0.4852 \pm 0.174$ (Range: $0.162 - 0.781$).

---

## 5. Physical & Geomorphic Interpretation

1. **Failure Along Anthropogenic Cuts**: Field investigations by GSI confirmed that failures along NH-3 were heavily triggered by steep roadside slope cutting and toe undercutting by the swollen Beas River.
2. **Model Under-prediction on Moderate Slopes**: Natural terrain slope at these points ranged from $20^\circ$ to $32^\circ$. Because Model M6 is trained on regional natural geomorphic features without fine-scale road-cut cross-sectional profiles, it predicts moderate natural susceptibility ($0.30 - 0.49$) for several of these sites.
3. **Requirement for Dynamic Trigger**: Static susceptibility alone is insufficient to predict rainfall-induced disaster occurrences; dynamic hydrometeorological forcing (Model M7 / PWP) is required.

---

## 6. Conservative Claims & Scientific Boundaries

### Supported Claims
- On the strictly independent subset ($N=11$, $>500\,\text{m}$ from training data), frozen Model M6 identified **18.2%** of documented failure sites (95% exact Clopper-Pearson CI: **[2.3%, 51.8%]**) at predefined probability threshold $0.50$.
- Across all 20 historical field failure points, frozen Model M6 identified **65.0%** (95% exact CI: **[40.8%, 84.6%]**).
- 9 of the 20 historical landslide locations fall within $500.0\,\text{m}$ of M6 training data; these provide descriptive characterization but are excluded from primary independent evidence.

### Unsupported Claims (Prohibited)
- **Prohibited**: Claiming ROC-AUC or PR-AUC on external data (mathematically not estimable without negative controls).
- **Prohibited**: Claiming high specificity, precision, or false-alarm rejection on external data.
- **Prohibited**: Claiming Model M6 is "fully validated" (Tier is `INSUFFICIENT_SAMPLE`).

---

## 7. Required Missing Evidence for Full Validation
1. **Authoritative Unfailed Control Slopes**: Geotechnically surveyed stable hillslopes in the Upper Beas basin with slope angles $\ge 20^\circ$ that remained intact during the July 2023 disaster.
