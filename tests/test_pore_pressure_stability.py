"""Unit and integration tests for Pore-Water Pressure and Slope Stability layer.

Tests physical mechanics, parameter bounds, sensor QA, data leakage,
M7 integration experiment, GeoTIFF raster generation, and timeseries animation.
"""

import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
import tifffile

from ml.landslide.pore_pressure import (
    DATA_AVAILABILITY_AUDIT,
    HYDROLOGICAL_ENGINEERED_FEATURES,
    M7_BASELINE_FEATURES,
    M7_EXTENDED_FEATURES,
    MANDATORY_SCIENTIFIC_DISCLAIMER,
    GeotechnicalParameters,
    HydrologicalFeaturePipeline,
    PiezometerReading,
    PorePressureOutput,
    PoreWaterPressureEstimator,
    SensorQualityAuditor,
    SlopeStabilityEngine,
    SlopeStabilityOutput,
    TensiometerReading,
    compare_model_with_sensor,
    compute_apparent_cohesion,
    compute_effective_normal_stress,
    compute_hydrostatic_pore_pressure,
    compute_infinite_slope_fos,
    compute_matric_suction,
    compute_slope_stability_indicator,
    compute_transient_saturation_ratio,
    generate_spatial_geotiffs,
    generate_timeseries_animation_snapshots,
    run_data_leakage_audit,
    run_m7_integration_experiment,
)


class TestPorePressurePhysics(unittest.TestCase):
    """Verifies limit-equilibrium equations and Terzaghi mechanics."""

    def setUp(self):
        self.params = GeotechnicalParameters()

    def test_effective_stress_non_negative(self):
        # Normal case
        eff = compute_effective_normal_stress(total_stress_kpa=40.0, pore_pressure_kpa=15.0)
        self.assertAlmostEqual(eff, 25.0, places=4)

        # Artesian/excess pressure case: effective stress clipped to 0
        eff_clipped = compute_effective_normal_stress(total_stress_kpa=20.0, pore_pressure_kpa=35.0)
        self.assertEqual(eff_clipped, 0.0)

        # Array case
        tot_arr = np.array([50.0, 20.0, 10.0])
        u_arr = np.array([10.0, 30.0, 5.0])
        eff_arr = compute_effective_normal_stress(tot_arr, u_arr)
        np.testing.assert_array_almost_equal(eff_arr, np.array([40.0, 0.0, 5.0]))

    def test_hydrostatic_pore_pressure_on_slope(self):
        # Flat ground: theta=0 -> cos(0)=1 -> u = gamma_w * hw
        u_flat = compute_hydrostatic_pore_pressure(water_table_height_m=2.0, slope_deg=0.0)
        self.assertAlmostEqual(u_flat, 9.81 * 2.0, places=3)

        # Steeper slope: cos^2(theta) reduces normal hydrostatic pressure
        u_slope = compute_hydrostatic_pore_pressure(water_table_height_m=2.0, slope_deg=45.0)
        expected = 9.81 * 2.0 * (np.cos(np.radians(45.0)) ** 2)
        self.assertAlmostEqual(u_slope, expected, places=3)
        self.assertLess(u_slope, u_flat)

    def test_matric_suction_monotonic_decrease(self):
        # Dry soil (S=0.1) -> high suction
        psi_dry = compute_matric_suction(0.1, max_suction_kpa=50.0)
        # Moderate moisture (S=0.5)
        psi_mod = compute_matric_suction(0.5, max_suction_kpa=50.0)
        # Saturated (S=1.0) -> suction is zero
        psi_sat = compute_matric_suction(1.0, max_suction_kpa=50.0)

        self.assertGreater(psi_dry, psi_mod)
        self.assertGreater(psi_mod, psi_sat)
        self.assertAlmostEqual(float(psi_sat), 0.0, places=5)

    def test_apparent_cohesion_vanishes_at_zero_suction(self):
        c_app = compute_apparent_cohesion(matric_suction_kpa=0.0, phi_b_deg=15.0)
        self.assertAlmostEqual(float(c_app), 0.0, places=5)

        c_app_pos = compute_apparent_cohesion(matric_suction_kpa=20.0, phi_b_deg=15.0)
        self.assertGreater(float(c_app_pos), 0.0)

    def test_infinite_slope_fos_bounds_and_behavior(self):
        # Gentle slope: high stability (FoS > 1.5)
        fos_gentle = compute_infinite_slope_fos(slope_deg=12.0, pore_pressure_kpa=0.0, matric_suction_kpa=10.0)
        self.assertGreater(fos_gentle, 1.5)

        # Same slope under high pore pressure: FoS decreases
        fos_flooded = compute_infinite_slope_fos(slope_deg=12.0, pore_pressure_kpa=18.0, matric_suction_kpa=0.0)
        self.assertLess(fos_flooded, fos_gentle)

        # Extreme steep slope: FoS drops significantly
        fos_steep = compute_infinite_slope_fos(slope_deg=55.0, pore_pressure_kpa=15.0, matric_suction_kpa=0.0)
        self.assertLess(fos_steep, 1.0)

    def test_saturation_ratio_bounds_and_twi(self):
        # Extreme rain caps at 1.0
        m_storm = compute_transient_saturation_ratio(
            initial_moisture_pct=85.0,
            rainfall_1h_mm=120.0,
            antecedent_rain_3d_mm=200.0,
        )
        self.assertLessEqual(float(m_storm), 1.0)

        # Higher TWI converges more lateral moisture -> higher saturation
        m_low_twi = compute_transient_saturation_ratio(
            initial_moisture_pct=50.0,
            rainfall_1h_mm=30.0,
            antecedent_rain_3d_mm=60.0,
            twi=5.0,
        )
        m_high_twi = compute_transient_saturation_ratio(
            initial_moisture_pct=50.0,
            rainfall_1h_mm=30.0,
            antecedent_rain_3d_mm=60.0,
            twi=14.0,
        )
        self.assertGreater(float(m_high_twi), float(m_low_twi))

    def test_geotechnical_parameters_immutability(self):
        # Frozen dataclass prevents accidental tampering during inference
        with self.assertRaises(Exception):
            self.params.cohesion_kpa = 50.0  # type: ignore

    def test_slope_stability_indicator_bounds(self):
        # At FoS = 1.0, SSI must be exactly 0.50
        ssi_crit = compute_slope_stability_indicator(1.0)
        self.assertAlmostEqual(ssi_crit, 0.50, places=4)

        # Unstable slope (FoS = 0.5) -> SSI < 0.50
        ssi_fail = compute_slope_stability_indicator(0.5)
        self.assertAlmostEqual(ssi_fail, 0.5 / 1.5, places=4)
        self.assertLess(ssi_fail, 0.50)

        # Stable slope (FoS = 2.0) -> SSI > 0.50
        ssi_stable = compute_slope_stability_indicator(2.0)
        self.assertAlmostEqual(ssi_stable, 2.0 / 3.0, places=4)
        self.assertGreater(ssi_stable, 0.50)

        # Array strictly bounded in [0, 1]
        arr_fos = np.array([0.05, 0.5, 1.0, 2.5, 10.0])
        arr_ssi = compute_slope_stability_indicator(arr_fos)
        self.assertTrue(np.all(arr_ssi >= 0.0))
        self.assertTrue(np.all(arr_ssi <= 1.0))


class TestPorePressureModel(unittest.TestCase):
    """Tests spatial grid and point estimation models."""

    def setUp(self):
        self.estimator = PoreWaterPressureEstimator()
        self.engine = SlopeStabilityEngine()

    def test_grid_estimation_shapes_and_types(self):
        shape = (20, 25)
        slope = np.full(shape, 35.0, dtype=np.float32)
        moist = np.full(shape, 65.0, dtype=np.float32)
        r1h = np.full(shape, 30.0, dtype=np.float32)
        r3d = np.full(shape, 80.0, dtype=np.float32)

        out = self.estimator.estimate_grid(slope, moist, r1h, r3d)
        self.assertIsInstance(out, PorePressureOutput)
        self.assertEqual(out.pore_pressure_kpa.shape, shape)
        self.assertEqual(out.matric_suction_kpa.shape, shape)
        self.assertTrue(np.all(out.saturation_ratio >= 0.0))
        self.assertTrue(np.all(out.saturation_ratio <= 1.0))
        self.assertTrue(np.all(out.confidence_score >= 0.0))

        stab = self.engine.evaluate_grid(slope, out.pore_pressure_kpa, out.matric_suction_kpa)
        self.assertIsInstance(stab, SlopeStabilityOutput)
        self.assertEqual(stab.factor_of_safety.shape, shape)
        self.assertEqual(stab.slope_stability_indicator.shape, shape)
        self.assertEqual(stab.critical_failure_mask.shape, shape)

    def test_point_estimation_consistency(self):
        pt_pwp = self.estimator.estimate_point(slope_deg=30.0, moisture_pct=60.0, rainfall_1h_mm=20.0, antecedent_rain_3d_mm=50.0)
        self.assertIn("pore_pressure_kpa", pt_pwp)
        self.assertIn("delta_pore_pressure_kpa", pt_pwp)
        self.assertIn("confidence_score", pt_pwp)

        pt_stab = self.engine.evaluate_point(slope_deg=30.0, pore_pressure_kpa=pt_pwp["pore_pressure_kpa"], matric_suction_kpa=pt_pwp["matric_suction_kpa"])
        self.assertIn("factor_of_safety", pt_stab)
        self.assertIn("slope_stability_indicator", pt_stab)
        self.assertIn("stability_class", pt_stab)
        self.assertIn(pt_stab["stability_class"], ["STABLE", "MARGINAL", "CRITICAL"])


class TestSensorAuditor(unittest.TestCase):
    """Tests IoT sensor telemetry schema, quality control, and spike detection."""

    def setUp(self):
        self.auditor = SensorQualityAuditor()

    def test_normal_reading_passed(self):
        reading = PiezometerReading(
            sensor_id="PZ_MANALI_01",
            timestamp="2026-07-15T12:00:00Z",
            pore_pressure_kpa=14.5,
            depth_m=2.0,
            battery_v=3.6,
        )
        audited = self.auditor.audit_piezometer_reading(reading)
        self.assertEqual(audited.quality_flag, "GOOD")
        self.assertEqual(audited.pore_pressure_kpa, 14.5)

    def test_out_of_range_reading_rejected(self):
        reading = PiezometerReading(
            sensor_id="PZ_MANALI_01",
            timestamp="2026-07-15T12:00:00Z",
            pore_pressure_kpa=350.0,  # Exceeds max 250 kPa
        )
        audited = self.auditor.audit_piezometer_reading(reading)
        self.assertEqual(audited.quality_flag, "OUT_OF_RANGE")

    def test_spike_rate_of_change_flagged(self):
        r1 = PiezometerReading(
            sensor_id="PZ_KULLU_02",
            timestamp="2026-07-15T10:00:00Z",
            pore_pressure_kpa=10.0,
        )
        self.auditor.audit_piezometer_reading(r1)

        # 15 minutes later: unphysical jump of 35 kPa (> 25 kPa/hr)
        r2 = PiezometerReading(
            sensor_id="PZ_KULLU_02",
            timestamp="2026-07-15T10:15:00Z",
            pore_pressure_kpa=45.0,
        )
        audited_r2 = self.auditor.audit_piezometer_reading(r2)
        self.assertEqual(audited_r2.quality_flag, "SUSPECT_SPIKE")

    def test_low_battery_flagged(self):
        reading = PiezometerReading(
            sensor_id="PZ_MANALI_03",
            timestamp="2026-07-15T12:00:00Z",
            pore_pressure_kpa=12.0,
            battery_v=2.8,  # Below minimum 3.2V
        )
        audited = self.auditor.audit_piezometer_reading(reading)
        self.assertEqual(audited.quality_flag, "LOW_BATTERY")

    def test_calibration_offset(self):
        auditor = SensorQualityAuditor(calibration_offsets={"PZ_01": 2.5})
        reading = PiezometerReading(
            sensor_id="PZ_01",
            timestamp="2026-07-15T12:00:00Z",
            pore_pressure_kpa=12.5,
        )
        audited = auditor.audit_piezometer_reading(reading)
        self.assertAlmostEqual(audited.pore_pressure_kpa, 10.0, places=3)
        self.assertEqual(audited.raw_pressure_kpa, 12.5)

    def test_tensiometer_reading_schema(self):
        tens = TensiometerReading(
            sensor_id="TM_01",
            timestamp="2026-07-15T12:00:00Z",
            matric_suction_kpa=28.5,
            depth_m=1.0,
            temperature_c=18.5,
            quality_flag="GOOD",
        )
        d = tens.to_dict()
        self.assertEqual(d["sensor_id"], "TM_01")
        self.assertEqual(d["matric_suction_kpa"], 28.5)

    def test_data_availability_audit_completeness(self):
        # Must account for all variables (Real, Derived, Proxy, Modelled, Unavailable)
        self.assertIn("piezometer_ground_truth", DATA_AVAILABILITY_AUDIT)
        self.assertIn("pore_pressure_est_kpa", DATA_AVAILABILITY_AUDIT)
        self.assertIn("soil_moisture_pct", DATA_AVAILABILITY_AUDIT)
        self.assertTrue(DATA_AVAILABILITY_AUDIT["piezometer_ground_truth"].startswith("UNAVAILABLE"))
        self.assertTrue(DATA_AVAILABILITY_AUDIT["pore_pressure_est_kpa"].startswith("MODELLED"))
        self.assertTrue(DATA_AVAILABILITY_AUDIT["soil_moisture_pct"].startswith("PROXY"))

    def test_sensor_comparison_disclaimer(self):
        reading = PiezometerReading(
            sensor_id="PZ_01",
            timestamp="2026-07-15T12:00:00Z",
            pore_pressure_kpa=10.0,
            quality_flag="GOOD",
        )
        comp = compare_model_with_sensor(modelled_pore_pressure_kpa=12.0, reading=reading)
        self.assertEqual(comp["status"], "VALIDATED_SAMPLE")
        self.assertIn("Direct pore-water pressure validation data are currently unavailable.", comp["disclaimer"])


class TestFeaturePipelineAndLeakage(unittest.TestCase):
    """Tests feature generation dataframe enrichment and data leakage audits."""

    def test_extract_features_df(self):
        df_mock = pd.DataFrame({
            "slope_deg": [15.0, 35.0, 48.0],
            "rainfall_1h": [5.0, 25.0, 60.0],
            "antecedent_rain_3d": [20.0, 80.0, 120.0],
            "soil_moisture_pct": [35.0, 65.0, 88.0],
            "susceptibility_class": [0, 1, 2],
            "landslide_triggered": [0, 1, 1],
        })

        pipe = HydrologicalFeaturePipeline()
        df_enriched = pipe.extract_features_df(df_mock)

        for col in HYDROLOGICAL_ENGINEERED_FEATURES:
            self.assertIn(col, df_enriched.columns)

        self.assertEqual(len(df_enriched), len(df_mock))
        # Ensure values are non-negative / physically reasonable
        self.assertTrue(np.all(df_enriched["pore_pressure_est_kpa"] >= 0.0))
        self.assertTrue(np.all(df_enriched["slope_stability_indicator"] >= 0.0))
        self.assertTrue(np.all(df_enriched["slope_stability_indicator"] <= 1.0))

    def test_missing_column_raises_error(self):
        df_bad = pd.DataFrame({"slope_deg": [20.0], "rainfall_1h": [10.0]})
        pipe = HydrologicalFeaturePipeline()
        with self.assertRaises(ValueError):
            pipe.extract_features_df(df_bad)

    def test_leakage_audit_clean_pass(self):
        df_train = pd.DataFrame({
            "slope_deg": [10.0, 20.0],
            "rainfall_1h": [5.0, 15.0],
            "landslide_triggered": [0, 1],
        }, index=[0, 1])

        df_test = pd.DataFrame({
            "slope_deg": [30.0, 40.0],
            "rainfall_1h": [25.0, 35.0],
            "landslide_triggered": [1, 0],
        }, index=[2, 3])

        audit = run_data_leakage_audit(df_train, df_test, ["slope_deg", "rainfall_1h"], "landslide_triggered")
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["index_overlap_count"], 0)
        self.assertFalse(audit["target_in_features"])

    def test_leakage_audit_catches_target_in_features(self):
        df_train = pd.DataFrame({"feat": [1, 2], "target": [0, 1]}, index=[0, 1])
        df_test = pd.DataFrame({"feat": [3, 4], "target": [1, 0]}, index=[2, 3])

        # Target improperly included in features
        audit = run_data_leakage_audit(df_train, df_test, ["feat", "target"], "target")
        self.assertFalse(audit["passed"])
        self.assertTrue(audit["target_in_features"])


class TestM7IntegrationExperiment(unittest.TestCase):
    """Verifies that the M7 integration experiment runs correctly on the real dataset."""

    def test_experiment_execution_and_schema(self):
        dataset_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "upper_beas" / "upper_beas_landslide_dataset.csv"
        if not dataset_path.exists():
            self.skipTest(f"Dataset {dataset_path} not found")

        metrics = run_m7_integration_experiment(dataset_path=dataset_path, random_state=42)

        self.assertIn("baseline_m7", metrics)
        self.assertIn("extended_m7_hydrological", metrics)
        self.assertIn("delta", metrics)
        self.assertIn("data_leakage_audit", metrics)
        self.assertIn("data_availability_audit", metrics)
        self.assertIn("mandatory_disclaimer", metrics)

        self.assertTrue(metrics["data_leakage_audit"]["baseline"]["passed"])
        self.assertTrue(metrics["data_leakage_audit"]["extended"]["passed"])

        self.assertGreaterEqual(metrics["baseline_m7"]["roc_auc"], 0.80)
        self.assertGreaterEqual(metrics["extended_m7_hydrological"]["roc_auc"], 0.80)
        self.assertIn(MANDATORY_SCIENTIFIC_DISCLAIMER, metrics["mandatory_disclaimer"])


class TestGISAndTimeseriesExport(unittest.TestCase):
    """Tests GeoTIFF raster generation and temporal animation snapshot outputs."""

    def test_geotiff_raster_generation(self):
        out_files = generate_spatial_geotiffs()
        expected_files = [
            "pore_pressure_estimate_kpa.tif",
            "pore_pressure_change_kpa.tif",
            "slope_stability_indicator.tif",
            "modelled_infinite_slope_fos.tif",
            "landslide_risk_hydrological.tif",
        ]

        for fname in expected_files:
            self.assertIn(fname, out_files)
            fpath = out_files[fname]
            self.assertTrue(fpath.exists(), f"Missing exported GeoTIFF: {fpath}")

            # Verify raster properties
            data = tifffile.imread(str(fpath))
            self.assertEqual(data.dtype, np.float32)
            self.assertEqual(data.shape, (500, 400))
            self.assertFalse(np.isnan(data).any(), f"NaN values found in {fname}")

    def test_timeseries_animation_snapshots(self):
        manifest = generate_timeseries_animation_snapshots(shape=(100, 80))
        self.assertEqual(len(manifest["snapshots"]), 5)
        self.assertEqual(manifest["event_date"], "2023-07-09")
        self.assertIn("scientific_disclaimer", manifest)

        # Check monotonic pore-water pressure rise across storm timesteps
        u_t0 = manifest["snapshots"][0]["mean_pore_pressure_kpa"]
        u_t30 = manifest["snapshots"][2]["mean_pore_pressure_kpa"]
class TestPhysicalEdgeCasesAndMonotonicity(unittest.TestCase):
    """Verifies strict physical monotonicity, unit consistency, and edge-case behavior."""

    def setUp(self):
        self.params = GeotechnicalParameters()
        self.estimator = PoreWaterPressureEstimator(self.params)
        self.engine = SlopeStabilityEngine(self.params)

    def test_dry_condition_zero_pore_pressure(self):
        # Bone-dry soil with 0 rainfall should have 0 pore water pressure and positive suction
        out = self.estimator.estimate_point(
            slope_deg=35.0,
            surface_moisture_proxy_pct=15.0,
            rainfall_1h_mm=0.0,
            antecedent_rain_3d_mm=0.0,
        )
        # Saturated water table does not emerge without sufficient water
        # At very low saturation (15% moisture), pore pressure is minimal (<2 kPa)
        self.assertLessEqual(out["delta_pore_pressure_kpa"], 0.05)
        self.assertGreater(out["matric_suction_kpa"], 25.0)

    def test_saturated_condition_reduces_effective_stress(self):
        tot_stress = 40.0
        eff_dry = compute_effective_normal_stress(tot_stress, pore_pressure_kpa=0.0)
        eff_partial = compute_effective_normal_stress(tot_stress, pore_pressure_kpa=10.0)
        eff_high = compute_effective_normal_stress(tot_stress, pore_pressure_kpa=25.0)

        self.assertGreater(eff_dry, eff_partial)
        self.assertGreater(eff_partial, eff_high)

    def test_stability_decreases_with_increasing_pore_pressure(self):
        slope = 30.0
        fos_low_u = compute_infinite_slope_fos(slope_deg=slope, pore_pressure_kpa=2.0, matric_suction_kpa=10.0, params=self.params)
        fos_med_u = compute_infinite_slope_fos(slope_deg=slope, pore_pressure_kpa=8.0, matric_suction_kpa=5.0, params=self.params)
        fos_high_u = compute_infinite_slope_fos(slope_deg=slope, pore_pressure_kpa=16.0, matric_suction_kpa=0.0, params=self.params)

        self.assertGreater(fos_low_u, fos_med_u)
        self.assertGreater(fos_med_u, fos_high_u)

    def test_rainfall_monotonicity_increases_pore_pressure(self):
        # Identical terrain and initial moisture; increasing rainfall must not decrease pore pressure
        u_10 = self.estimator.estimate_point(slope_deg=30.0, surface_moisture_proxy_pct=50.0, rainfall_1h_mm=10.0, antecedent_rain_3d_mm=30.0)["pore_pressure_kpa"]
        u_40 = self.estimator.estimate_point(slope_deg=30.0, surface_moisture_proxy_pct=50.0, rainfall_1h_mm=40.0, antecedent_rain_3d_mm=30.0)["pore_pressure_kpa"]
        u_80 = self.estimator.estimate_point(slope_deg=30.0, surface_moisture_proxy_pct=50.0, rainfall_1h_mm=80.0, antecedent_rain_3d_mm=30.0)["pore_pressure_kpa"]

        self.assertLessEqual(u_10, u_40)
        self.assertLessEqual(u_40, u_80)

    def test_numerical_safety_no_nan_or_inf(self):
        # Extreme terrain inputs: near zero slope, near vertical slope, negative values, extreme rain
        slopes = np.array([0.0, 0.1, 45.0, 89.9, 90.0], dtype=np.float32)
        moists = np.array([0.0, 20.0, 50.0, 99.0, 100.0], dtype=np.float32)
        r1h = np.array([0.0, 10.0, 100.0, 300.0, 500.0], dtype=np.float32)
        r3d = np.array([0.0, 20.0, 150.0, 400.0, 800.0], dtype=np.float32)

        out = self.estimator.estimate_grid(slopes, moisture_pct=moists, rainfall_1h_mm=r1h, antecedent_rain_3d_mm=r3d)
        self.assertFalse(np.isnan(out.pore_pressure_kpa).any())
        self.assertFalse(np.isinf(out.pore_pressure_kpa).any())
        self.assertFalse(np.isnan(out.matric_suction_kpa).any())
        self.assertFalse(np.isinf(out.matric_suction_kpa).any())

        stab = self.engine.evaluate_grid(slopes, out.pore_pressure_kpa, out.matric_suction_kpa)
        self.assertFalse(np.isnan(stab.factor_of_safety).any())
        self.assertFalse(np.isinf(stab.factor_of_safety).any())
        self.assertFalse(np.isnan(stab.slope_stability_indicator).any())
        self.assertFalse(np.isinf(stab.slope_stability_indicator).any())


if __name__ == "__main__":
    unittest.main()
