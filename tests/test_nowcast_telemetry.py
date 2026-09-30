"""
test_nowcast_telemetry.py — Unit Tests for Model M1 Nowcasting & Model M9 Telemetry Gateway
===========================================================================================
Verifies:
  1. Semi-Lagrangian nowcasting extrapolation for +15m to +120m timesteps.
  2. Cloudburst (>60 mm/hr) exceedance probability and impacted gorge identification.
  3. Ground station registry and live IoT telemetry ingestion.
  4. Model M9 Isolation Forest and physical bounds anomaly detection (stuck, spike, negative).
"""

import unittest

from ml.rainfall.nowcast_service import ShortTermNowcastService
from ml.telemetry.iot_gateway import IoTTelemetryGateway


class TestNowcastAndTelemetry(unittest.TestCase):

    def test_nowcast_service_generation(self):
        service = ShortTermNowcastService()
        res = service.generate_nowcast(
            catchment_name="Upper_Beas_Catchment",
            current_max_rain_mmh=85.0,
            storm_motion_dx_kmh=12.0,
            storm_motion_dy_kmh=-6.0,
        )

        self.assertEqual(res.catchment_name, "Upper_Beas_Catchment")
        self.assertEqual(res.cloudburst_risk_level, "EXTREME")
        self.assertEqual(len(res.timesteps), 4)

        # Check timesteps
        lead_times = [t.lead_time_min for t in res.timesteps]
        self.assertEqual(lead_times, [15, 30, 60, 120])
        self.assertGreater(res.timesteps[0].max_rainfall_rate_mmh, 60.0)
        self.assertGreater(res.timesteps[0].cloudburst_exceedance_pct, 50.0)
        self.assertIn("Sainj_Gorge", res.impacted_gorges)

    def test_iot_telemetry_valid_readings(self):
        gw = IoTTelemetryGateway()
        stations = gw.get_stations()
        self.assertGreaterEqual(len(stations), 4)

        # Ingest valid river gauge reading
        reading_valid = gw.ingest_reading(
            station_id="ST_AUT_01",
            sensor_type="RIVER_GAUGE",
            value=6.4,
        )
        self.assertTrue(reading_valid.is_valid)
        self.assertIsNone(reading_valid.anomaly_flag)
        self.assertEqual(reading_valid.unit, "m")
        self.assertEqual(reading_valid.quality_score, 1.0)

    def test_iot_telemetry_anomaly_rejection(self):
        gw = IoTTelemetryGateway()

        # 1. Negative water level (sensor error / baseline drift)
        r_neg = gw.ingest_reading(
            station_id="ST_AUT_01",
            sensor_type="RIVER_GAUGE",
            value=-2.5,
        )
        self.assertFalse(r_neg.is_valid)
        self.assertEqual(r_neg.anomaly_flag, "NEGATIVE_WATER_LEVEL")
        self.assertEqual(r_neg.quality_score, 0.0)

        # 2. Extreme impossible spike (e.g. 85m water level in river channel)
        r_spike = gw.ingest_reading(
            station_id="ST_AUT_01",
            sensor_type="RIVER_GAUGE",
            value=85.0,
        )
        self.assertFalse(r_spike.is_valid)
        self.assertEqual(r_spike.anomaly_flag, "EXTREME_SPIKE")

        # 3. Impossible rain rate (e.g. 500 mm/hr)
        r_rain = gw.ingest_reading(
            station_id="ST_BHUNTAR_01",
            sensor_type="RAIN_GAUGE",
            value=520.0,
        )
        self.assertFalse(r_rain.is_valid)
        self.assertEqual(r_rain.anomaly_flag, "IMPOSSIBLE_RAINFALL_VALUE")


if __name__ == "__main__":
    unittest.main()
