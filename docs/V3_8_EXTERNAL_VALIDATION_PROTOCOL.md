# FLOODY SHIELD v3.8 — Scientific External Validation Protocol

**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh  
**Protocol Version:** v3.8.0  
**Verification Tool:** `tools/validation/run_external_validation.py`  

---

## 1. Frozen Model Guarantee

Models **M2, M4, M6, and M7** are immutable frozen scientific models. The validation protocol enforces the following absolute constraints:
- **No Fine-Tuning**: Hyperparameters and weights are locked.
- **No Threshold Cheating**: Predefined operational thresholds ($\tau = 0.50$) are used.
- **Pre & Post Hash Checks**: SHA-256 digests are computed immediately before and after validation runs. Any change terminates the pipeline with exit code 1.

---

## 2. Statistical Validation Metrics

### A. Classification & Susceptibility Models (M6, M7, M9, M20)
- **Accuracy**, **Precision**, **Recall**, and **Macro F1-Score**.
- **Area Under the ROC Curve (AUROC)**: Assesses rank discrimination.
- **Brier Score**: Evaluates probability calibration loss ($BS = \frac{1}{N}\sum (p_i - y_i)^2$).
- **95% Bootstrap Confidence Intervals**: 1,000 bootstrap resamples computed for all sample sizes $N \ge 30$.

### B. Hydrological & Hydrodynamic Models (M2, M10, M11, M14, M19)
- **Nash-Sutcliffe Efficiency (NSE)**:
  $$NSE = 1 - \frac{\sum_{t=1}^T (Q_o^t - Q_m^t)^2}{\sum_{t=1}^T (Q_o^t - \overline{Q_o})^2}$$
- **Kling-Gupta Efficiency (KGE)**:
  $$KGE = 1 - \sqrt{(r - 1)^2 + (\alpha - 1)^2 + (\beta - 1)^2}$$
- **Percent Bias (PBIAS)**:
  $$PBIAS = 100 \times \frac{\sum_{t=1}^T (Q_m^t - Q_o^t)}{\sum_{t=1}^T Q_o^t}$$
- **Root Mean Square Error (RMSE)** and **Mean Absolute Percentage Error (MAPE)**.

---

## 3. Data Leakage Prevention

1. **Spatial Disjointness**: Evaluation points are verified to maintain spatial separation $> 500\text{ m}$ from historical training polygons.
2. **Temporal Split Independence**: Validation events are strictly out-of-time (e.g., July 2023 disaster events evaluated on models trained on pre-2022 historical distributions).
