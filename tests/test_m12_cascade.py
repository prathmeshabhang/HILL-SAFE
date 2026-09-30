"""
test_m12_cascade.py — Unit Tests for Model M12 Hazard Cascade Prediction Engine
================================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.flood.m12_cascade.infer import predict
from ml.flood.m12_cascade.physics import (
    compute_costa_peak_outflow,
    compute_froehlich_breach_parameters,
)
from ml.flood.m12_cascade.schema import CascadeSeverity
from ml.flood.m12_cascade.validation import run_m12_validation
from ml.flood.m12_compound_cascade import (
    CompoundCascadeEngine,
    LandslideDamBreachResult,
)


class TestM12Cascade(unittest.TestCase):

    def test_universal_predict_contract(self):
        input_data = {
            "dam_location": "Larji_Sainj_Confluence",
            "dam_height_m": 35.0,
            "impounded_volume_m3": 8_500_000.0,
            "normal_river_discharge_m3s": 450.0,
        }
        res = predict(input_data)
        self.assertIn("prediction", res)
        self.assertIn("confidence", res)
        self.assertIn("uncertainty", res)
        self.assertIn("data_quality", res)
        self.assertIn("model_version", res)
        self.assertIn("applicability", res)

        pred = res["prediction"]
        self.assertEqual(pred["dam_location"], "Larji_Sainj_Confluence")
        self.assertGreater(pred["peak_outflow_discharge_m3s"], 5000.0)
        self.assertIn(pred["cascade_severity"], [
            CascadeSeverity.MAJOR_DISASTER.value,
            CascadeSeverity.CATASTROPHIC_OUTBURST.value,
        ])
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertGreaterEqual(res["data_quality"], 0.70)

    def test_froehlich_breach_physics(self):
        params = compute_froehlich_breach_parameters(
            dam_height_m=40.0,
            impounded_volume_m3=10_000_000.0,
        )
        self.assertIn("peak_breach_discharge_m3s", params)
        self.assertIn("breach_formation_time_min", params)
        self.assertIn("average_breach_width_m", params)
        self.assertGreater(params["peak_breach_discharge_m3s"], 4000.0)
        self.assertGreater(params["breach_formation_time_min"], 10.0)

    def test_backward_compatibility_compound_cascade_engine(self):
        engine = CompoundCascadeEngine()
        res = engine.simulate_dam_breach(
            dam_location="Test_Gorge",
            dam_height_m=30.0,
            impounded_volume_m3=5_000_000.0,
            normal_river_discharge_m3s=300.0,
        )
        self.assertIsInstance(res, LandslideDamBreachResult)
        self.assertEqual(res.dam_location, "Test_Gorge")
        self.assertGreater(len(res.downstream_impacts), 0)
        self.assertEqual(res.downstream_impacts[0].location_name, "Aut_Gorge_Settlement")

    def test_downstream_wave_attenuation_and_travel_time(self):
        input_data = {
            "dam_location": "Sainj_Dam",
            "dam_height_m": 45.0,
            "impounded_volume_m3": 12_000_000.0,
        }
        res = predict(input_data)
        impacts = res["prediction"]["breach_result"]["downstream_impacts"]
        
        # Peak discharge must attenuate as wave travels further downstream
        q_aut = impacts[0]["peak_discharge_m3s"]
        q_mandi = impacts[-1]["peak_discharge_m3s"]
        self.assertGreater(q_aut, q_mandi)

        # Arrival time must increase downstream
        t_aut = impacts[0]["flood_wave_lead_time_min"]
        t_mandi = impacts[-1]["flood_wave_lead_time_min"]
        self.assertLess(t_aut, t_mandi)

    def test_run_m12_validation(self):
        val_res = run_m12_validation()
        self.assertEqual(val_res["status"], "PASS")
        self.assertIn("case_study_benchmarks", val_res)
        self.assertTrue(val_res["case_study_benchmarks"]["sun_kosi_2014"]["in_historical_range"])
        self.assertTrue(val_res["case_study_benchmarks"]["pareechu_2000"]["in_historical_range"])


if __name__ == "__main__":
    unittest.main()
