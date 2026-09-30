"""
backend/app/services/ingestion/multi_source_service.py
======================================================
Multi-Source Observation & Fail-Soft Aggregation Service for FLOODY SHIELD.
Orchestrates heterogeneous ingestion across INSAT-3DS, SMAP, IoT, IMD AWS, CWC, and Sentinel,
enforcing strict provenance tagging and fail-soft composite risk intelligence.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation
from backend.app.services.ingestion.adapters.insat3ds import INSAT3DSAdapter
from backend.app.services.ingestion.adapters.smap import SMAPAdapter
from backend.app.services.ingestion.adapters.iot import IoTTelemetryAdapter
from backend.app.services.ingestion.adapters.weather import IMDAWSAdapter, GPMIMERGAdapter
from backend.app.services.ingestion.adapters.river import CWCRiverAdapter
from backend.app.services.ingestion.adapters.satellite import SentinelSceneAdapter
from backend.app.services.ingestion.ingestion_service import TelemetryIngestionService
from backend.app.services.ingestion.source_health import (
    MultiSourceHealthMonitor,
    SourceHealthStatus,
    source_health_monitor,
)

logger = get_logger("floody.ingestion.multi_source")


class MultiSourceObservationService:
    """
    Unified manager for multi-source ingestion.
    Coordinates external agency feeds, satellite rasters, and IoT telemetry.
    Guarantees fail-soft continuity: when any source fails or goes stale, the remaining
    sources continue processing without fabricating synthetic substitution data.
    """

    def __init__(
        self,
        ingestion_service: Optional[TelemetryIngestionService] = None,
        health_monitor: Optional[MultiSourceHealthMonitor] = None,
    ):
        self.ingestion_service = ingestion_service or TelemetryIngestionService()
        self.health_monitor = health_monitor or source_health_monitor

        # Instantiated adapters
        self.adapters: Dict[str, DataSourceAdapter] = {
            "INSAT_3DS": INSAT3DSAdapter(),
            "SMAP": SMAPAdapter(),
            "UPPER_BEAS_IOT": IoTTelemetryAdapter(),
            "IMD_AWS": IMDAWSAdapter(),
            "CWC_RIVER": CWCRiverAdapter(),
            "SENTINEL_COPERNICUS": SentinelSceneAdapter(),
            "GPM_IMERG": GPMIMERGAdapter(),
        }

    def get_adapter(self, source_id: str) -> Optional[DataSourceAdapter]:
        return self.adapters.get(source_id)

    def normalize_and_ingest(
        self,
        db: Session,
        source_id: str,
        raw_record: Dict[str, Any],
        ingestion_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalizes a raw external record via the designated adapter and commits it
        through the canonical TelemetryIngestionService pipeline.
        Updates source health and freshness statistics.
        """
        adapter = self.get_adapter(source_id)
        if not adapter:
            err_msg = f"No adapter registered for data source: {source_id}"
            self.health_monitor.record_poll_failure(source_id, err_msg)
            raise ValueError(err_msg)

        try:
            norm_obs = adapter.normalize(raw_record)
        except Exception as exc:
            err_msg = f"Adapter normalization failed for {source_id}: {exc}"
            self.health_monitor.record_poll_failure(source_id, err_msg)
            raise

        # Pipe through canonical quality gate and database persistence
        res = self.ingestion_service.ingest_normalized_observation(
            db=db,
            obs=norm_obs,
            ingestion_run_id=ingestion_run_id,
        )

        # Update health monitor on successful ingestion
        self.health_monitor.record_poll_success(
            source_id=source_id,
            observation_timestamp=norm_obs.timestamp,
            station_or_granule_id=norm_obs.station_id,
        )

        res["normalized_observation"] = norm_obs.model_dump()
        return res

    def get_composite_basin_snapshot(
        self,
        recent_observations: Optional[List[NormalizedObservation]] = None,
        as_of: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes a multi-source observation snapshot of the Upper Beas Basin.
        Enforces FAIL-SOFT rules:
        - Never fabricates missing or stale source data.
        - Computes dynamic confidence based on source availability and freshness.
        - Clearly lists active, stale, and missing sources.
        """
        now = as_of or datetime.datetime.now(datetime.timezone.utc)
        health_report = self.health_monitor.get_all_source_health(as_of=now)

        obs_by_type: Dict[str, List[NormalizedObservation]] = {
            "PRECIPITATION": [],
            "WATER_LEVEL": [],
            "SOIL_MOISTURE": [],
            "DISPLACEMENT": [],
            "SAR_INUNDATION": [],
        }

        active_sources: set[str] = set()

        if recent_observations:
            for obs in recent_observations:
                obs_ts = obs.timestamp if obs.timestamp.tzinfo else obs.timestamp.replace(tzinfo=datetime.timezone.utc)
                source_cfg = health_report.get(obs.source_id, {})
                threshold_sec = source_cfg.get("freshness_threshold_seconds", 3600.0)
                age = (now - obs_ts).total_seconds()

                # Only include fresh observations (not expired)
                if age <= threshold_sec * 3.0:
                    obs_type = obs.observation_type
                    if obs_type in obs_by_type:
                        obs_by_type[obs_type].append(obs)
                    elif "RAIN" in obs_type or "PRECIP" in obs_type:
                        obs_by_type["PRECIPITATION"].append(obs)
                    active_sources.add(obs.source_id)

        # Baseline weight allocation for multi-hazard situational awareness
        weights = {
            "PRECIPITATION": 0.35,
            "WATER_LEVEL": 0.25,
            "SOIL_MOISTURE": 0.20,
            "DISPLACEMENT": 0.10,
            "SAR_INUNDATION": 0.10,
        }

        available_weight = 0.0
        for obs_type, items in obs_by_type.items():
            if items:
                available_weight += weights.get(obs_type, 0.0)

        # Determine composite status
        if available_weight >= 0.70:
            fusion_state = "NOMINAL_MULTI_SOURCE"
            confidence = round(available_weight, 2)
        elif available_weight > 0.0:
            fusion_state = "DEGRADED_PARTIAL_SOURCES"
            confidence = round(available_weight, 2)
        else:
            fusion_state = "UNAVAILABLE_NO_DATA"
            confidence = 0.0

        # Primary physical summaries (using real data only)
        max_rain = max([o.value for o in obs_by_type["PRECIPITATION"] if o.value is not None], default=None)
        max_water = max([o.value for o in obs_by_type["WATER_LEVEL"] if o.value is not None], default=None)
        avg_soil_moist = (
            sum(o.value for o in obs_by_type["SOIL_MOISTURE"] if o.value is not None) / len(obs_by_type["SOIL_MOISTURE"])
            if obs_by_type["SOIL_MOISTURE"] else None
        )
        max_displacement = max([o.value for o in obs_by_type["DISPLACEMENT"] if o.value is not None], default=None)

        # Determine missing or stale feeds
        all_monitored = set(self.adapters.keys())
        missing_sources = sorted(list(all_monitored - active_sources))

        return {
            "timestamp": now.isoformat(),
            "fusion_state": fusion_state,
            "confidence_score": confidence,
            "active_sources_count": len(active_sources),
            "active_sources": sorted(list(active_sources)),
            "missing_or_stale_sources": missing_sources,
            "physical_indicators": {
                "max_rainfall_rate_mmh": max_rain,
                "max_water_level_m": max_water,
                "avg_soil_moisture_cm3cm3": round(avg_soil_moist, 4) if avg_soil_moist is not None else None,
                "max_slope_displacement_mm": max_displacement,
            },
            "source_health": health_report,
            "fail_soft_engaged": len(missing_sources) > 0,
            "data_authenticity_notice": (
                "Composite synthesized strictly from verified real-world feeds. "
                "Missing sensors are not filled with synthetic approximations."
            ),
        }


# Global singleton service
multi_source_service = MultiSourceObservationService()
