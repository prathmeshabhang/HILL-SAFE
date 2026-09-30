"""
backend/app/services/ingestion/source_health.py
===============================================
Operational health, freshness tracking, and availability monitor for external agencies
and remote sensing feeds. Evaluates source degradation, latency skew, and fail-soft readiness.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("floody.ingestion.source_health")


class SourceHealthStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    OFFLINE = "OFFLINE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class SourceHealthRecord(BaseModel):
    source_id: str
    source_type: str
    status: SourceHealthStatus
    is_configured: bool
    last_poll_at: Optional[datetime.datetime] = None
    last_success_at: Optional[datetime.datetime] = None
    last_observation_timestamp: Optional[datetime.datetime] = None
    freshness_age_seconds: Optional[float] = None
    freshness_threshold_seconds: float
    success_count: int = 0
    error_count: int = 0
    consecutive_failures: int = 0
    last_error_message: Optional[str] = None
    active_stations_or_granules: List[str] = Field(default_factory=list)


class MultiSourceHealthMonitor:
    """
    Central monitor tracking heartbeat, data freshness, and error rates across all 6
    ingestion sources: INSAT-3DS, SMAP, Field IoT, IMD AWS, CWC River, Sentinel.
    """

    def __init__(self):
        self._sources: Dict[str, SourceHealthRecord] = {}
        self._init_defaults()

    def _init_defaults(self):
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        default_configs = [
            {
                "source_id": "INSAT_3DS",
                "source_type": "SATELLITE",
                "threshold_sec": settings.INSAT3DS_FRESHNESS_MINUTES * 60.0,
                "is_configured": bool(settings.INSAT3DS_MOSDAC_ENDPOINT),
            },
            {
                "source_id": "SMAP",
                "source_type": "SATELLITE",
                "threshold_sec": settings.SMAP_FRESHNESS_HOURS * 3600.0,
                "is_configured": bool(settings.SMAP_EARTHDATA_ENDPOINT),
            },
            {
                "source_id": "UPPER_BEAS_IOT",
                "source_type": "IOT_EXTENSOMETER",
                "threshold_sec": settings.IOT_FIELD_FRESHNESS_MINUTES * 60.0,
                "is_configured": True,  # Native LoRa API is always configured
            },
            {
                "source_id": "IMD_AWS",
                "source_type": "AGENCY_AWS",
                "threshold_sec": settings.IMD_AWS_FRESHNESS_MINUTES * 60.0,
                "is_configured": bool(settings.IMD_AWS_ENDPOINT),
            },
            {
                "source_id": "CWC_RIVER",
                "source_type": "RIVER_GAUGE",
                "threshold_sec": settings.CWC_RIVER_FRESHNESS_MINUTES * 60.0,
                "is_configured": bool(settings.CWC_RIVER_ENDPOINT),
            },
            {
                "source_id": "SENTINEL_COPERNICUS",
                "source_type": "SATELLITE",
                "threshold_sec": settings.SENTINEL_FRESHNESS_HOURS * 3600.0,
                "is_configured": bool(settings.SENTINEL_COPERNICUS_ENDPOINT),
            },
        ]

        for cfg in default_configs:
            is_cfg = cfg["is_configured"]
            initial_status = SourceHealthStatus.UNAVAILABLE if not is_cfg else SourceHealthStatus.ONLINE
            self._sources[cfg["source_id"]] = SourceHealthRecord(
                source_id=cfg["source_id"],
                source_type=cfg["source_type"],
                status=initial_status,
                is_configured=is_cfg,
                freshness_threshold_seconds=cfg["threshold_sec"],
            )

    def record_poll_success(
        self,
        source_id: str,
        observation_timestamp: datetime.datetime,
        station_or_granule_id: Optional[str] = None,
        poll_time: Optional[datetime.datetime] = None,
    ) -> SourceHealthRecord:
        """Records successful fetch/reception of an observation from a source."""
        now = poll_time or datetime.datetime.now(datetime.timezone.utc)
        if observation_timestamp.tzinfo is None:
            observation_timestamp = observation_timestamp.replace(tzinfo=datetime.timezone.utc)

        if source_id not in self._sources:
            self._sources[source_id] = SourceHealthRecord(
                source_id=source_id,
                source_type="UNKNOWN",
                status=SourceHealthStatus.ONLINE,
                is_configured=True,
                freshness_threshold_seconds=3600.0,
            )

        rec = self._sources[source_id]
        rec.is_configured = True
        rec.last_poll_at = now
        rec.last_success_at = now
        rec.last_observation_timestamp = observation_timestamp
        rec.success_count += 1
        rec.consecutive_failures = 0
        rec.last_error_message = None

        if station_or_granule_id and station_or_granule_id not in rec.active_stations_or_granules:
            rec.active_stations_or_granules.append(station_or_granule_id)
            if len(rec.active_stations_or_granules) > 50:
                rec.active_stations_or_granules.pop(0)

        # Freshness evaluation
        age = max(0.0, (now - observation_timestamp).total_seconds())
        rec.freshness_age_seconds = age

        if age <= rec.freshness_threshold_seconds:
            rec.status = SourceHealthStatus.ONLINE
        elif age <= rec.freshness_threshold_seconds * 3.0:
            rec.status = SourceHealthStatus.STALE
        else:
            rec.status = SourceHealthStatus.OFFLINE

        return rec

    def set_configured(self, source_id: str, is_configured: bool = True):
        """Explicitly update configured state of a data source."""
        if source_id in self._sources:
            self._sources[source_id].is_configured = is_configured
            if not is_configured:
                self._sources[source_id].status = SourceHealthStatus.NOT_CONFIGURED

    def record_poll_failure(
        self,
        source_id: str,
        error_message: str,
        poll_time: Optional[datetime.datetime] = None,
    ) -> SourceHealthRecord:
        """Records a connection timeout, HTTP error, or parsing failure from a source."""
        now = poll_time or datetime.datetime.now(datetime.timezone.utc)

        if source_id not in self._sources:
            self._sources[source_id] = SourceHealthRecord(
                source_id=source_id,
                source_type="UNKNOWN",
                status=SourceHealthStatus.ERROR,
                is_configured=True,
                freshness_threshold_seconds=3600.0,
            )

        rec = self._sources[source_id]
        rec.last_poll_at = now
        rec.error_count += 1
        rec.consecutive_failures += 1
        rec.last_error_message = error_message

        if not rec.is_configured and rec.success_count == 0:
            rec.status = SourceHealthStatus.NOT_CONFIGURED
        elif rec.consecutive_failures >= 3:
            rec.status = SourceHealthStatus.ERROR
        else:
            rec.status = SourceHealthStatus.DEGRADED

        logger.warning(
            f"Source [{source_id}] poll failure (consecutive={rec.consecutive_failures}): {error_message}"
        )
        return rec

    def evaluate_health(
        self,
        source_id: str,
        as_of: Optional[datetime.datetime] = None,
    ) -> SourceHealthRecord:
        """Evaluates live freshness status against current or specified evaluation time."""
        now = as_of or datetime.datetime.now(datetime.timezone.utc)
        if source_id not in self._sources:
            return SourceHealthRecord(
                source_id=source_id,
                source_type="UNKNOWN",
                status=SourceHealthStatus.UNAVAILABLE,
                is_configured=False,
                freshness_threshold_seconds=3600.0,
            )

        rec = self._sources[source_id]
        if not rec.is_configured and rec.success_count == 0:
            rec.status = SourceHealthStatus.NOT_CONFIGURED
            return rec

        if rec.last_observation_timestamp:
            obs_ts = rec.last_observation_timestamp
            if obs_ts.tzinfo is None:
                obs_ts = obs_ts.replace(tzinfo=datetime.timezone.utc)
            age = max(0.0, (now - obs_ts).total_seconds())
            rec.freshness_age_seconds = age

            if rec.consecutive_failures >= 3:
                rec.status = SourceHealthStatus.ERROR
            elif rec.consecutive_failures > 0:
                rec.status = SourceHealthStatus.DEGRADED
            elif age > rec.freshness_threshold_seconds * 3.0:
                rec.status = SourceHealthStatus.OFFLINE
            elif age > rec.freshness_threshold_seconds:
                rec.status = SourceHealthStatus.STALE
            else:
                rec.status = SourceHealthStatus.ONLINE
        else:
            if rec.consecutive_failures >= 3:
                rec.status = SourceHealthStatus.ERROR
            elif rec.consecutive_failures > 0:
                rec.status = SourceHealthStatus.DEGRADED
            else:
                rec.status = SourceHealthStatus.UNAVAILABLE

        return rec

    def get_all_source_health(
        self,
        as_of: Optional[datetime.datetime] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Returns health summaries for all monitored sources."""
        now = as_of or datetime.datetime.now(datetime.timezone.utc)
        report: Dict[str, Dict[str, Any]] = {}
        for source_id in self._sources:
            rec = self.evaluate_health(source_id, as_of=now)
            report[source_id] = {
                "source_id": rec.source_id,
                "source_type": rec.source_type,
                "status": rec.status.value,
                "is_configured": rec.is_configured,
                "last_poll_at": rec.last_poll_at.isoformat() if rec.last_poll_at else None,
                "last_success_at": rec.last_success_at.isoformat() if rec.last_success_at else None,
                "last_observation_timestamp": (
                    rec.last_observation_timestamp.isoformat() if rec.last_observation_timestamp else None
                ),
                "freshness_age_seconds": rec.freshness_age_seconds,
                "freshness_threshold_seconds": rec.freshness_threshold_seconds,
                "success_count": rec.success_count,
                "error_count": rec.error_count,
                "consecutive_failures": rec.consecutive_failures,
                "last_error_message": rec.last_error_message,
                "active_stations": rec.active_stations_or_granules,
            }
        return report

    def get_basin_connectivity_summary(self) -> Dict[str, Any]:
        """Provides high-level operational capacity for multi-source risk fusion."""
        healths = self.get_all_source_health()
        total = len(healths)
        online_count = sum(1 for h in healths.values() if h["status"] == SourceHealthStatus.ONLINE.value)
        degraded_count = sum(1 for h in healths.values() if h["status"] in (SourceHealthStatus.DEGRADED.value, SourceHealthStatus.STALE.value))
        offline_count = sum(1 for h in healths.values() if h["status"] in (SourceHealthStatus.OFFLINE.value, SourceHealthStatus.ERROR.value, SourceHealthStatus.UNAVAILABLE.value, SourceHealthStatus.NOT_CONFIGURED.value))

        # Operational capacity score
        capacity_pct = round(((online_count + (degraded_count * 0.5)) / max(1, total)) * 100.0, 1)

        return {
            "monitored_sources_count": total,
            "online_count": online_count,
            "degraded_or_stale_count": degraded_count,
            "offline_or_unavailable_count": offline_count,
            "operational_capacity_pct": capacity_pct,
            "is_fail_soft_active": degraded_count > 0 or offline_count > 0,
            "sources": healths,
        }


# Global singleton monitor
source_health_monitor = MultiSourceHealthMonitor()
