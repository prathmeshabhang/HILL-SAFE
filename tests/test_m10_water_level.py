"""
test_m10_water_level.py — Unit Tests for Model M10 River Water-Level Forecast Engine
===================================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.flood.m10_water_level.features import compute_stage_rate_of_rise
from ml.flood.m10_water_level.infer import predict
from ml.flood.m10_water_level.schema import StageAlertLevel
from ml.flood.m10_water_level.validation import run_m10_validation


class TestM10WaterLevel(unittest.TestCase):

    def test_nominal_stage_prediction(self):
        reading = {
            "station_id": "CWC_MANALI_01",
            "latitude": 32.24,
            "longitude": 77.18,
            "elevation_m": 2050.0,
            "current_stage_m": 2.2,
            "rate_of_rise_m_hr": 0.05,
            "rainfall_1h_mm": 5.0,
            "rainfall_3h_mm": 12.0,
            "soil_moisture_pct": 35.0,
            "warning_level_m": 5.0,
            "danger_level_m": 7.0,
            "hfl_m": 9.5,
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
        self.assertGreater(pred["forecasted_stage_m"], 0.0)
        self.assertEqual(pred["alert_level"], StageAlertLevel.NORMAL_FLOW.value)
        self.assertEqual(len(pred["horizon_forecasts"]), 4)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertGreaterEqual(res["data_quality"], 0.80)

    def test_danger_level_exceedance_flood_surge(self):
        reading = {
            "station_id": "CWC_BHUNTAR_CONFLUENCE",
            "latitude": 31.88,
            "longitude": 77.15,
            "elevation_m": 1090.0,
            "current_stage_m": 6.9,
            "rate_of_rise_m_hr": 1.2,
            "rainfall_1h_mm": 55.0,
            "rainfall_3h_mm": 110.0,
            "rainfall_6h_mm": 160.0,
            "soil_moisture_pct": 92.0,
            "warning_level_m": 5.0,
            "danger_level_m": 7.0,
            "hfl_m": 9.5,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertGreater(pred["forecasted_stage_m"], 7.0)
        self.assertIn(pred["alert_level"], [StageAlertLevel.DANGER_LEVEL.value, StageAlertLevel.HIGH_FLOOD_LEVEL.value])
        self.assertGreaterEqual(pred["exceedance_prob_danger"], 0.75)

    def test_multi_horizon_forecasting_horizons(self):
        reading = {
            "station_id": "CWC_PANDOH",
            "latitude": 31.67,
            "longitude": 77.01,
            "elevation_m": 900.0,
            "current_stage_m": 3.8,
            "rate_of_rise_m_hr": 0.2,
        }
        res = predict(reading)
        horizons = [f["horizon"] for f in res["prediction"]["horizon_forecasts"]]
        self.assertEqual(horizons, ["30m", "1h", "3h", "6h"])

    def test_rate_of_rise_computation(self):
        history = [2.0, 2.25]  # rise of 0.25m in 15 mins (0.25h) -> 1.0 m/hr
        rate = compute_stage_rate_of_rise(history, timestep_hours=0.25)
        self.assertAlmostEqual(rate, 1.0, places=2)

    def test_unphysical_sensor_input_degrades_quality(self):
        reading = {
            "station_id": "CWC_CORRUPT",
            "latitude": 55.0,  # Far outside AOI
            "longitude": 12.0,
            "elevation_m": 9000.0,
            "water_level_m": 45.0,  # Far above 25m ceiling
        }
        res = predict(reading)
        self.assertLess(res["data_quality"], 0.70)

    def test_run_m10_validation(self):
        val_res = run_m10_validation()
        self.assertEqual(val_res["status"], "PASS")
        self.assertIn("horizon_metrics", val_res)
        self.assertIn("1h", val_res["horizon_metrics"])
        self.assertIn("extreme_surge_test", val_res)
        self.assertTrue(val_res["extreme_surge_test"]["danger_exceeded"])


if __name__ == "__main__":
    unittest.main()
