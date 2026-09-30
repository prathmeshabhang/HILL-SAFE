"""
ml/data_quality/rules.py
=======================
Deterministic physical range, rate-of-change, and spatial boundary rules for Upper Beas Basin.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Upper Beas Basin Geographic Bounding Box (Kullu - Manali)
UPPER_BEAS_BOUNDS = {
    "min_lon": 76.80,
    "max_lon": 77.45,
    "min_lat": 31.40,
    "max_lat": 32.45,
    "min_elevation_m": 700.0,
    "max_elevation_m": 6000.0,
}

# Physical bounds by sensor / feature type
PHYSICAL_SENSOR_BOUNDS: Dict[str, Dict[str, float]] = {
    "rainfall_rate_mmh": {"min": 0.0, "max": 300.0, "max_delta_15m": 80.0},
    "rainfall_1h_mm": {"min": 0.0, "max": 200.0, "max_delta_1h": 120.0},
    "water_level_m": {"min": 0.0, "max": 25.0, "max_delta_15m": 4.0},
    "soil_moisture_pct": {"min": 0.0, "max": 100.0, "max_delta_15m": 35.0},
    "pore_pressure_kpa": {"min": 0.0, "max": 250.0, "max_delta_15m": 50.0},
    "displacement_mm": {"min": -500.0, "max": 5000.0, "max_delta_15m": 500.0},
    "cumulative_displacement_mm": {"min": -500.0, "max": 5000.0, "max_delta_15m": 500.0},
    "velocity_mm_day": {"min": -100.0, "max": 1000.0, "max_delta_1h": 200.0},
    "tilt_deg": {"min": -90.0, "max": 90.0, "max_delta_15m": 25.0},
    "temperature_c": {"min": -30.0, "max": 50.0, "max_delta_1h": 15.0},
}


def check_spatial_bounds(lat: float, lon: float, elevation_m: Optional[float] = None) -> Tuple[bool, Optional[str]]:
    """Validates whether coordinates lie strictly within the Upper Beas AOI."""
    if not (UPPER_BEAS_BOUNDS["min_lat"] <= lat <= UPPER_BEAS_BOUNDS["max_lat"]):
        return False, f"Latitude {lat:.4f} outside Upper Beas AOI [{UPPER_BEAS_BOUNDS['min_lat']}, {UPPER_BEAS_BOUNDS['max_lat']}]"
    if not (UPPER_BEAS_BOUNDS["min_lon"] <= lon <= UPPER_BEAS_BOUNDS["max_lon"]):
        return False, f"Longitude {lon:.4f} outside Upper Beas AOI [{UPPER_BEAS_BOUNDS['min_lon']}, {UPPER_BEAS_BOUNDS['max_lon']}]"
    if elevation_m is not None:
        if not (UPPER_BEAS_BOUNDS["min_elevation_m"] <= elevation_m <= UPPER_BEAS_BOUNDS["max_elevation_m"]):
            return False, f"Elevation {elevation_m:.1f}m outside valid range [{UPPER_BEAS_BOUNDS['min_elevation_m']}, {UPPER_BEAS_BOUNDS['max_elevation_m']}]"
    return True, None


def check_sensor_range(sensor_type: str, value: float) -> Tuple[bool, Optional[str]]:
    """Checks physical bounds for a given sensor reading."""
    bounds = PHYSICAL_SENSOR_BOUNDS.get(sensor_type)
    if not bounds:
        return True, None  # No strict rule configured

    if value < bounds["min"]:
        return False, f"Value {value} below physical minimum {bounds['min']} for {sensor_type}"
    if value > bounds["max"]:
        return False, f"Value {value} exceeds physical maximum {bounds['max']} for {sensor_type}"
    return True, None
