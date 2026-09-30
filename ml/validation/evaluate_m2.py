"""
evaluate_m2.py — Scientific Validation of Model M2 (Calibrated XGBoost Flood Model)
===================================================================================
Executes spatial holdout evaluation on Model M2:
  - Precision, Recall, F1, PR-AUC, ROC-AUC
  - Brier Score Loss & Expected Calibration Error (ECE)
  - Confusion matrix (TP, FP, TN, FN)
  - Spatial error diagnostics
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np

from ml.validation.calibration import evaluate_probability_calibration
from ml.validation.datasets import M2_EXPECTED_FEATURES, M2_TARGET, load_and_audit_flood_dataset
from ml.validation.event_split import create_event_holdout, create_temporal_holdout
from ml.validation.metrics import evaluate_binary_predictions
from ml.validation.spatial_metrics import analyze_spatial_prediction_errors
from ml.validation.spatial_split import create_spatial_block_holdout

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "ml" / "flood" / "m2_upper_beas_flood_model.joblib"


def run_m2_validation(model_path: Path = MODEL_PATH) -> Dict[str, Any]:
    """Runs complete scientific validation for Model M2."""
    df, audit = load_and_audit_flood_dataset()

    if not model_path.exists():
        raise FileNotFoundError(f"Model M2 artifact not found at {model_path}")

    model = joblib.load(model_path)

    # 1. Spatial Holdout Split
    spatial_split = create_spatial_block_holdout(df, lat_col="lat", lon_col="lon", test_fraction=0.20)
    test_df = df.iloc[spatial_split.test_indices]

    X_test = test_df[M2_EXPECTED_FEATURES]
    y_test = test_df[M2_TARGET].values

    # 2. Inference
    y_prob = model.predict_proba(X_test)[:, 1]

    # 3. Metrics
    binary_metrics = evaluate_binary_predictions(y_test, y_prob)
    calib_report = evaluate_probability_calibration(y_test, y_prob)
    spatial_err = analyze_spatial_prediction_errors(test_df, y_test, y_prob)

    # 4. Check Event/Temporal holdout availability
    event_check = create_event_holdout(df)
    temporal_check = create_temporal_holdout(df)

    return {
        "model_name": "Model_M2_Calibrated_XGBoost",
        "model_version": "v1.0-calibrated",
        "artifact_path": str(model_path),
        "validation_strategy": {
            "spatial_holdout": "AVAILABLE_AND_EVALUATED",
            "spatial_split_details": {
                "method": spatial_split.split_method,
                "train_samples": spatial_split.train_count,
                "test_samples": spatial_split.test_count,
                "train_lat_range": spatial_split.train_lat_range,
                "test_lat_range": spatial_split.test_lat_range,
            },
            "event_holdout": event_check.status_message,
            "temporal_holdout": temporal_check.status_message,
        },
        "dataset_audit": {
            "dataset_name": audit.dataset_name,
            "sha256_hash": audit.sha256_hash,
            "total_rows": audit.row_count,
            "target_distribution": audit.target_distribution,
        },
        "metrics": {
            "accuracy": binary_metrics.accuracy,
            "precision": binary_metrics.precision,
            "recall": binary_metrics.recall,
            "specificity": binary_metrics.specificity,
            "f1_score": binary_metrics.f1_score,
            "roc_auc": binary_metrics.roc_auc,
            "pr_auc": binary_metrics.pr_auc,
            "brier_score": binary_metrics.brier_score,
            "expected_calibration_error": calib_report.expected_calibration_error,
            "is_well_calibrated": calib_report.is_well_calibrated,
            "confusion_matrix": {
                "true_positives": binary_metrics.true_positives,
                "false_positives": binary_metrics.false_positives,
                "true_negatives": binary_metrics.true_negatives,
                "false_negatives": binary_metrics.false_negatives,
            },
            "false_alarm_rate": binary_metrics.false_alarm_rate,
            "miss_rate": binary_metrics.miss_rate,
        },
        "spatial_error_analysis": {
            "false_positives": spatial_err.false_positive_count,
            "false_negatives": spatial_err.false_negative_count,
            "fp_mean_elevation_m": spatial_err.fp_mean_elevation_m,
            "fn_mean_elevation_m": spatial_err.fn_mean_elevation_m,
            "fp_mean_slope_deg": spatial_err.fp_mean_slope_deg,
            "fn_mean_slope_deg": spatial_err.fn_mean_slope_deg,
        },
    }


if __name__ == "__main__":
    report = run_m2_validation()
    print(json.dumps(report, indent=2))
