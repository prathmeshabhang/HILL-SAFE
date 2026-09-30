"""
backend/app/api/v1/endpoints/devices.py
=======================================
REST API endpoints for Physical Station, Device, Sensor Lifecycle Management,
Calibration records, Heartbeats, and Diagnostic Health evaluations.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models.user import UserModel
from backend.app.services.devices.registry_service import device_registry_service
from backend.app.services.devices.health_service import sensor_health_service
from backend.app.core.security import get_current_user, require_role

router = APIRouter(tags=["Physical Stations, Devices & Sensors"])


# --- Schemas ---
class CreateStationRequest(BaseModel):
    station_id: Optional[str] = Field(None, description="Unique Station Code, e.g. STN_KULLU_01")
    name: str = Field(..., description="Descriptive station name")
    station_type: str = Field("MET_HYDRO_IOT", description="Type of station")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    elevation_m: Optional[float] = Field(None, description="Station elevation in meters")
    river_basin: str = Field("Upper Beas Basin", description="River basin designation")
    status: str = Field("ACTIVE", description="Lifecycle status (PLANNED, SURVEYED, INSTALLED, COMMISSIONED, ACTIVE, DEGRADED, OFFLINE, RETIRED)")


class UpdateStationStatusRequest(BaseModel):
    status: str = Field(..., description="New station lifecycle status (PLANNED, SURVEYED, INSTALLED, COMMISSIONED, ACTIVE, DEGRADED, OFFLINE, RETIRED)")


class SurveyStationRequest(BaseModel):
    surveyor_name: str = Field(..., description="Name or identifier of field surveyor")
    survey_notes: Optional[str] = Field(None, description="Observations regarding terrain, line of sight, power")
    coordinates_verified: bool = Field(True, description="Ground GPS coordinate ground-truthing flag")
    elevation_m: Optional[float] = Field(None, description="Measured altitude in meters")
    site_suitability_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Suitability score 0-100")
    photos_metadata: Optional[List[Dict[str, Any]]] = Field(None, description="Metadata of survey site photographs")


class InstallStationRequest(BaseModel):
    installer_name: str = Field(..., description="Field technician / installation contractor")
    hardware_manifest: Optional[Dict[str, Any]] = Field(None, description="Hardware manifest (sensors, solar panel, mast)")
    firmware_version: Optional[str] = Field(None, description="Initial node firmware version")
    notes: Optional[str] = Field(None, description="Installation notes")


class CommissionStationRequest(BaseModel):
    commissioner_name: str = Field(..., description="Senior Engineer / Commissioning Authority")
    sensor_check: bool = Field(..., description="Verification that all sensors are live and reading expected ranges")
    calibration_check: bool = Field(..., description="Verification of zero-offset and slope calibrations")
    lora_check: bool = Field(..., description="Verification of LoRa/Cellular transmission and SNR")
    battery_check: bool = Field(..., description="Verification of power subsystem and battery voltage")
    timestamp_check: bool = Field(..., description="Verification of RTC and clock synchronization")
    remarks: Optional[str] = Field(None, description="Commissioning authority sign-off remarks")


class CreateDeviceRequest(BaseModel):
    device_id: str = Field(..., description="Unique device ID, e.g. DEV_AUT_PWP_01")
    station_id: str = Field(..., description="Associated station ID")
    serial_number: str = Field(..., description="Hardware serial number / IMEI")
    device_type: str = Field(..., description="Device classification (LORA_NODE, CELLULAR_GATEWAY)")
    manufacturer: str = Field("FloodyShield-Hardware", description="Manufacturer name")
    firmware_version: str = Field("1.0.0", description="Firmware version tag")
    protocol: str = Field("LORAWAN", description="Communication protocol (LORAWAN, MQTT, HTTP, CELLULAR)")
    status: str = Field("PLANNED", description="Lifecycle status (PLANNED, INSTALLED, ACTIVE, DEGRADED, OFFLINE, RETIRED)")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[float] = None


class UpdateDeviceStatusRequest(BaseModel):
    status: str = Field(..., description="New lifecycle status (PLANNED, INSTALLED, ACTIVE, DEGRADED, OFFLINE, RETIRED)")


class CreateSensorRequest(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor ID, e.g. SNS_AUT_RAIN_01")
    device_id: str = Field(..., description="Parent device ID")
    sensor_type: str = Field(..., description="RAIN_GAUGE, WATER_LEVEL, WATER_FLOW, SOIL_MOISTURE, PORE_WATER_PRESSURE, TILT, VIBRATION, TEMPERATURE, HUMIDITY, BATTERY")
    unit: str = Field(..., description="Unit of measurement (mm/h, m, m3/s, %, kPa, deg, mm/s2, C, V)")
    measurement_range_min: Optional[float] = None
    measurement_range_max: Optional[float] = None
    sampling_interval_sec: int = Field(60, ge=1)


class CalibrationRequest(BaseModel):
    calibrated_by: str = Field(..., description="Name or ID of calibration technician/authority")
    standard_reference: Optional[str] = Field(None, description="Calibration reference instrument/traceability ID")
    zero_offset: float = Field(0.0, description="Sensor zero offset")
    scale_factor: float = Field(1.0, description="Sensor scale multiplier")
    notes: Optional[str] = Field(None, description="Technician notes")


class HeartbeatRequest(BaseModel):
    battery_voltage: Optional[float] = Field(None, description="Voltage in Volts")
    battery_percentage: Optional[float] = Field(None, description="Battery percentage (0-100)")
    rssi_dbm: Optional[float] = Field(None, description="Received Signal Strength in dBm")
    snr_db: Optional[float] = Field(None, description="Signal-to-Noise Ratio in dB")
    firmware_version: Optional[str] = None
    error_flags: int = Field(0, description="Hardware error bitmask")


# --- Endpoints ---

@router.get("/api/v1/stations", summary="List physical telemetry stations")
def list_stations(
    station_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    stations = device_registry_service.list_stations(db, station_type, is_active, limit, offset)
    return {
        "total": len(stations),
        "limit": limit,
        "offset": offset,
        "stations": [s.to_dict() for s in stations],
    }


@router.post("/api/v1/stations", summary="Register a physical station (Admin/Analyst/Operator)")
def register_station(
    req: CreateStationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user),
) -> Dict[str, Any]:
    stn_id = req.station_id or f"STN_{uuid.uuid4().hex[:8].upper()}"
    station = device_registry_service.register_station(
        db=db,
        station_id=stn_id,
        name=req.name,
        station_type=req.station_type,
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=req.elevation_m,
        river_basin=req.river_basin,
        status=req.status,
    )
    return {"status": "REGISTERED", "station": station.to_dict()}


@router.delete("/api/v1/stations/{station_id}", summary="Delete a physical station")
def delete_station(
    station_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user),
) -> Dict[str, Any]:
    device_registry_service.delete_station(db, station_id)
    return {"status": "DELETED", "station_id": station_id}


@router.patch("/api/v1/stations/{station_id}/status", summary="Update station lifecycle status")
def update_station_status(
    station_id: str,
    req: UpdateStationStatusRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    station = device_registry_service.update_station_status(db, station_id, req.status)
    return {"status": "UPDATED", "station": station.to_dict()}


@router.post("/api/v1/stations/{station_id}/survey", summary="Record station field survey (Analyst/Admin)")
def record_station_survey(
    station_id: str,
    req: SurveyStationRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    station = device_registry_service.record_survey(
        db=db,
        station_id=station_id,
        surveyor_name=req.surveyor_name,
        survey_notes=req.survey_notes,
        coordinates_verified=req.coordinates_verified,
        elevation_m=req.elevation_m,
        site_suitability_score=req.site_suitability_score,
        photos_metadata=req.photos_metadata,
    )
    return {"status": "SURVEYED", "station": station.to_dict()}


@router.post("/api/v1/stations/{station_id}/install", summary="Record station physical installation (Analyst/Admin)")
def record_station_installation(
    station_id: str,
    req: InstallStationRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    station = device_registry_service.record_installation(
        db=db,
        station_id=station_id,
        installer_name=req.installer_name,
        hardware_manifest=req.hardware_manifest,
        firmware_version=req.firmware_version,
        notes=req.notes,
    )
    return {"status": "INSTALLED", "station": station.to_dict()}


@router.post("/api/v1/stations/{station_id}/commission", summary="Verify checklist and commission station (Senior Commander/Admin)")
def commission_station(
    station_id: str,
    req: CommissionStationRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    checklist = {
        "sensor_check": req.sensor_check,
        "calibration_check": req.calibration_check,
        "lora_check": req.lora_check,
        "battery_check": req.battery_check,
        "timestamp_check": req.timestamp_check,
    }
    station = device_registry_service.commission_station(
        db=db,
        station_id=station_id,
        commissioner_name=req.commissioner_name,
        checklist=checklist,
        remarks=req.remarks,
    )
    return {"status": "ACTIVE", "station": station.to_dict()}


@router.get("/api/v1/stations/{station_id}/commissioning", summary="Get station commissioning status and record")
def get_station_commissioning(
    station_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return device_registry_service.get_commissioning_data(db, station_id)


@router.get("/api/v1/devices", summary="List field IoT devices")
def list_devices(
    station_id: Optional[str] = None,
    status: Optional[str] = None,
    device_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    devices = device_registry_service.list_devices(db, station_id, status, device_type, limit, offset)
    return {
        "total": len(devices),
        "limit": limit,
        "offset": offset,
        "devices": [d.to_dict() for d in devices],
    }


@router.post("/api/v1/devices", summary="Register a field device (Admin/Analyst)")
def register_device(
    req: CreateDeviceRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    device = device_registry_service.register_device(
        db=db,
        device_id=req.device_id,
        station_id=req.station_id,
        serial_number=req.serial_number,
        device_type=req.device_type,
        manufacturer=req.manufacturer,
        firmware_version=req.firmware_version,
        protocol=req.protocol,
        status=req.status,
        latitude=req.latitude,
        longitude=req.longitude,
        elevation=req.elevation,
    )
    return {"status": "REGISTERED", "device": device.to_dict()}


@router.get("/api/v1/devices/{device_id}", summary="Get device detail")
def get_device(device_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    device = device_registry_service.get_device(db, device_id)
    return {"device": device.to_dict()}


@router.patch("/api/v1/devices/{device_id}/status", summary="Update device lifecycle status")
def update_device_status(
    device_id: str,
    req: UpdateDeviceStatusRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    device = device_registry_service.update_device_status(db, device_id, req.status)
    return {"status": "UPDATED", "device": device.to_dict()}


@router.post("/api/v1/devices/{device_id}/heartbeat", summary="Record device heartbeat and radio telemetry")
def record_heartbeat(
    device_id: str,
    req: HeartbeatRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    hb = device_registry_service.record_heartbeat(
        db=db,
        device_id=device_id,
        battery_voltage=req.battery_voltage,
        battery_percentage=req.battery_percentage,
        rssi_dbm=req.rssi_dbm,
        snr_db=req.snr_db,
        firmware_version=req.firmware_version,
        error_flags=req.error_flags,
    )
    return {"status": "HEARTBEAT_RECORDED", "heartbeat": hb.to_dict()}


@router.get("/api/v1/sensors", summary="List sensors")
def list_sensors(
    device_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    sensors = device_registry_service.list_sensors(db, device_id, sensor_type, limit, offset)
    return {
        "total": len(sensors),
        "limit": limit,
        "offset": offset,
        "sensors": [s.to_dict() for s in sensors],
    }


@router.post("/api/v1/sensors", summary="Register a sensor attached to a device")
def register_sensor(
    req: CreateSensorRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    sensor = device_registry_service.register_sensor(
        db=db,
        sensor_id=req.sensor_id,
        device_id=req.device_id,
        sensor_type=req.sensor_type,
        unit=req.unit,
        measurement_range_min=req.measurement_range_min,
        measurement_range_max=req.measurement_range_max,
        sampling_interval_sec=req.sampling_interval_sec,
    )
    return {"status": "REGISTERED", "sensor": sensor.to_dict()}


@router.post("/api/v1/sensors/{sensor_id}/calibrate", summary="Add calibration record for a sensor")
@router.post("/api/v1/sensors/{sensor_id}/calibrations", summary="Add calibration record for a sensor (alias)")
def calibrate_sensor(
    sensor_id: str,
    req: CalibrationRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["ANALYST", "SENIOR_INCIDENT_COMMANDER", "ADMIN"])),
) -> Dict[str, Any]:
    calib = device_registry_service.add_calibration_record(
        db=db,
        sensor_id=sensor_id,
        calibrated_by=req.calibrated_by,
        standard_reference=req.standard_reference,
        zero_offset=req.zero_offset,
        scale_factor=req.scale_factor,
        notes=req.notes,
    )
    return {"status": "CALIBRATED", "record": calib.to_dict(), "calibration": calib.to_dict()}


@router.get("/api/v1/devices/{device_id}/health", summary="Evaluate device operational health")
def get_device_health(device_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return sensor_health_service.evaluate_device_health(db, device_id)


@router.get("/api/v1/stations/{station_id}/health", summary="Evaluate station operational health")
def get_station_health(station_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return sensor_health_service.evaluate_station_health(db, station_id)
