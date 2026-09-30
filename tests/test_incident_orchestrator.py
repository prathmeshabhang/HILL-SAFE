"""
test_incident_orchestrator.py — Unit Tests for Autonomous Incident Orchestrator
================================================================================
Verifies:
  1. Triggering an autonomous multi-hazard incident pipeline.
  2. M12 dam breach simulation integration.
  3. M15 & M16 dynamic evacuation route solving bypassing flooded NH-3 corridors.
  4. M20 rescue prioritization generation.
  5. Bilingual (English & Hindi) CAP v1.2 XML synthesis.
  6. Incident lifecycle state transitions and audit trails.
"""

import unittest

from ml.orchestrator.incident_manager import IncidentManager, get_incident_manager


class TestIncidentOrchestrator(unittest.TestCase):

    def setUp(self):
        self.mgr = IncidentManager()

    def test_default_seeded_incident(self):
        incidents = self.mgr.list_incidents()
        self.assertGreaterEqual(len(incidents), 1)

        default_inc = self.mgr.get_incident("INC-BEAS-LARJI-01")
        self.assertIsNotNone(default_inc)
        self.assertEqual(default_inc.incident_type, "NATURAL_DAM_BREACH")
        self.assertEqual(default_inc.severity_level, "CRITICAL")
        self.assertIn("Peak Q=", default_inc.audit_log[1]["action"])

    def test_trigger_custom_incident(self):
        record = self.mgr.trigger_incident(
            incident_type="CLOUDBURST_FLASH_FLOOD",
            severity_level="CRITICAL",
            trigger_source="NOWCAST_EXTRAPOLATION",
            trigger_location="Aut_Gorge",
            dam_height_m=42.0,
            impounded_volume_m3=12_000_000.0,
            rainfall_rate_mmh=85.0,
            simulate_nh3_closure=True,
            custom_id="INC-TEST-AUT-99",
        )

        self.assertEqual(record.incident_id, "INC-TEST-AUT-99")
        self.assertEqual(record.severity_level, "CRITICAL")
        self.assertGreater(record.cascade_simulation["peak_outflow_discharge_m3s"], 5_000.0)
        self.assertTrue(record.evacuation_plan["nh3_closure_simulated"])

        # Check evacuation route
        route_sol = record.evacuation_plan["route_solution"]
        self.assertEqual(route_sol["route_status"], "FOUND_SAFER_FEASIBLE")
        self.assertGreater(route_sol["total_distance_km"], 0.0)

        # Check rescue prioritization
        self.assertGreater(len(record.rescue_prioritization), 0)

        # Check CAP alert
        self.assertIn("<?xml", record.cap_alert_xml)
        self.assertIn("<alert", record.cap_alert_xml)
        self.assertIn("FLASH FLOOD", record.cap_alert_summary_en)
        self.assertIn("sachet.ndma.gov.in", record.cap_alert_xml)
        self.assertIn("<language>hi-IN</language>", record.cap_alert_xml)

        # Check audit trail
        self.assertGreaterEqual(len(record.audit_log), 4)

    def test_status_update_and_audit(self):
        record = self.mgr.trigger_incident(
            incident_type="NATURAL_DAM_BREACH",
            custom_id="INC-AUDIT-TEST",
        )
        self.assertEqual(record.status, "ACTIVE")

        updated = self.mgr.update_incident_status(
            incident_id="INC-AUDIT-TEST",
            new_status="CONTAINED",
            notes="Controlled spillway trench excavated by engineering regiment.",
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, "CONTAINED")
        last_log = updated.audit_log[-1]
        self.assertIn("CONTAINED", last_log["action"])
        self.assertIn("spillway trench", last_log["action"])


if __name__ == "__main__":
    unittest.main()
