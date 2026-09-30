"""
backend/app/services/ingestion/quality_gate.py
==============================================
Data Quality Gating & Pre-flight Validation for FLOODY SHIELD v3.3.
Centralizes spatial bounds checks, temporal freshness grading, physical limits,
and multivariate anomaly screening (Model M9 Isolation Forest).
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.errors import DataQualityError
from backend.app.core.logging import get_logger
from ml.anomaly.m9_sensor_anomaly import M9SensorAnomalyDetector

logger = get_logger("floody.ingestion.quality_gate")


class QualityState(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    DEGRADED = "DEGRADED"
    CRITICAL_ERROR = "CRITICAL_ERROR"


class TelemetryQualityGate:
    """
    Multi-stage verification gate ensuring incoming observational data meets
    physical bounds, geographic containment, temporal freshness, and anomaly criteria.
    """

    def __init__(self, stale_threshold_hours: float = 3.0, expired_threshold_hours: float = 24.0):
        self.stale_threshold_hours = stale_threshold_hours
        self.expired_threshold_hours = expired_threshold_hours
        self.m9_detector = M9SensorAnomalyDetector()

    def validate_spatial_bounds(self, latitude: float, longitude: float) -> bool:
        """Verifies if coordinates reside within the Upper Beas River Basin catchment."""
        in_lat = settings.MIN_LATITUDE <= latitude <= settings.MAX_LATITUDE
        in_lon = settings.MIN_LONGITUDE <= longitude <= settings.MAX_LONGITUDE
        if not (in_lat and in_lon):
            raise DataQualityError(
                message=f"Coordinate ({latitude:.4f}, {longitude:.4f}) is outside Upper Beas catchment AOI",
                details={
                    "latitude": latitude,
                    "longitude": longitude,
                    "bounds": {
                        "lat_min": settings.MIN_LATITUDE,
                        "lat_max": settings.MAX_LATITUDE,
                        "lon_min": settings.MIN_LONGITUDE,
                        "lon_max": settings.MAX_LONGITUDE,
                    },
                    "quality_state": QualityState.CRITICAL_ERROR.value,
                },
            )
        return True

    def validate_temporal_freshness(self, timestamp: datetime.datetime) -> Dict[str, Any]:
        """
        Validates timestamp freshness and categorizes into FRESH, STALE, or EXPIRED.
        Strictly rejects future-dated observations beyond allowable clock drift margin (5 min).
        """
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

        diff_seconds = (now_utc - timestamp).total_seconds()

        # Reject future timestamps beyond 5 minutes (300 seconds)
        if diff_seconds < -300:
            raise DataQualityError(
                message="Observation timestamp is in the future beyond allowable clock skew (5 min)",
                details={
                    "timestamp": timestamp.isoformat(),
                    "now_utc": now_utc.isoformat(),
                    "quality_state": QualityState.CRITICAL_ERROR.value,
                },
            )

        age_hours = max(0.0, diff_seconds / 3600.0)
        if age_hours < self.stale_threshold_hours:
            quality_state = QualityState.FRESH
        elif age_hours <= self.expired_threshold_hours:
            quality_state = QualityState.STALE
        else:
            quality_state = QualityState.EXPIRED

        return {
            "quality_state": quality_state.value,
            "is_fresh": quality_state == QualityState.FRESH,
            "age_hours": age_hours,
            "timestamp": timestamp.isoformat(),
        }

    def validate_physical_limits(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifies deterministic physical plausibility bounds.
        """
        violations = []
        rain = values.get("rainfall_rate_mmh")
        if rain is not None:
            if rain < 0.0:
                violations.append(f"Negative rainfall rate: {rain} mm/h")
            elif rain > 500.0:
                violations.append(f"Rainfall rate exceeds sensor hardware ceiling (500 mm/h): {rain}")

        water_level = values.get("water_level_m")
        if water_level is not None:
            if water_level < 0.0:
                violations.append(f"Negative river stage: {water_level} m")
            elif water_level > 50.0:
                violations.append(f"River stage exceeds upper channel canyon ceiling: {water_level} m")

        pwp = values.get("pore_pressure_kpa")
        if pwp is not None and (pwp < -50.0 or pwp > 2000.0):
            violations.append(f"Pore water pressure out of physical range: {pwp} kPa")

        sm = values.get("soil_moisture_volumetric")
        if sm is not None and (sm < 0.0 or sm > 1.0):
            violations.append(f"Volumetric soil moisture out of physical range (0.0 to 1.0 cm3/cm3): {sm}")

        tir1 = values.get("tir1_brightness_temp_k")
        if tir1 is not None and (tir1 < 100.0 or tir1 > 360.0):
            violations.append(f"TIR-1 brightness temperature out of physical range (100 to 360 K): {tir1}")

        if violations:
            raise DataQualityError(
                message=f"Physical limits violated: {'; '.join(violations)}",
                details={"violations": violations, "quality_state": QualityState.CRITICAL_ERROR.value},
            )

        return {"valid": True}

    def check_flatlining(self, history: List[float], tolerance: float = 1e-4) -> bool:
        """Detects stuck sensor if 5+ consecutive readings are identical non-zero values."""
        if len(history) < 5:
            return False
        first = history[0]
        if abs(first) > tolerance and all(abs(x - first) < tolerance for x in history):
            return True
        return False

    def check_rate_of_change(self, current_val: float, previous_val: float, dt_seconds: float, m_type: str) -> bool:
        """Detects physically implausible sudden jumps in sensor readings."""
        if dt_seconds <= 0:
            return False
        rate_per_min = abs(current_val - previous_val) / max(0.1, dt_seconds / 60.0)
        m_upper = m_type.upper()
        if "RAIN" in m_upper and rate_per_min > 50.0:  # > 50 mm/h jump in 1 min
            return True
        if ("WATER" in m_upper or "RIVER" in m_upper) and rate_per_min > 2.0:  # > 2m jump in 1 min
            return True
        if "PORE" in m_upper and rate_per_min > 200.0:  # > 200 kPa jump in 1 min
            return True
        if "DISPLACEMENT" in m_upper and rate_per_min > 50.0:  # > 50 mm jump in 1 min
            return True
        return False

    def check_anomalies_m9(self, recent_samples: List[Dict[str, float]]) -> Dict[str, Any]:
        """Delegates multivariate anomaly screening to Model M9."""
        try:
            return self.m9_detector.check_telemetry_stream(recent_samples)
        except Exception as exc:
            logger.warning(f"M9 anomaly evaluation fallback triggered: {exc}")
            return {
                "status": "EVALUATION_SKIPPED",
                "is_anomalous": False,
                "flags": [f"M9 detector bypassed: {exc}"],
            }


quality_gate = TelemetryQualityGate()
