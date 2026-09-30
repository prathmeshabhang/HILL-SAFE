"""
train_m6_m7_landslide.py — FLOODY SHIELD Models M6 & M7
=========================================================
Trains and evaluates:
  1. Model M6: Landslide Susceptibility Baseline (Random Forest on static terrain & lithology)
  2. Model M7: Dynamic Landslide Trigger Model (LightGBM on rainfall intensity & soil saturation)

SCIENTIFIC DECOUPLING PRINCIPLE:
--------------------------------
Susceptibility (M6) represents static geotechnical vulnerability.
Trigger Risk (M7) represents dynamic hydro-meteorological loading.
Current Risk = Susceptibility × Dynamic Trigger.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

M6_STATIC_FEATURES = [
    "elevation",
    "slope",
    "aspect",
    "curvature",
    "lithology",
    "dist_to_stream",
    "land_cover",
]
M6_TARGET = "susceptibility_class"  # 0: Low, 1: Medium, 2: High

M7_DYNAMIC_FEATURES = [
    "susceptibility_class",
    "slope",
    "rainfall_1h",
    "antecedent_rain_3d",
    "soil_moisture",
]
M7_TARGET = "landslide_triggered"  # 0: No trigger, 1: Triggered


def train_m6_m7_models(data_path: Path, model_dir: Path) -> Dict[str, Any]:
    df = pd.read_csv(data_path)
    model_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Train Model M6 (Static Susceptibility Random Forest)
    # ---------------------------------------------------------
    X_m6 = df[M6_STATIC_FEATURES]
    y_m6 = df[M6_TARGET]
    X6_train, X6_test, y6_train, y6_test = train_test_split(
        X_m6, y_m6, test_size=0.20, random_state=42, stratify=y_m6
    )

    rf_m6 = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        random_state=42,
        class_weight="balanced",
    )
    rf_m6.fit(X6_train, y6_train)
    y6_pred = rf_m6.predict(X6_test)
    m6_f1_macro = float(f1_score(y6_test, y6_pred, average="macro"))

    m6_importances = dict(zip(M6_STATIC_FEATURES, [round(float(v), 4) for v in rf_m6.feature_importances_]))
    sorted_m6_imp = dict(sorted(m6_importances.items(), key=lambda item: item[1], reverse=True))

    # ---------------------------------------------------------
    # 2. Train Model M7 (Dynamic Trigger LightGBM)
    # ---------------------------------------------------------
    X_m7 = df[M7_DYNAMIC_FEATURES]
    y_m7 = df[M7_TARGET]
    X7_train, X7_test, y7_train, y7_test = train_test_split(
        X_m7, y_m7, test_size=0.20, random_state=42, stratify=y_m7
    )

    lgb_m7 = LGBMClassifier(
        n_estimators=120,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
        verbose=-1,
    )
    lgb_m7.fit(X7_train, y7_train)
    y7_prob = lgb_m7.predict_proba(X7_test)[:, 1]
    y7_pred = (y7_prob >= 0.5).astype(int)

    m7_auc = float(roc_auc_score(y7_test, y7_prob))
    m7_f1 = float(f1_score(y7_test, y7_pred))

    # Save artifacts
    joblib.dump(rf_m6, model_dir / "m6_landslide_susceptibility.joblib")
    joblib.dump(lgb_m7, model_dir / "m7_landslide_trigger.joblib")

    report = {
        "m6_susceptibility": {
            "algorithm": "RandomForestClassifier",
            "f1_macro": round(m6_f1_macro, 4),
            "feature_importances": sorted_m6_imp,
            "classes": ["LOW", "MEDIUM", "HIGH"],
        },
        "m7_dynamic_trigger": {
            "algorithm": "LGBMClassifier",
            "roc_auc": round(m7_auc, 4),
            "f1_score": round(m7_f1, 4),
            "features": M7_DYNAMIC_FEATURES,
        },
    }

    with open(model_dir / "landslide_models_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    data_file = Path("data/samples/catchment_landslide_training.csv")
    model_folder = Path("ml/landslide")

    print("Training Models M6 & M7: Landslide Susceptibility & Dynamic Trigger...")
    metrics = train_m6_m7_models(data_file, model_folder)

    print()
    print("=" * 60)
    print("LANDSLIDE MODELS (M6 & M7) VALIDATION REPORT")
    print("=" * 60)
    print(f"Model M6 (Susceptibility) F1-Macro : {metrics['m6_susceptibility']['f1_macro']}")
    print("Top Susceptibility Controls:")
    for k, v in list(metrics["m6_susceptibility"]["feature_importances"].items())[:3]:
        print(f"  - {k:<18}: {v}")
    print()
    print(f"Model M7 (Trigger Risk) ROC-AUC    : {metrics['m7_dynamic_trigger']['roc_auc']}")
    print(f"Model M7 (Trigger Risk) F1-Score   : {metrics['m7_dynamic_trigger']['f1_score']}")
    print("=" * 60)
    print("Models saved in: ml/landslide/")
