"""
test_cap_alerts.py — Unit Tests for NDMA Sachet CAP v1.2 Early Warning Generator
"""

import unittest
import xml.etree.ElementTree as ET
from dataclasses import asdict

from ml.security.cap_alert_engine import CAPAlertEngine, CAP_XMLNS
from ml.flood.m12_compound_cascade import CompoundCascadeEngine


class TestCAPAlerts(unittest.TestCase):

    def test_cascade_dam_breach_cap_alert(self):
        cascade_engine = CompoundCascadeEngine()
        breach_result = cascade_engine.simulate_dam_breach(
            dam_location="Larji_Sainj_Confluence",
            dam_height_m=40.0,
            impounded_volume_m3=10_000_000.0,
        )

        cap_engine = CAPAlertEngine()
        alert = cap_engine.generate_cascade_breach_alert(asdict(breach_result))

        self.assertTrue(alert.identifier.startswith("IN-HP-NDMA-FS-"))
        self.assertEqual(alert.msg_type, "Alert")
        self.assertEqual(alert.status, "Actual")
        self.assertEqual(len(alert.infos), 2)

        # Verify English info
        info_en = alert.infos[0]
        self.assertEqual(info_en.language, "en-IN")
        self.assertEqual(info_en.urgency, "Immediate")
        self.assertEqual(info_en.severity, "Extreme")
        self.assertIn("Larji_Sainj_Confluence", info_en.description)
        self.assertGreaterEqual(len(info_en.area.polygons), 1)

        # Verify Hindi info
        info_hi = alert.infos[1]
        self.assertEqual(info_hi.language, "hi-IN")
        self.assertEqual(info_hi.urgency, "Immediate")
        self.assertIn("फ्लैश फ्लड", info_hi.event)

        # Test XML Serialization
        xml_str = alert.to_xml_string()
        self.assertIn('xmlns="urn:oasis:names:tc:emergency:cap:1.2"', xml_str)

        # Parse XML back
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, f"{{{CAP_XMLNS}}}alert")

        # Verify elements inside XML
        ident = root.find(f"{{{CAP_XMLNS}}}identifier")
        self.assertIsNotNone(ident)
        self.assertEqual(ident.text, alert.identifier)

        infos_xml = root.findall(f"{{{CAP_XMLNS}}}info")
        self.assertEqual(len(infos_xml), 2)

        # Test JSON/dict serialization
        d = alert.to_dict()
        self.assertEqual(d["identifier"], alert.identifier)
        self.assertEqual(len(d["infos"]), 2)
        self.assertNotEqual(d["infos"][0]["parameters"]["PeakOutflowDischargeM3s"], "")

    def test_high_hazard_zone_alert(self):
        cap_engine = CAPAlertEngine()
        poly = [(31.95, 77.10), (31.96, 77.12), (31.94, 77.11), (31.95, 77.10)]
        alert = cap_engine.generate_high_hazard_zone_alert(
            zone_name="Kullu Right Bank Sector 4",
            hazard_type="Flood & Debris Flow",
            coordinates_polygon=poly,
        )

        self.assertEqual(len(alert.infos), 2)
        xml_str = alert.to_xml_string()
        self.assertIn("Kullu Right Bank Sector 4", xml_str)
        self.assertIn("Section 36", xml_str)


if __name__ == "__main__":
    unittest.main()
