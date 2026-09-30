"""
tests/test_phase2_real_data.py
==============================
Comprehensive Unit & Integration Test Suite for FLOODY SHIELD v3.1 Phase 2.
Verifies:
  1. GPM IMERG and IMD AWS rainfall adapters (spatial bounding, sensor limits).
  2. CWC river stage & discharge telemetry (rate of rise, statutory marks).
  3. Satellite flood mask distinction (OBSERVED vs PROXY).
  4. Landslide inventory & M6 non-proxy stable-slope control framework.
  5. M7 1-storm=1-event independence & catalog separation.
  6. InSAR & GNSS deformation velocity / acceleration calculations.
  7. Infrastructure & observed damage loaders (VALUE_UNAVAILABLE handling).
  8. M19 verified impact timestamp chronological ordering.
  9. Real-time data quality freshness & latency gates (FRESH vs STALE vs EXPIRED).
  10. Model input gate blocking on CRITICAL_ERROR and confidence scaling on DEGRADED.
  11. Distribution drift detector (PSI and KS statistic).
  12. Human authorization boundary & cryptographic sign-off for emergency alerts.
  13. Dashboard API contract data schema.
"""

import datetime
import pytest
import numpy as np

# Ingestion adapters
from ml.data_ingestion.manifest import DatasetManifest, create_manifest_for_file
from ml.data_ingestion.rainfall.gpm_imerg import GPMIMERGAdapter
from ml.data_ingestion.rainfall.imd_aws import IMDAWSAdapter
from ml.data_ingestion.river.cwc_river import CWCRiverAdapter
from ml.data_ingestion.flood.satellite_flood import SatelliteFloodAdapter, FloodMaskType
from ml.data_ingestion.landslide.inventory_loader import LandslideInventoryLoader
from ml.data_ingestion.landslide.stable_controls import StableControlFramework
from ml.data_ingestion.landslide.storm_catalog import StormLandslideCatalog
from ml.data_ingestion.deformation.insar_gnss import InSARDeformationLoader
from ml.data_ingestion.exposure.infrastructure import InfrastructureAssetLoader
from ml.data_ingestion.exposure.damage import ObservedDamageLoader, DamageEvidenceType
from ml.data_ingestion.exposure.impact_timestamps import ImpactTimestampLoader

# Quality, drift, security, validation
from ml.data_quality.schema import QualityStatus, FreshnessStatus
from ml.data_quality.validator import DataQualityValidator
from ml.data_quality.input_gate import ModelInputGate
from ml.monitoring.drift_detector import DistributionDriftMonitor
from ml.security.human_authorization import HumanAuthorizationGateway, AuthorizedAgency, AuthorizationStatus
from ml.security.dashboard_contract import DashboardPayloadContract, ValueTruthStatus
from ml.validation.real_data.validation_pipeline import ExternalValidationPipeline, clopper_pearson_ci


class TestPhase2DataIngestion:

    def test_gpm_imerg_adapter_spatial_and_range(self):
        adapter = GPMIMERGAdapter()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Valid reading inside Upper Beas (Manali: 32.24N, 77.18E)
        valid_raw = {
            "timestamp": now_iso,
            "latitude": 32.24,
            "longitude": 77.18,
            "rainfall_mm": 15.5,
        }
        rec, err = adapter.parse_record(valid_raw)
        assert rec is not None
        assert rec.quality_flag == "VALID"
        assert rec.rainfall_mm == 15.5
        assert err is None

        # Out-of-bounds reading (Delhi: 28.61N, 77.20E)
        oob_raw = {
            "timestamp": now_iso,
            "latitude": 28.61,
            "longitude": 77.20,
            "rainfall_mm": 5.0,
        }
        rec_oob, err_oob = adapter.parse_record(oob_raw)
        assert rec_oob.quality_flag == "OUT_OF_BOUNDS"
        assert "outside Upper Beas AOI" in err_oob

    def test_imd_aws_adapter_and_stations(self):
        adapter = IMDAWSAdapter()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Ingest batch with known stations
        batch = [
            {"station_id": "IMD_MANALI", "timestamp": now_iso, "rainfall_1h_mm": 22.4, "temperature_c": 18.5},
            {"station_id": "IMD_KULLU", "timestamp": now_iso, "rainfall_1h_mm": 12.0, "temperature_c": 24.0},
            {"station_id": "INVALID_STATION", "timestamp": now_iso, "latitude": 10.0, "longitude": 10.0, "rainfall_1h_mm": 5.0},
        ]
        res = adapter.ingest_batch(batch)
        assert res["total_records"] == 3
        assert res["valid_records_count"] == 2
        assert res["error_count"] == 1

    def test_cwc_river_adapter_statutory_thresholds_and_rate(self):
        adapter = CWCRiverAdapter()
        t0 = "2026-07-10T10:00:00+00:00"
        t1 = "2026-07-10T11:00:00+00:00"

        # Reading 1: Normal level at Kullu
        r1, _ = adapter.parse_gauge_reading({
            "station_id": "CWC_KULLU",
            "timestamp": t0,
            "water_level_m": 6.5,
        })
        assert r1.status_indicator == "NORMAL"
        assert r1.quality_flag == "VALID"

        # Reading 2: Rapid surge above Danger Level (10.0m at Kullu)
        r2, _ = adapter.parse_gauge_reading({
            "station_id": "CWC_KULLU",
            "timestamp": t1,
            "water_level_m": 11.2,
        }, previous_reading=r1)
        assert r2.status_indicator == "ABOVE_DANGER"
        assert r2.rate_of_rise_mh == pytest.approx(4.7, 0.1)
        assert r2.quality_flag == "RATE_EXCEEDED"

    def test_satellite_flood_mask_typing(self):
        adapter = SatelliteFloodAdapter()
        scene = adapter.register_scene(
            event_id="BEAS_JULY_2023",
            acquisition_time="2023-07-10T04:30:00+00:00",
            satellite="Sentinel-1A",
            sensor="C-SAR",
            orbit_direction="DESCENDING",
            relative_orbit=136,
            crs="EPSG:32643",
            resolution_m=10.0,
            bbox={"min_lat": 31.8, "max_lat": 32.3, "min_lon": 77.0, "max_lon": 77.3},
            mask_type=FloodMaskType.OBSERVED_FLOOD_MASK,
            total_area_km2=450.0,
            inundated_area_km2=42.5,
        )
        assert scene.mask_type == FloodMaskType.OBSERVED_FLOOD_MASK
        assert scene.water_fraction == pytest.approx(42.5 / 450.0, 0.001)
        assert scene.quality_flag == "VALID"

    def test_m6_stable_controls_rejects_built_proxies(self):
        framework = StableControlFramework()

        # Candidate 1: Cultural building (temple on ridge) without slope data -> MUST BE REJECTED
        candidate_temple = {
            "control_id": "CTRL_TEMPLE_01",
            "latitude": 31.95,
            "longitude": 77.12,
            "elevation_m": 1400.0,
            "slope_angle_deg": 25.0,
            "failure_absence_evidence": "Ancient stone temple intact since 1905 disaster",
            "monitoring_method": "FIELD_GEOTECHNICAL_AUDIT",
            "max_measured_velocity_mm_yr": 2.0,
        }
        rec, err = framework.validate_control_candidate(candidate_temple)
        assert rec is None
        assert "PROXY_REJECTION" in err

        # Candidate 2: Valid InSAR verified stable rock slope -> MUST BE ACCEPTED
        candidate_insar = {
            "control_id": "CTRL_INSAR_ROCK_01",
            "latitude": 31.95,
            "longitude": 77.12,
            "elevation_m": 1400.0,
            "slope_angle_deg": 32.0,
            "aspect_deg": 180.0,
            "lithology_class": "Gneissic Bedrock",
            "failure_absence_evidence": "Sentinel-1 InSAR multi-temporal coherence verified zero scarp formation",
            "monitoring_method": "INSAR_COHERENCE",
            "max_measured_velocity_mm_yr": 1.5,
        }
        rec2, err2 = framework.validate_control_candidate(candidate_insar)
        assert rec2 is not None
        assert rec2.quality_flag == "VALID"
        assert err2 is None

    def test_m7_storm_catalog_preserves_1storm_1event(self):
        cat = StormLandslideCatalog(min_separation_days=5.0)
        episodes = [
            {
                "storm_id": "STORM_2023_01",
                "start_time": "2023-07-08T00:00:00+00:00",
                "end_time": "2023-07-11T12:00:00+00:00",
                "rainfall_total_mm": 280.0,
                "peak_intensity_mmh": 45.0,
                "landslide_count": 48,
            },
            {
                "storm_id": "STORM_2023_02_CLOSE",  # Only 2 days after previous storm
                "start_time": "2023-07-13T00:00:00+00:00",
                "end_time": "2023-07-14T12:00:00+00:00",
                "rainfall_total_mm": 40.0,
                "peak_intensity_mmh": 12.0,
                "landslide_count": 0,
            },
            {
                "storm_id": "STORM_2023_03_INDEPENDENT",  # 20 days later
                "start_time": "2023-08-05T00:00:00+00:00",
                "end_time": "2023-08-07T12:00:00+00:00",
                "rainfall_total_mm": 110.0,
                "peak_intensity_mmh": 28.0,
                "landslide_count": 5,
            },
        ]
        res = cat.ingest_catalog(episodes)
        assert res["valid_independent_episodes"] == 3
        assert len(res["temporal_overlaps_flagged"]) == 1
        assert res["triggered_storms_count"] == 2
        assert res["non_triggered_control_storms_count"] == 1

    def test_insar_deformation_velocity_and_acceleration(self):
        loader = InSARDeformationLoader()
        samples = [
            {"timestamp": "2023-05-01T00:00:00+00:00", "los_displacement_mm": 10.0, "coherence": 0.8},
            {"timestamp": "2023-05-13T00:00:00+00:00", "los_displacement_mm": 22.0, "coherence": 0.8},  # +12mm in 12 days -> 1.0 mm/day
            {"timestamp": "2023-05-25T00:00:00+00:00", "los_displacement_mm": 46.0, "coherence": 0.8},  # +24mm in 12 days -> 2.0 mm/day (acc = +1/12)
        ]
        res = loader.parse_time_series("SITE_01", lat=32.1, lon=77.15, elevation_m=1600.0, raw_samples=samples)
        assert res["valid_coherent_points"] == 3
        pts = res["points"]
        assert pts[1]["velocity_mm_day"] == pytest.approx(1.0, 0.05)
        assert pts[2]["velocity_mm_day"] == pytest.approx(2.0, 0.05)
        assert pts[2]["acceleration_mm_day2"] > 0.0

    def test_infrastructure_and_damage_separation(self):
        infra_loader = InfrastructureAssetLoader()
        asset_raw = {
            "asset_id": "NH3_MANALI_BRIDGE",
            "asset_name": "Manali Bypass Bridge",
            "asset_type": "BRIDGE",
            "latitude": 32.235,
            "longitude": 77.185,
            "elevation_m": 1950.0,
            "criticality_tier": 1,
            "replacement_value_inr_lakh": 1200.0,
        }
        asset_rec, _ = infra_loader.parse_asset(asset_raw)
        assert asset_rec.quality_flag == "VALID"

        # Observed damage loader separating observed vs modelled
        dmg_loader = ObservedDamageLoader()
        dmg_raw = {
            "damage_id": "DMG_001",
            "asset_id": "NH3_MANALI_BRIDGE",
            "event_id": "BEAS_JULY_2023",
            "hazard_type": "FLASH_FLOOD",
            "observed_flood_depth_m": 3.8,
            "damage_state": "SEVERE",
            "damage_evidence_type": "OBSERVED_DAMAGE",
        }
        dmg_rec, _ = dmg_loader.parse_damage_record(dmg_raw)
        assert dmg_rec.damage_evidence_type == DamageEvidenceType.OBSERVED_DAMAGE

    def test_impact_timestamps_chronology_check(self):
        loader = ImpactTimestampLoader()

        # Valid chronological event
        valid_ev = {
            "event_id": "PAREECHU_2005",
            "event_name": "Pareechu Landslide Dam Outburst",
            "distance_km": 65.0,
            "initiation_time": "2005-06-26T08:00:00+00:00",
            "threshold_crossing_time": "2005-06-26T09:30:00+00:00",
            "impact_time": "2005-06-26T13:00:00+00:00",
        }
        rec, err = loader.parse_event(valid_ev)
        assert rec is not None
        assert rec.observed_lead_time_minutes == 210.0
        assert rec.observed_total_transit_minutes == 300.0

        # Invalid chronological event (impact before threshold crossing)
        invalid_ev = {
            "event_id": "TIME_PARADOX_01",
            "distance_km": 10.0,
            "initiation_time": "2023-07-09T10:00:00+00:00",
            "threshold_crossing_time": "2023-07-09T12:00:00+00:00",
            "impact_time": "2023-07-09T11:00:00+00:00",  # Paradox
        }
        rec2, err2 = loader.parse_event(invalid_ev)
        assert rec2 is None
        assert "Chronology violation" in err2


class TestPhase2QualityGatesAndDrift:

    def test_freshness_and_latency_status(self):
        validator = DataQualityValidator(freshness_threshold_seconds=1800.0)  # 30 min
        now = datetime.datetime.now(datetime.timezone.utc)

        # Fresh observation (10 minutes old)
        t_fresh = (now - datetime.timedelta(minutes=10)).isoformat()
        rep_fresh = validator.validate_record(
            sample_id="SAMPLE_FRESH",
            features={"rainfall_1h_mm": 5.0},
            observation_time_iso=t_fresh,
            reference_now_iso=now.isoformat(),
        )
        assert rep_fresh.status == QualityStatus.VALID
        assert rep_fresh.latency.freshness_status == FreshnessStatus.FRESH

        # Stale observation (45 minutes old)
        t_stale = (now - datetime.timedelta(minutes=45)).isoformat()
        rep_stale = validator.validate_record(
            sample_id="SAMPLE_STALE",
            features={"rainfall_1h_mm": 5.0},
            observation_time_iso=t_stale,
            reference_now_iso=now.isoformat(),
        )
        assert rep_stale.status == QualityStatus.DEGRADED
        assert rep_stale.latency.freshness_status == FreshnessStatus.STALE

        # Expired observation (120 minutes old)
        t_expired = (now - datetime.timedelta(minutes=120)).isoformat()
        rep_expired = validator.validate_record(
            sample_id="SAMPLE_EXPIRED",
            features={"rainfall_1h_mm": 5.0},
            observation_time_iso=t_expired,
            reference_now_iso=now.isoformat(),
        )
        assert rep_expired.status == QualityStatus.CRITICAL_ERROR
        assert rep_expired.latency.freshness_status == FreshnessStatus.EXPIRED

    def test_model_input_gate_blocks_critical_and_scales_degraded(self):
        gate = ModelInputGate()

        def dummy_infer(feats):
            return {"prediction": "NORMAL", "confidence": 0.90}

        # 1. Unphysical value -> CRITICAL_ERROR -> Blocked
        blocked_res = gate.guard_inference(
            sample_id="SAMPLE_CRITICAL",
            features={"water_level_m": 150.0},  # Impossibly high (>25m)
            inference_fn=dummy_infer,
        )
        assert blocked_res["inference_status"] == "BLOCKED_BY_QUALITY_GATE"
        assert blocked_res["prediction"] is None
        assert blocked_res["confidence"] == 0.0

        # 2. Missing value -> DEGRADED -> Passed with scaled confidence
        degraded_res = gate.guard_inference(
            sample_id="SAMPLE_DEGRADED",
            features={"water_level_m": 4.5, "rainfall_1h_mm": None},
            inference_fn=dummy_infer,
        )
        assert degraded_res["prediction"] == "NORMAL"
        assert degraded_res["confidence"] == pytest.approx(0.90 * 0.65, 0.01)
        assert "gate_warnings" in degraded_res

    def test_distribution_drift_monitoring(self):
        monitor = DistributionDriftMonitor()
        rng = np.random.RandomState(42)

        baseline = rng.normal(loc=10.0, scale=2.0, size=500)
        stable_target = rng.normal(loc=10.1, scale=2.0, size=500)
        drifted_target = rng.normal(loc=20.0, scale=5.0, size=500)

        # Stable evaluation
        res_stable = monitor.evaluate_feature("rainfall", baseline, stable_target)
        assert res_stable.drift_status == "NO_DRIFT"

        # Shifted evaluation
        res_drift = monitor.evaluate_feature("rainfall", baseline, drifted_target)
        assert res_drift.drift_status == "DRIFT_DETECTED"
        assert "Distribution drift detected" in res_drift.recommendation


class TestPhase2SecurityAndValidation:

    def test_human_authorization_gateway_workflow(self, tmp_path):
        gateway = HumanAuthorizationGateway(audit_log_path=tmp_path / "audit.jsonl")

        # Submit alert advisory
        rec = gateway.submit_advisory_for_review(
            advisory_id="ADV_2026_001",
            cap_identifier="CAP_KULLU_001",
            severity="EMERGENCY_EVACUATE",
            hazard_type="FLASH_FLOOD",
            affected_settlements=["Manali", "Patlikuhal"],
            cap_payload={"headline": "Immediate Evacuation Ordered for Beas Corridor"},
        )
        assert rec.authorization_status == AuthorizationStatus.PENDING_OFFICIAL_REVIEW

        # Officer signs and authorizes release
        ok, auth_rec, msg = gateway.authorize_and_sign(
            advisory_id="ADV_2026_001",
            officer_id="DC_KULLU_OFFICER_01",
            agency=AuthorizedAgency.DDMA_KULLU,
            passcode="SECURE_INCIDENT_COMMAND_TOKEN",
            notes="Field confirmation of Larji surge; authorized public sirens.",
        )
        assert ok is True
        assert auth_rec.authorization_status == AuthorizationStatus.AUTHORIZED_FOR_RELEASE
        assert auth_rec.officer_digital_signature_hash is not None
        assert (tmp_path / "audit.jsonl").exists()

    def test_dashboard_contract_truth_status(self):
        contract = DashboardPayloadContract()
        contract.add_indicator(
            key="beas_water_level_manali",
            value=4.8,
            unit="m",
            truth_status=ValueTruthStatus.OBSERVED,
            source_id="river_cwc_telemetry",
            quality="VALID",
        )
        contract.add_indicator(
            key="m2_flood_risk_score",
            value=0.78,
            unit="probability",
            truth_status=ValueTruthStatus.PREDICTED,
            source_id="M2",
            confidence=0.85,
        )
        d = contract.to_dict()
        assert d["indicators"]["beas_water_level_manali"]["truth_status"] == "OBSERVED"
        assert d["indicators"]["m2_flood_risk_score"]["truth_status"] == "PREDICTED"

    def test_external_validation_pipeline_metrics(self):
        pipeline = ExternalValidationPipeline(spatial_buffer_m=500.0)
        y_true = [1, 1, 1, 1, 0, 0, 0, 0]
        y_pred = [1, 1, 1, 0, 0, 0, 0, 1]
        y_prob = [0.9, 0.8, 0.85, 0.4, 0.1, 0.2, 0.15, 0.7]
        distances = [600.0, 700.0, 800.0, 900.0, 450.0, 600.0, 750.0, 850.0]  # 1 sample inside 500m buffer

        report = pipeline.evaluate_binary_classifier(
            model_id="M2",
            dataset_id="july2023_survey_points",
            y_true=y_true,
            y_pred=y_pred,
            y_prob=y_prob,
            spatial_distances_to_train_m=distances,
        )
        assert report.total_samples == 8
        assert report.samples_inside_buffer == 1
        assert report.samples_outside_buffer == 7
        assert report.recall == 0.75
        assert report.specificity == 0.75
        assert report.brier_score is not None
        assert report.status_recommendation == "PRELIMINARY_EVIDENCE_ONLY_N_LESS_THAN_50"
