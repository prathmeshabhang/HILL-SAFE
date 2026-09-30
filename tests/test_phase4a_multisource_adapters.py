"""
tests/test_phase4a_multisource_adapters.py
==========================================
Authoritative Verification Suite for Phase 04A:
Multi-Source Observation Layer & External Agency Adapters.

Verifies:
  Test 1:  INSAT-3DS adapter normalizes MOSDAC HEM rain rate, IMSRA, and TIR-1 temperature.
  Test 2:  SMAP adapter normalizes NASA volumetric soil moisture, saturation %, and quality flags.
  Test 3:  IoT adapter normalizes slope & riverbed geotechnical telemetry package.
  Test 4:  IMD AWS adapter normalizes rain gauge telemetry and 24h accumulation.
  Test 5:  CWC River adapter normalizes river stage, discharge, and danger levels.
  Test 6:  Sentinel adapter normalizes SAR flood inundation and optical scenes.
  Test 7:  Deterministic deduplication hashing across all adapter types.
  Test 8:  Provenance preservation and classification compliance with Phase 03 safety rules.
  Test 9:  Honest configuration reporting (is_configured false without valid endpoints).
  Test 10: Multi-source health monitor records poll successes, poll failures, and error counts.
  Test 11: Dynamic freshness aging transitions (ONLINE -> STALE -> OFFLINE).
  Test 12: Fail-soft continuity when Ground IoT is lost (satellite/agency continues, no fake ground data).
  Test 13: Fail-soft continuity when Satellite is lost (IoT/agency continues, no fake satellite data).
  Test 14: Fail-soft continuity when all feeds are lost (clean UNAVAILABLE report, zero synthetic data).
  Test 15: End-to-end normalization and database persistence via TelemetryIngestionService.
"""

from __future__ import annotations

import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.core.config import settings
from backend.app.core.provenance import (
    DataMode,
    is_operational_provenance,
)
from backend.app.database.models.telemetry import SensorObservationModel, SensorStationModel
from backend.app.database.models.ingestion import DataQualityRecordModel
from backend.app.services.ingestion.adapters.base import NormalizedObservation
from backend.app.services.ingestion.adapters.insat3ds import INSAT3DSAdapter
from backend.app.services.ingestion.adapters.smap import SMAPAdapter
from backend.app.services.ingestion.adapters.iot import IoTTelemetryAdapter
from backend.app.services.ingestion.adapters.weather import IMDAWSAdapter, GPMIMERGAdapter
from backend.app.services.ingestion.adapters.river import CWCRiverAdapter
from backend.app.services.ingestion.adapters.satellite import SentinelSceneAdapter
from backend.app.services.ingestion.source_health import (
    MultiSourceHealthMonitor,
    SourceHealthStatus,
)
from backend.app.services.ingestion.multi_source_service import (
    MultiSourceObservationService,
    multi_source_service,
)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# Test 1: INSAT-3DS Adapter Normalization
# ==============================================================================
def test_insat3ds_adapter_normalization():
    adapter = INSAT3DSAdapter()
    raw_record = {
        "product_id": "3DS_IMG_20231910600_L3B_HEM",
        "acquisition_time": "2023-07-10T06:00:00Z",
        "bbox": [76.80, 31.40, 77.45, 32.45],
        "hem_rain_rate_mmh": 42.5,
        "imsra_rain_rate_mmh": 38.0,
        "tir1_brightness_temp_k": 218.4,
        "cloud_cover_pct": 85.0,
        "granule_id": "MOSDAC_INSAT3DS_20230710_0600_BEAS.h5",
    }
    obs = adapter.normalize(raw_record)

    assert isinstance(obs, NormalizedObservation)
    assert obs.source_id == "INSAT_3DS"
    assert obs.station_id == "3DS_IMG_20231910600_L3B_HEM"
    assert obs.observation_type == "PRECIPITATION"
    assert obs.source_type == "SATELLITE"
    assert obs.value == 42.5
    assert obs.unit == "mm/h"
    assert obs.values["hem_rain_rate_mmh"] == 42.5
    assert obs.values["imsra_rain_rate_mmh"] == 38.0
    assert obs.values["tir1_brightness_temp_k"] == 218.4
    assert obs.spatial_extent is not None
    assert obs.idempotency_hash != ""


# ==============================================================================
# Test 2: SMAP Soil Moisture Adapter Normalization
# ==============================================================================
def test_smap_adapter_normalization():
    adapter = SMAPAdapter()
    raw_record = {
        "grid_cell_id": "SMAP_EASE2_9KM_32.00_77.10",
        "granule_time": "2023-07-10T00:30:00Z",
        "latitude": 32.00,
        "longitude": 77.10,
        "soil_moisture_volumetric": 0.38,
        "soil_porosity": 0.45,
        "surface_temp_k": 288.2,
        "retrieval_quality_flag": 0,
        "freeze_thaw_flag": "UNFROZEN",
        "granule_id": "SMAP_L3_SM_P_20230710_R18290_001.h5",
    }
    obs = adapter.normalize(raw_record)

    assert isinstance(obs, NormalizedObservation)
    assert obs.source_id == "SMAP"
    assert obs.observation_type == "SOIL_MOISTURE"
    assert obs.source_type == "SATELLITE"
    assert obs.value == 0.38
    assert obs.unit == "cm3/cm3"
    assert round(obs.values["soil_saturation_pct"], 1) == round((0.38 / 0.45) * 100.0, 1)
    assert obs.quality["retrieval_quality_flag"] == 0
    assert obs.quality["is_recommended_for_analysis"] is True


# ==============================================================================
# Test 3: IoT Geotechnical Array Adapter Normalization
# ==============================================================================
def test_iot_telemetry_adapter_normalization():
    adapter = IoTTelemetryAdapter()
    raw_record = {
        "station_id": "IOT_SLOPE_AUT_02",
        "timestamp": "2023-07-10T06:15:00Z",
        "latitude": 31.75,
        "longitude": 77.20,
        "elevation_m": 1150.0,
        "pore_pressure_kpa": 45.2,
        "displacement_mm": 12.8,
        "acoustic_emission_db": 62.0,
        "rainfall_rate_mmh": 15.0,
        "water_level_m": 0.0,
        "packet_id": 48291,
    }
    obs = adapter.normalize(raw_record)

    assert isinstance(obs, NormalizedObservation)
    assert obs.source_id == "UPPER_BEAS_IOT"
    assert obs.station_id == "IOT_SLOPE_AUT_02"
    assert obs.observation_type == "DISPLACEMENT"
    assert obs.value == 12.8
    assert obs.unit == "mm"
    assert obs.values["pore_pressure_kpa"] == 45.2
    assert obs.values["acoustic_emission_db"] == 62.0
    assert obs.provenance["data_mode"] == DataMode.REAL_FIELD_OBSERVATION.value


# ==============================================================================
# Test 4: IMD AWS Weather Adapter Normalization
# ==============================================================================
def test_imd_aws_adapter_normalization():
    adapter = IMDAWSAdapter()
    raw_record = {
        "station_code": "STN_MANALI_IMD",
        "obs_time": "2023-07-10T06:00:00Z",
        "latitude": 32.24,
        "longitude": 77.19,
        "elevation_m": 2050.0,
        "rain_rate_mm": 35.0,
        "accum_rain_24h": 142.0,
        "temp_c": 14.5,
        "humidity_pct": 98.0,
    }
    obs = adapter.normalize(raw_record)

    assert isinstance(obs, NormalizedObservation)
    assert obs.source_id == "IMD_AWS"
    assert obs.station_id == "STN_MANALI_IMD"
    assert obs.observation_type == "PRECIPITATION"
    assert obs.value == 35.0
    assert obs.unit == "mm/h"
    assert obs.values["accumulated_24h_mm"] == 142.0
    assert obs.provenance["data_mode"] == DataMode.REAL_AGENCY_DATA.value


# ==============================================================================
# Test 5: CWC River Gauge Adapter Normalization
# ==============================================================================
def test_cwc_river_adapter_normalization():
    adapter = CWCRiverAdapter()
    raw_record = {
        "site_id": "CWC_BHUNTAR_01",
        "measurement_time": "2023-07-10T06:00:00Z",
        "latitude": 31.89,
        "longitude": 77.15,
        "water_level_m": 6.85,
        "discharge_m3s": 1450.0,
        "warning_level_m": 5.0,
        "danger_level_m": 7.0,
        "hfl_m": 9.5,
    }
    obs = adapter.normalize(raw_record)

    assert isinstance(obs, NormalizedObservation)
    assert obs.source_id == "CWC_RIVER"
    assert obs.station_id == "CWC_BHUNTAR_01"
    assert obs.observation_type == "WATER_LEVEL"
    assert obs.value == 6.85
    assert obs.unit == "m"
    assert obs.values["discharge_m3s"] == 1450.0
    assert obs.provenance["data_mode"] == DataMode.REAL_AGENCY_DATA.value


# ==============================================================================
# Test 6: Sentinel Scene Adapter Normalization
# ==============================================================================
def test_sentinel_scene_adapter_normalization():
    adapter = SentinelSceneAdapter()
    raw_record = {
        "scene_id": "S1A_IW_GRDH_1SDV_20230710T012345",
        "acquisition_time": "2023-07-10T01:23:45Z",
        "mission": "SENTINEL-1",
        "bbox": [76.85, 31.50, 77.40, 32.40],
        "inundated_area_km2": 18.4,
        "granule_id": "S1A_IW_GRDH_GRANULE_99",
    }
    obs = adapter.normalize(raw_record)

    assert isinstance(obs, NormalizedObservation)
    assert obs.source_id == "SENTINEL_COPERNICUS"
    assert obs.observation_type == "SAR_INUNDATION"
    assert obs.value == 18.4
    assert obs.unit == "km2"
    assert obs.provenance["data_mode"] == DataMode.REMOTE_SENSING_OBSERVATION.value


# ==============================================================================
# Test 7: Deterministic Idempotency Deduplication Hashing
# ==============================================================================
def test_idempotency_hash_determinism():
    adapter = INSAT3DSAdapter()
    ts = datetime.datetime(2023, 7, 10, 6, 0, 0, tzinfo=datetime.timezone.utc)

    hash1 = adapter.compute_idempotency_hash("GRANULE_A", ts, "REF_01")
    hash2 = adapter.compute_idempotency_hash("GRANULE_A", ts, "REF_01")
    hash_different_granule = adapter.compute_idempotency_hash("GRANULE_B", ts, "REF_01")
    hash_different_ts = adapter.compute_idempotency_hash(
        "GRANULE_A",
        ts + datetime.timedelta(minutes=30),
        "REF_01",
    )

    assert hash1 == hash2
    assert hash1 != hash_different_granule
    assert hash1 != hash_different_ts


# ==============================================================================
# Test 8: Provenance Preservation and Classification Compliance
# ==============================================================================
def test_provenance_preservation_and_classification():
    adapters = [
        (IoTTelemetryAdapter(), DataMode.REAL_FIELD_OBSERVATION.value),
        (IMDAWSAdapter(), DataMode.REAL_AGENCY_DATA.value),
        (CWCRiverAdapter(), DataMode.REAL_AGENCY_DATA.value),
        (INSAT3DSAdapter(), DataMode.REMOTE_SENSING_OBSERVATION.value),
        (SMAPAdapter(), DataMode.REMOTE_SENSING_OBSERVATION.value),
        (SentinelSceneAdapter(), DataMode.REMOTE_SENSING_OBSERVATION.value),
    ]

    for adapter, expected_mode in adapters:
        prov = adapter.provenance()
        assert prov["data_mode"] == expected_mode
        assert prov["provenance"] == expected_mode
        # Phase 03 compliance check: operational provenance classification
        assert is_operational_provenance(expected_mode) is True


# ==============================================================================
# Test 9: Configuration Honesty
# ==============================================================================
def test_configuration_honesty(monkeypatch):
    # Without external endpoints configured, adapters must report is_configured = False
    monkeypatch.setattr(settings, "INSAT3DS_MOSDAC_ENDPOINT", None)
    monkeypatch.setattr(settings, "SMAP_EARTHDATA_ENDPOINT", None)

    unconfigured_insat = INSAT3DSAdapter()
    unconfigured_smap = SMAPAdapter()

    assert unconfigured_insat.is_configured is False
    assert unconfigured_smap.is_configured is False

    # When configured with explicit endpoint, is_configured returns True
    configured_insat = INSAT3DSAdapter(endpoint="https://mosdac.gov.in/api/v1")
    configured_smap = SMAPAdapter(endpoint="https://cmr.earthdata.nasa.gov")

    assert configured_insat.is_configured is True
    assert configured_smap.is_configured is True


# ==============================================================================
# Test 10: Multi-Source Health Monitor Recording
# ==============================================================================
def test_source_health_monitor_recording():
    monitor = MultiSourceHealthMonitor()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # 1. Record successful poll
    rec = monitor.record_poll_success("INSAT_3DS", now_utc, "MOSDAC_GRANULE_01")
    assert rec.success_count == 1
    assert rec.consecutive_failures == 0
    assert rec.status == SourceHealthStatus.ONLINE
    assert "MOSDAC_GRANULE_01" in rec.active_stations_or_granules

    # 2. Record failures
    monitor.record_poll_failure("INSAT_3DS", "Connection timed out")
    rec = monitor.evaluate_health("INSAT_3DS", as_of=now_utc)
    assert rec.consecutive_failures == 1
    assert rec.status == SourceHealthStatus.DEGRADED

    # 3. Third failure triggers ERROR status
    monitor.record_poll_failure("INSAT_3DS", "Connection refused")
    monitor.record_poll_failure("INSAT_3DS", "Gateway 504")
    rec = monitor.evaluate_health("INSAT_3DS", as_of=now_utc)
    assert rec.consecutive_failures == 3
    assert rec.status == SourceHealthStatus.ERROR


# ==============================================================================
# Test 11: Dynamic Freshness Aging Transitions
# ==============================================================================
def test_source_health_freshness_transitions():
    monitor = MultiSourceHealthMonitor()
    t0 = datetime.datetime(2023, 7, 10, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # Upper Beas IoT threshold is 15 minutes (900 sec)
    monitor.record_poll_success("UPPER_BEAS_IOT", t0, "IOT_SLOPE_AUT_01", poll_time=t0)

    # Check at t0 + 5 min: ONLINE
    rec_fresh = monitor.evaluate_health("UPPER_BEAS_IOT", as_of=t0 + datetime.timedelta(minutes=5))
    assert rec_fresh.status == SourceHealthStatus.ONLINE

    # Check at t0 + 25 min (>15 min threshold): STALE
    rec_stale = monitor.evaluate_health("UPPER_BEAS_IOT", as_of=t0 + datetime.timedelta(minutes=25))
    assert rec_stale.status == SourceHealthStatus.STALE

    # Check at t0 + 60 min (>3x threshold): OFFLINE
    rec_offline = monitor.evaluate_health("UPPER_BEAS_IOT", as_of=t0 + datetime.timedelta(minutes=60))
    assert rec_offline.status == SourceHealthStatus.OFFLINE


# ==============================================================================
# Test 12: Fail-Soft Continuity — Ground IoT Lost
# ==============================================================================
def test_fail_soft_iot_lost():
    service = MultiSourceObservationService()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Active feeds: INSAT-3DS and IMD AWS only (IoT is missing/offline)
    insat_obs = INSAT3DSAdapter().normalize({
        "product_id": "3DS_IMG_HEM_TEST",
        "acquisition_time": now_utc.isoformat(),
        "hem_rain_rate_mmh": 35.0,
    })
    imd_obs = IMDAWSAdapter().normalize({
        "station_code": "STN_KULLU_IMD",
        "obs_time": now_utc.isoformat(),
        "rain_rate_mm": 28.0,
    })

    snapshot = service.get_composite_basin_snapshot(
        recent_observations=[insat_obs, imd_obs],
        as_of=now_utc,
    )

    # Assert fail-soft properties
    assert snapshot["fail_soft_engaged"] is True
    assert "UPPER_BEAS_IOT" in snapshot["missing_or_stale_sources"]
    assert "INSAT_3DS" in snapshot["active_sources"]
    assert "IMD_AWS" in snapshot["active_sources"]
    assert snapshot["physical_indicators"]["max_rainfall_rate_mmh"] == 35.0
    # ZERO synthetic substitution for missing IoT geotechnical data
    assert snapshot["physical_indicators"]["max_slope_displacement_mm"] is None
    assert snapshot["confidence_score"] > 0.0
    assert snapshot["confidence_score"] < 1.0  # Degraded confidence due to missing sources


# ==============================================================================
# Test 13: Fail-Soft Continuity — Satellite Lost
# ==============================================================================
def test_fail_soft_satellite_lost():
    service = MultiSourceObservationService()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Active feeds: Ground IoT and CWC gauge only (Satellite feeds missing)
    iot_obs = IoTTelemetryAdapter().normalize({
        "station_id": "IOT_SLOPE_AUT_01",
        "timestamp": now_utc.isoformat(),
        "displacement_mm": 8.5,
        "pore_pressure_kpa": 32.0,
    })
    cwc_obs = CWCRiverAdapter().normalize({
        "site_id": "CWC_BHUNTAR_01",
        "measurement_time": now_utc.isoformat(),
        "water_level_m": 5.4,
    })

    snapshot = service.get_composite_basin_snapshot(
        recent_observations=[iot_obs, cwc_obs],
        as_of=now_utc,
    )

    # Assert fail-soft properties
    assert snapshot["fail_soft_engaged"] is True
    assert "INSAT_3DS" in snapshot["missing_or_stale_sources"]
    assert "SMAP" in snapshot["missing_or_stale_sources"]
    assert "UPPER_BEAS_IOT" in snapshot["active_sources"]
    assert "CWC_RIVER" in snapshot["active_sources"]
    assert snapshot["physical_indicators"]["max_water_level_m"] == 5.4
    assert snapshot["physical_indicators"]["max_slope_displacement_mm"] == 8.5
    # ZERO synthetic substitution for missing satellite soil moisture
    assert snapshot["physical_indicators"]["avg_soil_moisture_cm3cm3"] is None


# ==============================================================================
# Test 14: Fail-Soft Continuity — All Sources Lost
# ==============================================================================
def test_fail_soft_all_sources_lost():
    service = MultiSourceObservationService()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Zero recent observations available
    snapshot = service.get_composite_basin_snapshot(
        recent_observations=[],
        as_of=now_utc,
    )

    assert snapshot["fusion_state"] == "UNAVAILABLE_NO_DATA"
    assert snapshot["confidence_score"] == 0.0
    assert snapshot["active_sources_count"] == 0
    assert snapshot["physical_indicators"]["max_rainfall_rate_mmh"] is None
    assert snapshot["physical_indicators"]["max_water_level_m"] is None
    assert snapshot["physical_indicators"]["avg_soil_moisture_cm3cm3"] is None
    assert snapshot["physical_indicators"]["max_slope_displacement_mm"] is None
    assert snapshot["fail_soft_engaged"] is True


# ==============================================================================
# Test 15: End-to-End Normalization & Database Persistence
# ==============================================================================
def test_end_to_end_normalization_and_persistence(db_session: Session):
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    raw_cwc = {
        "site_id": "CWC_KULLU_TEST_01",
        "measurement_time": now_utc.isoformat(),
        "latitude": 31.95,
        "longitude": 77.10,
        "water_level_m": 4.80,
        "discharge_m3s": 850.0,
        "record_id": f"REC_CWC_{now_utc.timestamp()}",
    }

    # Ingest through multi_source_service
    res = multi_source_service.normalize_and_ingest(
        db=db_session,
        source_id="CWC_RIVER",
        raw_record=raw_cwc,
    )

    assert res["status"] == "INGESTED"
    assert res["station_id"] == "CWC_KULLU_TEST_01"
    obs_id = res["observation_id"]

    # Verify database persistence
    db_obs = db_session.query(SensorObservationModel).filter_by(id=obs_id).first()
    assert db_obs is not None
    assert db_obs.data_source_id == "CWC_RIVER"
    assert db_obs.water_level_m == 4.80
    assert "REAL_AGENCY_DATA" in db_obs.provenance_json

    # Verify quality record was generated
    q_rec = db_session.query(DataQualityRecordModel).filter_by(station_or_scene_id="CWC_KULLU_TEST_01").first()
    assert q_rec is not None
    assert q_rec.source_id == "CWC_RIVER"
    assert q_rec.passed in ("PASS", "DEGRADED")
