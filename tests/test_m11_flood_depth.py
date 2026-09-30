"""
test_m11_flood_depth.py — Unit Tests for Model M11 Flood Propagation & Depth Forecast Engine
=============================================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.flood.m11_flood_depth.features import compute_wave_celerity_and_attenuation
from ml.flood.m11_flood_depth.infer import predict
from ml.flood.m11_flood_depth.schema import InundationSeverity
from ml.flood.m11_flood_depth.validation import run_m11_validation


class TestM11FloodDepth(unittest.TestCase):

    def test_nominal_dry_bench_prediction(self):
        reading = {
            "source_stage_m": 2.5,
            "source_discharge_m3s": 250.0,
            "target_reach_id": "REACH_02_MANALI_PATLIKUHAL",
            "hand_m": 8.5,  # High safe terrace
            "distance_to_river_m": 250.0,
            "slope_deg": 12.0,
        }
        res = predict(reading)
        self.assertIn("prediction", res)
        self.assertIn("confidence", res)
        self.assertIn("uncertainty", res)
        self.assertIn("data_quality", res)
        self.assertIn("model_version", res)
        self.assertIn("applicability", res)

        pred = res["prediction"]
        self.assertEqual(pred["forecasted_depth_m"], 0.0)
        self.assertEqual(pred["inundation_severity"], InundationSeverity.NO_INUNDATION.value)
        self.assertEqual(len(pred["reach_forecasts"]), 6)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertGreaterEqual(res["data_quality"], 0.80)

    def test_catastrophic_floodplain_submergence(self):
        reading = {
            "source_stage_m": 8.8,
            "source_discharge_m3s": 2800.0,
            "target_reach_id": "REACH_03_PATLIKUHAL_KULLU",
            "hand_m": 0.8,  # Low active floodplain
            "distance_to_river_m": 35.0,
            "slope_deg": 3.0,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertGreaterEqual(pred["forecasted_depth_m"], 2.0)
        self.assertIn(pred["inundation_severity"], [
            InundationSeverity.SEVERE_DANGER.value,
            InundationSeverity.CATASTROPHIC_SUBMERGENCE.value,
        ])

    def test_downstream_wave_travel_time_monotonicity(self):
        reading = {
            "source_stage_m": 6.0,
            "source_discharge_m3s": 1200.0,
        }
        res = predict(reading)
        forecasts = res["prediction"]["reach_forecasts"]
        arrival_times = [r["wave_arrival_time_min"] for r in forecasts]
        # Cumulative arrival times must strictly increase as we move downstream
        for i in range(len(arrival_times) - 1):
            self.assertLess(arrival_times[i], arrival_times[i + 1])

    def test_hydraulic_wave_celerity_calculation(self):
        hyd = compute_wave_celerity_and_attenuation(
            discharge_m3s=1500.0,
            reach_slope=0.015,
            manning_n=0.040,
            channel_width_m=60.0,
        )
        self.assertIn("celerity_mps", hyd)
        self.assertIn("velocity_mps", hyd)
        self.assertGreater(hyd["celerity_mps"], 2.0)
        self.assertLessEqual(hyd["celerity_mps"], 10.0)

    def test_unphysical_sensor_input_degrades_quality(self):
        reading = {
            "latitude": 55.0,  # Far outside AOI
            "longitude": 12.0,
            "elevation_m": 9000.0,
            "source_stage_m": 45.0,  # Impossible stage
        }
        res = predict(reading)
        self.assertLess(res["data_quality"], 0.70)

    def test_run_m11_validation(self):
        val_res = run_m11_validation()
        self.assertEqual(val_res["status"], "PASS")
        self.assertIn("validation_metrics", val_res)
        self.assertIn("disaster_scenario_test", val_res)
        self.assertTrue(val_res["disaster_scenario_test"]["submergence_confirmed"])


if __name__ == "__main__":
    unittest.main()
