"""
backend/app/services/devices/registry_service.py
================================================
Physical Station, Device, and Sensor Registry Service for FLOODY SHIELD v3.4.
Manages hardware lifecycles, operational states, calibration records, and heartbeats.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.core.errors import ResourceNotFoundError, FloodyShieldException
from backend.app.database.models.telemetry import SensorStationModel
from backend.app.database.models.device import (
    DeviceModel,
    SensorModel,
    CalibrationRecordModel,
    DeviceHeartbeatModel,
)


ALLOWED_DEVICE_STATUSES = {"PLANNED", "SURVEYED", "INSTALLED", "COMMISSIONED", "ACTIVE", "DEGRADED", "OFFLINE", "RETIRED"}
ALLOWED_STATION_STATUSES = ALLOWED_DEVICE_STATUSES
ALLOWED_SENSOR_TYPES = {
    "RAIN_GAUGE",
    "WATER_LEVEL",
    "WATER_FLOW",
    "SOIL_MOISTURE",
    "PORE_WATER_PRESSURE",
    "TILT",
    "VIBRATION",
    "TEMPERATURE",
    "HUMIDITY",
    "BATTERY",
}


class DeviceRegistryService:
    """Manages physical sensor and device inventory, installations, and calibrations."""

    def register_station(
        self,
        db: Session,
        station_id: str,
        name: str,
        station_type: str,
        latitude: float,
        longitude: float,
        elevation_m: Optional[float] = None,
        river_basin: str = "Upper Beas Basin",
        status: str = "PLANNED",
    ) -> SensorStationModel:
        existing = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if existing:
            return existing

        station = SensorStationModel(
            id=station_id,
            name=name,
            station_type=station_type,
            latitude=latitude,
            longitude=longitude,
            elevation_m=elevation_m,
            river_basin=river_basin,
            status=status,
            is_active=True,
            last_heartbeat=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(station)
        db.commit()
        db.refresh(station)
        return station

    def update_station_status(self, db: Session, station_id: str, new_status: str) -> SensorStationModel:
        if new_status not in ALLOWED_STATION_STATUSES:
            raise FloodyShieldException(
                message=f"Invalid station status '{new_status}'. Allowed: {ALLOWED_STATION_STATUSES}",
                error_code="INVALID_STATION_STATUS",
                status_code=400,
            )
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            raise ResourceNotFoundError(resource_type="Station", resource_id=station_id)
        station.status = new_status
        db.commit()
        db.refresh(station)
        return station

    def delete_station(self, db: Session, station_id: str) -> bool:
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            raise ResourceNotFoundError(resource_type="Station", resource_id=station_id)
        # Delete associated devices first
        devices = db.query(DeviceModel).filter(DeviceModel.station_id == station_id).all()
        for dev in devices:
            db.delete(dev)
        db.delete(station)
        db.commit()
        return True

    def record_survey(
        self,
        db: Session,
        station_id: str,
        surveyor_name: str,
        survey_notes: Optional[str] = None,
        coordinates_verified: bool = True,
        elevation_m: Optional[float] = None,
        site_suitability_score: Optional[float] = None,
        photos_metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> SensorStationModel:
        import json
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            raise ResourceNotFoundError(resource_type="Station", resource_id=station_id)

        existing_data = {}
        if station.commissioning_data:
            try:
                existing_data = json.loads(station.commissioning_data)
            except Exception:
                existing_data = {}

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        existing_data["survey"] = {
            "surveyor_name": surveyor_name,
            "survey_date": now_iso,
            "coordinates_verified": coordinates_verified,
            "elevation_m": elevation_m,
            "site_suitability_score": site_suitability_score,
            "survey_notes": survey_notes,
            "photos_metadata": photos_metadata or [],
        }
        if elevation_m is not None:
            station.elevation_m = elevation_m
        station.status = "SURVEYED"
        station.commissioning_data = json.dumps(existing_data)
        db.commit()
        db.refresh(station)
        return station

    def record_installation(
        self,
        db: Session,
        station_id: str,
        installer_name: str,
        hardware_manifest: Optional[Dict[str, Any]] = None,
        firmware_version: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> SensorStationModel:
        import json
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            raise ResourceNotFoundError(resource_type="Station", resource_id=station_id)

        existing_data = {}
        if station.commissioning_data:
            try:
                existing_data = json.loads(station.commissioning_data)
            except Exception:
                existing_data = {}

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        existing_data["installation"] = {
            "installer_name": installer_name,
            "installation_date": now_iso,
            "hardware_manifest": hardware_manifest or {},
            "firmware_version": firmware_version,
            "notes": notes,
        }
        station.status = "INSTALLED"
        station.commissioning_data = json.dumps(existing_data)
        db.commit()
        db.refresh(station)
        return station

    def commission_station(
        self,
        db: Session,
        station_id: str,
        commissioner_name: str,
        checklist: Dict[str, bool],
        remarks: Optional[str] = None,
    ) -> SensorStationModel:
        import json
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            raise ResourceNotFoundError(resource_type="Station", resource_id=station_id)

        required_gates = ["sensor_check", "calibration_check", "lora_check", "battery_check", "timestamp_check"]
        failed_gates = [g for g in required_gates if not checklist.get(g, False)]

        if failed_gates:
            raise FloodyShieldException(
                message=f"Commissioning verification failed. Unmet requirements: {', '.join(failed_gates)}",
                error_code="COMMISSIONING_VERIFICATION_FAILED",
                status_code=400,
            )

        existing_data = {}
        if station.commissioning_data:
            try:
                existing_data = json.loads(station.commissioning_data)
            except Exception:
                existing_data = {}

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        existing_data["commissioning"] = {
            "commissioner_name": commissioner_name,
            "commissioned_at": now_utc.isoformat(),
            "checklist": checklist,
            "remarks": remarks,
            "verification_status": "PASSED",
        }

        station.status = "ACTIVE"
        station.is_active = True
        station.commissioned_at = now_utc
        station.commissioned_by = commissioner_name
        station.commissioning_data = json.dumps(existing_data)
        db.commit()
        db.refresh(station)
        return station

    def get_commissioning_data(self, db: Session, station_id: str) -> Dict[str, Any]:
        import json
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            raise ResourceNotFoundError(resource_type="Station", resource_id=station_id)

        parsed = {}
        if station.commissioning_data:
            try:
                parsed = json.loads(station.commissioning_data)
            except Exception:
                parsed = {"raw": station.commissioning_data}

        return {
            "station_id": station.id,
            "name": station.name,
            "status": station.status,
            "commissioned_at": station.commissioned_at.isoformat() if station.commissioned_at else None,
            "commissioned_by": station.commissioned_by,
            "commissioning_data": parsed,
        }

    def list_stations(
        self,
        db: Session,
        station_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SensorStationModel]:
        query = db.query(SensorStationModel)
        if station_type:
            query = query.filter(SensorStationModel.station_type == station_type)
        if is_active is not None:
            query = query.filter(SensorStationModel.is_active == is_active)
        query = query.order_by(SensorStationModel.last_heartbeat.desc().nullslast())
        return query.offset(offset).limit(limit).all()

    def register_device(
        self,
        db: Session,
        device_id: str,
        station_id: str,
        serial_number: str,
        device_type: str,
        manufacturer: str = "FloodyShield-Hardware",
        firmware_version: str = "1.0.0",
        protocol: str = "LORAWAN",
        status: str = "PLANNED",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        elevation: Optional[float] = None,
    ) -> DeviceModel:
        if status not in ALLOWED_DEVICE_STATUSES:
            raise FloodyShieldException(
                message=f"Invalid device status '{status}'. Must be one of {ALLOWED_DEVICE_STATUSES}",
                error_code="INVALID_DEVICE_STATUS",
                status_code=400,
            )

        # Verify station exists or create default
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            station = self.register_station(
                db=db,
                station_id=station_id,
                name=f"Station for {device_id}",
                station_type="MET_HYDRO_IOT",
                latitude=latitude or 31.75,
                longitude=longitude or 77.20,
                elevation_m=elevation,
            )

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        device = DeviceModel(
            device_id=device_id,
            station_id=station_id,
            serial_number=serial_number,
            device_type=device_type,
            manufacturer=manufacturer,
            firmware_version=firmware_version,
            protocol=protocol,
            status=status,
            installed_at=now_utc if status in ("INSTALLED", "ACTIVE") else None,
            last_seen_at=now_utc if status in ("INSTALLED", "ACTIVE") else None,
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
        )
        db.add(device)
        try:
            db.commit()
            db.refresh(device)
            return device
        except IntegrityError:
            db.rollback()
            existing = db.query(DeviceModel).filter(DeviceModel.device_id == device_id).first()
            if existing:
                return existing
            raise

    def get_device(self, db: Session, device_id: str) -> DeviceModel:
        device = db.query(DeviceModel).filter(DeviceModel.device_id == device_id).first()
        if not device:
            raise ResourceNotFoundError(f"Device '{device_id}' not found")
        return device

    def list_devices(
        self,
        db: Session,
        station_id: Optional[str] = None,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DeviceModel]:
        query = db.query(DeviceModel)
        if station_id:
            query = query.filter(DeviceModel.station_id == station_id)
        if status:
            query = query.filter(DeviceModel.status == status)
        if device_type:
            query = query.filter(DeviceModel.device_type == device_type)
        return query.offset(offset).limit(limit).all()

    def update_device_status(self, db: Session, device_id: str, new_status: str) -> DeviceModel:
        if new_status not in ALLOWED_DEVICE_STATUSES:
            raise FloodyShieldException(
                message=f"Invalid device status '{new_status}'. Allowed: {ALLOWED_DEVICE_STATUSES}",
                error_code="INVALID_DEVICE_STATUS",
                status_code=400,
            )
        device = self.get_device(db, device_id)
        device.status = new_status
        device.updated_at = datetime.datetime.now(datetime.timezone.utc)
        if new_status in ("ACTIVE", "INSTALLED") and not device.installed_at:
            device.installed_at = device.updated_at
        db.commit()
        db.refresh(device)
        return device

    def register_sensor(
        self,
        db: Session,
        sensor_id: str,
        device_id: str,
        sensor_type: str,
        unit: str,
        measurement_range_min: Optional[float] = None,
        measurement_range_max: Optional[float] = None,
        sampling_interval_sec: int = 60,
    ) -> SensorModel:
        if sensor_type not in ALLOWED_SENSOR_TYPES:
            raise FloodyShieldException(
                message=f"Invalid sensor type '{sensor_type}'. Must be one of {ALLOWED_SENSOR_TYPES}",
                error_code="INVALID_SENSOR_TYPE",
                status_code=400,
            )
        # Ensure device exists
        self.get_device(db, device_id)

        sensor = SensorModel(
            sensor_id=sensor_id,
            device_id=device_id,
            sensor_type=sensor_type,
            unit=unit,
            measurement_range_min=measurement_range_min,
            measurement_range_max=measurement_range_max,
            sampling_interval_sec=sampling_interval_sec,
            calibration_status="VALID",
            last_calibration_at=datetime.datetime.now(datetime.timezone.utc),
            next_calibration_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365),
            is_active=True,
        )
        db.add(sensor)
        try:
            db.commit()
            db.refresh(sensor)
            return sensor
        except IntegrityError:
            db.rollback()
            existing = db.query(SensorModel).filter(SensorModel.sensor_id == sensor_id).first()
            if existing:
                return existing
            raise

    def list_sensors(
        self,
        db: Session,
        device_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SensorModel]:
        query = db.query(SensorModel)
        if device_id:
            query = query.filter(SensorModel.device_id == device_id)
        if sensor_type:
            query = query.filter(SensorModel.sensor_type == sensor_type)
        return query.offset(offset).limit(limit).all()

    def add_calibration_record(
        self,
        db: Session,
        sensor_id: str,
        calibrated_by: str,
        standard_reference: Optional[str] = None,
        zero_offset: float = 0.0,
        scale_factor: float = 1.0,
        notes: Optional[str] = None,
    ) -> CalibrationRecordModel:
        sensor = db.query(SensorModel).filter(SensorModel.sensor_id == sensor_id).first()
        if not sensor:
            raise ResourceNotFoundError(f"Sensor '{sensor_id}' not found")

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        record = CalibrationRecordModel(
            id=str(uuid.uuid4()),
            sensor_id=sensor_id,
            calibrated_at=now_utc,
            calibrated_by=calibrated_by,
            standard_reference=standard_reference,
            zero_offset=zero_offset,
            scale_factor=scale_factor,
            notes=notes,
        )
        sensor.calibration_status = "VALID"
        sensor.last_calibration_at = now_utc
        sensor.next_calibration_at = now_utc + datetime.timedelta(days=365)

        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def record_heartbeat(
        self,
        db: Session,
        device_id: str,
        battery_voltage: Optional[float] = None,
        battery_percentage: Optional[float] = None,
        rssi_dbm: Optional[float] = None,
        snr_db: Optional[float] = None,
        firmware_version: Optional[str] = None,
        error_flags: int = 0,
    ) -> DeviceHeartbeatModel:
        device = db.query(DeviceModel).filter(DeviceModel.device_id == device_id).first()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if device:
            device.last_seen_at = now_utc
            if battery_percentage is not None:
                device.battery_level = battery_percentage
            elif battery_voltage is not None:
                device.battery_level = battery_voltage
            if rssi_dbm is not None:
                device.signal_strength = rssi_dbm
            if firmware_version:
                device.firmware_version = firmware_version
            if device.status == "OFFLINE":
                device.status = "ACTIVE"

        heartbeat = DeviceHeartbeatModel(
            device_id=device_id,
            timestamp=now_utc,
            battery_voltage=battery_voltage,
            battery_percentage=battery_percentage,
            rssi_dbm=rssi_dbm,
            snr_db=snr_db,
            firmware_version=firmware_version,
            error_flags=error_flags,
        )
        db.add(heartbeat)
        db.commit()
        db.refresh(heartbeat)
        return heartbeat


device_registry_service = DeviceRegistryService()
