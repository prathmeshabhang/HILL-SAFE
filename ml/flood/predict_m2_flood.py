"""
predict_m2_flood.py — FLOODY SHIELD Model M2 Predictor
========================================================
Inference service for Model M2 (Flood Occurrence & Risk).
Exposes a Level 1 Prototype / Research Decision Support scoring function with risk stratification and driver extraction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "m2_flood_model.joblib"
METRICS_PATH = MODEL_DIR / "m2_flood_metrics.json"


class FloodRiskPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {model_path}")
        self.model = joblib.load(model_path)
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        self.feature_cols = self.metadata["feature_list"]
        self.feature_weights = self.metadata.get("feature_importances", {})

    def predict_point(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates flood probability, risk tier, and key risk drivers for a single site.
        """
        df_in = pd.DataFrame([features])[self.feature_cols]
        prob = float(self.model.predict_proba(df_in)[0, 1])

        # Stratify risk level
        if prob >= 0.75:
            risk_tier = "CRITICAL"
        elif prob >= 0.50:
            risk_tier = "HIGH"
        elif prob >= 0.25:
            risk_tier = "MODERATE"
        else:
            risk_tier = "LOW"

        # Identify key active drivers
        drivers: List[str] = []
        if features.get("river_level", 0.0) >= 6.0 or features.get("river_level_change_1h", 0.0) >= 0.3:
            drivers.append("Rapidly rising or high river stage")
        if features.get("soil_moisture", 0.0) >= 70.0:
            drivers.append("High soil saturation")
        if features.get("rainfall_1h", 0.0) >= 20.0 or features.get("rainfall_3h", 0.0) >= 40.0:
            drivers.append("Intense localized rainfall")
        if features.get("slope", 90.0) <= 8.0 and features.get("dist_to_stream", 1000.0) <= 150.0:
            drivers.append("Low-lying floodplain channel proximity")

        if not drivers:
            drivers.append("Normal catchment baseline")

        return {
            "model": "M2_Flood_XGBoost",
            "flood_probability": round(prob, 3),
            "risk_tier": risk_tier,
            "confidence": "MODERATE_VALIDATED",
            "key_drivers": drivers,
        }


if __name__ == "__main__":
    predictor = FloodRiskPredictor()

    # Test Site 1: Dangerous Valley Bottom during Heavy Monsoon
    sample_severe = {
        "elevation": 720.0,
        "slope": 4.5,
        "flow_accumulation": 4500.0,
        "dist_to_stream": 35.0,
        "land_cover": 4,  # Settlement
        "rainfall_1h": 32.0,
        "rainfall_3h": 68.0,
        "rainfall_6h": 95.0,
        "rainfall_24h": 140.0,
        "antecedent_rain_3d": 110.0,
        "soil_moisture": 86.0,
        "river_level": 7.8,
        "river_level_change_1h": 0.45,
    }

    res = predictor.predict_point(sample_severe)
    print("=" * 60)
    print("M2 INFERENCE TEST: SEVERE CATCHMENT SCENARIO")
    print("=" * 60)
    print(json.dumps(res, indent=2))
