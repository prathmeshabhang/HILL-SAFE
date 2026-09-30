"""
conformal_engine.py — Rigorous Conformal Uncertainty Quantification for FLOODY SHIELD
======================================================================================
Provides finite-sample statistical coverage guarantees (P(Y in C(X)) >= 1 - alpha)
for:
  1. Model M2: Flash Flood Prediction
  2. Model M7: Dynamic Landslide Trigger

Generates:
  - Nonconformity quantiles (q_hat) at alpha = 0.10 (90% coverage) and alpha = 0.05 (95% coverage)
  - Conformal prediction sets:
      * {1}: Definite Hazard (Actionable High Risk)
      * {0}: Definite Safe (Low Risk)
      * {0, 1}: High Epistemic Uncertainty (Sensors / Field Observation Alert)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass
class ConformalCalibrator:
    alpha: float
    q_hat: float
    coverage_empirical: float
    set_efficiency: float  # Fraction of singleton prediction sets

    def predict_set(self, prob_positive: float) -> Tuple[List[int], str]:
        """
        Computes conformal prediction set for a given P(Y = 1).
        Nonconformity for y=1 is 1 - p. Nonconformity for y=0 is p.
        y in C(X) iff nonconformity <= q_hat <=> (for y=1: p >= 1 - q_hat, for y=0: 1 - p >= 1 - q_hat => p <= q_hat)
        """
        threshold_for_1 = 1.0 - self.q_hat
        threshold_for_0 = self.q_hat

        pred_set = []
        if prob_positive <= threshold_for_0:
            pred_set.append(0)
        if prob_positive >= threshold_for_1:
            pred_set.append(1)

        # Fallback if empty set (due to strict nonconformity)
        if not pred_set:
            pred_set = [int(prob_positive >= 0.5)]

        if pred_set == [1]:
            label = "DEFINITE_HAZARD"
        elif pred_set == [0]:
            label = "DEFINITE_SAFE"
        else:
            label = "EPISTEMIC_UNCERTAINTY"

        return pred_set, label


def calibrate_conformal_binary(
    y_calib: np.ndarray,
    probs_calib: np.ndarray,
    alpha: float = 0.10,
) -> ConformalCalibrator:
    """
    Computes split-conformal calibration quantile on holdout calibration data.
    """
    n = len(y_calib)
    # Nonconformity score s_i = 1 - P(Y = y_i)
    scores = np.where(y_calib == 1, 1.0 - probs_calib, probs_calib)

    # Conformal quantile level
    p_level = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / n)
    q_hat = float(np.quantile(scores, p_level, method="higher"))

    # Verify empirical coverage on calibration set
    calibrator = ConformalCalibrator(alpha=alpha, q_hat=q_hat, coverage_empirical=0.0, set_efficiency=0.0)
    covered = 0
    singletons = 0
    for y_true, p_hat in zip(y_calib, probs_calib):
        c_set, _ = calibrator.predict_set(p_hat)
        if y_true in c_set:
            covered += 1
        if len(c_set) == 1:
            singletons += 1

    calibrator.coverage_empirical = round(covered / n, 4)
    calibrator.set_efficiency = round(singletons / n, 4)
    return calibrator


def run_conformal_benchmarks() -> Dict[str, Any]:
    """
    Calibrates Conformal Predictors for M2 Flood and M7 Landslide Trigger models.
    """
    report = {}

    # 1. Calibrate Model M2
    flood_path = Path("data/processed/master_himalayan/himalayan_master_flood_dataset.csv")
    m2_model_file = Path("ml/flood/m2_deep_himalayan_flood_model.joblib")
    m2_scaler_file = Path("ml/flood/m2_flood_scaler.joblib")

    if flood_path.exists() and m2_model_file.exists() and m2_scaler_file.exists():
        from ml.flood.train_deep_m2_flood import FEATURE_COLS_26

        df_f = pd.read_csv(flood_path)
        model = joblib.load(m2_model_file)
        scaler = joblib.load(m2_scaler_file)

        X = df_f[FEATURE_COLS_26]
        y = df_f["flash_flood_occurred"].values
        _, X_cal, _, y_cal = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        X_cal_s = scaler.transform(X_cal)
        probs_cal = model.predict_proba(X_cal_s)[:, 1]

        cal_90 = calibrate_conformal_binary(y_cal, probs_cal, alpha=0.10)
        cal_95 = calibrate_conformal_binary(y_cal, probs_cal, alpha=0.05)

        report["m2_flood_conformal"] = {
            "alpha_0.10": {
                "guaranteed_coverage": "90%",
                "empirical_coverage": f"{cal_90.coverage_empirical * 100:.2f}%",
                "singleton_efficiency": f"{cal_90.set_efficiency * 100:.2f}%",
                "q_hat": round(cal_90.q_hat, 4),
            },
            "alpha_0.05": {
                "guaranteed_coverage": "95%",
                "empirical_coverage": f"{cal_95.coverage_empirical * 100:.2f}%",
                "singleton_efficiency": f"{cal_95.set_efficiency * 100:.2f}%",
                "q_hat": round(cal_95.q_hat, 4),
            },
        }

    # 2. Calibrate Model M7
    landslide_path = Path("data/processed/master_himalayan/himalayan_master_landslide_dataset.csv")
    m7_model_file = Path("ml/landslide/m7_deep_lgbm_trigger.joblib")
    m7_scaler_file = Path("ml/landslide/m7_landslide_scaler.joblib")

    if landslide_path.exists() and m7_model_file.exists() and m7_scaler_file.exists():
        df_l = pd.read_csv(landslide_path)
        m7_lgb = joblib.load(m7_model_file)
        scaler7 = joblib.load(m7_scaler_file)

        from ml.landslide.train_deep_landslide_suite import M7_DYNAMIC_FEATURES, DeepLandslideTriggerNN
        import torch

        # Load PyTorch weights
        net = DeepLandslideTriggerNN(input_dim=len(M7_DYNAMIC_FEATURES), hidden_dim=128, num_blocks=3)
        torch_file = Path("ml/landslide/m7_deep_resmlp_trigger.pt")
        net.load_state_dict(torch.load(torch_file, map_location="cpu"))
        net.eval()

        X_l = df_l[M7_DYNAMIC_FEATURES].values
        y_l = df_l["landslide_triggered"].values
        _, X_cal_l, _, y_cal_l = train_test_split(X_l, y_l, test_size=0.3, random_state=42, stratify=y_l)

        X_cal_l_s = scaler7.transform(X_cal_l)
        with torch.no_grad():
            t_X = torch.tensor(X_cal_l_s, dtype=torch.float32)
            p_nn = torch.sigmoid(net(t_X)).numpy()
        p_lgb = m7_lgb.predict_proba(X_cal_l_s)[:, 1]
        p_ensemble = (0.60 * p_nn) + (0.40 * p_lgb)

        cal_90_l = calibrate_conformal_binary(y_cal_l, p_ensemble, alpha=0.10)
        cal_95_l = calibrate_conformal_binary(y_cal_l, p_ensemble, alpha=0.05)

        report["m7_landslide_conformal"] = {
            "alpha_0.10": {
                "guaranteed_coverage": "90%",
                "empirical_coverage": f"{cal_90_l.coverage_empirical * 100:.2f}%",
                "singleton_efficiency": f"{cal_90_l.set_efficiency * 100:.2f}%",
                "q_hat": round(cal_90_l.q_hat, 4),
            },
            "alpha_0.05": {
                "guaranteed_coverage": "95%",
                "empirical_coverage": f"{cal_95_l.coverage_empirical * 100:.2f}%",
                "singleton_efficiency": f"{cal_95_l.set_efficiency * 100:.2f}%",
                "q_hat": round(cal_95_l.q_hat, 4),
            },
        }

    return report


if __name__ == "__main__":
    rep = run_conformal_benchmarks()
    import json
    print(json.dumps(rep, indent=2))
