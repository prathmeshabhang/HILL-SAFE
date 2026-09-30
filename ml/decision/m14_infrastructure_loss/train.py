"""
ml/decision/m14_infrastructure_loss/train.py
============================================
Training pipeline for Model M14: Infrastructure Damage & Loss GBDT.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from ml.decision.m14_infrastructure_loss.assets import BEAS_INFRASTRUCTURE_ASSETS
from ml.decision.m14_infrastructure_loss.features import FEATURE_NAMES, extract_damage_features
from ml.decision.m14_infrastructure_loss.schema import M14DamageInput
from ml.decision.m14_infrastructure_loss.vulnerability_curves import evaluate_asset_damage


def generate_damage_scenarios(seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates realistic infrastructure damage training scenarios
    covering low inundation to catastrophic flash-flood overtopping.
    """
    rng = np.random.RandomState(seed)
    X_list = []
    y_list = []

    assets = list(BEAS_INFRASTRUCTURE_ASSETS.values())

    for asset in assets:
        for _ in range(120):
            depth = float(rng.exponential(1.2))
            v = float(rng.uniform(0.2, 5.5)) if depth > 0.1 else float(rng.uniform(0.0, 0.5))
            debris = bool(rng.rand() < 0.35) if depth > 0.8 else False
            duration = float(rng.uniform(1.0, 48.0))

            inp = M14DamageInput(
                asset_id=asset.asset_id,
                flood_depth_m=depth,
                flow_velocity_ms=v,
                debris_impact_flag=debris,
                inundation_duration_hours=duration,
            )

            feat_vec, _ = extract_damage_features(inp, asset=asset)

            # Ground truth: deterministic vulnerability curve + realistic geotechnical scatter
            curve_d, _, _, _, _ = evaluate_asset_damage(
                asset=asset,
                flood_depth_m=depth,
                flow_velocity_ms=v,
                debris_flag=debris,
                duration_hours=duration,
            )

            noise = float(rng.normal(0, 0.015))
            target_d = float(np.clip(curve_d + noise, 0.0, 1.0))

            X_list.append(feat_vec)
            y_list.append(target_d)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    return X, y


def train_m14_model(
    output_path: str | None = None,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Trains and saves the GBDT regressor for Model M14.
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "m14_infrastructure_gbdt.joblib")

    X, y = generate_damage_scenarios(seed=seed)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.20, random_state=seed, shuffle=True
    )

    model = GradientBoostingRegressor(
        n_estimators=120,
        learning_rate=0.07,
        max_depth=4,
        random_state=seed,
    )
    model.fit(X_train, y_train)

    val_preds = model.predict(X_val)
    mae = float(mean_absolute_error(y_val, val_preds))
    r2 = float(r2_score(y_val, val_preds))

    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "version": "1.0.0",
        "val_mae": mae,
        "val_r2": r2,
    }

    joblib.dump(artifact, output_path)
    return {"val_mae": mae, "val_r2": r2, "samples": len(X)}


if __name__ == "__main__":
    metrics = train_m14_model()
    print(f"Model M14 GBDT Trained successfully: R2={metrics['val_r2']:.4f}, MAE={metrics['val_mae']:.4f}")
