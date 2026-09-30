"""
ml/rainfall/m1_nowcast/train.py
===============================
Training pipeline for Model M1 Multi-Horizon Extreme Rainfall Nowcasting.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from ml.rainfall.m1_nowcast.model import DEFAULT_MODEL_PATH, HORIZON_HOURS, HORIZONS


def generate_monsoon_storm_series(n_timesteps: int = 4000, seed: int = 42) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    Generates synthetic-calibrated convective storm episodes based on
    Upper Beas historical IMD AWS distributions (July/August storms).
    """
    np.random.seed(seed)
    
    # Base intermittent rainfall process with autoregression
    rates = np.zeros(n_timesteps)
    in_storm = False
    storm_intensity = 0.0

    for t in range(n_timesteps):
        if not in_storm:
            if np.random.rand() < 0.04:  # Storm ignition probability
                in_storm = True
                # Convective cloudburst vs moderate pulse
                storm_intensity = np.random.choice([15.0, 35.0, 75.0], p=[0.70, 0.22, 0.08])
        else:
            # Storm decaying
            storm_intensity *= np.random.uniform(0.70, 0.96)
            if storm_intensity < 1.0:
                in_storm = False
                storm_intensity = 0.0
        rates[t] = max(0.0, storm_intensity + np.random.normal(0.0, 1.5))

    # Features: [r_15m, r_30m, r_1h, r_3h, rolling_intensity, accel, elev, orog]
    X_list = []
    y_dict: Dict[str, List[float]] = {h: [] for h in HORIZONS}

    for t in range(48, n_timesteps - 96):
        r_current = rates[t]
        r_15m = rates[t] * 0.25
        r_30m = (rates[t] + rates[t-1]) * 0.25
        r_1h = np.sum(rates[t-3:t+1]) * 0.25
        r_3h = np.sum(rates[t-11:t+1]) * 0.25
        accel = (rates[t] - rates[t-1]) / 0.25
        elev = 1800.0 + np.random.uniform(-400, 800)
        orog = 1.0 + (elev - 1000.0) / 4000.0

        feat = [r_15m, r_30m, r_1h, r_3h, r_current, accel, elev, orog]
        X_list.append(feat)

        # Targets: future accumulations for each horizon
        y_dict["15m"].append(rates[t+1] * 0.25)
        y_dict["30m"].append((rates[t+1] + rates[t+2]) * 0.25)
        y_dict["1h"].append(np.sum(rates[t+1:t+5]) * 0.25)
        y_dict["3h"].append(np.sum(rates[t+1:t+13]) * 0.25)
        y_dict["6h"].append(np.sum(rates[t+1:t+25]) * 0.25)
        y_dict["24h"].append(np.sum(rates[t+1:t+97]) * 0.25)

    X = np.array(X_list, dtype=np.float32)
    Y = {h: np.array(y_dict[h], dtype=np.float32) for h in HORIZONS}
    return X, Y


def train_m1_model(save_path: Path = DEFAULT_MODEL_PATH) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
    """Trains multi-horizon LightGBM regressors."""
    X, Y = generate_monsoon_storm_series(n_timesteps=4000, seed=42)
    models_by_horizon: Dict[str, LGBMRegressor] = {}
    metrics_by_horizon: Dict[str, Any] = {}

    # Chronological 80/20 train/validation split
    n_train = int(len(X) * 0.8)
    X_train, X_val = X[:n_train], X[n_train:]

    for h in HORIZONS:
        y_train = Y[h][:n_train]
        y_val = Y[h][n_train:]

        model = LGBMRegressor(
            n_estimators=120,
            learning_rate=0.04,
            max_depth=6,
            random_state=42,
            verbosity=-1,
        )
        model.fit(X_train, y_train)
        models_by_horizon[h] = model

        preds = model.predict(X_val)
        mae = float(np.mean(np.abs(preds - y_val)))
        rmse = float(np.sqrt(np.mean((preds - y_val) ** 2)))
        metrics_by_horizon[h] = {"mae_mm": round(mae, 3), "rmse_mm": round(rmse, 3)}

    bundle = {
        "models_by_horizon": models_by_horizon,
        "metrics_by_horizon": metrics_by_horizon,
        "feature_names": ["r_15m", "r_30m", "r_1h", "r_3h", "rolling_intensity", "accel", "elev", "orog"],
    }

    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, save_path)

    # Compute SHA-256
    h_sha = hashlib.sha256()
    with open(save_path, "rb") as f:
        while chunk := f.read(65536):
            h_sha.update(chunk)
    sha256 = h_sha.hexdigest()

    return bundle, sha256, metrics_by_horizon


if __name__ == "__main__":
    _, sha, met = train_m1_model()
    print(f"Model M1 trained! SHA-256: {sha}")
