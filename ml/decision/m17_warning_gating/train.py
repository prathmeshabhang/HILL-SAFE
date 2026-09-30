"""
ml/decision/m17_warning_gating/train.py
======================================
Training pipeline for Model M17: Early Warning Gating Classifier.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

from ml.decision.m17_warning_gating.features import FEATURE_NAMES, extract_warning_features
from ml.decision.m17_warning_gating.schema import M17WarningInput


def generate_warning_scenarios(seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates diverse multi-hazard warning scenarios across the 4 NDMA alert levels.
    """
    rng = np.random.RandomState(seed)
    X_list = []
    y_list = []

    # 1. GREEN scenarios (Normal baseline) - 400 samples
    for _ in range(400):
        stage = float(rng.uniform(1.0, 4.0))
        warn = 5.0
        danger = 7.0
        rain = float(rng.exponential(3.0))
        p_fld = float(rng.beta(1.0, 6.0))
        p_sld = float(rng.beta(1.0, 6.0))
        pwp = float(rng.uniform(0.15, 0.40))
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_MANALI",
            rainfall_intensity_mmh=rain,
            rainfall_3h_mm=rain * 2.5,
            flood_probability=p_fld,
            river_water_level_m=stage,
            warning_level_m=warn,
            danger_level_m=danger,
            flood_depth_m=0.0,
            landslide_probability=p_sld,
            pore_water_pressure_ratio=pwp,
        )
        vec, _ = extract_warning_features(inp)
        X_list.append(vec)
        y_list.append(0)

    # 2. YELLOW scenarios (Advisory watch) - 400 samples
    for _ in range(400):
        stage = float(rng.uniform(4.0, 5.2))
        warn = 5.0
        danger = 7.0
        rain = float(rng.uniform(15.0, 35.0))
        p_fld = float(rng.uniform(0.35, 0.60))
        p_sld = float(rng.uniform(0.25, 0.50))
        pwp = float(rng.uniform(0.40, 0.65))
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_KULLU",
            rainfall_intensity_mmh=rain,
            rainfall_3h_mm=rain * 2.8,
            flood_probability=p_fld,
            river_water_level_m=stage,
            warning_level_m=warn,
            danger_level_m=danger,
            flood_depth_m=float(rng.uniform(0.05, 0.35)),
            landslide_probability=p_sld,
            pore_water_pressure_ratio=pwp,
        )
        vec, _ = extract_warning_features(inp)
        X_list.append(vec)
        y_list.append(1)

    # 3. ORANGE scenarios (Alert / Severe risk) - 400 samples
    for _ in range(400):
        stage = float(rng.uniform(5.2, 6.8))
        warn = 5.0
        danger = 7.0
        rain = float(rng.uniform(35.0, 70.0))
        p_fld = float(rng.uniform(0.60, 0.80))
        p_sld = float(rng.uniform(0.50, 0.75))
        pwp = float(rng.uniform(0.65, 0.80))
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_AUT",
            rainfall_intensity_mmh=rain,
            rainfall_3h_mm=rain * 3.0,
            flood_probability=p_fld,
            river_water_level_m=stage,
            warning_level_m=warn,
            danger_level_m=danger,
            flood_depth_m=float(rng.uniform(0.40, 1.20)),
            landslide_probability=p_sld,
            pore_water_pressure_ratio=pwp,
            arterial_road_blocked=bool(rng.rand() < 0.4),
        )
        vec, _ = extract_warning_features(inp)
        X_list.append(vec)
        y_list.append(2)

    # 4. RED scenarios (Mandatory Evacuation) - 400 samples
    for _ in range(400):
        stage = float(rng.uniform(7.0, 10.5))
        warn = 5.0
        danger = 7.0
        rain = float(rng.uniform(65.0, 130.0))
        p_fld = float(rng.uniform(0.80, 0.98))
        p_sld = float(rng.uniform(0.70, 0.95))
        pwp = float(rng.uniform(0.80, 0.99))
        outburst = float(rng.uniform(800.0, 3500.0)) if rng.rand() < 0.5 else 0.0
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_BHUNTAR",
            rainfall_intensity_mmh=rain,
            rainfall_3h_mm=rain * 3.0,
            flood_probability=p_fld,
            river_water_level_m=stage,
            warning_level_m=warn,
            danger_level_m=danger,
            flood_depth_m=float(rng.uniform(1.20, 3.50)),
            flood_arrival_time_min=float(rng.uniform(15.0, 60.0)),
            landslide_probability=p_sld,
            pore_water_pressure_ratio=pwp,
            natural_dam_outburst_discharge_m3s=outburst,
            arterial_road_blocked=True,
            critical_bridge_submerged=bool(rng.rand() < 0.7),
        )
        vec, _ = extract_warning_features(inp)
        X_list.append(vec)
        y_list.append(3)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y


def train_m17_model(
    output_path: str | None = None,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Trains and saves the GradientBoostingClassifier for Model M17.
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "m17_warning_classifier.joblib")

    X, y = generate_warning_scenarios(seed=seed)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.20, random_state=seed, stratify=y
    )

    clf = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.08,
        max_depth=4,
        random_state=seed,
    )
    clf.fit(X_train, y_train)

    val_preds = clf.predict(X_val)
    macro_f1 = float(f1_score(y_val, val_preds, average="macro"))
    acc = float(np.mean(val_preds == y_val))

    artifact = {
        "model": clf,
        "feature_names": FEATURE_NAMES,
        "version": "1.0.0",
        "val_macro_f1": macro_f1,
        "val_accuracy": acc,
    }

    joblib.dump(artifact, output_path)
    return {"val_macro_f1": macro_f1, "val_accuracy": acc, "samples": len(X)}


if __name__ == "__main__":
    metrics = train_m17_model()
    print(f"Model M17 Classifier Trained successfully: Accuracy={metrics['val_accuracy']:.4f}, Macro-F1={metrics['val_macro_f1']:.4f}")
