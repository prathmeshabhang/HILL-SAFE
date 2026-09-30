"""
tests/test_m14_infrastructure_loss.py
=====================================
Unit tests for Model M14: Infrastructure Damage & Loss Estimation Engine.
"""

import unittest
from ml.decision.m14_infrastructure_loss import (
    BEAS_INFRASTRUCTURE_ASSETS,
    AssetCategory,
    DamageState,
    LifelineStatus,
    M14DamageInput,
    M14InfrastructureLossModel,
    assess_corridor_infrastructure,
    compute_bridge_damage,
    compute_road_damage,
    get_asset_or_default,
    predict_infrastructure_loss,
    validate_m14_prediction,
)


class TestM14InfrastructureLoss(unittest.TestCase):
    def setUp(self):
        self.model = M14InfrastructureLossModel()

    def test_universal_model_contract(self):
        """Model M14 output must strictly conform to the universal FLOODY SHIELD contract."""
        inp = M14DamageInput(
            asset_id="NH3_AUT_GORGE",
            flood_depth_m=1.8,
            flow_velocity_ms=3.2,
            debris_impact_flag=True,
        )
        res = self.model.predict(inp)
        d = res.to_dict()

        for key in ["prediction", "confidence", "uncertainty", "data_quality", "model_version", "applicability", "provenance"]:
            self.assertIn(key, d, f"Missing required contract key: {key}")

        pred = d["prediction"]
        self.assertEqual(pred["asset_id"], "NH3_AUT_GORGE")
        self.assertIn("damage_state", pred)
        self.assertIn("structural_damage_ratio", pred)
        self.assertIn("estimated_direct_loss_lakhs_inr", pred)
        self.assertIn("service_outage_hours", pred)
        self.assertIn("lifeline_status", pred)
        self.assertGreater(res.confidence, 0.5)

    def test_bridge_overtopping_and_debris_response(self):
        """Water reaching above deck with debris must severely escalate bridge damage."""
        bridge = get_asset_or_default("BR_AUT_SUSPENSION")
        # Under clearance: depth = 2.0m vs deck height = 4.5m
        d_clear = compute_bridge_damage(depth_m=2.0, velocity_ms=2.0, debris_flag=False, freeboard_clearance_m=bridge.soffit_or_deck_height_m)
        # Submerged with debris: depth = 6.0m vs deck height = 4.5m
        d_submerged = compute_bridge_damage(depth_m=6.0, velocity_ms=4.0, debris_flag=True, freeboard_clearance_m=bridge.soffit_or_deck_height_m)

        self.assertLess(d_clear, 0.10, "Bridge below deck clearance should have negligible structural damage")
        self.assertGreater(d_submerged, 0.70, "Bridge deeply submerged with debris battering must suffer heavy damage")

    def test_highway_washout_hydrodynamic_scaling(self):
        """NH-3 submerged under high velocity must suffer severe damage and road closure."""
        inp = M14DamageInput(
            asset_id="NH3_AUT_GORGE",
            flood_depth_m=2.2,
            flow_velocity_ms=3.8,
            debris_impact_flag=True,
        )
        res = self.model.predict(inp)

        self.assertIn(res.damage_state, [DamageState.EXTENSIVE_DAMAGE, DamageState.COLLAPSED_DESTROYED])
        self.assertEqual(res.lifeline_status, LifelineStatus.STRUCTURALLY_FAILED)
        self.assertGreater(res.estimated_direct_loss_lakhs_inr, 2000.0)
        self.assertGreater(res.service_outage_hours, 100.0)

    def test_zero_water_intact_state(self):
        """Zero water depth must output NEGLIGIBLE_INTACT and OPERATIONAL status."""
        inp = M14DamageInput(asset_id="HOSP_KULLU_REGIONAL", flood_depth_m=0.0, flow_velocity_ms=0.0)
        res = self.model.predict(inp)

        self.assertEqual(res.damage_state, DamageState.NEGLIGIBLE_INTACT)
        self.assertEqual(res.lifeline_status, LifelineStatus.OPERATIONAL)
        self.assertEqual(res.service_outage_hours, 0.0)
        self.assertLess(res.structural_damage_ratio, 0.05)

    def test_substation_plinth_protection(self):
        """Substation below plinth height (1.5m) must sustain low damage, but escalate rapidly once plinth is breached."""
        sub = get_asset_or_default("SUB_LARJI_HYDEL")
        inp_low = M14DamageInput(asset_id="SUB_LARJI_HYDEL", flood_depth_m=0.8)
        inp_breach = M14DamageInput(asset_id="SUB_LARJI_HYDEL", flood_depth_m=2.5)

        res_low = self.model.predict(inp_low)
        res_breach = self.model.predict(inp_breach)

        self.assertLess(res_low.structural_damage_ratio, 0.20)
        self.assertGreater(res_breach.structural_damage_ratio, 0.65)
        self.assertGreater(res_breach.estimated_direct_loss_lakhs_inr, res_low.estimated_direct_loss_lakhs_inr * 3.0)

    def test_physical_invariants_and_bounds(self):
        """Loss cannot exceed replacement value and CI bounds must be ordered."""
        inp = M14DamageInput(asset_id="BR_BHUNTAR_CONFLUENCE", flood_depth_m=7.5, flow_velocity_ms=5.0, debris_impact_flag=True)
        res = self.model.predict(inp)
        v_check = validate_m14_prediction(res)

        self.assertTrue(v_check["is_valid"], f"Validation errors: {v_check.get('issues')}")
        self.assertLessEqual(res.estimated_direct_loss_lakhs_inr, 2600.0 * 1.02)
        self.assertGreaterEqual(res.structural_damage_ratio, 0.0)
        self.assertLessEqual(res.structural_damage_ratio, 1.0)

    def test_corridor_wide_assessment(self):
        """Corridor-wide assessment must return all registered assets sorted by monetary loss."""
        hazard_map = {
            "NH3_AUT_GORGE": {"flood_depth_m": 2.5, "flow_velocity_ms": 3.5, "debris_impact_flag": True},
            "SUB_LARJI_HYDEL": {"flood_depth_m": 2.2, "flow_velocity_ms": 2.0},
        }
        results = assess_corridor_infrastructure(hazard_map)

        self.assertEqual(len(results), len(BEAS_INFRASTRUCTURE_ASSETS))
        # Verify descending loss order
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i].estimated_direct_loss_lakhs_inr,
                results[i + 1].estimated_direct_loss_lakhs_inr,
            )


if __name__ == "__main__":
    unittest.main()
