"""
backend/app/services/ingestion/adapters/satellite.py
====================================================
Ingestion adapter for Sentinel-1 SAR and Sentinel-2 Optical acquisitions covering Upper Beas.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation


class SentinelSceneAdapter(DataSourceAdapter):
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(
            source_id="SENTINEL_COPERNICUS",
            source_type="SATELLITE",
            evidence_tier="VALIDATION_GRADE_DATA",
            data_mode=DataMode.REMOTE_SENSING_OBSERVATION.value,
        )
        self.endpoint = endpoint or settings.SENTINEL_COPERNICUS_ENDPOINT
        self.api_key = api_key or settings.SENTINEL_COPERNICUS_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.endpoint.strip())

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes Sentinel-1/2 scene metadata.
        """
        scene_id = raw_record.get("scene_id") or raw_record.get("product_id") or "S1A_IW_GRDH_1SDV_20230710"
        ts_raw = raw_record.get("acquisition_time") or raw_record.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        bbox = raw_record.get("bbox") or [76.80, 31.40, 77.45, 32.45]
        center_lat = (bbox[1] + bbox[3]) / 2.0
        center_lon = (bbox[0] + bbox[2]) / 2.0

        mission = raw_record.get("mission", "SENTINEL-1")
        cloud_cover = float(raw_record.get("cloud_cover_pct", 0.0))
        inundated_area_km2 = float(raw_record.get("inundated_area_km2", 0.0))

        raw_ref = raw_record.get("granule_id") or raw_record.get("file_uri")
        idem_hash = self.compute_idempotency_hash(scene_id, ts, raw_ref)

        obs_type = "SAR_INUNDATION" if "SENTINEL-1" in mission.upper() or "S1" in mission.upper() else "OPTICAL_SCENE"

        return NormalizedObservation(
            station_id=scene_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=center_lat,
            longitude=center_lon,
            values={
                "mission": mission,
                "sensor_mode": raw_record.get("sensor_mode", "IW"),
                "cloud_cover_pct": cloud_cover,
                "bbox": bbox,
                "file_uri": raw_record.get("file_uri", ""),
                "inundated_area_km2": inundated_area_km2,
            },
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type=obs_type,
            acquisition_timestamp=ts,
            spatial_extent={"bbox": bbox, "crs": "EPSG:4326"},
            value=inundated_area_km2 if obs_type == "SAR_INUNDATION" else (100.0 - cloud_cover),
            unit="km2" if obs_type == "SAR_INUNDATION" else "%",
            quality={"cloud_cover_pct": cloud_cover, "orbit_direction": raw_record.get("orbit_direction", "DESCENDING")},
            source_status="ONLINE" if self.is_configured else "NOT_CONFIGURED",
            raw_reference=raw_ref,
        )
