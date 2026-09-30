"""
test_m9_sensor_anomaly.py — Unit Tests for Model M9 Sensor Anomaly Engine
========================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.anomaly.m9_sensor.infer import predict
from ml.anomaly.m9_sensor.schema import SensorAnomalyType, SensorStatus
from ml.anomaly.m9_sensor.validation import run_m9_validation


class TestM9SensorAnomaly(unittest.TestCase):

    def test_nominal_reading_passes(self):
        reading = {
            "rainfall_rate_mmh": 15.0,
            "water_level_m": 2.5,
            "soil_moisture_pct": 40.0,
            "tilt_deg": 0.1,
            "pore_pressure_kpa": 3.0,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertEqual(pred["sensor_status"], "NORMAL")
        self.assertTrue(pred["is_valid_reading"])
        self.assertEqual(pred["anomaly_type"], "NONE")
        self.assertGreater(res["confidence"], 0.70)
        self.assertGreater(res["data_quality"], 0.70)

    def test_negative_reading_rejected(self):
        reading = {
            "rainfall_rate_mmh": -10.0,
            "water_level_m": 2.0,
            "soil_moisture_pct": 30.0,
            "tilt_deg": 0.0,
            "pore_pressure_kpa": 1.0,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertEqual(pred["sensor_status"], "FAULTY")
        self.assertFalse(pred["is_valid_reading"])
        self.assertEqual(pred["anomaly_type"], "PHYSICAL_RANGE_VIOLATION")

    def test_stuck_sensor_flagged(self):
        reading = {"water_level_m": 4.5, "rainfall_rate_mmh": 20.0}
        history = [
            {"water_level_m": 4.5},
            {"water_level_m": 4.5},
            {"water_level_m": 4.5},
            {"water_level_m": 4.5},
        ]
        res = predict(reading, recent_history=history)
        pred = res["prediction"]
        self.assertEqual(pred["sensor_status"], "FAULTY")
        self.assertFalse(pred["is_valid_reading"])
        self.assertEqual(pred["anomaly_type"], "STUCK_SENSOR")

    def test_cross_sensor_inconsistency(self):
        # Water rises sharply with 0 rain
        reading = {"water_level_m": 6.0, "rainfall_rate_mmh": 0.0}
        history = [
            {"water_level_m": 2.0, "rainfall_rate_mmh": 0.0},
            {"water_level_m": 2.2, "rainfall_rate_mmh": 0.0},
        ]
        res = predict(reading, recent_history=history)
        pred = res["prediction"]
        self.assertEqual(pred["sensor_status"], "ANOMALOUS")
        self.assertEqual(pred["anomaly_type"], "CROSS_SENSOR_INCONSISTENCY")

    def test_authentic_storm_spike_preserved(self):
        # High rainfall + high river level + high soil moisture = legitimate disaster storm!
        reading = {
            "rainfall_rate_mmh": 85.0,
            "water_level_m": 7.5,
            "soil_moisture_pct": 85.0,
            "tilt_deg": 1.2,
            "pore_pressure_kpa": 15.0,
        }
        res = predict(reading)
        pred = res["prediction"]
        self.assertEqual(pred["sensor_status"], "NORMAL")
        self.assertTrue(pred["is_valid_reading"])

    def test_validation_benchmark_run(self):
        rep = run_m9_validation()
        self.assertEqual(rep["model_id"], "M9")
        self.assertEqual(rep["accuracy"], 1.0)
        self.assertTrue(rep["storm_spike_preserved_as_valid"])


if __name__ == "__main__":
    unittest.main()
