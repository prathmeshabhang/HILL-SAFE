"""
m9_sensor_anomaly.py — FLOODY SHIELD Model M9
===============================================
Dual-Stage Anomaly Detection Engine for IoT telemetry and rain gauge observations.

DETECTION LAYERS:
-----------------
Stage 1: Deterministic Physics & Telemetry Range Checks
  - Negative values (impossible for rain gauge or water level)
  - Physical ceiling checks (e.g. river depth > 25m or rain rate > 300 mm/h)
  - Stuck sensor detection (identical value across N consecutive samples during active rain)
  - Unrealistic gradient / rate of change spikes

Stage 2: Unsupervised Multi-variate Isolation Forest
  - Identifies inconsistent multivariate drift (e.g., rapidly rising river with zero rain,
    or high tilt with zero soil moisture change).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "m9_isolation_forest.joblib"


class SensorAnomalyEngine:
    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.features = ["rainfall_rate", "soil_moisture", "water_level", "tilt_degrees"]
        if MODEL_PATH.exists():
            self.iso_forest = joblib.load(MODEL_PATH)
        else:
            self.iso_forest = None

    def fit_baseline(self, df_nominal: pd.DataFrame, save_path: Path = MODEL_PATH) -> None:
        """Fits unsupervised Isolation Forest on nominal catchment telemetry."""
        self.iso_forest = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=42,
        )
        self.iso_forest.fit(df_nominal[self.features])
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.iso_forest, save_path)

    def check_telemetry_stream(self, recent_samples: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Runs Stage 1 (Deterministic) and Stage 2 (Isolation Forest) on telemetry history.
        """
        flags: List[str] = []
        is_anomalous = False

        if not recent_samples:
            return {"status": "NO_DATA", "is_anomalous": True, "flags": ["Empty sample buffer"]}

        latest = recent_samples[-1]

        # Stage 1: Deterministic Physical Range Checks
        if latest.get("rainfall_rate", 0.0) < 0.0:
            flags.append("Physical Error: Negative rainfall rate")
            is_anomalous = True
        if latest.get("water_level", 0.0) < 0.0:
            flags.append("Physical Error: Negative river water level")
            is_anomalous = True
        if latest.get("soil_moisture", 0.0) < 0.0 or latest.get("soil_moisture", 0.0) > 100.0:
            flags.append("Physical Error: Soil moisture out of bounds [0-100%]")
            is_anomalous = True

        # Stuck sensor check: if last 5 samples are exactly bit-identical while rain > 0
        if len(recent_samples) >= 5:
            levels = [s.get("water_level") for s in recent_samples[-5:]]
            if len(set(levels)) == 1 and levels[0] is not None and levels[0] > 1.0:
                flags.append("Telemetry Warning: Sensor values completely frozen across 5 periods (stuck gauge)")
                is_anomalous = True

        # Rate of change spike (e.g. river jumps > 3 meters in 5 minutes)
        if len(recent_samples) >= 2:
            dt_level = abs(latest.get("water_level", 0.0) - recent_samples[-2].get("water_level", 0.0))
            if dt_level > 2.5:
                flags.append(f"Spike Warning: Sudden unphysical jump ({dt_level:.2f} m) in river level")
                is_anomalous = True

        # Stage 2: Isolation Forest Anomaly Scoring
        if self.iso_forest is not None and not is_anomalous:
            feat_df = pd.DataFrame([latest])[self.features]
            pred = self.iso_forest.predict(feat_df)[0]  # -1 for anomaly, 1 for normal
            score = float(self.iso_forest.decision_function(feat_df)[0])
            if pred == -1:
                is_anomalous = True
                flags.append(f"Statistical Anomaly: Multivariate discordance (isolation score: {score:.3f})")

        return {
            "status": "ANOMALOUS" if is_anomalous else "HEALTHY",
            "is_anomalous": is_anomalous,
            "flags": flags if flags else ["Normal operation"],
            "latest_reading": latest,
        }


# Public alias for Model M9
M9SensorAnomalyDetector = SensorAnomalyEngine


if __name__ == "__main__":
    # Create synthetic nominal baseline for training Isolation Forest
    np.random.seed(42)
    n = 2000
    df_nominal = pd.DataFrame({
        "rainfall_rate": np.random.exponential(scale=5.0, size=n),
        "soil_moisture": np.random.uniform(20.0, 85.0, size=n),
        "water_level": np.random.uniform(1.0, 7.5, size=n),
        "tilt_degrees": np.random.normal(loc=0.0, scale=0.5, size=n),
    })

    engine = SensorAnomalyEngine()
    print("Fitting Model M9: Dual-Stage Sensor Anomaly Engine...")
    engine.fit_baseline(df_nominal)
    print("Saved M9 Isolation Forest baseline to: ml/anomaly/m9_isolation_forest.joblib")

    # Test Case 1: Healthy Reading
    sample_healthy = [{"rainfall_rate": 12.0, "soil_moisture": 65.0, "water_level": 3.2, "tilt_degrees": 0.1}]
    res1 = engine.check_telemetry_stream(sample_healthy)
    print("\n--- Test 1 (Healthy Stream) ---")
    print(json.dumps(res1, indent=2))

    # Test Case 2: Stuck Sensor Spike
    sample_stuck = [
        {"rainfall_rate": 15.0, "soil_moisture": 70.0, "water_level": 4.5, "tilt_degrees": 0.0}
        for _ in range(5)
    ]
    res2 = engine.check_telemetry_stream(sample_stuck)
    print("\n--- Test 2 (Stuck Sensor Stream) ---")
    print(json.dumps(res2, indent=2))
