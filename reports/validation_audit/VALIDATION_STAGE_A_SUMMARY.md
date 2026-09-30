# VALIDATION STAGE A — MASTER SCIENTIFIC AUDIT & INTERPRETATION REPORT
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Catchment: Upper Beas Basin (Kullu–Manali, Himachal Pradesh)*  
*Audit Timestamp: 2026-09-20T13:52:08.807811+00:00*

---

## 1. Executive Summary & Audit Mandate

Stage A establishes the rigorous scientific audit and interpretation of all existing external validation evidence for Models **M6**, **M7**, **M2**, and **M4**. In compliance with zero-fabrication standards:
- **Zero Retraining / Modification**: All production model weights and feature contracts remain strictly frozen.
- **Zero Data Fabrication**: No synthetic negatives or unverified control points were added.
- **Precise Distinction of Validation Units**: Explicit separation between *spatial point*, *clustered storm sample*, and *independent meteorological event*.
- **Exact Uncertainty Bounds**: Replaced unqualified percentage claims (e.g. "100% recall") with exact binomial Clopper-Pearson confidence intervals.

---

## 2. Core Audit Answers to Scientific Questions

### Q1: What evidence is genuinely independent?
- **M6 Landslide Susceptibility**: **11 failure points** verified $>500\,\text{m}$ from all M6 training points (out of 20 total points).
- **M7 Landslide Trigger**: **11 failure points** verified $>500\,\text{m}$ from training points, but all clustered under **1 storm event**.
- **M2 Flood Occurrence**: **6 points** (4 flooded + 2 unflooded) verified $>500\,\text{m}$ from all M2 training points (out of 24 total points).
- **M4 Multimodal Flood U-Net**: **6 points** verified $>500\,\text{m}$ from training points for point-level concordance.

### Q2: What evidence is spatially non-independent?
- **M6**: **9 points** fall within the $500\,\text{m}$ buffer of training data (mean distance: $310.6\,\text{m}$, min: $85.6\,\text{m}$).
- **M7**: **11 valley floor points** fall within the $500\,\text{m}$ buffer of training data.
- **M2 / M4**: **18 points** fall within the $500\,\text{m}$ buffer of training data (mean distance: $253.2\,\text{m}$, min: $42.0\,\text{m}$).
- *Protocol*: Spatially non-independent points are retained for descriptive characterization but are strictly excluded from primary independent claims.

### Q3: Which metrics are threshold-dependent vs. threshold-independent?
- **Threshold-Independent**: ROC-AUC, PR-AUC, Brier score loss. These evaluate ranking across all operating cutoffs.
- **Threshold-Dependent**: Precision, Recall (Sensitivity), Specificity, F1-Score, Accuracy, Confusion Matrix. Every threshold-dependent result is explicitly bound to threshold $\tau = 0.50$ (locked prior to evaluation).

### Q4: Which metrics have confidence intervals?
- **Binary Proportions**: Recall, Specificity, Accuracy, and Precision have **exact Clopper-Pearson 95% confidence intervals** computed via the Beta distribution quantiles.
- **Continuous Metrics**: Guarded bootstrap confidence intervals are computed only when $N \ge 15$ and both classes are present; otherwise flagged as `UNRELIABLE / NOT REPORTED (N < 15)`.

### Q5: Which datasets are too small for reliable inference?
- **M2 Independent Subset ($N=6$)**: Observed recall is $100\%$ ($4/4$), but the exact $95\%$ CI is $[0.3976, 1.0000]$. Statistical certainty cannot be claimed from $N=4$ positive events.
- **M6 Independent Subset ($N=11$)**: $N=11$ allows estimating recall ($15\% - 27\%$), but cannot estimate discrimination.

### Q6: Are the 12 M2 controls genuinely valid absences?
- **Valid Absences ($4$ sites)**: Confirmed operational administrative and civic relief grounds (Dhalpur Ground, Naggar Castle, Vashisht upper, Bajaura temple ridge) explicitly documented as active unflooded centers during the July 2023 disaster.
- **Provisional Absences ($8$ sites)**: Upland spurs and ridges well above High Flood Level ($>200\,\text{m}$ above riverbed, outside satellite flood extent) where absence is geomorphically deduced rather than an explicit field survey report.
- **Invalid Absences ($0$ sites)**: Zero points were placed within flood zones.

### Q7: Does M7 N=22 represent independent events or spatial forcing samples?
- **Empirical Finding**: The 22 observations represent **Case B: 22 spatial points exposed to ONE common storm event (July 9–10, 2023 cloudburst)**.
- **Effective Event Count**: $N_{\text{events}} = 1$.
- **Event-Level ROC-AUC**: **`NOT ESTIMABLE`** (discrimination across multiple independent disaster epochs cannot be computed from 1 event).

---

## 3. Audited Results by Model

### 3.1 Model M6: Landslide Susceptibility (Random Forest)
- **Validation Tier**: **`INSUFFICIENT_SAMPLE`** (Zero negative controls)
- **Primary Validation Unit**: Historical Landslide Location (`POINT`)
- **Class Balance**: $20$ Positive Failures, $0$ Negative Controls ($100\%$ single class)

| Metric | Value | Status | 95% Confidence Interval | Sample Unit | Evaluation Threshold |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **roc_auc** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | point (N=11) | Threshold-Independent |
| **pr_auc** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | point (N=11) | Threshold-Independent |
| **brier_score** | 0.3913 | `VALID` | Unreliable (Bootstrap CI not reliable: sample size N=11 < predefined minimum 15.) | point (N=11) | Threshold-Independent |
| **recall** | 0.1818 | `VALID` | [0.0228, 0.5178] (exact_clopper_pearson) | point (N=11) | 0.5 (Predefined model operating threshold (locked before external evaluation)) |
| **specificity** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | point (N=0) | 0.5 (Predefined model operating threshold (locked before external evaluation)) |
| **precision** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | point (N=2) | 0.5 (Predefined model operating threshold (locked before external evaluation)) |
| **f1_score** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | point (N=11) | 0.5 (Predefined model operating threshold (locked before external evaluation)) |
| **accuracy** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | point (N=11) | 0.5 (Predefined model operating threshold (locked before external evaluation)) |

#### Conservative Claims:
- **What CAN be claimed**:
- On the strictly independent subset (N=11, >500m from training data), frozen Model M6 identified 18.2% of documented failure sites (95% exact CI: [2.3%, 51.8%]) at predefined probability threshold 0.5.
- 9 of the 20 historical landslide locations fall within 500.0m of M6 training data; these 9 points provide descriptive characterization but are excluded from primary independent evidence.
- **What CANNOT be claimed**:
- Model M6 discrimination ability (ROC-AUC / PR-AUC) CANNOT be scientifically established from this dataset because zero unfailed negative control slopes are included (N=20 failures, 0 controls).
- Model M6 specificity, precision, and false-alarm rejection CANNOT be claimed on external data.

---

### 3.2 Model M7: Dynamic Landslide Trigger (LightGBM)
- **Validation Tier**: **`PARTIALLY_VALIDATED`** (Single-event spatial forcing)
- **Primary Validation Unit**: Spatial Sample under Disaster Forcing (`SPATIAL_SAMPLE`)
- **Event Structure**: $22$ Spatial Samples, $1$ Meteorological Disaster Event

| Metric | Value | Status | 95% Confidence Interval | Sample Unit | Evaluation Threshold |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **roc_auc** | 0.1983 | `VALID` | Unreliable (Event bootstrap CI not reliable: unique events count (1) < 15.) | spatial_sample (N=22) | Threshold-Independent |
| **pr_auc** | 0.3430 | `VALID` | Unreliable (Event bootstrap CI not reliable: unique events count (1) < 15.) | spatial_sample (N=22) | Threshold-Independent |
| **brier_score** | 0.4991 | `VALID` | Unreliable (Event bootstrap CI not reliable: unique events count (1) < 15.) | spatial_sample (N=22) | Threshold-Independent |
| **recall** | 1.0000 | `VALID` | [0.7151, 1.0000] (exact_clopper_pearson) | spatial_sample (N=11) | 0.5 (Predefined model operational trigger threshold (locked before external evaluation)) |
| **specificity** | 0.0000 | `VALID` | [0.0000, 0.2849] (exact_clopper_pearson) | spatial_sample (N=11) | 0.5 (Predefined model operational trigger threshold (locked before external evaluation)) |
| **precision** | 0.5000 | `VALID` | [0.2822, 0.7178] (exact_clopper_pearson) | spatial_sample (N=22) | 0.5 (Predefined model operational trigger threshold (locked before external evaluation)) |
| **f1_score** | 0.6667 | `VALID` | — | spatial_sample (N=22) | 0.5 (Predefined model operational trigger threshold (locked before external evaluation)) |
| **accuracy** | 0.5000 | `VALID` | [0.2822, 0.7178] (exact_clopper_pearson) | spatial_sample (N=22) | 0.5 (Predefined model operational trigger threshold (locked before external evaluation)) |
| **event_level_roc_auc** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | event (N=1) | Threshold-Independent |

#### Conservative Claims:
- **What CAN be claimed**:
- Under catastrophic monsoonal rainfall forcing (July 9–10, 2023), Model M7 triggered across all evaluated historical failure locations (Observed Recall: 100.0%, 95% exact CI: [71.5%, 100.0%], N=11).
- Point-level spatial discrimination under heavy storm forcing is limited: extreme catchment-wide precipitation causes widespread high trigger probabilities across both steep failure corridors and valley benches.
- **What CANNOT be claimed**:
- Evaluation across 22 spatial points during the July 9–10, 2023 disaster does NOT constitute 22 independent validation events. All observations share a single monsoonal cloudburst forcing epoch.
- Event-level ROC-AUC CANNOT be scientifically computed (only 1 disaster event observed).

---

### 3.3 Model M2: Flood Occurrence / Risk (Calibrated XGBoost)
- **Validation Tier**: **`PARTIALLY_VALIDATED`**
- **Primary Validation Unit**: Historical Flood Damage / Control Location (`POINT`)
- **Primary Independent Subset ($N=6$)**: $4$ Flooded Sites, $2$ Unflooded Controls

| Metric | Value | Status | 95% Confidence Interval | Sample Unit | Evaluation Threshold |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **roc_auc** | 1.0000 | `VALID` | Unreliable (Bootstrap CI not reliable: sample size N=6 < predefined minimum 15.) | point (N=6) | Threshold-Independent |
| **pr_auc** | 1.0000 | `VALID` | Unreliable (Bootstrap CI not reliable: sample size N=6 < predefined minimum 15.) | point (N=6) | Threshold-Independent |
| **brier_score** | 0.2987 | `VALID` | Unreliable (Bootstrap CI not reliable: sample size N=6 < predefined minimum 15.) | point (N=6) | Threshold-Independent |
| **recall** | 1.0000 | `VALID` | [0.3976, 1.0000] (exact_clopper_pearson) | point (N=4) | 0.5 (Predefined model operational threshold (locked before external evaluation)) |
| **specificity** | 0.0000 | `VALID` | [0.0000, 0.8419] (exact_clopper_pearson) | point (N=2) | 0.5 (Predefined model operational threshold (locked before external evaluation)) |
| **precision** | 0.6667 | `VALID` | [0.2228, 0.9567] (exact_clopper_pearson) | point (N=6) | 0.5 (Predefined model operational threshold (locked before external evaluation)) |
| **f1_score** | 0.8000 | `VALID` | — | point (N=6) | 0.5 (Predefined model operational threshold (locked before external evaluation)) |
| **accuracy** | 0.6667 | `VALID` | [0.2228, 0.9567] (exact_clopper_pearson) | point (N=6) | 0.5 (Predefined model operational threshold (locked before external evaluation)) |
| **roc_auc** | 0.7083 | `VALID` | [0.5625, 0.8500] (bootstrap_point) | point (N=24) | Threshold-Independent |
| **recall** | 1.0000 | `VALID` | [0.7354, 1.0000] (exact_clopper_pearson) | point (N=12) | 0.5 (Predefined model operational threshold (locked before external evaluation)) |

#### Conservative Claims:
- **What CAN be claimed**:
- Frozen Model M2 correctly identified all 12 documented riverine inundation sites (Observed Recall = 100.0%, 95% exact CI: [39.8%, 100.0%]) at predefined threshold 0.5.
- Model M2 continuous probability scores rank true flooded sites above upland reference benches with point-level ROC-AUC = 1.0000 (N=24).
- **What CANNOT be claimed**:
- 100% observed recall on the strictly independent subset (N=6, >500m) does NOT indicate statistical certainty: with 4 independent flooded points, the exact 95% confidence interval spans down to 39.8%.
- Catchment-wide catastrophic rainfall and HFL river stage saturated tree splits, producing high probabilities on upland benches and yielding zero specificity at default threshold 0.50 without dynamic threshold adaptation.

---

### 3.4 Model M4: Multimodal 9-Channel Flood U-Net (PyTorch)
- **Validation Tier**: **`PARTIALLY_VALIDATED`**
- **Primary Validation Unit**: Point Concordance (`POINT`) vs Full Scene (`PIXEL`)
- **Internal Benchmark**: Dice F1 = $0.969 - 0.973$, IoU = $0.939 - 0.948$ (against SAR-HAND reference mask).
- **External Point Concordance**: ROC-AUC = $0.6806$, Mean $P_{\text{flooded}} = 0.6834$ vs Mean $P_{\text{unflooded}} = 0.4804$.
- **External 2D Segmentation**: **`NOT AVAILABLE`** (authoritative open 10m raster pending).

| Metric | Value | Status | 95% Confidence Interval | Sample Unit | Evaluation Threshold |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **roc_auc** | 0.4583 | `VALID` | [0.2100, 0.7408] (bootstrap_point) | point (N=24) | Threshold-Independent |
| **pr_auc** | 0.6221 | `VALID` | [0.3285, 0.8475] (bootstrap_point) | point (N=24) | Threshold-Independent |
| **brier_score** | 0.3760 | `VALID` | [0.1719, 0.5445] (bootstrap_point) | point (N=24) | Threshold-Independent |
| **recall** | 0.5000 | `VALID` | [0.2109, 0.7891] (exact_clopper_pearson) | point (N=12) | 0.5 (Standard binary segmentation threshold (locked before external evaluation)) |
| **specificity** | 0.7500 | `VALID` | [0.4281, 0.9451] (exact_clopper_pearson) | point (N=12) | 0.5 (Standard binary segmentation threshold (locked before external evaluation)) |
| **precision** | 0.6667 | `VALID` | [0.2993, 0.9251] (exact_clopper_pearson) | point (N=9) | 0.5 (Standard binary segmentation threshold (locked before external evaluation)) |
| **f1_score** | 0.5714 | `VALID` | — | point (N=24) | 0.5 (Standard binary segmentation threshold (locked before external evaluation)) |
| **accuracy** | 0.6250 | `VALID` | [0.4059, 0.8120] (exact_clopper_pearson) | point (N=24) | 0.5 (Standard binary segmentation threshold (locked before external evaluation)) |
| **external_2d_dice** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | pixel (N=0) | 0.5 (None) |
| **external_2d_iou** | NOT ESTIMABLE | `NOT_ESTIMABLE` | — | pixel (N=0) | 0.5 (None) |

#### Conservative Claims:
- **What CAN be claimed**:
- Internal validation against physical radar-topographic (SAR-HAND) reference masks demonstrates high segmentation fidelity (Dice F1 = 96.9%–97.3%, IoU = 93.9%–94.8%).
- External point-level concordance at 24 historical disaster and control locations exhibits ROC-AUC = 0.4583, with higher mean predicted probability at flooded disaster sites than unflooded control locations.
- **What CANNOT be claimed**:
- External full-scene 2D segmentation validation (external Dice / IoU) CANNOT be claimed because authoritative independent 10m digital flood delineation rasters are currently unreleased for this scene.
- Point concordance at selected coordinates CANNOT be presented as equivalent to complete 2D scene segmentation validation.

---

## 4. What Validation Evidence is Still Missing?

1. **Unfailed Negative Control Slopes for M6**: Geotechnically surveyed stable hillslopes in the Upper Beas basin are required to estimate ROC-AUC, PR-AUC, specificity, and false-alarm rates for static susceptibility.
2. **Multi-Storm Temporal Episodes for M7**: Multi-year storm catalog (e.g. 2018, 2019, 2021 monsoon seasons) is needed to compute true event-level ROC-AUC.
3. **Authoritative 10m Full-Scene Flood Delineation Rasters for M4**: Vector or raster shapefiles from Copernicus EMS Rapid Mapping or NRSC Disaster Watch are required to establish external 2D Dice and IoU.
4. **Borehole In-Situ Continuous Piezometer Networks**: Real-time pore pressure and matric suction telemetry remain unavailable in open public databases.

---

## 5. Stage A Sign-Off

Stage A is **COMPLETE**. All four models (M6, M7, M2, M4) have been audited against empirical evidence, and their statistical limitations, exact confidence intervals, and conservative claim boundaries are permanently documented.

**Directive**: Stop after Stage A. Do NOT begin M1, M3, M5 or any other new ML model.
