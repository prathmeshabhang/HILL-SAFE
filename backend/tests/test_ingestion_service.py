"""
backend/tests/test_ingestion_service.py
=======================================
Unit tests for data ingestion, quality gating, bounds checking, and M9 anomaly detection.
"""

from __future__ import annotations

import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.core.errors import DataQualityError
from backend.app.services.ingestion.quality_gate import quality_gate
from backend.app.services.ingestion.schemas import RainGaugeReading, RiverWaterLevelReading
from backend.app.services.ingestion.ingestion_service import ingestion_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_spatial_bounds_validation():
    # Inside Upper Beas AOI
    assert quality_gate.validate_spatial_bounds(32.0, 77.2) is True

    # Outside Upper Beas AOI (Latitude too low)
    with pytest.raises(DataQualityError) as exc_info:
        quality_gate.validate_spatial_bounds(28.61, 77.20)  # Delhi
    assert "outside Upper Beas catchment AOI" in str(exc_info.value)


def test_temporal_freshness_future_rejection():
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    with pytest.raises(DataQualityError) as exc_info:
        quality_gate.validate_temporal_freshness(future_time)
    assert "future beyond allowable clock skew" in str(exc_info.value)


def test_temporal_freshness_stale_flagging():
    stale_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)
    res = quality_gate.validate_temporal_freshness(stale_time)
    assert res["is_fresh"] is False
    assert res["age_hours"] >= 48.0


def test_m9_anomaly_integration():
    # Test negative rainfall detection
    samples = [{"rainfall_rate": -15.0, "water_level": 2.0, "soil_moisture": 30.0}]
    res = quality_gate.check_anomalies_m9(samples)
    assert res["is_anomalous"] is True
    assert any("Negative rainfall rate" in f for f in res["flags"])


def test_ingest_rainfall_and_persistence(db_session):
    now = datetime.datetime.now(datetime.timezone.utc)
    reading = RainGaugeReading(
        station_id="STN_BHUNTAR_01",
        timestamp=now,
        rainfall_rate_mmh=12.0,
    )
    result = ingestion_service.ingest_rainfall(db_session, reading)
    assert result["status"] == "INGESTED"
    assert result["station_id"] == "STN_BHUNTAR_01"
    assert result["is_anomalous"] is False
    assert result["observation_id"] is not None


def test_ingest_anomalous_reading_flagged(db_session):
    now = datetime.datetime.now(datetime.timezone.utc)
    reading = RainGaugeReading(
        station_id="STN_ANOM_01",
        timestamp=now,
        rainfall_rate_mmh=280.0,  # extreme unphysical spike
    )
    result = ingestion_service.ingest_rainfall(db_session, reading)
    assert result["status"] == "INGESTED"
    assert result["is_anomalous"] is True
    assert "Statistical Anomaly" in result["anomaly_reason"]
