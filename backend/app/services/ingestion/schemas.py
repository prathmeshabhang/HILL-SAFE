"""
backend/app/services/ingestion/schemas.py
=========================================
Pydantic schemas for external telemetry, satellite feeds, and quality validation.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class BaseTelemetryPayload(BaseModel):
    station_id: str = Field(..., description="Unique sensor station identifier, e.g. STN_KULLU_01")
    timestamp: datetime.datetime = Field(..., description="UTC timestamp of observation")


class RainGaugeReading(BaseTelemetryPayload):
    rainfall_rate_mmh: float = Field(..., ge=0.0, le=500.0, description="Precipitation rate in mm/hr")
    accumulated_24h_mm: Optional[float] = Field(None, ge=0.0, le=2000.0, description="24h cumulative rainfall")


class RiverWaterLevelReading(BaseTelemetryPayload):
    water_level_m: float = Field(..., ge=0.0, le=100.0, description="Gauge stage / water level in meters")
    discharge_m3s: Optional[float] = Field(None, ge=0.0, description="Estimated instantaneous discharge")
    danger_level_m: Optional[float] = Field(None, description="CWC danger mark threshold")


class GeotechnicalSensorReading(BaseTelemetryPayload):
    pore_water_pressure_kpa: Optional[float] = Field(None, ge=-50.0, le=2000.0, description="Pore pressure in kPa")
    slope_displacement_mm: Optional[float] = Field(None, ge=-1000.0, le=5000.0, description="Cumulative displacement")
    acoustic_emission_db: Optional[float] = Field(None, ge=0.0, le=150.0, description="Subsurface micro-crack acoustic energy")


class CombinedIoTTelemetryBatch(BaseModel):
    batch_id: str = Field(..., description="Unique batch UUID")
    source_network: str = Field("UPPER_BEAS_IOT_ARRAY", description="Origin telemetry network")
    readings: List[Dict[str, Any]] = Field(..., description="List of raw station observations")


class SatelliteSceneIngest(BaseModel):
    scene_id: str = Field(..., description="Acquisition identifier, e.g. S2A_MSIL2A_20230709T051701")
    mission: Literal["SENTINEL-1", "SENTINEL-2", "LANDSAT-8", "LANDSAT-9"]
    sensor_mode: str = Field("IW", description="Acquisition mode (e.g. IW, GRD, MSI)")
    acquisition_time: datetime.datetime
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="[min_lon, min_lat, max_lon, max_lat]")
    cloud_cover_pct: float = Field(0.0, ge=0.0, le=100.0)
    file_uri: Optional[str] = Field(None, description="Local path or Cloud Object storage URI")
