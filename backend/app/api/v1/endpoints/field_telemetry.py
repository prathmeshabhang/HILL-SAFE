"""
backend/app/api/v1/endpoints/field_telemetry.py
===============================================
REST API endpoints for real-time field telemetry ingestion, batch processing,
and aggregated time-series retrieval for FLOODY SHIELD v3.4.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models.telemetry import SensorObservationModel
from backend.app.services.ingestion.ingestion_service import ingestion_service
from backend.app.services.ingestion.lora_gateway import lora_gateway_service
from backend.app.services.devices.health_service import sensor_health_service

router = APIRouter(tags=["Field Telemetry & Time-Series"])


class RawLoRaFrameRequest(BaseModel):
    hex_payload: str = Field(..., description="Hexadecimal-encoded compact binary LoRa frame")
    gateway_id: str = Field("GW_ROHTANG_01", description="ID of gateway receiving frame")


class GatewayBackhaulRequest(BaseModel):
    gateway_id: str = Field("GW_ROHTANG_01", description="Gateway ID")
    online: bool = Field(..., description="Backhaul connection status")


class TelemetryPacketRequest(BaseModel):
    source_id: str = Field("UPPER_BEAS_IOT", description="Originating data source identifier")
    station_id: str = Field(..., description="Unique station ID")
    device_id: Optional[str] = Field(None, description="Physical device ID")
    sensor_id: Optional[str] = Field(None, description="Physical sensor ID")
    observed_at: str = Field(..., description="ISO-8601 observation timestamp")
    received_at: Optional[str] = Field(None, description="ISO-8601 gateway reception timestamp")
    measurement_type: str = Field(..., description="RAINFALL, WATER_LEVEL, PORE_WATER_PRESSURE, TILT, DISPLACEMENT, etc.")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Measurement unit (mm/h, m, kPa, deg, etc.)")
    sequence_number: Optional[int] = Field(None, description="Device packet increment counter")
    firmware_version: Optional[str] = Field(None, description="Device firmware version")
    quality_hint: Optional[str] = Field(None, description="Optional raw sensor quality code")
    provenance: Optional[str] = Field(
        "REAL",
        description="Data provenance: REAL, REAL_FIELD_OBSERVATION, REAL_AGENCY_DATA, REMOTE_SENSING_OBSERVATION, PROXY_DATA, SIMULATED, REPLAY, SYNTHETIC, TEST",
    )
    environment: Optional[str] = Field("FIELD", description="Environment: FIELD, TEST, LAB, STAGING")
    qc_flags: Optional[str] = Field(None, description="Initial QC flags or error tags")


class BatchTelemetryRequest(BaseModel):
    packets: List[TelemetryPacketRequest] = Field(..., max_length=500, description="List of telemetry packets (max 500)")


@router.post("/api/v1/telemetry", summary="Ingest single field telemetry packet with strict idempotency")
def ingest_telemetry(
    req: TelemetryPacketRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return ingestion_service.ingest_telemetry_packet(db, req.model_dump())


@router.post("/api/v1/telemetry/batch", summary="Ingest a batch of field telemetry packets")
def ingest_telemetry_batch(
    req: BatchTelemetryRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    packet_dicts = [p.model_dump() for p in req.packets]
    return ingestion_service.ingest_telemetry_batch(db, packet_dicts)


@router.post("/api/v1/telemetry/lora/frame", summary="Ingest raw binary LoRa frame with CRC-16 check and sequence tracking")
def ingest_lora_frame(
    req: RawLoRaFrameRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        raw_bytes = bytes.fromhex(req.hex_payload.strip())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid hex payload: {e}")

    try:
        return lora_gateway_service.process_raw_frame(db, raw_bytes, gateway_id=req.gateway_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v1/telemetry/lora/gateway/backhaul", summary="Set gateway backhaul online/offline status")
def set_gateway_backhaul(
    req: GatewayBackhaulRequest,
) -> Dict[str, Any]:
    lora_gateway_service.set_backhaul_status(req.online)
    return {"gateway_id": req.gateway_id, "online": req.online}


@router.post("/api/v1/telemetry/lora/gateway/flush", summary="Flush offline buffered LoRa packets chronologically")
def flush_gateway_buffer(
    gateway_id: str = Query("GW_ROHTANG_01"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return lora_gateway_service.flush_offline_buffer(db, gateway_id=gateway_id)


@router.get("/api/v1/telemetry/lora/device/{device_id}/stats", summary="Get sequence continuity and packet loss stats")
def get_device_lora_stats(
    device_id: str,
) -> Dict[str, Any]:
    tracker = lora_gateway_service.get_tracker(device_id)
    return {
        "device_id": device_id,
        "last_sequence": tracker.last_seq,
        "total_received": tracker.total_received,
        "total_duplicates": tracker.total_duplicates,
        "total_gaps": tracker.total_gaps,
        "total_dropped": tracker.total_dropped,
        "packet_loss_pct": tracker.packet_loss_pct,
    }


@router.get("/api/v1/telemetry/health/summary", summary="Get aggregated field telemetry and hardware health summary")
def get_telemetry_health_summary(
    window: Literal["24h", "72h", "7d", "30d"] = Query("24h", description="Aggregation time window"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return sensor_health_service.get_health_summary(db, window=window)


@router.get("/api/v1/observations/timeseries", summary="Query aggregated time-series telemetry")
def get_observations_timeseries(
    station_id: Optional[str] = None,
    device_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    measurement_type: Optional[str] = None,
    quality: Optional[str] = None,
    provenance: Optional[str] = None,
    environment: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    aggregation: Literal["raw", "min", "max", "mean", "sum", "count", "latest"] = "raw",
    interval: Optional[str] = None,  # e.g., 1h, 15m, 1d
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns time-series observations with unit safety, filtering, and optional statistical aggregation.
    """
    query = db.query(SensorObservationModel)

    if station_id:
        query = query.filter(SensorObservationModel.station_id == station_id)
    if device_id:
        query = query.filter(SensorObservationModel.device_id == device_id)
    if sensor_id:
        query = query.filter(SensorObservationModel.sensor_id == sensor_id)
    if measurement_type:
        query = query.filter(SensorObservationModel.measurement_type == measurement_type.upper())
    if quality:
        query = query.filter(SensorObservationModel.quality_state == quality.upper())
    if provenance:
        query = query.filter(SensorObservationModel.provenance == provenance.upper())
    if environment:
        query = query.filter(SensorObservationModel.environment == environment.upper())

    if start:
        try:
            start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
            query = query.filter(SensorObservationModel.timestamp >= start_dt)
        except Exception:
            pass
    if end:
        try:
            end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
            query = query.filter(SensorObservationModel.timestamp <= end_dt)
        except Exception:
            pass

    if aggregation == "latest":
        rec = query.order_by(SensorObservationModel.timestamp.desc()).first()
        return {
            "aggregation": "latest",
            "station_id": station_id,
            "measurement_type": measurement_type,
            "data": [rec.to_dict()] if rec else [],
        }

    if aggregation == "raw":
        total = query.count()
        records = query.order_by(SensorObservationModel.timestamp.desc()).offset(offset).limit(limit).all()
        return {
            "aggregation": "raw",
            "total_records": total,
            "limit": limit,
            "offset": offset,
            "data": [r.to_dict() for r in records],
        }

    # Summary aggregations
    count_val = query.count()
    if count_val == 0:
        return {
            "aggregation": aggregation,
            "total_records": 0,
            "value": None,
            "unit": None,
        }

    if aggregation == "count":
        return {"aggregation": "count", "value": count_val}

    first_unit = query.filter(SensorObservationModel.unit.isnot(None)).first()
    unit_str = first_unit.unit if first_unit else None

    if aggregation == "min":
        val = query.with_entities(func.min(SensorObservationModel.value)).scalar()
    elif aggregation == "max":
        val = query.with_entities(func.max(SensorObservationModel.value)).scalar()
    elif aggregation == "mean":
        val = query.with_entities(func.avg(SensorObservationModel.value)).scalar()
    elif aggregation == "sum":
        val = query.with_entities(func.sum(SensorObservationModel.value)).scalar()
    else:
        val = None

    return {
        "aggregation": aggregation,
        "station_id": station_id,
        "measurement_type": measurement_type,
        "total_records": count_val,
        "value": round(float(val), 4) if val is not None else None,
        "unit": unit_str,
    }


# ==============================================================================
# Phase 04A: Multi-Source Observation & Agency Health Endpoints
# ==============================================================================

@router.get("/api/v1/sources/health", summary="Get multi-source external agency health and freshness report")
def get_sources_health() -> Dict[str, Any]:
    """
    Returns operational health, data freshness, and fail-soft availability for
    all monitored sources: INSAT-3DS, SMAP, Field IoT, IMD AWS, CWC River, Sentinel.
    """
    from backend.app.services.ingestion.source_health import source_health_monitor
    return source_health_monitor.get_basin_connectivity_summary()


@router.get("/api/v1/sources/snapshot", summary="Get composite fail-soft basin observation snapshot")
def get_sources_snapshot() -> Dict[str, Any]:
    """
    Synthesizes current basin observation indicators from verified active feeds.
    Strictly fail-soft: if any feed is missing, remaining feeds continue without fake substitution.
    """
    from backend.app.services.ingestion.multi_source_service import multi_source_service
    return multi_source_service.get_composite_basin_snapshot()


@router.post("/api/v1/sources/ingest/{source_id}", summary="Ingest raw record via source adapter")
def ingest_from_source(
    source_id: str,
    raw_payload: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Normalizes and ingests a raw record from an external agency or satellite feed
    (INSAT_3DS, SMAP, IMD_AWS, CWC_RIVER, SENTINEL_COPERNICUS, UPPER_BEAS_IOT).
    """
    from backend.app.services.ingestion.multi_source_service import multi_source_service
    try:
        return multi_source_service.normalize_and_ingest(db, source_id.upper(), raw_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

