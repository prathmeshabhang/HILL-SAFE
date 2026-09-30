"""
tests/test_m17_warning_gating.py
================================
Unit tests for Model M17: Early Warning Gating & Evacuation Urgency Recommendation Engine.
"""

import unittest
from ml.decision.m17_warning_gating import (
    EvacuationStrategy,
    EvacuationUrgencyTier,
    M17WarningGatingModel,
    M17WarningInput,
    WarningAlertLevel,
    evaluate_basin_alert_matrix,
    issue_early_warning_and_evacuation,
    validate_m17_prediction,
)


class TestM17WarningGating(unittest.TestCase):
    def setUp(self):
        self.model = M17WarningGatingModel()

    def test_universal_model_contract(self):
        """Model M17 output must strictly conform to the universal FLOODY SHIELD contract."""
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_MANALI",
            river_water_level_m=5.8,
            warning_level_m=5.0,
            danger_level_m=7.0,
            rainfall_intensity_mmh=45.0,
        )
        res = self.model.predict(inp)
        d = res.to_dict()

        for key in ["prediction", "confidence", "uncertainty", "data_quality", "model_version", "applicability", "provenance"]:
            self.assertIn(key, d, f"Missing required contract key: {key}")

        pred = d["prediction"]
        self.assertEqual(pred["reach_or_settlement_id"], "REACH_MANALI")
        self.assertIn("alert_level", pred)
        self.assertIn("urgency_tier", pred)
        self.assertIn("evacuation_strategy", pred)
        self.assertIn("actionable_recommendations", pred)
        self.assertIn("cap_compliant_payload", pred)
        self.assertGreater(res.confidence, 0.5)

    def test_deterministic_danger_level_breach_forces_red(self):
        """Breaching CWC Danger Level must trigger mandatory RED_EVACUATE."""
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_BHUNTAR",
            river_water_level_m=7.6,  # > danger_level 7.0
            warning_level_m=5.0,
            danger_level_m=7.0,
            rainfall_intensity_mmh=20.0,
        )
        res = self.model.predict(inp)

        self.assertEqual(res.alert_level, WarningAlertLevel.RED_EVACUATE)
        self.assertTrue(res.deterministic_override_triggered)
        self.assertEqual(res.urgency_tier, EvacuationUrgencyTier.IMMEDIATE_ACTION)
        self.assertTrue(any("MANDATORY RED ALERT" in r for r in res.actionable_recommendations))

    def test_natural_dam_outburst_forces_red(self):
        """Active catastrophic natural dam outburst wave (Q >= 1000 m3/s) must trigger mandatory RED."""
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_AUT",
            river_water_level_m=3.5,  # Below danger level
            natural_dam_outburst_discharge_m3s=1850.0,
            flood_arrival_time_min=30.0,
        )
        res = self.model.predict(inp)

        self.assertEqual(res.alert_level, WarningAlertLevel.RED_EVACUATE)
        self.assertTrue(res.deterministic_override_triggered)
        self.assertTrue(any("natural dam outburst" in r.lower() for r in res.actionable_recommendations))

    def test_vertical_shelter_in_place_strategy_selection(self):
        """When arterial road is blocked and flood wave arrives before road evacuation can clear (EUI > 1.0), force vertical shelter."""
        inp = M17WarningInput(
            reach_or_settlement_id="SETTLEMENT_BAHANG",
            river_water_level_m=7.8,
            danger_level_m=7.0,
            flood_arrival_time_min=25.0,  # 25 min lead time
            at_risk_population=2500,     # Requires ~75 min to clear single lane
            arterial_road_blocked=True,
        )
        res = self.model.predict(inp)

        self.assertEqual(res.alert_level, WarningAlertLevel.RED_EVACUATE)
        self.assertEqual(res.evacuation_strategy, EvacuationStrategy.VERTICAL_SHELTER_IN_PLACE)
        self.assertGreater(res.evacuation_urgency_index, 1.0)
        self.assertTrue(any("reinforced upper-floor structures" in r or "high-ground" in r for r in res.actionable_recommendations))

    def test_cap_compliant_payload_structure(self):
        """CAP payload must follow OASIS CAP v1.2 specification."""
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_KULLU",
            river_water_level_m=7.2,
            danger_level_m=7.0,
        )
        res = self.model.predict(inp)
        cap = res.cap_compliant_payload

        self.assertEqual(cap["msgType"], "Alert")
        self.assertEqual(cap["status"], "Actual")
        self.assertEqual(cap["info"]["severity"], "Extreme")
        self.assertEqual(cap["info"]["certainty"], "Observed")
        self.assertIn("headline", cap["info"])
        self.assertIn("instruction", cap["info"])

    def test_green_normal_baseline(self):
        """Normal dry baseline flow must result in GREEN_NORMAL and ROUTINE_MONITORING."""
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_LARJI",
            river_water_level_m=2.0,
            warning_level_m=5.0,
            danger_level_m=7.0,
            rainfall_intensity_mmh=2.0,
            flood_probability=0.05,
            landslide_probability=0.03,
        )
        res = self.model.predict(inp)

        self.assertEqual(res.alert_level, WarningAlertLevel.GREEN_NORMAL)
        self.assertEqual(res.urgency_tier, EvacuationUrgencyTier.ROUTINE_MONITORING)
        self.assertFalse(res.deterministic_override_triggered)

    def test_physical_validation_zero_false_negative(self):
        """Validation helper must pass and detect safety violations."""
        inp = M17WarningInput(
            reach_or_settlement_id="REACH_PATLIKUHAL",
            river_water_level_m=7.5,
            danger_level_m=7.0,
        )
        res = self.model.predict(inp)
        v_check = validate_m17_prediction(res, inp)

        self.assertTrue(v_check["is_valid"], f"Validation errors: {v_check.get('issues')}")

    def test_basin_alert_matrix_sorting(self):
        """Basin alert matrix must prioritize RED_EVACUATE at top of alert list."""
        inputs = [
            M17WarningInput(reach_or_settlement_id="REACH_GREEN", river_water_level_m=2.0),
            M17WarningInput(reach_or_settlement_id="REACH_RED", river_water_level_m=8.2, danger_level_m=7.0),
            M17WarningInput(reach_or_settlement_id="REACH_ORANGE", river_water_level_m=5.6, warning_level_m=5.0, danger_level_m=7.0),
        ]
        outputs = evaluate_basin_alert_matrix(inputs)

        self.assertEqual(outputs[0].alert_level, WarningAlertLevel.RED_EVACUATE)
        self.assertEqual(outputs[1].alert_level, WarningAlertLevel.ORANGE_ALERT)
        self.assertEqual(outputs[2].alert_level, WarningAlertLevel.GREEN_NORMAL)


if __name__ == "__main__":
    unittest.main()
