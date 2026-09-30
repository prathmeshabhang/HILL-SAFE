"""
ml/anomaly/m9_sensor/train.py
=============================
Training pipeline for Model M9 Isolation Forest on nominal catchment telemetry.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml.anomaly.m9_sensor.model import DEFAULT_MODEL_PATH, M9SensorAnomalyModel


def generate_nominal_catchment_telemetry(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generates nominal environmental telemetry grounded in Upper Beas seasonal ranges."""
    np.random.seed(seed)
    
    # 1. Rainfall: mostly dry/low, occasional showers
    rain = np.random.exponential(scale=3.5, size=n_samples)
    rain[rain < 0.2] = 0.0
    rain = np.clip(rain, 0.0, 50.0)

    # 2. Water level: correlated with rain
    water = 2.0 + (rain * 0.08) + np.random.normal(0.0, 0.25, size=n_samples)
    water = np.clip(water, 1.2, 8.5)

    # 3. Soil moisture: correlated with rain
    soil = 35.0 + (rain * 0.6) + np.random.normal(0.0, 4.0, size=n_samples)
    soil = np.clip(soil, 15.0, 85.0)

    # 4. Tilt: near zero on stable slopes
    tilt = np.random.normal(0.0, 0.4, size=n_samples)
    tilt = np.clip(tilt, -2.5, 2.5)

    # 5. Pore pressure: correlated with moisture
    pore = (soil - 20.0) * 0.15 + np.random.normal(0.0, 0.5, size=n_samples)
    pore = np.clip(pore, 0.0, 25.0)

    return pd.DataFrame({
        "rainfall_rate_mmh": rain,
        "water_level_m": water,
        "soil_moisture_pct": soil,
        "tilt_deg": tilt,
        "pore_pressure_kpa": pore,
    })


def train_m9_model(save_path: Path = DEFAULT_MODEL_PATH) -> Tuple[M9SensorAnomalyModel, str, Dict[str, Any]]:
    """Trains the Model M9 Isolation Forest and returns model, sha256, and metadata."""
    df_nominal = generate_nominal_catchment_telemetry(n_samples=5000, seed=42)
    feature_cols = ["rainfall_rate_mmh", "water_level_m", "soil_moisture_pct", "tilt_deg", "pore_pressure_kpa"]
    X = df_nominal[feature_cols].values

    model = M9SensorAnomalyModel(model_path=save_path)
    model.fit(X, save=True)

    # Compute SHA-256
    h = hashlib.sha256()
    with open(save_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    sha256 = h.hexdigest()

    metrics = {
        "n_training_samples": len(df_nominal),
        "contamination": 0.05,
        "features": feature_cols,
        "nominal_inlier_ratio": 0.95,
    }

    return model, sha256, metrics


if __name__ == "__main__":
    m, sha, met = train_m9_model()
    print(f"Model M9 trained successfully! SHA-256: {sha}")
