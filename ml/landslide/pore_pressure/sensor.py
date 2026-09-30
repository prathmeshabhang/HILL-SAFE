"""IoT Piezometer and Tensiometer In-Situ Telemetry Ingestion & Quality Control.

Provides strict schemas, physical range bounds, spike anomaly detection,
and calibration hook functions for ground geotechnical instrumentation.

DISCLAIMER:
Direct continuous pore-water pressure field validation datasets are currently
unavailable for the Upper Beas catchment. This module provides the operational
interface, telemetry contract, quality control, and calibration hooks required
once IoT vibrating-wire piezometer networks are deployed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import numpy as np


# Operational bounds for shallow (0.5m - 5.0m) slope piezometers
VALID_MIN_PORE_PRESSURE_KPA = -30.0   # Negative pore-water pressure (suction threshold)
VALID_MAX_PORE_PRESSURE_KPA = 250.0   # Saturated / artesian head limit
MAX_PLAUSIBLE_RATE_KPA_PER_HR = 25.0  # Plausible maximum rate of rise without sensor malfunction
MIN_BATTERY_VOLTAGE_V = 3.2           # Minimum node battery level for sensor reliability


@dataclass
class PiezometerReading:
    """Telemetry record from an in-situ vibrating-wire or silicon-piezoresistive piezometer."""
    sensor_id: str
    timestamp: str                       # ISO 8601 format
    pore_pressure_kpa: float
    depth_m: float = 2.0
    temperature_c: Optional[float] = None
    battery_v: Optional[float] = 3.6
    quality_flag: str = "UNCHECKED"       # GOOD, SUSPECT_SPIKE, OUT_OF_RANGE, LOW_BATTERY
    raw_pressure_kpa: Optional[float] = None

    def to_dict(self) -> Dict[str, Union[str, float, None]]:
        return {
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp,
            "pore_pressure_kpa": float(self.pore_pressure_kpa),
            "depth_m": float(self.depth_m),
            "temperature_c": float(self.temperature_c) if self.temperature_c is not None else None,
            "battery_v": float(self.battery_v) if self.battery_v is not None else None,
            "quality_flag": self.quality_flag,
            "raw_pressure_kpa": float(self.raw_pressure_kpa) if self.raw_pressure_kpa is not None else float(self.pore_pressure_kpa),
        }


@dataclass
class TensiometerReading:
    """Telemetry record from an in-situ soil matric suction tensiometer."""
    sensor_id: str
    timestamp: str
    matric_suction_kpa: float
    depth_m: float = 1.0
    temperature_c: Optional[float] = None
    quality_flag: str = "UNCHECKED"

    def to_dict(self) -> Dict[str, Union[str, float, None]]:
        return {
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp,
            "matric_suction_kpa": float(self.matric_suction_kpa),
            "depth_m": float(self.depth_m),
            "temperature_c": float(self.temperature_c) if self.temperature_c is not None else None,
            "quality_flag": self.quality_flag,
        }


class SensorQualityAuditor:
    """Audits, filters, and calibrates incoming piezometric and suction sensor telemetry."""

    def __init__(self, calibration_offsets: Optional[Dict[str, float]] = None):
        """Args:

        calibration_offsets: Map of sensor_id -> offset in kPa to subtract from raw reading.
        """
        self.calibration_offsets = calibration_offsets or {}
        self._previous_readings: Dict[str, Tuple[datetime, float]] = {}

    def audit_piezometer_reading(self, reading: PiezometerReading) -> PiezometerReading:
        """Applies calibration offset, range validation, and rate-of-change spike checks."""
        raw_val = reading.pore_pressure_kpa
        reading.raw_pressure_kpa = raw_val

        # 1. Apply calibration offset if present
        offset = self.calibration_offsets.get(reading.sensor_id, 0.0)
        calibrated_val = raw_val - offset
        reading.pore_pressure_kpa = round(calibrated_val, 3)

        # 2. Battery health check
        if reading.battery_v is not None and reading.battery_v < MIN_BATTERY_VOLTAGE_V:
            reading.quality_flag = "LOW_BATTERY"
            return reading

        # 3. Absolute physical range check
        if not (VALID_MIN_PORE_PRESSURE_KPA <= calibrated_val <= VALID_MAX_PORE_PRESSURE_KPA):
            reading.quality_flag = "OUT_OF_RANGE"
            return reading

        # 4. Spike / Rate-of-change check
        try:
            current_dt = datetime.fromisoformat(reading.timestamp.replace("Z", "+00:00"))
        except Exception:
            current_dt = None

        if current_dt and reading.sensor_id in self._previous_readings:
            prev_dt, prev_val = self._previous_readings[reading.sensor_id]
            delta_hours = max((current_dt - prev_dt).total_seconds() / 3600.0, 0.001)
            rate_kpa_per_hr = abs(calibrated_val - prev_val) / delta_hours
            if rate_kpa_per_hr > MAX_PLAUSIBLE_RATE_KPA_PER_HR:
                reading.quality_flag = "SUSPECT_SPIKE"
                return reading

        if current_dt:
            self._previous_readings[reading.sensor_id] = (current_dt, calibrated_val)

        reading.quality_flag = "GOOD"
        return reading

    def calibrate_sensor(self, sensor_id: str, baseline_zero_kpa: float) -> None:
        """Sets the zero-offset calibration constant for a sensor."""
        self.calibration_offsets[sensor_id] = baseline_zero_kpa


def compare_model_with_sensor(
    modelled_pore_pressure_kpa: float,
    reading: PiezometerReading,
) -> Dict[str, Union[float, str]]:
    """Calculates residual between physical model estimate and validated in-situ sensor reading.

    NOTE: Direct field validation data are currently unavailable.
    """
    if reading.quality_flag != "GOOD":
        return {
            "sensor_id": reading.sensor_id,
            "status": "REJECTED_SENSOR_READING",
            "quality_flag": reading.quality_flag,
            "disclaimer": "Direct pore-water pressure validation data are currently unavailable.",
        }

    residual = modelled_pore_pressure_kpa - reading.pore_pressure_kpa
    relative_err_pct = abs(residual) / max(abs(reading.pore_pressure_kpa), 1.0) * 100.0

    return {
        "sensor_id": reading.sensor_id,
        "modelled_kpa": float(modelled_pore_pressure_kpa),
        "observed_kpa": float(reading.pore_pressure_kpa),
        "residual_kpa": float(round(residual, 3)),
        "relative_error_pct": float(round(relative_err_pct, 2)),
        "status": "VALIDATED_SAMPLE",
        "disclaimer": "Direct pore-water pressure validation data are currently unavailable.",
    }
