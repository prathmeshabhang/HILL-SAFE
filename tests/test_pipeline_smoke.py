"""
=============================================================================
SYNTHETIC SMOKE TEST  ·  FLOODY SHIELD End-to-End Pipeline
=============================================================================
⚠️  THIS IS NOT VALIDATION EVIDENCE  ⚠️
=============================================================================
Purpose : Exercise every model's import, instantiation, and predict/assess
          call with CLEARLY SYNTHETIC inputs. Verifies schema compatibility,
          output field presence, and reasonable value types only.

THIS FILE:
  - Uses ONLY synthetic / mock inputs (no real observations).
  - Does NOT retrain or modify any model artifact on disk.
  - Does NOT constitute scientific validation, accuracy benchmarking,
    or operational readiness certification.
  - Must be labelled SYNTHETIC SMOKE TEST in all output and commits.

Pipeline chain tested:
  M1  (rainfall nowcast)
  → M2  (flood risk)
  → M9  (sensor anomaly)
  → M10 (water level)
  → M11 (flood depth)
  → M12 (hazard cascade)
  → M13 (vulnerability)
  → M14 (infrastructure loss)
  → M17 (warning gating)
  → M18 (calibration)
  → M19 (time-to-impact)
  → M20 (damage assessment)
Individual models also tested: M6/M7 (via joblib), M8 (deformation).

Author  : FLOODY SHIELD Automated Test Generator
Date    : 2026-09-21
=============================================================================
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure repo root is on sys.path so all ml.* imports resolve correctly
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ===========================================================================
# HELPER — print a clear SYNTHETIC SMOKE TEST banner in any captured output
# ===========================================================================

def _smoke_banner(model_tag: str) -> str:
    return f"[SYNTHETIC SMOKE TEST] {model_tag} — NOT VALIDATION EVIDENCE"


# ===========================================================================
# M1 — Extreme Rainfall Nowcasting
# ===========================================================================

class TestM1NowcastSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M1 Rainfall Nowcast"""

    # Minimal synthetic feature dict — all values are fabricated
    _SYNTH_FEATURES = {
        "station_id": "SYNTH_AWS_01",
        "latitude": 32.20,
        "longitude": 77.18,
        "elevation_m": 2000.0,
        "slope_deg": 20.0,
        "r_15m": 5.0,
        "r_30m": 9.0,
        "r_1h": 15.0,
        "r_3h": 30.0,
        "r_6h": 45.0,
        "r_12h": 60.0,
        "r_24h": 80.0,
        "r_72h": 100.0,
        "rolling_intensity_mmh": 15.0,
        "rainfall_acceleration": 0.5,
        "storm_motion_dx": 2.0,
        "storm_motion_dy": -1.0,
    }

    def test_m1_import(self):
        print(_smoke_banner("M1"))
        from ml.rainfall.m1_nowcast import infer as m1_infer  # noqa: F401
        self.assertTrue(callable(m1_infer.predict))

    def test_m1_predict_returns_dict(self):
        print(_smoke_banner("M1"))
        from ml.rainfall.m1_nowcast.infer import predict
        result = predict(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m1_output_schema(self):
        print(_smoke_banner("M1"))
        from ml.rainfall.m1_nowcast.infer import predict
        result = predict(self._SYNTH_FEATURES)
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, result, f"M1 output missing key: {key}")

    def test_m1_prediction_fields(self):
        print(_smoke_banner("M1"))
        from ml.rainfall.m1_nowcast.infer import predict
        result = predict(self._SYNTH_FEATURES)
        pred = result["prediction"]
        for key in ("primary_horizon", "predicted_rainfall_mm",
                    "extreme_rain_probability", "risk_level", "horizon_forecasts"):
            self.assertIn(key, pred, f"M1 prediction missing key: {key}")
        self.assertIsInstance(pred["predicted_rainfall_mm"], float)
        self.assertGreaterEqual(pred["predicted_rainfall_mm"], 0.0)
        self.assertGreaterEqual(pred["extreme_rain_probability"], 0.0)
        self.assertLessEqual(pred["extreme_rain_probability"], 1.0)
        self.assertEqual(len(pred["horizon_forecasts"]), 6)


# ===========================================================================
# M2 — Flood Occurrence & Risk
# ===========================================================================

class TestM2FloodRiskSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M2 Flood Risk"""

    # Synthetic features matching the M2 feature list from m2_flood_metrics.json
    _SYNTH_FEATURES = {
        "elevation": 900.0,
        "slope": 5.0,
        "flow_accumulation": 2000.0,
        "dist_to_stream": 80.0,
        "land_cover": 3,
        "rainfall_1h": 20.0,
        "rainfall_3h": 45.0,
        "rainfall_6h": 70.0,
        "rainfall_24h": 100.0,
        "antecedent_rain_3d": 80.0,
        "soil_moisture": 75.0,
        "river_level": 5.5,
        "river_level_change_1h": 0.2,
    }

    def test_m2_import(self):
        print(_smoke_banner("M2"))
        from ml.flood.predict_m2_flood import FloodRiskPredictor  # noqa: F401
        self.assertTrue(callable(FloodRiskPredictor))

    def test_m2_predict_returns_dict(self):
        print(_smoke_banner("M2"))
        from ml.flood.predict_m2_flood import FloodRiskPredictor
        predictor = FloodRiskPredictor()
        result = predictor.predict_point(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m2_output_schema(self):
        print(_smoke_banner("M2"))
        from ml.flood.predict_m2_flood import FloodRiskPredictor
        predictor = FloodRiskPredictor()
        result = predictor.predict_point(self._SYNTH_FEATURES)
        for key in ("model", "flood_probability", "risk_tier",
                    "confidence", "key_drivers"):
            self.assertIn(key, result, f"M2 output missing key: {key}")
        prob = result["flood_probability"]
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        self.assertIn(result["risk_tier"],
                      ("LOW", "MODERATE", "HIGH", "CRITICAL"))


# ===========================================================================
# M9 — IoT Sensor Anomaly Detection
# ===========================================================================

class TestM9SensorAnomalySmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M9 Sensor Anomaly"""

    _SYNTH_FEATURES = {
        "station_id": "SYNTH_IOT_SENSOR_01",
        "timestamp_utc": "2026-09-21T03:00:00Z",
        "rainfall_rate_mmh": 12.0,
        "water_level_m": 3.5,
        "soil_moisture_pct": 60.0,
        "tilt_deg": 0.5,
        "pore_pressure_kpa": 25.0,
        "temperature_c": 18.0,
    }

    def test_m9_import(self):
        print(_smoke_banner("M9"))
        from ml.anomaly.m9_sensor import infer as m9_infer  # noqa: F401
        self.assertTrue(callable(m9_infer.predict))

    def test_m9_predict_returns_dict(self):
        print(_smoke_banner("M9"))
        from ml.anomaly.m9_sensor.infer import predict
        result = predict(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m9_output_schema(self):
        print(_smoke_banner("M9"))
        from ml.anomaly.m9_sensor.infer import predict
        result = predict(self._SYNTH_FEATURES)
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, result, f"M9 output missing key: {key}")

    def test_m9_prediction_fields(self):
        print(_smoke_banner("M9"))
        from ml.anomaly.m9_sensor.infer import predict
        result = predict(self._SYNTH_FEATURES)
        pred = result["prediction"]
        for key in ("sensor_status", "anomaly_score", "anomaly_type", "is_valid_reading"):
            self.assertIn(key, pred, f"M9 prediction missing key: {key}")
        score = pred["anomaly_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


# ===========================================================================
# M10 — River Water-Level Forecast
# ===========================================================================

class TestM10WaterLevelSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M10 Water Level Forecast"""

    _SYNTH_FEATURES = {
        "station_id": "CWC_SYNTH_01",
        "station_name": "Synthetic Gauge Station",
        "latitude": 31.95,
        "longitude": 77.10,
        "elevation_m": 1200.0,
        "current_stage_m": 3.5,
        "rate_of_rise_m_hr": 0.15,
        "rainfall_15m_mm": 4.0,
        "rainfall_1h_mm": 12.0,
        "rainfall_3h_mm": 25.0,
        "rainfall_6h_mm": 40.0,
        "soil_moisture_pct": 65.0,
    }

    def test_m10_import(self):
        print(_smoke_banner("M10"))
        from ml.flood.m10_water_level import infer as m10_infer  # noqa: F401
        self.assertTrue(callable(m10_infer.predict))

    def test_m10_predict_returns_dict(self):
        print(_smoke_banner("M10"))
        from ml.flood.m10_water_level.infer import predict
        result = predict(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m10_output_schema(self):
        print(_smoke_banner("M10"))
        from ml.flood.m10_water_level.infer import predict
        result = predict(self._SYNTH_FEATURES)
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, result, f"M10 output missing key: {key}")

    def test_m10_prediction_fields(self):
        print(_smoke_banner("M10"))
        from ml.flood.m10_water_level.infer import predict
        result = predict(self._SYNTH_FEATURES)
        pred = result["prediction"]
        for key in ("primary_horizon", "forecasted_stage_m", "alert_level",
                    "horizon_forecasts"):
            self.assertIn(key, pred, f"M10 prediction missing key: {key}")
        self.assertIsInstance(pred["forecasted_stage_m"], float)
        self.assertGreaterEqual(pred["forecasted_stage_m"], 0.0)


# ===========================================================================
# M11 — Flood Propagation & Depth Forecast
# ===========================================================================

class TestM11FloodDepthSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M11 Flood Depth"""

    _SYNTH_FEATURES = {
        "source_stage_m": 6.5,
        "source_discharge_m3s": 800.0,
        "target_reach_id": "REACH_03_PATLIKUHAL_KULLU",
        "hand_m": 1.8,
        "distance_to_river_m": 90.0,
        "slope_deg": 5.5,
        "elevation_m": 1180.0,
        "latitude": 31.96,
        "longitude": 77.11,
    }

    def test_m11_import(self):
        print(_smoke_banner("M11"))
        from ml.flood.m11_flood_depth import infer as m11_infer  # noqa: F401
        self.assertTrue(callable(m11_infer.predict))

    def test_m11_predict_returns_dict(self):
        print(_smoke_banner("M11"))
        from ml.flood.m11_flood_depth.infer import predict
        result = predict(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m11_output_schema(self):
        print(_smoke_banner("M11"))
        from ml.flood.m11_flood_depth.infer import predict
        result = predict(self._SYNTH_FEATURES)
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, result, f"M11 output missing key: {key}")

    def test_m11_prediction_fields(self):
        print(_smoke_banner("M11"))
        from ml.flood.m11_flood_depth.infer import predict
        result = predict(self._SYNTH_FEATURES)
        pred = result["prediction"]
        for key in ("forecasted_depth_m", "inundation_severity",
                    "flood_wave_arrival_time_min", "reach_forecasts"):
            self.assertIn(key, pred, f"M11 prediction missing key: {key}")
        self.assertIsInstance(pred["forecasted_depth_m"], float)
        self.assertGreaterEqual(pred["forecasted_depth_m"], 0.0)


# ===========================================================================
# M12 — Hazard Cascade / Landslide Dam Breach
# ===========================================================================

class TestM12CascadeSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M12 Hazard Cascade"""

    _SYNTH_FEATURES = {
        "dam_location": "SYNTH_Landslide_Dam_01",
        "dam_height_m": 30.0,
        "impounded_volume_m3": 5_000_000.0,
        "normal_river_discharge_m3s": 350.0,
        "trigger_type": "LANDSLIDE_DAM",
        "trigger_probability": 0.75,
    }

    def test_m12_import(self):
        print(_smoke_banner("M12"))
        from ml.flood.m12_cascade import infer as m12_infer  # noqa: F401
        self.assertTrue(callable(m12_infer.predict))

    def test_m12_predict_returns_dict(self):
        print(_smoke_banner("M12"))
        from ml.flood.m12_cascade.infer import predict
        result = predict(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m12_output_schema(self):
        print(_smoke_banner("M12"))
        from ml.flood.m12_cascade.infer import predict
        result = predict(self._SYNTH_FEATURES)
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, result, f"M12 output missing key: {key}")

    def test_m12_prediction_fields(self):
        print(_smoke_banner("M12"))
        from ml.flood.m12_cascade.infer import predict
        result = predict(self._SYNTH_FEATURES)
        pred = result["prediction"]
        for key in ("dam_location", "peak_outflow_discharge_m3s",
                    "cascade_severity", "breach_result"):
            self.assertIn(key, pred, f"M12 prediction missing key: {key}")
        self.assertIsInstance(pred["peak_outflow_discharge_m3s"], float)
        self.assertGreater(pred["peak_outflow_discharge_m3s"], 0.0)


# ===========================================================================
# M13 — Vulnerability & Population Exposure
# ===========================================================================

class TestM13VulnerabilitySmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M13 Vulnerability"""

    def test_m13_import(self):
        print(_smoke_banner("M13"))
        from ml.decision.m13_vulnerability import infer as m13_infer  # noqa: F401
        self.assertTrue(callable(m13_infer.predict_vulnerability_exposure))

    def test_m13_predict_returns_output(self):
        print(_smoke_banner("M13"))
        from ml.decision.m13_vulnerability.infer import predict_vulnerability_exposure
        from ml.decision.m13_vulnerability.schema import M13ExposureInput
        # Use first registered settlement ID
        from ml.decision.m13_vulnerability.demographics import BEAS_SETTLEMENT_REGISTER
        sid = next(iter(BEAS_SETTLEMENT_REGISTER.keys()))
        inp = M13ExposureInput(
            settlement_id=sid,
            month=7,
            flood_prob=0.65,
            flood_depth_m=1.2,
            landslide_prob=0.30,
            debris_flow_prob=0.20,
            river_distance_m=120.0,
        )
        result = predict_vulnerability_exposure(inp)
        self.assertIsNotNone(result)

    def test_m13_output_schema(self):
        print(_smoke_banner("M13"))
        from ml.decision.m13_vulnerability.infer import predict_vulnerability_exposure
        from ml.decision.m13_vulnerability.schema import M13ExposureInput, M13PredictionOutput
        from ml.decision.m13_vulnerability.demographics import BEAS_SETTLEMENT_REGISTER
        sid = next(iter(BEAS_SETTLEMENT_REGISTER.keys()))
        inp = M13ExposureInput(
            settlement_id=sid,
            month=7,
            flood_prob=0.65,
            flood_depth_m=1.2,
            landslide_prob=0.30,
            debris_flow_prob=0.20,
            river_distance_m=120.0,
        )
        result = predict_vulnerability_exposure(inp)
        self.assertIsInstance(result, M13PredictionOutput)
        self.assertIsInstance(result.total_exposed_population, int)
        self.assertGreaterEqual(result.composite_vulnerability_score, 0.0)
        self.assertLessEqual(result.composite_vulnerability_score, 1.0)
        self.assertIsNotNone(result.vulnerability_tier)
        self.assertIsNotNone(result.life_safety_priority)

    def test_m13_dict_output(self):
        print(_smoke_banner("M13"))
        from ml.decision.m13_vulnerability.infer import predict_vulnerability_exposure
        from ml.decision.m13_vulnerability.schema import M13ExposureInput
        from ml.decision.m13_vulnerability.demographics import BEAS_SETTLEMENT_REGISTER
        sid = next(iter(BEAS_SETTLEMENT_REGISTER.keys()))
        inp = M13ExposureInput(
            settlement_id=sid,
            month=8,
            flood_prob=0.50,
            flood_depth_m=0.8,
            landslide_prob=0.15,
            debris_flow_prob=0.10,
            river_distance_m=200.0,
        )
        result = predict_vulnerability_exposure(inp)
        d = result.to_dict()
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, d, f"M13 dict missing key: {key}")


# ===========================================================================
# M14 — Infrastructure Damage & Loss
# ===========================================================================

class TestM14InfrastructureSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M14 Infrastructure Loss"""

    def test_m14_import(self):
        print(_smoke_banner("M14"))
        from ml.decision.m14_infrastructure_loss import infer as m14_infer  # noqa: F401
        self.assertTrue(callable(m14_infer.predict_infrastructure_loss))

    def test_m14_predict_returns_output(self):
        print(_smoke_banner("M14"))
        from ml.decision.m14_infrastructure_loss.infer import predict_infrastructure_loss
        from ml.decision.m14_infrastructure_loss.schema import M14DamageInput
        from ml.decision.m14_infrastructure_loss.assets import BEAS_INFRASTRUCTURE_ASSETS
        asset_id = next(iter(BEAS_INFRASTRUCTURE_ASSETS.keys()))
        inp = M14DamageInput(
            asset_id=asset_id,
            flood_depth_m=1.5,
            flow_velocity_ms=2.0,
            debris_impact_flag=False,
            inundation_duration_hours=3.0,
        )
        result = predict_infrastructure_loss(inp)
        self.assertIsNotNone(result)

    def test_m14_output_schema(self):
        print(_smoke_banner("M14"))
        from ml.decision.m14_infrastructure_loss.infer import predict_infrastructure_loss
        from ml.decision.m14_infrastructure_loss.schema import (
            M14DamageInput, M14PredictionOutput
        )
        from ml.decision.m14_infrastructure_loss.assets import BEAS_INFRASTRUCTURE_ASSETS
        asset_id = next(iter(BEAS_INFRASTRUCTURE_ASSETS.keys()))
        inp = M14DamageInput(
            asset_id=asset_id,
            flood_depth_m=1.5,
            flow_velocity_ms=2.0,
            debris_impact_flag=False,
            inundation_duration_hours=3.0,
        )
        result = predict_infrastructure_loss(inp)
        self.assertIsInstance(result, M14PredictionOutput)
        self.assertIsInstance(result.structural_damage_ratio, float)
        self.assertGreaterEqual(result.structural_damage_ratio, 0.0)
        self.assertLessEqual(result.structural_damage_ratio, 1.0)
        self.assertGreaterEqual(result.estimated_direct_loss_lakhs_inr, 0.0)


# ===========================================================================
# M17 — Early Warning Gating & Evacuation
# ===========================================================================

class TestM17WarningGatingSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M17 Warning Gating"""

    def test_m17_import(self):
        print(_smoke_banner("M17"))
        from ml.decision.m17_warning_gating import infer as m17_infer  # noqa: F401
        self.assertTrue(callable(m17_infer.issue_early_warning_and_evacuation))

    def test_m17_predict_returns_output(self):
        print(_smoke_banner("M17"))
        from ml.decision.m17_warning_gating.infer import issue_early_warning_and_evacuation
        from ml.decision.m17_warning_gating.schema import M17WarningInput
        inp = M17WarningInput(
            reach_or_settlement_id="SYNTH_REACH_01",
            rainfall_intensity_mmh=55.0,
            rainfall_3h_mm=85.0,
            flood_probability=0.72,
            river_water_level_m=6.2,
            warning_level_m=5.0,
            danger_level_m=7.0,
            hfl_m=9.5,
            flood_depth_m=1.0,
            flood_arrival_time_min=45.0,
            landslide_probability=0.35,
            pore_water_pressure_ratio=0.45,
            natural_dam_outburst_discharge_m3s=2500.0,
            at_risk_population=3500,
            arterial_road_blocked=True,
            critical_bridge_submerged=False,
        )
        result = issue_early_warning_and_evacuation(inp)
        self.assertIsNotNone(result)

    def test_m17_output_schema(self):
        print(_smoke_banner("M17"))
        from ml.decision.m17_warning_gating.infer import issue_early_warning_and_evacuation
        from ml.decision.m17_warning_gating.schema import (
            M17WarningInput, M17WarningOutput
        )
        inp = M17WarningInput(
            reach_or_settlement_id="SYNTH_REACH_02",
            rainfall_intensity_mmh=20.0,
            rainfall_3h_mm=35.0,
            flood_probability=0.30,
            river_water_level_m=3.5,
            warning_level_m=5.0,
            danger_level_m=7.0,
            hfl_m=9.5,
            flood_depth_m=0.2,
            flood_arrival_time_min=120.0,
            landslide_probability=0.10,
            at_risk_population=800,
        )
        result = issue_early_warning_and_evacuation(inp)
        self.assertIsInstance(result, M17WarningOutput)
        d = result.to_dict()
        for key in ("prediction", "confidence", "uncertainty", "data_quality"):
            self.assertIn(key, d, f"M17 dict missing key: {key}")
        pred = d["prediction"]
        for key in ("alert_level", "urgency_tier", "evacuation_strategy",
                    "lead_time_minutes", "evacuation_urgency_index",
                    "actionable_recommendations"):
            self.assertIn(key, pred, f"M17 prediction missing key: {key}")


# ===========================================================================
# M18 — Probability Calibration
# ===========================================================================

class TestM18CalibrationSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M18 Risk Calibration"""

    def test_m18_import(self):
        print(_smoke_banner("M18"))
        from ml.calibration.m18_calibration import infer as m18_infer  # noqa: F401
        self.assertTrue(callable(m18_infer.calibrate))

    def test_m18_calibrate_returns_output(self):
        print(_smoke_banner("M18"))
        from ml.calibration.m18_calibration.infer import calibrate
        from ml.calibration.m18_calibration.schema import M18CalibrationInput
        inp = M18CalibrationInput(
            source_model="M2_FLOOD_RISK",
            raw_probability=0.68,
            data_quality=0.90,
        )
        result = calibrate(inp)
        self.assertIsNotNone(result)

    def test_m18_output_schema(self):
        print(_smoke_banner("M18"))
        from ml.calibration.m18_calibration.infer import calibrate
        from ml.calibration.m18_calibration.schema import (
            M18CalibrationInput, M18CalibrationOutput
        )
        inp = M18CalibrationInput(
            source_model="M2_FLOOD_RISK",
            raw_probability=0.68,
            data_quality=0.90,
        )
        result = calibrate(inp)
        self.assertIsInstance(result, M18CalibrationOutput)
        self.assertEqual(result.model, "M18_RISK_CALIBRATION")
        self.assertGreaterEqual(result.calibrated_probability, 0.0)
        self.assertLessEqual(result.calibrated_probability, 1.0)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)

    def test_m18_degraded_input_passthrough(self):
        """Low data-quality should return DEGRADED_INPUT passthrough."""
        print(_smoke_banner("M18"))
        from ml.calibration.m18_calibration.infer import calibrate
        from ml.calibration.m18_calibration.schema import (
            M18CalibrationInput, CalibrationStatus
        )
        inp = M18CalibrationInput(
            source_model="M1_RAINFALL",
            raw_probability=0.55,
            data_quality=0.20,   # below 0.30 threshold
        )
        result = calibrate(inp)
        self.assertEqual(result.status, CalibrationStatus.DEGRADED_INPUT)
        self.assertEqual(result.calibrated_probability, result.raw_probability)


# ===========================================================================
# M19 — Time-to-Impact
# ===========================================================================

class TestM19TimeToImpactSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M19 Time-to-Impact"""

    def test_m19_import(self):
        print(_smoke_banner("M19"))
        from ml.impact.m19_time_to_impact import infer as m19_infer  # noqa: F401
        self.assertTrue(callable(m19_infer.predict))

    def test_m19_predict_flood_inundation(self):
        print(_smoke_banner("M19"))
        from ml.impact.m19_time_to_impact.infer import predict
        from ml.impact.m19_time_to_impact.schema import (
            M19TimeToImpactInput, M19TimeToImpactOutput, ImpactType
        )
        inp = M19TimeToImpactInput(
            impact_type=ImpactType.FLOOD_INUNDATION,
            distance_km=15.0,
            peak_discharge_m3s=1500.0,
            channel_slope_pct=1.5,
            floodplain_width_m=300.0,
            upstream_rainfall_mm_1h=40.0,
            soil_saturation_ratio=0.70,
            data_quality=0.85,
        )
        result = predict(inp)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, M19TimeToImpactOutput)
        self.assertGreater(result.p50_minutes, 0.0)
        self.assertLessEqual(result.p10_minutes, result.p50_minutes)
        self.assertLessEqual(result.p50_minutes, result.p90_minutes)

    def test_m19_output_schema(self):
        print(_smoke_banner("M19"))
        from ml.impact.m19_time_to_impact.infer import predict
        from ml.impact.m19_time_to_impact.schema import (
            M19TimeToImpactInput, ImpactType
        )
        inp = M19TimeToImpactInput(
            impact_type=ImpactType.LANDSLIDE_RUNOUT,
            distance_km=5.0,
            slope_angle_deg=35.0,
            debris_depth_m=3.0,
            soil_saturation_ratio=0.85,
            data_quality=0.80,
        )
        result = predict(inp)
        self.assertEqual(result.model, "M19_TIME_TO_IMPACT")
        self.assertIsNotNone(result.status)
        self.assertIsNotNone(result.method)
        self.assertGreaterEqual(result.confidence, 0.0)

    def test_m19_degraded_input(self):
        print(_smoke_banner("M19"))
        from ml.impact.m19_time_to_impact.infer import predict
        from ml.impact.m19_time_to_impact.schema import (
            M19TimeToImpactInput, ImpactType, TTIStatus
        )
        import math
        inp = M19TimeToImpactInput(
            impact_type=ImpactType.DAM_BREACH_OUTBURST,
            distance_km=20.0,
            data_quality=0.15,  # below 0.30 threshold → DEGRADED_INPUT
        )
        result = predict(inp)
        self.assertEqual(result.status, TTIStatus.DEGRADED_INPUT)
        self.assertTrue(math.isnan(result.p50_minutes))


# ===========================================================================
# M20 — Post-Event Damage Assessment
# ===========================================================================

class TestM20DamageAssessmentSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M20 Damage Assessment"""

    def test_m20_import(self):
        print(_smoke_banner("M20"))
        from ml.assessment.m20_damage_assessment import infer as m20_infer  # noqa: F401
        self.assertTrue(callable(m20_infer.assess))

    def test_m20_assess_with_satellite_data(self):
        print(_smoke_banner("M20"))
        from ml.assessment.m20_damage_assessment.infer import assess
        from ml.assessment.m20_damage_assessment.schema import (
            M20DamageInput, M20DamageOutput, SatelliteObservation
        )
        sat = SatelliteObservation(
            ndvi_pre=0.55,
            ndvi_post=0.25,
            ndwi_pre=-0.10,
            ndwi_post=0.40,
            sar_coherence_pre=0.80,
            sar_coherence_post=0.35,
        )
        inp = M20DamageInput(
            asset_id="SYNTH_BRIDGE_NH3_01",
            hazard_type="FLOOD",
            satellite=sat,
            flood_depth_m=2.0,
            flow_velocity_ms=3.5,
            asset_category="bridge",
            data_quality=0.88,
        )
        result = assess(inp)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, M20DamageOutput)

    def test_m20_output_schema(self):
        print(_smoke_banner("M20"))
        from ml.assessment.m20_damage_assessment.infer import assess
        from ml.assessment.m20_damage_assessment.schema import (
            M20DamageInput, M20DamageOutput, SatelliteObservation
        )
        sat = SatelliteObservation(
            ndvi_pre=0.55,
            ndvi_post=0.25,
            ndwi_pre=-0.10,
            ndwi_post=0.40,
            sar_coherence_pre=0.80,
            sar_coherence_post=0.35,
        )
        inp = M20DamageInput(
            asset_id="SYNTH_ROAD_NH3_01",
            hazard_type="COMPOUND",
            satellite=sat,
            flood_depth_m=1.5,
            asset_category="road",
            data_quality=0.90,
        )
        result = assess(inp)
        self.assertIsInstance(result.damage_probability, float)
        self.assertGreaterEqual(result.damage_probability, 0.0)
        self.assertLessEqual(result.damage_probability, 1.0)
        self.assertIsInstance(result.change_detected, bool)
        self.assertIn(result.external_validation_note,
                      ("EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE",))

    def test_m20_physics_only_path(self):
        """Test M20 with physics inputs only (no satellite obs)."""
        print(_smoke_banner("M20"))
        from ml.assessment.m20_damage_assessment.infer import assess
        from ml.assessment.m20_damage_assessment.schema import (
            M20DamageInput, SatelliteObservation
        )
        inp = M20DamageInput(
            asset_id="SYNTH_BUILDING_01",
            hazard_type="LANDSLIDE",
            satellite=SatelliteObservation(),   # all None
            flood_depth_m=None,
            flow_velocity_ms=None,
            landslide_runout_m=80.0,
            asset_category="building",
            data_quality=0.75,
        )
        result = assess(inp)
        self.assertIsNotNone(result.damage_class)

    def test_m20_degraded_input(self):
        print(_smoke_banner("M20"))
        from ml.assessment.m20_damage_assessment.infer import assess
        from ml.assessment.m20_damage_assessment.schema import (
            M20DamageInput, SatelliteObservation, AssessmentStatus
        )
        inp = M20DamageInput(
            asset_id="SYNTH_CORRUPT_ASSET",
            hazard_type="FLOOD",
            satellite=SatelliteObservation(),
            data_quality=0.10,   # below 0.30 threshold
        )
        result = assess(inp)
        self.assertEqual(result.status, AssessmentStatus.DEGRADED_INPUT)
        self.assertEqual(result.damage_probability, 0.0)


# ===========================================================================
# M8 — Ground-Movement & Slope Deformation Forecast  (frozen artifact)
# ===========================================================================

class TestM8DeformationSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M8 Deformation Forecast"""

    _SYNTH_FEATURES = {
        "sensor_or_pixel_id": "SYNTH_INSAR_PIXEL_01",
        "latitude": 32.18,
        "longitude": 77.20,
        "elevation_m": 2800.0,
        "slope_deg": 32.0,
        "current_displacement_mm": 12.5,
        "cumulative_displacement_mm": 45.0,
        "velocity_mm_day": 3.5,
        "acceleration_mm_day2": 0.8,
        "rainfall_72h_mm": 90.0,
        "insar_coherence": 0.65,
        "tilt_rate_deg_day": 0.05,
        "crack_width_rate_mm_day": 0.2,
    }

    def test_m8_import(self):
        print(_smoke_banner("M8"))
        from ml.landslide.m8_deformation import infer as m8_infer  # noqa: F401
        self.assertTrue(callable(m8_infer.predict))

    def test_m8_predict_returns_dict(self):
        print(_smoke_banner("M8"))
        from ml.landslide.m8_deformation.infer import predict
        result = predict(self._SYNTH_FEATURES)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_m8_output_schema(self):
        print(_smoke_banner("M8"))
        from ml.landslide.m8_deformation.infer import predict
        result = predict(self._SYNTH_FEATURES)
        for key in ("prediction", "confidence", "uncertainty", "data_quality",
                    "model_version", "applicability"):
            self.assertIn(key, result, f"M8 output missing key: {key}")
        pred = result["prediction"]
        for key in ("movement_regime", "horizon_forecasts"):
            self.assertIn(key, pred, f"M8 prediction missing key: {key}")


# ===========================================================================
# M6 / M7 — Landslide Susceptibility & Trigger  (frozen joblib artifacts)
# ===========================================================================

class TestM6M7LandslideSmoke(unittest.TestCase):
    """SYNTHETIC SMOKE TEST · M6 Landslide Susceptibility & M7 Trigger (joblib)"""

    _LANDSLIDE_DIR = REPO_ROOT / "ml" / "landslide"

    def test_m6_artifact_loadable(self):
        """M6 joblib artifact can be loaded without error."""
        print(_smoke_banner("M6"))
        import joblib
        model_path = self._LANDSLIDE_DIR / "m6_landslide_susceptibility.joblib"
        self.assertTrue(model_path.exists(),
                        f"M6 artifact not found at {model_path}")
        model = joblib.load(model_path)
        self.assertIsNotNone(model)

    def test_m6_predict_synthetic(self):
        """M6 produces a numeric output for synthetic terrain features."""
        print(_smoke_banner("M6"))
        import joblib
        import numpy as np
        model_path = self._LANDSLIDE_DIR / "m6_landslide_susceptibility.joblib"
        model = joblib.load(model_path)
        # Features: elevation, slope, aspect, curvature, lithology, dist_to_stream, land_cover
        cols = getattr(model, "feature_names_in_", None)
        if cols is not None:
            import pandas as pd
            X_synth = pd.DataFrame([[2200.0, 35.0, 180.0, -0.005, 3, 120.0, 2]], columns=cols)
        else:
            X_synth = np.array([[2200.0, 35.0, 180.0, -0.005, 3, 120.0, 2]])
        pred = model.predict(X_synth)
        self.assertEqual(len(pred), 1)
        self.assertIn(int(pred[0]), [0, 1, 2])   # susceptibility class

    def test_m7_artifact_loadable(self):
        """M7 joblib artifact can be loaded without error."""
        print(_smoke_banner("M7"))
        import joblib
        model_path = self._LANDSLIDE_DIR / "m7_landslide_trigger.joblib"
        self.assertTrue(model_path.exists(),
                        f"M7 artifact not found at {model_path}")
        model = joblib.load(model_path)
        self.assertIsNotNone(model)

    def test_m7_predict_synthetic(self):
        """M7 produces a 0/1 output for synthetic trigger features."""
        print(_smoke_banner("M7"))
        import joblib
        import numpy as np
        model_path = self._LANDSLIDE_DIR / "m7_landslide_trigger.joblib"
        model = joblib.load(model_path)
        # Features: susceptibility_class, slope, rainfall_1h, antecedent_rain_3d, soil_moisture
        cols = getattr(model, "feature_names_in_", getattr(model, "feature_name_", None))
        if cols is not None:
            import pandas as pd
            X_synth = pd.DataFrame([[2, 38.0, 25.0, 95.0, 82.0]], columns=cols)
        else:
            X_synth = np.array([[2, 38.0, 25.0, 95.0, 82.0]])
        pred = model.predict(X_synth)
        self.assertEqual(len(pred), 1)
        self.assertIn(int(pred[0]), [0, 1])


# ===========================================================================
# End-to-end CHAIN test — synthetic values flow through models in sequence
# ===========================================================================

class TestPipelineChainSmoke(unittest.TestCase):
    """
    SYNTHETIC SMOKE TEST · Full Pipeline Chain
    M1 → M2 → M9 → M10 → M11 → M12 → M13 → M14 → M17 → M18 → M19 → M20

    Each model's synthetic output is used to populate the next model's input.
    No real observations are used at any stage.
    THIS IS NOT VALIDATION EVIDENCE.
    """

    def test_full_pipeline_chain(self):
        print(_smoke_banner("FULL CHAIN"))

        # --- M1: Rainfall nowcast ---
        from ml.rainfall.m1_nowcast.infer import predict as m1_predict
        m1_features = {
            "station_id": "CHAIN_AWS_01",
            "latitude": 32.20,
            "longitude": 77.18,
            "elevation_m": 2000.0,
            "slope_deg": 20.0,
            "r_1h": 35.0,
            "r_3h": 80.0,
            "r_6h": 110.0,
            "rolling_intensity_mmh": 35.0,
        }
        m1_out = m1_predict(m1_features)
        self.assertIn("prediction", m1_out)
        m1_pred = m1_out["prediction"]
        rainfall_intensity = m1_pred["predicted_rainfall_mm"]
        extreme_rain_prob = m1_pred["extreme_rain_probability"]

        # --- M2: Flood risk ---
        from ml.flood.predict_m2_flood import FloodRiskPredictor
        m2_predictor = FloodRiskPredictor()
        m2_features = {
            "elevation": 900.0,
            "slope": 4.0,
            "flow_accumulation": 3000.0,
            "dist_to_stream": 60.0,
            "land_cover": 4,
            "rainfall_1h": max(rainfall_intensity, 0.0),
            "rainfall_3h": max(rainfall_intensity * 2.5, 0.0),
            "rainfall_6h": max(rainfall_intensity * 4.0, 0.0),
            "rainfall_24h": max(rainfall_intensity * 8.0, 0.0),
            "antecedent_rain_3d": 90.0,
            "soil_moisture": 75.0,
            "river_level": 5.8,
            "river_level_change_1h": 0.25,
        }
        m2_out = m2_predictor.predict_point(m2_features)
        self.assertIn("flood_probability", m2_out)
        flood_prob = m2_out["flood_probability"]

        # --- M9: Sensor anomaly (quality check) ---
        from ml.anomaly.m9_sensor.infer import predict as m9_predict
        m9_features = {
            "station_id": "CHAIN_IOT_01",
            "timestamp_utc": "2026-09-21T03:30:00Z",
            "rainfall_rate_mmh": rainfall_intensity,
            "water_level_m": 5.8,
            "soil_moisture_pct": 75.0,
            "tilt_deg": 0.3,
            "pore_pressure_kpa": 30.0,
            "temperature_c": 16.0,
        }
        m9_out = m9_predict(m9_features)
        self.assertIn("prediction", m9_out)
        sensor_valid = m9_out["prediction"]["is_valid_reading"]

        # --- M10: Water level forecast ---
        from ml.flood.m10_water_level.infer import predict as m10_predict
        m10_features = {
            "station_id": "CWC_CHAIN_01",
            "station_name": "Chain Gauge Station",
            "latitude": 31.95,
            "longitude": 77.10,
            "elevation_m": 1200.0,
            "current_stage_m": 5.8,
            "rate_of_rise_m_hr": 0.25,
            "rainfall_1h_mm": rainfall_intensity,
            "rainfall_3h_mm": rainfall_intensity * 2.5,
        }
        m10_out = m10_predict(m10_features)
        self.assertIn("prediction", m10_out)
        forecasted_stage = m10_out["prediction"]["forecasted_stage_m"]

        # --- M11: Flood depth ---
        from ml.flood.m11_flood_depth.infer import predict as m11_predict
        m11_features = {
            "source_stage_m": forecasted_stage,
            "source_discharge_m3s": 900.0,
        }
        m11_out = m11_predict(m11_features)
        self.assertIn("prediction", m11_out)
        flood_depth = m11_out["prediction"]["forecasted_depth_m"]
        wave_arrival = m11_out["prediction"]["flood_wave_arrival_time_min"]

        # --- M12: Cascade ---
        from ml.flood.m12_cascade.infer import predict as m12_predict
        m12_features = {
            "dam_location": "CHAIN_LandslidePoint",
            "dam_height_m": 28.0,
            "impounded_volume_m3": 4_000_000.0,
            "normal_river_discharge_m3s": 350.0,
            "trigger_type": "LANDSLIDE_DAM",
            "trigger_probability": 0.80,
        }
        m12_out = m12_predict(m12_features)
        self.assertIn("prediction", m12_out)
        peak_outflow = m12_out["prediction"]["peak_outflow_discharge_m3s"]

        # --- M13: Vulnerability ---
        from ml.decision.m13_vulnerability.infer import predict_vulnerability_exposure
        from ml.decision.m13_vulnerability.schema import M13ExposureInput
        from ml.decision.m13_vulnerability.demographics import BEAS_SETTLEMENT_REGISTER
        sid = next(iter(BEAS_SETTLEMENT_REGISTER.keys()))
        m13_inp = M13ExposureInput(
            settlement_id=sid,
            month=7,
            flood_prob=flood_prob,
            flood_depth_m=flood_depth,
            landslide_prob=0.30,
            debris_flow_prob=0.20,
            river_distance_m=100.0,
        )
        m13_out = predict_vulnerability_exposure(m13_inp)
        self.assertIsNotNone(m13_out)
        at_risk_pop = m13_out.total_exposed_population

        # --- M14: Infrastructure loss ---
        from ml.decision.m14_infrastructure_loss.infer import predict_infrastructure_loss
        from ml.decision.m14_infrastructure_loss.schema import M14DamageInput
        from ml.decision.m14_infrastructure_loss.assets import BEAS_INFRASTRUCTURE_ASSETS
        asset_id = next(iter(BEAS_INFRASTRUCTURE_ASSETS.keys()))
        m14_inp = M14DamageInput(
            asset_id=asset_id,
            flood_depth_m=flood_depth,
            flow_velocity_ms=2.5,
            debris_impact_flag=True,
            inundation_duration_hours=4.0,
        )
        m14_out = predict_infrastructure_loss(m14_inp)
        self.assertIsNotNone(m14_out)
        road_blocked = m14_out.lifeline_status.value in (
            "IMPASSABLE_CUT_OFF", "STRUCTURALLY_FAILED"
        )

        # --- M17: Warning gating ---
        from ml.decision.m17_warning_gating.infer import issue_early_warning_and_evacuation
        from ml.decision.m17_warning_gating.schema import M17WarningInput
        m17_inp = M17WarningInput(
            reach_or_settlement_id=sid,
            rainfall_intensity_mmh=rainfall_intensity,
            rainfall_3h_mm=rainfall_intensity * 2.5,
            flood_probability=flood_prob,
            river_water_level_m=forecasted_stage,
            warning_level_m=5.0,
            danger_level_m=7.0,
            hfl_m=9.5,
            flood_depth_m=flood_depth,
            flood_arrival_time_min=wave_arrival,
            landslide_probability=0.30,
            natural_dam_outburst_discharge_m3s=peak_outflow,
            at_risk_population=at_risk_pop,
            arterial_road_blocked=road_blocked,
        )
        m17_out = issue_early_warning_and_evacuation(m17_inp)
        self.assertIsNotNone(m17_out.alert_level)

        # --- M18: Calibration ---
        from ml.calibration.m18_calibration.infer import calibrate
        from ml.calibration.m18_calibration.schema import M18CalibrationInput
        m18_inp = M18CalibrationInput(
            source_model="M2_FLOOD_RISK",
            raw_probability=flood_prob,
            data_quality=0.85,
        )
        m18_out = calibrate(m18_inp)
        calibrated_prob = m18_out.calibrated_probability
        self.assertGreaterEqual(calibrated_prob, 0.0)
        self.assertLessEqual(calibrated_prob, 1.0)

        # --- M19: Time-to-impact ---
        from ml.impact.m19_time_to_impact.infer import predict as m19_predict
        from ml.impact.m19_time_to_impact.schema import (
            M19TimeToImpactInput, ImpactType
        )
        m19_inp = M19TimeToImpactInput(
            impact_type=ImpactType.FLOOD_INUNDATION,
            distance_km=12.0,
            peak_discharge_m3s=peak_outflow,
            channel_slope_pct=1.8,
            floodplain_width_m=280.0,
            soil_saturation_ratio=0.75,
            data_quality=0.80,
        )
        m19_out = m19_predict(m19_inp)
        self.assertGreater(m19_out.p50_minutes, 0.0)

        # --- M20: Damage assessment ---
        from ml.assessment.m20_damage_assessment.infer import assess
        from ml.assessment.m20_damage_assessment.schema import (
            M20DamageInput, SatelliteObservation
        )
        sat = SatelliteObservation(
            ndvi_pre=0.50,
            ndvi_post=0.22,
            ndwi_pre=-0.05,
            ndwi_post=0.38,
            sar_coherence_pre=0.78,
            sar_coherence_post=0.30,
        )
        m20_inp = M20DamageInput(
            asset_id=asset_id,
            hazard_type="FLOOD",
            satellite=sat,
            flood_depth_m=flood_depth,
            flow_velocity_ms=2.5,
            asset_category="bridge",
            data_quality=0.85,
        )
        m20_out = assess(m20_inp)
        self.assertIsNotNone(m20_out.damage_class)
        self.assertGreaterEqual(m20_out.damage_probability, 0.0)
        self.assertLessEqual(m20_out.damage_probability, 1.0)

        print(
            f"\n[SYNTHETIC SMOKE TEST] CHAIN SUMMARY (NOT VALIDATION EVIDENCE)\n"
            f"  M1  rainfall_mm      = {rainfall_intensity:.2f}\n"
            f"  M1  extreme_rain_p   = {extreme_rain_prob:.3f}\n"
            f"  M2  flood_prob       = {flood_prob:.3f}\n"
            f"  M9  sensor_valid     = {sensor_valid}\n"
            f"  M10 forecasted_stage = {forecasted_stage:.2f} m\n"
            f"  M11 flood_depth      = {flood_depth:.2f} m\n"
            f"  M12 peak_outflow     = {peak_outflow:.1f} m³/s\n"
            f"  M13 at_risk_pop      = {at_risk_pop}\n"
            f"  M14 road_blocked     = {road_blocked}\n"
            f"  M17 alert_level      = {m17_out.alert_level}\n"
            f"  M18 calib_prob       = {calibrated_prob:.3f}\n"
            f"  M19 p50_minutes      = {m19_out.p50_minutes:.1f}\n"
            f"  M20 damage_class     = {m20_out.damage_class}\n"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
