"""
test_m1_nowcast.py — Unit Tests for Model M1 Extreme Rainfall Nowcasting Engine
=============================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.rainfall.m1_nowcast.infer import predict
from ml.rainfall.m1_nowcast.schema import CloudburstRiskLevel
from ml.rainfall.m1_nowcast.validation import run_m1_validation


class TestM1Nowcast(unittest.TestCase):

    def test_nominal_rainfall_nowcast(self):
        reading = {
            "station_id": "AWS_MANALI_01",
            "latitude": 32.24,
            "longitude": 77.18,
            "elevation_m": 2050.0,
            "slope_deg": 22.0,
            "rainfall_rate_mmh": 12.0,
            "r_15m": 3.0,
            "r_1h": 10.0,
            "r_3h": 22.0,
        }
        res = predict(reading)
        self.assertIn("prediction", res)
        self.assertIn("confidence", res)
        self.assertIn("uncertainty", res)
        self.assertIn("data_quality", res)
        self.assertIn("model_version", res)
        self.assertIn("applicability", res)

        pred = res["prediction"]
        self.assertEqual(pred["primary_horizon"], "1h")
        self.assertGreaterEqual(pred["predicted_rainfall_mm"], 0.0)
        self.assertIn("horizon_forecasts", pred)
        self.assertEqual(len(pred["horizon_forecasts"]), 6)

        # Check horizons
        horizons = [hf["horizon"] for hf in pred["horizon_forecasts"]]
        self.assertEqual(horizons, ["15m", "30m", "1h", "3h", "6h", "24h"])
        self.assertGreaterEqual(res["confidence"], 0.5)
        self.assertGreaterEqual(res["data_quality"], 0.7)

    def test_extreme_cloudburst_detection(self):
        reading = {
            "station_id": "AWS_SOLANG_01",
            "latitude": 32.31,
            "longitude": 77.15,
            "elevation_m": 2400.0,
            "slope_deg": 35.0,
            "rainfall_rate_mmh": 95.0,
            "r_15m": 24.0,
            "r_1h": 85.0,
            "r_3h": 140.0,
        }
        res = predict(reading)
        pred = res["prediction"]
        # Extreme rain probability should be very high
        self.assertGreaterEqual(pred["extreme_rain_probability"], 0.70)
        self.assertIn(pred["risk_level"], [CloudburstRiskLevel.HIGH.value, CloudburstRiskLevel.EXTREME.value])

    def test_multi_horizon_monotonicity_tendency(self):
        # Accumulated predicted rainfall over longer horizons should generally not decrease
        reading = {
            "station_id": "AWS_KULLU_01",
            "latitude": 31.95,
            "longitude": 77.10,
            "elevation_m": 1200.0,
            "rainfall_rate_mmh": 25.0,
        }
        res = predict(reading)
        forecasts = res["prediction"]["horizon_forecasts"]
        
        # 15m accumulated <= 24h accumulated
        h15 = [f["predicted_rainfall_mm"] for f in forecasts if f["horizon"] == "15m"][0]
        h24 = [f["predicted_rainfall_mm"] for f in forecasts if f["horizon"] == "24h"][0]
        self.assertLessEqual(h15, h24)

    def test_unphysical_sensor_input_degrades_quality(self):
        reading = {
            "station_id": "AWS_CORRUPT",
            "latitude": 45.0,  # Far outside Upper Beas AOI
            "longitude": 85.0,
            "elevation_m": 8500.0,  # Unphysical elevation
            "rainfall_rate_mmh": 650.0,  # Above ceiling
        }
        res = predict(reading)
        self.assertLess(res["data_quality"], 0.70)

    def test_run_m1_validation(self):
        val_res = run_m1_validation()
        self.assertIn("results_by_horizon", val_res)
        self.assertIn("1h", val_res["results_by_horizon"])
        self.assertIn("m1_mae_mm", val_res["results_by_horizon"]["1h"])
        self.assertIn("persistence_mae_mm", val_res["results_by_horizon"]["1h"])


if __name__ == "__main__":
    unittest.main()
