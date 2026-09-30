"""
train_m2_flood.py — FLOODY SHIELD Model M2
============================================
Trains and evaluates the Flood Occurrence & Risk Model (M2) using XGBoost
with isotonic probability calibration and feature importance extraction.

INPUT FEATURES:
  - rainfall_1h, rainfall_3h, rainfall_6h, rainfall_24h, antecedent_rain_3d
  - soil_moisture, river_level, river_level_change_1h
  - elevation, slope, flow_accumulation, dist_to_stream, land_cover

EVALUATION METRICS:
  - ROC-AUC, PR-AUC, Precision, Recall, F1-Score
  - Brier Score (probability calibration)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    brier_score_loss,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

FEATURE_COLS = [
    "elevation",
    "slope",
    "flow_accumulation",
    "dist_to_stream",
    "land_cover",
    "rainfall_1h",
    "rainfall_3h",
    "rainfall_6h",
    "rainfall_24h",
    "antecedent_rain_3d",
    "soil_moisture",
    "river_level",
    "river_level_change_1h",
]
TARGET_COL = "flood_occurred"


def train_m2_flood_model(
    data_path: Path,
    model_dir: Path,
) -> Dict[str, float]:
    """Trains, calibrates, evaluates, and saves Model M2."""
    df = pd.read_csv(data_path)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    # Stratified Train/Holdout Test Split (80% / 20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Base XGBoost model
    base_xgb = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
    )

    # Calibrated Classifier to ensure probabilities reflect empirical risk
    calibrated_model = CalibratedClassifierCV(
        estimator=base_xgb,
        method="isotonic",
        cv=3,
    )
    calibrated_model.fit(X_train, y_train)

    # Predictions & Probabilities on Holdout Set
    y_prob = calibrated_model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    # Calculate rigorous validation metrics
    roc_auc = float(roc_auc_score(y_test, y_prob))
    brier = float(brier_score_loss(y_test, y_prob))
    precision = float(precision_score(y_test, y_pred))
    recall = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))

    metrics = {
        "model_name": "M2_Flood_Occurrence_XGBoost_Calibrated",
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_list": FEATURE_COLS,
    }

    # Extract feature importances from first fitted estimator
    base_fitted = calibrated_model.calibrated_classifiers_[0].estimator
    importances = dict(zip(FEATURE_COLS, [round(float(v), 4) for v in base_fitted.feature_importances_]))
    # Sort descending
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    metrics["feature_importances"] = sorted_importances

    # Save artifacts
    model_dir.mkdir(parents=True, exist_ok=True)
    model_file = model_dir / "m2_flood_model.joblib"
    metrics_file = model_dir / "m2_flood_metrics.json"

    joblib.dump(calibrated_model, model_file)
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    data_file = Path("data/samples/catchment_flood_training.csv")
    model_folder = Path("ml/flood")

    print("Training Model M2: Flood Occurrence & Risk Model (XGBoost)...")
    res = train_m2_flood_model(data_file, model_folder)

    print()
    print("=" * 60)
    print("MODEL M2 (FLOOD RISK) VALIDATION REPORT")
    print("=" * 60)
    print(f"ROC-AUC      : {res['roc_auc']} (Target >= 0.85)")
    print(f"Brier Score  : {res['brier_score']} (Target <= 0.15, closer to 0 is better)")
    print(f"Precision    : {res['precision']}")
    print(f"Recall       : {res['recall']}")
    print(f"F1-Score     : {res['f1_score']}")
    print("\nTop 5 Primary Risk Drivers:")
    for feat, score in list(res["feature_importances"].items())[:5]:
        print(f"  - {feat:<22} : {score}")
    print("=" * 60)
    print("Model M2 saved to: ml/flood/m2_flood_model.joblib")
