"""
backend/app/database/models/device.py
=====================================
SQLAlchemy models for Physical Devices, Sensors, Calibration, and Heartbeats.
Part of FLOODY SHIELD v3.4 Field Operationalization & Sensor Registry.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.database.session import Base


class DeviceModel(Base):
    __tablename__ = "devices"

    device_id = Column(String(64), primary_key=True)
    station_id = Column(String(64), ForeignKey("sensor_stations.id"), nullable=False, index=True)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    device_type = Column(String(64), nullable=False)  # LORA_NODE, CELLULAR_GATEWAY, WEATHER_STATION_LOGGER
    manufacturer = Column(String(128), nullable=False, default="FloodyShield-Hardware")
    firmware_version = Column(String(64), nullable=False, default="1.0.0")
    protocol = Column(String(32), nullable=False, default="LORAWAN")  # LORAWAN, MQTT, HTTP, CELLULAR
    status = Column(String(32), nullable=False, default="PLANNED")  # PLANNED, INSTALLED, ACTIVE, DEGRADED, OFFLINE, RETIRED
    installed_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    battery_level = Column(Float, nullable=True)  # Percentage (0-100) or Voltage (V)
    signal_strength = Column(Float, nullable=True)  # RSSI in dBm
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    station = relationship("SensorStationModel", backref="devices")
    sensors = relationship("SensorModel", back_populates="device", cascade="all, delete-orphan")
    heartbeats = relationship("DeviceHeartbeatModel", back_populates="device", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "station_id": self.station_id,
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "firmware_version": self.firmware_version,
            "protocol": self.protocol,
            "status": self.status,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "battery_level": self.battery_level,
            "signal_strength": self.signal_strength,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SensorModel(Base):
    __tablename__ = "sensors"

    sensor_id = Column(String(64), primary_key=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False, index=True)
    sensor_type = Column(String(64), nullable=False, index=True)  # RAIN_GAUGE, WATER_LEVEL, WATER_FLOW, SOIL_MOISTURE, PORE_WATER_PRESSURE, TILT, VIBRATION, TEMPERATURE, HUMIDITY, BATTERY
    unit = Column(String(32), nullable=False)  # mm/h, m, m3/s, %, kPa, deg, mm/s2, C, V
    measurement_range_min = Column(Float, nullable=True)
    measurement_range_max = Column(Float, nullable=True)
    sampling_interval_sec = Column(Integer, default=60)
    calibration_status = Column(String(32), default="VALID")  # VALID, EXPIRED, UNSUPPORTED
    last_calibration_at = Column(DateTime, nullable=True)
    next_calibration_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    device = relationship("DeviceModel", back_populates="sensors")
    calibrations = relationship("CalibrationRecordModel", back_populates="sensor", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "device_id": self.device_id,
            "sensor_type": self.sensor_type,
            "unit": self.unit,
            "measurement_range_min": self.measurement_range_min,
            "measurement_range_max": self.measurement_range_max,
            "sampling_interval_sec": self.sampling_interval_sec,
            "calibration_status": self.calibration_status,
            "last_calibration_at": self.last_calibration_at.isoformat() if self.last_calibration_at else None,
            "next_calibration_at": self.next_calibration_at.isoformat() if self.next_calibration_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CalibrationRecordModel(Base):
    __tablename__ = "calibration_records"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(64), ForeignKey("sensors.sensor_id"), nullable=False, index=True)
    calibrated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    calibrated_by = Column(String(128), nullable=False)
    standard_reference = Column(String(128), nullable=True)
    zero_offset = Column(Float, default=0.0)
    scale_factor = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)

    sensor = relationship("SensorModel", back_populates="calibrations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "calibrated_at": self.calibrated_at.isoformat() if self.calibrated_at else None,
            "calibrated_by": self.calibrated_by,
            "standard_reference": self.standard_reference,
            "zero_offset": self.zero_offset,
            "scale_factor": self.scale_factor,
            "notes": self.notes,
        }


class DeviceHeartbeatModel(Base):
    __tablename__ = "device_heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    battery_voltage = Column(Float, nullable=True)
    battery_percentage = Column(Float, nullable=True)
    rssi_dbm = Column(Float, nullable=True)
    snr_db = Column(Float, nullable=True)
    firmware_version = Column(String(64), nullable=True)
    error_flags = Column(Integer, default=0)

    device = relationship("DeviceModel", back_populates="heartbeats")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "battery_voltage": self.battery_voltage,
            "battery_percentage": self.battery_percentage,
            "rssi_dbm": self.rssi_dbm,
            "snr_db": self.snr_db,
            "firmware_version": self.firmware_version,
            "error_flags": self.error_flags,
        }
