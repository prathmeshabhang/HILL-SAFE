"""
ml/landslide/m8_deformation/train.py
====================================
Training pipeline for Model M8 Multi-Horizon Displacement Regressors.
Calibrated against synthetic creeping slopes with empirical Himalayan deformation kinematics.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from ml.landslide.m8_deformation.model import DEFAULT_MODEL_PATH, HORIZON_DAYS


def generate_deformation_training_dataset(
    n_samples: int = 4000,
    seed: int = 42,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    Generates realistic slope deformation scenarios across Upper Beas terrain:
    - 60% stable/sub-millimeter slopes (v ~ 0.0 - 0.8 mm/day)
    - 25% linear seasonal creep slopes (v ~ 1.0 - 4.5 mm/day)
    - 12% accelerating slopes (v ~ 5.0 - 15.0 mm/day, a > 0.5 mm/day^2)
    - 3% paroxysmal failure slopes (v > 20.0 mm/day, a > 2.0 mm/day^2)
    """
    np.random.seed(seed)

    slope_deg = np.random.uniform(15.0, 55.0, size=n_samples)
    rain_72h = np.random.exponential(scale=25.0, size=n_samples)
    rain_72h = np.clip(rain_72h, 0.0, 220.0)

    # Base velocity distribution
    regime_probs = [0.60, 0.25, 0.12, 0.03]
    regimes = np.random.choice([0, 1, 2, 3], size=n_samples, p=regime_probs)

    v0 = np.zeros(n_samples)
    a0 = np.zeros(n_samples)

    # Stable
    v0[regimes == 0] = np.random.uniform(0.01, 0.8, size=np.sum(regimes == 0))
    a0[regimes == 0] = np.random.normal(0.0, 0.05, size=np.sum(regimes == 0))

    # Linear Creep
    v0[regimes == 1] = np.random.uniform(1.0, 4.5, size=np.sum(regimes == 1))
    a0[regimes == 1] = np.random.normal(0.05, 0.1, size=np.sum(regimes == 1))

    # Accelerating
    v0[regimes == 2] = np.random.uniform(5.0, 14.0, size=np.sum(regimes == 2))
    a0[regimes == 2] = np.random.uniform(0.5, 2.0, size=np.sum(regimes == 2))

    # Paroxysmal
    v0[regimes == 3] = np.random.uniform(15.0, 45.0, size=np.sum(regimes == 3))
    a0[regimes == 3] = np.random.uniform(2.5, 8.0, size=np.sum(regimes == 3))

    cum_disp = v0 * np.random.uniform(15.0, 90.0, size=n_samples) + np.random.normal(0.0, 2.0, size=n_samples)
    cum_disp = np.clip(cum_disp, 0.0, 1500.0)

    coherence = np.random.beta(a=8, b=2, size=n_samples)
    coherence = np.clip(coherence, 0.25, 0.98)

    slope_rad = np.radians(slope_deg)
    hydro_driving = rain_72h * np.sin(slope_rad)

    # Features: [velocity, acceleration, cumulative_disp, rain_72h, slope, hydro_driving, coherence]
    X = np.column_stack([
        v0,
        a0,
        cum_disp,
        rain_72h,
        slope_deg,
        hydro_driving,
        coherence,
    ])

    # Targets for horizons: 24h, 72h, 7d
    Y: Dict[str, np.ndarray] = {}
    for h, days in HORIZON_DAYS.items():
        # Physics displacement: v0 * t + 0.5 * a * t^1.8 * damping + hydro_bump + measurement noise
        damping = np.exp(-0.06 * days)
        base_inc = (v0 * days) + (0.5 * (a0 + hydro_driving * 0.004) * (days ** 1.7) * damping)
        noise = np.random.normal(0.0, 1.2 / coherence, size=n_samples)
        Y[h] = np.clip(base_inc + noise, 0.0, 2500.0)

    return X, Y


def train_m8_model(
    model_path: Path = DEFAULT_MODEL_PATH,
) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
    """
    Fits LightGBM multi-horizon regressors for Model M8.
    """
    X, Y = generate_deformation_training_dataset(n_samples=4000, seed=42)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]

    models: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}

    for h, days in HORIZON_DAYS.items():
        y_train, y_val = Y[h][:split_idx], Y[h][split_idx:]

        reg = LGBMRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            verbose=-1,
        )
        reg.fit(X_train, y_train)

        preds = reg.predict(X_val)
        mae = float(mean_absolute_error(y_val, preds))
        r2 = float(r2_score(y_val, preds))

        models[h] = reg
        metrics[h] = {
            "val_mae_mm": round(mae, 3),
            "val_r2": round(r2, 4),
        }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "models_by_horizon": models,
        "feature_names": [
            "velocity_mm_day",
            "acceleration_mm_day2",
            "cumulative_displacement_mm",
            "rainfall_72h_mm",
            "slope_deg",
            "hydro_driving_index",
            "insar_coherence",
        ],
        "training_metrics": metrics,
    }
    joblib.dump(bundle, model_path)

    hasher = hashlib.sha256()
    with open(model_path, "rb") as f:
        hasher.update(f.read())
    sha256 = hasher.hexdigest()

    return bundle, sha256, metrics


if __name__ == "__main__":
    b, sha, m = train_m8_model()
    print(f"M8 Trained successfully! SHA-256: {sha}")
    print(f"Metrics: {m}")
