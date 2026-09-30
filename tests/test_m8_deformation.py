"""
test_m8_deformation.py — Unit Tests for Model M8 Ground Movement & Slope Deformation Forecast
==============================================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.landslide.m8_deformation.features import compute_kinematic_derivatives
from ml.landslide.m8_deformation.infer import predict
from ml.landslide.m8_deformation.schema import MovementRegime
from ml.landslide.m8_deformation.validation import run_m8_validation


class TestM8Deformation(unittest.TestCase):

    def test_stable_slope_prediction(self):
        reading = {
            "sensor_or_pixel_id": "PX_KULLU_STABLE_01",
            "latitude": 31.95,
            "longitude": 77.10,
            "elevation_m": 1250.0,
            "slope_deg": 18.0,
            "velocity_mm_day": 0.2,
            "acceleration_mm_day2": 0.01,
            "cumulative_displacement_mm": 5.4,
            "rainfall_72h_mm": 10.0,
            "insar_coherence": 0.92,
        }
        res = predict(reading)
        self.assertIn("prediction", res)
        self.assertIn("confidence", res)
        self.assertIn("uncertainty", res)
        self.assertIn("data_quality", res)
        self.assertIn("model_version", res)
        self.assertIn("applicability", res)

        pred = res["prediction"]
        self.assertEqual(pred["movement_regime"], MovementRegime.STABLE.value)
        self.assertIsNone(pred["time_to_failure_est_hours"])
        self.assertEqual(len(pred["horizon_forecasts"]), 3)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertGreaterEqual(res["data_quality"], 0.80)

    def test_linear_creep_slope(self):
        reading = {
            "sensor_or_pixel_id": "PX_MANALI_CREEP_02",
            "latitude": 32.24,
            "longitude": 77.18,
            "elevation_m": 2050.0,
            "slope_deg": 32.0,
            "velocity_mm_day": 2.5,
            "acceleration_mm_day2": 0.05,
            "cumulative_displacement_mm": 45.0,
            "rainfall_72h_mm": 35.0,
            "insar_coherence": 0.85,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertEqual(pred["movement_regime"], MovementRegime.LINEAR_CREEP.value)

    def test_saito_critical_failure_acceleration(self):
        reading = {
            "sensor_or_pixel_id": "PX_SOLANG_PAROXYSMAL",
            "latitude": 32.31,
            "longitude": 77.15,
            "elevation_m": 2450.0,
            "slope_deg": 42.0,
            "velocity_mm_day": 28.0,
            "acceleration_mm_day2": 4.0,
            "cumulative_displacement_mm": 210.0,
            "rainfall_72h_mm": 120.0,
            "insar_coherence": 0.75,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertEqual(pred["movement_regime"], MovementRegime.CRITICAL_FAILURE_IMMINENT.value)
        self.assertIsNotNone(pred["time_to_failure_est_hours"])
        # With v=28 and a=4.0: t_f = 28 / 4 = 7 days = 168h
        self.assertGreater(pred["time_to_failure_est_hours"], 0.0)

    def test_multi_horizon_displacement_progression(self):
        reading = {
            "sensor_or_pixel_id": "PX_TEST",
            "latitude": 32.22,
            "longitude": 77.17,
            "elevation_m": 1900.0,
            "slope_deg": 28.0,
            "velocity_mm_day": 4.0,
            "acceleration_mm_day2": 0.2,
            "cumulative_displacement_mm": 20.0,
            "rainfall_72h_mm": 50.0,
        }
        res = predict(reading)
        hf = {f["horizon"]: f["cumulative_projected_displacement_mm"] for f in res["prediction"]["horizon_forecasts"]}
        self.assertIn("24h", hf)
        self.assertIn("72h", hf)
        self.assertIn("7d", hf)
        self.assertLessEqual(hf["24h"], hf["72h"])
        self.assertLessEqual(hf["72h"], hf["7d"])

    def test_kinematic_derivatives_from_series(self):
        disp_series = [10.0, 12.5, 15.5, 19.5]  # velocities: 2.5, 3.0, 4.0 (accelerating)
        kin = compute_kinematic_derivatives(disp_series, timestep_days=1.0)
        self.assertAlmostEqual(kin["velocity_mm_day"], 4.0, places=2)
        self.assertAlmostEqual(kin["acceleration_mm_day2"], 1.0, places=2)
        self.assertAlmostEqual(kin["inverse_velocity_day_mm"], 0.25, places=2)

    def test_unphysical_sensor_input_degrades_quality(self):
        reading = {
            "sensor_or_pixel_id": "PX_BAD",
            "latitude": 55.0,  # Far outside Upper Beas
            "longitude": 12.0,
            "elevation_m": 9000.0,
            "displacement_mm": 12000.0,  # Far above physical maximum
        }
        res = predict(reading)
        self.assertLess(res["data_quality"], 0.70)

    def test_run_m8_validation(self):
        val_res = run_m8_validation()
        self.assertEqual(val_res["status"], "PASS")
        self.assertIn("horizon_metrics", val_res)
        self.assertIn("24h", val_res["horizon_metrics"])
        self.assertIn("saito_tertiary_test", val_res)
        self.assertTrue(val_res["saito_tertiary_test"]["is_critical_failure_detected"])


if __name__ == "__main__":
    unittest.main()
