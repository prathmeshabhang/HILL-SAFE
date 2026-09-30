"""
telemetry.py — Model M9 IoT Sensor Telemetry & Anomaly Gating API Router
========================================================================
Exposes endpoints for:
  - Live ground sensor telemetry ingestion (river levels, rain gauges, piezometers).
  - Model M9 Isolation Forest anomaly filtering & quality scores.
  - Active ground station health and ping monitors.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ml.telemetry.iot_gateway import IoTTelemetryGateway

router = APIRouter(prefix="/api/v1/telemetry", tags=["IoT Telemetry & Quality Gating (M9)"])
gateway = IoTTelemetryGateway()


class IngestTelemetryRequest(BaseModel):
    station_id: str = Field(..., description="Unique station identifier (e.g., ST_AUT_01)")
    sensor_type: Literal["RIVER_GAUGE", "RAIN_GAUGE", "PIEZOMETER", "GEOPHONE"] = Field(..., description="Sensor type")
    value: float = Field(..., description="Observed metric value")
    timestamp_utc: Optional[str] = Field(None, description="ISO-8601 observation timestamp")


@router.post("/ingest", summary="Ingest and quality-audit real-time ground sensor reading")
def ingest_ground_reading(req: IngestTelemetryRequest) -> Dict[str, Any]:
    """Ingests sensor reading, verifies physical plausibility, and flags telemetry anomalies."""
    reading = gateway.ingest_reading(
        station_id=req.station_id,
        sensor_type=req.sensor_type,
        value=req.value,
        timestamp_utc=req.timestamp_utc,
    )
    return {
        "status": "success" if reading.is_valid else "rejected_anomaly",
        "reading": asdict(reading),
    }


@router.get("/stations", summary="List all registered IoT ground telemetry stations")
def list_ground_stations() -> Dict[str, Any]:
    """Returns active hydrological, meteorological, and geotechnical monitoring stations."""
    stations = gateway.get_stations()
    return {
        "status": "success",
        "total_stations": len(stations),
        "stations": stations,
    }


@router.get("/recent", summary="Get recent verified telemetry readings")
def get_recent_readings(limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    """Retrieves recent stream of telemetry readings with quality scores."""
    readings = gateway.get_recent_telemetry(limit=limit)
    return {
        "status": "success",
        "count": len(readings),
        "readings": readings,
    }
