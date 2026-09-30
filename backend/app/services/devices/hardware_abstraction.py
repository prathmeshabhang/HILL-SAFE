"""
backend/app/services/devices/hardware_abstraction.py
====================================================
Hardware Abstraction Layer (HAL) for Physical Sensors and IoT Nodes.
Enforces vendor-agnostic sensor interfaces, physical unit bounds, calibration offsets,
and single-sensor failure isolation.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PhysicalSensorType(str, Enum):
    RAIN_GAUGE = "RAIN_GAUGE"
    WATER_LEVEL = "WATER_LEVEL"
    SOIL_MOISTURE = "SOIL_MOISTURE"
    PORE_WATER_PRESSURE = "PORE_WATER_PRESSURE"
    TILT = "TILT"
    VIBRATION = "VIBRATION"
    TEMPERATURE = "TEMPERATURE"
    HUMIDITY = "HUMIDITY"
    BATTERY = "BATTERY"


@dataclass(frozen=True)
class PhysicalSensorLimits:
    sensor_type: PhysicalSensorType
    unit: str
    physical_min: float
    physical_max: float
    plausible_min: float
    plausible_max: float


# Upper Beas Himalayan Physical Environment Limits
SENSOR_LIMITS_SPEC: Dict[PhysicalSensorType, PhysicalSensorLimits] = {
    PhysicalSensorType.RAIN_GAUGE: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.RAIN_GAUGE,
        unit="mm/h",
        physical_min=0.0,
        physical_max=500.0,
        plausible_min=0.0,
        plausible_max=350.0,  # Extreme Himalayan cloudburst upper threshold
    ),
    PhysicalSensorType.WATER_LEVEL: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.WATER_LEVEL,
        unit="m",
        physical_min=0.0,
        physical_max=35.0,
        plausible_min=0.1,
        plausible_max=25.0,  # Gorge flood crest limit
    ),
    PhysicalSensorType.SOIL_MOISTURE: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.SOIL_MOISTURE,
        unit="%",
        physical_min=0.0,
        physical_max=100.0,
        plausible_min=2.0,
        plausible_max=98.0,
    ),
    PhysicalSensorType.PORE_WATER_PRESSURE: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.PORE_WATER_PRESSURE,
        unit="kPa",
        physical_min=-100.0,
        physical_max=2000.0,
        plausible_min=-20.0,
        plausible_max=1200.0,
    ),
    PhysicalSensorType.TILT: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.TILT,
        unit="deg",
        physical_min=-90.0,
        physical_max=90.0,
        plausible_min=-60.0,
        plausible_max=60.0,
    ),
    PhysicalSensorType.VIBRATION: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.VIBRATION,
        unit="mm/s2",
        physical_min=0.0,
        physical_max=1000.0,
        plausible_min=0.0,
        plausible_max=500.0,
    ),
    PhysicalSensorType.TEMPERATURE: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.TEMPERATURE,
        unit="C",
        physical_min=-40.0,
        physical_max=60.0,
        plausible_min=-25.0,
        plausible_max=45.0,
    ),
    PhysicalSensorType.HUMIDITY: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.HUMIDITY,
        unit="%",
        physical_min=0.0,
        physical_max=100.0,
        plausible_min=5.0,
        plausible_max=100.0,
    ),
    PhysicalSensorType.BATTERY: PhysicalSensorLimits(
        sensor_type=PhysicalSensorType.BATTERY,
        unit="V",
        physical_min=0.0,
        physical_max=24.0,
        plausible_min=2.8,
        plausible_max=14.8,
    ),
}


@dataclass
class SensorReading:
    sensor_id: str
    sensor_type: PhysicalSensorType
    raw_value: float
    unit: str
    timestamp: datetime.datetime
    calibrated_value: Optional[float] = None
    is_valid: bool = True
    status_flags: List[str] = field(default_factory=list)
    quality_code: str = "GOOD"  # GOOD, SUSPECT, OUT_OF_BOUNDS, CALIBRATION_EXPIRED, ERROR


@dataclass
class StationTelemetryFrame:
    station_id: str
    device_id: str
    timestamp: datetime.datetime
    sequence_number: int
    readings: List[SensorReading]
    battery_voltage: float
    rssi_dbm: float
    snr_db: float
    station_health: str = "HEALTHY"


class HardwareAbstractionService:
    """Manages physical bounds checks, calibration mathematics, and failure isolation."""

    def __init__(self, limits_spec: Optional[Dict[PhysicalSensorType, PhysicalSensorLimits]] = None):
        self.limits = limits_spec or SENSOR_LIMITS_SPEC

    def validate_reading_bounds(
        self,
        sensor_type: PhysicalSensorType,
        value: float,
        unit: Optional[str] = None,
    ) -> Tuple[bool, str, List[str]]:
        """
        Validates whether a raw/calibrated reading falls within physical and plausible bounds.
        Returns: (is_valid, quality_code, flags)
        """
        spec = self.limits.get(sensor_type)
        if not spec:
            return True, "GOOD", []

        flags = []
        # Check units
        if unit and unit != spec.unit:
            flags.append(f"UNIT_MISMATCH: expected {spec.unit}, got {unit}")

        # Check physical absolute bounds
        if value < spec.physical_min or value > spec.physical_max:
            flags.append(f"EXCEEDS_PHYSICAL_LIMITS: {value} outside [{spec.physical_min}, {spec.physical_max}]")
            return False, "OUT_OF_BOUNDS", flags

        # Check plausible domain bounds
        if value < spec.plausible_min or value > spec.plausible_max:
            flags.append(f"IMPLAUSIBLE_VALUE: {value} outside [{spec.plausible_min}, {spec.plausible_max}]")
            return True, "SUSPECT", flags

        return True, "GOOD", flags

    def apply_calibration(
        self,
        raw_value: float,
        zero_offset: float = 0.0,
        scale_factor: float = 1.0,
        is_expired: bool = False,
    ) -> Tuple[float, List[str]]:
        """
        Applies zero offset and scale factor:
        calibrated_value = (raw_value * scale_factor) + zero_offset
        """
        flags = []
        calibrated_value = (raw_value * scale_factor) + zero_offset
        if is_expired:
            flags.append("CALIBRATION_EXPIRED")
        return calibrated_value, flags

    def process_station_frame(
        self,
        station_id: str,
        device_id: str,
        timestamp: datetime.datetime,
        sequence_number: int,
        raw_readings: List[Dict[str, Any]],
        battery_voltage: float,
        rssi_dbm: float,
        snr_db: float,
        sensor_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> StationTelemetryFrame:
        """
        Processes a multi-sensor frame from a physical station.
        Crucial Invariant: Single-Sensor Failure Isolation.
        If sensor A fails (e.g. rain gauge out of bounds), sensor B (water level)
        and sensor C (soil moisture) MUST continue processing normally.
        """
        processed_readings: List[SensorReading] = []
        any_degraded = False
        all_failed = True

        meta = sensor_metadata or {}

        for r in raw_readings:
            s_id = r.get("sensor_id", "UNKNOWN")
            s_type_raw = r.get("sensor_type", "RAIN_GAUGE")
            try:
                s_type = PhysicalSensorType(s_type_raw)
            except ValueError:
                s_type = PhysicalSensorType.RAIN_GAUGE

            raw_val = float(r.get("value", 0.0))
            unit = r.get("unit", "")

            # Look up calibration metadata if provided
            s_meta = meta.get(s_id, {})
            zero_offset = s_meta.get("zero_offset", 0.0)
            scale_factor = s_meta.get("scale_factor", 1.0)
            is_calib_expired = s_meta.get("is_calibration_expired", False)

            calibrated_val, cal_flags = self.apply_calibration(
                raw_val, zero_offset=zero_offset, scale_factor=scale_factor, is_expired=is_calib_expired
            )

            is_valid, quality_code, bound_flags = self.validate_reading_bounds(s_type, calibrated_val, unit)
            all_flags = cal_flags + bound_flags

            if is_calib_expired and quality_code == "GOOD":
                quality_code = "CALIBRATION_EXPIRED"

            if not is_valid:
                any_degraded = True
            else:
                all_failed = False

            processed_readings.append(
                SensorReading(
                    sensor_id=s_id,
                    sensor_type=s_type,
                    raw_value=raw_val,
                    calibrated_value=calibrated_val,
                    unit=unit,
                    timestamp=timestamp,
                    is_valid=is_valid,
                    status_flags=all_flags,
                    quality_code=quality_code,
                )
            )

        if not processed_readings:
            station_health = "OFFLINE"
        elif all_failed:
            station_health = "CRITICAL"
        elif any_degraded or battery_voltage < 11.5 or rssi_dbm < -115.0:
            station_health = "DEGRADED"
        else:
            station_health = "HEALTHY"

        return StationTelemetryFrame(
            station_id=station_id,
            device_id=device_id,
            timestamp=timestamp,
            sequence_number=sequence_number,
            readings=processed_readings,
            battery_voltage=battery_voltage,
            rssi_dbm=rssi_dbm,
            snr_db=snr_db,
            station_health=station_health,
        )


hal_service = HardwareAbstractionService()
