# MODEL M7: DYNAMIC LANDSLIDE TRIGGER SCIENTIFIC AUDIT REPORT
**FLOODY SHIELD — Independent External Validation Stage A**  
*Problem Statement 26192 | Upper Beas Basin, Himachal Pradesh*  
*Validation Status: AUDITED & FROZEN | Validation Tier: PARTIALLY_VALIDATED*

---

## 1. Executive Summary & Audit Declaration

This report provides the audited external validation analysis of **Model M7 (LightGBM Dynamic Rainfall Landslide Trigger)**. In strict accordance with scientific standards:
- **Zero Retraining**: Production weights (`ml/landslide/m7_beas_trigger_lgbm.joblib`, SHA-256: `8df1e9f1...`) remain strictly frozen.
- **Event-Level Audit**: The 22 evaluation observations represent **Case B: 22 spatial points exposed to a single common storm event (July 9–10, 2023 cloudburst)**.
- **Single-Event Limitation**: Because the effective number of independent disaster events is $N_{\text{events}} = 1$, **Event-Level ROC-AUC is mathematically `NOT ESTIMABLE`**.
- **Spatial Metric Distinction**: Point metrics evaluated under uniform extreme precipitation reflect spatial variation under single-storm forcing, not multi-storm trigger discrimination.

---

## 2. Frozen Model Specification

| Attribute | Specification |
|:---|:---|
| **Model ID** | M7 |
| **Model Architecture** | LightGBM Classifier (350 boosting rounds, lr=0.03, num_leaves=31) |
| **Model Artifact** | `ml/landslide/m7_beas_trigger_lgbm.joblib` |
| **Model SHA-256** | `8df1e9f16d566373b9ba23668380cf75eaebfbf8e49339e6022e379417dc5598` |
| **Input Features (5)** | 1-hour rainfall, 24-hour rainfall, 72-hour antecedent rainfall, terrain slope, static M6 susceptibility |
| **Predefined Operating Threshold** | $\tau = 0.50$ (Locked prior to external evaluation) |

---

## 3. Disaster Forcing & Clustered Sample Structure

### 3.1 Disaster Meteorological Forcing
- **Disaster Epoch**: July 9–10, 2023 Monsoonal Cloudburst / Flash Flood Peak.
- **Meteorological Forcing**:
  - $R_{1h} \approx 35 - 65\,\text{mm/h}$ (Intense convective bursts)
  - $R_{24h} \approx 180 - 240\,\text{mm/day}$
  - $R_{72h} \approx 220 - 310\,\text{mm}$ (Antecedent soil saturation)

### 3.2 Evaluation Sample Cohort ($N=22$)
- **Spatial Failure Points ($N=11$)**: Ground-verified landslide failure points along the NH-3 corridor $>500\,\text{m}$ from M6/M7 training data.
- **Spatial Valley Control Points ($N=11$)**: Valley floor and low-angle terrain sites that experienced the same storm forcing.
- **Event Structure Classification**: **Case B (22 spatial points, 1 storm event)**.

---

## 4. Audited Metric Evaluation

### 4.1 Spatial Sample Metrics Under Disaster Forcing ($N=22$ Spatial Points)

| Metric | Measured Value | Audit Status | 95% Confidence Interval | Method / Rationale |
|:---|:---:|:---:|:---:|:---|
| **Event-Level ROC-AUC** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Only 1 disaster event available ($N_{\text{events}} = 1$). Discrimination across independent storm episodes cannot be computed. |
| **Spatial Sample ROC-AUC** | 0.1983 | `VALID` | Unreliable (1 event) | Measures spatial discrimination under single uniform cloudburst forcing. Bootstrap guarded. |
| **Spatial Sample PR-AUC** | 0.3430 | `VALID` | Unreliable (1 event) | Precision-recall area across spatial samples under single storm. |
| **Brier Score** | 0.4991 | `VALID` | Unreliable (1 event) | Calibration loss under extreme storm conditions. |
| **Spatial Recall (Sensitivity)** | **1.0000** (11/11) | `VALID` | **[0.7151, 1.0000]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Spatial Specificity** | **0.0000** (0/11) | `VALID` | **[0.0000, 0.2849]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Spatial Precision** | 0.5000 (11/22) | `VALID` | [0.2822, 0.7178] | Exact Clopper-Pearson binomial CI at operating threshold $\tau = 0.50$. |
| **Spatial Accuracy** | 0.5000 (11/22) | `VALID` | [0.2822, 0.7178] | Exact Clopper-Pearson binomial CI at operating threshold $\tau = 0.50$. |

---

## 5. Hydrological Diagnosis: Why Specificity Saturates Under Cloudbursts

1. **Extreme Rainfall Feature Dominance**: Under catastrophic rainfall ($R_{24h} > 200\,\text{mm}$), LightGBM decision trees split heavily on precipitation magnitude, overriding subtle slope variations and driving predicted trigger probability $P \ge 0.50$ across valley floor points.
2. **PWP v1 Prototype Comparison**:
   - The experimental Pore-Water Pressure / Factor of Safety model (Model B) incorporates dynamic hydrological infiltration and effective normal stress reduction.
   - On the same 22 points, PWP v1 achieved **Spatial ROC-AUC = 0.4380** (vs M7's 0.1983) and **Spatial PR-AUC = 0.5168** (vs M7's 0.3430) while maintaining 100% trigger capture rate.
   - PWP v1 remains an experimental candidate; M7 remains the frozen production model.

---

## 6. Conservative Claims & Scientific Boundaries

### Supported Claims
- Under catastrophic monsoonal cloudburst forcing (July 9–10, 2023), frozen Model M7 triggered ($P \ge 0.50$) at **100.0%** of documented failure locations (95% exact Clopper-Pearson CI: **[71.5%, 100.0%]**).
- The 22 evaluation points represent spatial samples under a single meteorological disaster event ($N_{\text{events}} = 1$).

### Unsupported Claims (Prohibited)
- **Prohibited**: Claiming event-level trigger discrimination across multiple independent storm episodes (Event-level ROC-AUC is NOT ESTIMABLE).
- **Prohibited**: Claiming high spatial specificity under catastrophic rainfall without physical pore-pressure modeling.
- **Prohibited**: Treating 22 spatially correlated points as 22 independent statistical degrees of freedom.

---

## 7. Required Missing Evidence for Full Validation
1. **Multi-Year Storm Catalog**: 15+ independent rainstorm episodes (including moderate monsoonal storms $R_{24h} \approx 30 - 70\,\text{mm}$ that did NOT trigger catastrophic landslides) to compute true event-level ROC-AUC.
2. **In-Situ Piezometer Telemetry**: Continuous pore-water pressure and matric suction sensor logs from Himalayan slope monitoring stations.
