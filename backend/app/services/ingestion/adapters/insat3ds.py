"""
backend/app/services/ingestion/adapters/insat3ds.py
===================================================
Ingestion adapter for ISRO/MOSDAC INSAT-3DS meteorological satellite products.
Processes Hydro-Estimator Precipitation (HEM), IMSRA rain rate, and TIR-1 brightness temperature
covering the Upper Beas Basin and Western Himalayan orographic region.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation


class INSAT3DSAdapter(DataSourceAdapter):
    """
    Adapter for ISRO / MOSDAC INSAT-3DS geostationary meteorological payload.
    Extracts precipitation estimates (HEM, IMSRA) and thermal infrared (TIR-1) brightness temperature.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(
            source_id="INSAT_3DS",
            source_type="SATELLITE",
            evidence_tier="OPERATIONAL_AGENCY",
            data_mode=DataMode.REMOTE_SENSING_OBSERVATION.value,
        )
        self.endpoint = endpoint or settings.INSAT3DS_MOSDAC_ENDPOINT
        self.api_key = api_key or settings.INSAT3DS_API_KEY

    @property
    def is_configured(self) -> bool:
        """True only if an explicit MOSDAC endpoint or API key has been provisioned."""
        return bool(self.endpoint and self.endpoint.strip())

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes raw MOSDAC HDF5/NetCDF metadata or JSON API response into canonical schema.
        Handles HEM rain rate, IMSRA, TIR-1 temperature, and cloud top properties.
        """
        product_id = (
            raw_record.get("product_id")
            or raw_record.get("granule_id")
            or raw_record.get("scene_id")
            or f"3DS_IMG_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%j%H%M')}"
        )

        ts_raw = (
            raw_record.get("acquisition_time")
            or raw_record.get("timestamp")
            or raw_record.get("scan_start_utc")
        )
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        # Coordinate resolution: explicit center or bbox midpoint, fallback to Beas basin centroid
        bbox = raw_record.get("bbox") or [
            settings.MIN_LONGITUDE,
            settings.MIN_LATITUDE,
            settings.MAX_LONGITUDE,
            settings.MAX_LATITUDE,
        ]
        lat = float(raw_record.get("latitude") or raw_record.get("lat") or (bbox[1] + bbox[3]) / 2.0)
        lon = float(raw_record.get("longitude") or raw_record.get("lon") or (bbox[0] + bbox[2]) / 2.0)

        # Product values extraction
        hem_rate = float(
            raw_record.get("hem_rain_rate_mmh")
            or raw_record.get("rainfall_rate_mmh")
            or raw_record.get("precipitation_mmh")
            or 0.0
        )
        imsra_rate = float(
            raw_record.get("imsra_rain_rate_mmh")
            or raw_record.get("imsra_mmh")
            or 0.0
        )
        tir1_temp = float(
            raw_record.get("tir1_brightness_temp_k")
            or raw_record.get("bt_tir1_k")
            or 0.0
        )
        cloud_cover = float(raw_record.get("cloud_cover_pct") or 0.0)

        # Determine primary measurement
        if hem_rate > 0.0 or imsra_rate > 0.0 or "rainfall" in str(raw_record).lower():
            primary_val = hem_rate if hem_rate > 0.0 else imsra_rate
            primary_unit = "mm/h"
            obs_type = "PRECIPITATION"
        elif tir1_temp > 0.0:
            primary_val = tir1_temp
            primary_unit = "K"
            obs_type = "BRIGHTNESS_TEMPERATURE"
        else:
            primary_val = hem_rate
            primary_unit = "mm/h"
            obs_type = "PRECIPITATION"

        raw_ref = raw_record.get("granule_id") or raw_record.get("file_uri") or raw_record.get("h5_path")
        idem_hash = self.compute_idempotency_hash(product_id, ts, raw_ref)

        quality_dict = {
            "retrieval_status": raw_record.get("retrieval_status", "NOMINAL"),
            "cloud_mask": raw_record.get("cloud_mask", "CONVECTIVE" if cloud_cover > 50 else "CLEAR"),
            "calibration_valid": bool(raw_record.get("calibration_valid", True)),
            "pixel_resolution_km": float(raw_record.get("spatial_resolution_km", 4.0)),
        }

        return NormalizedObservation(
            station_id=product_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=raw_record.get("elevation_m"),
            values={
                "rainfall_rate_mmh": primary_val if obs_type == "PRECIPITATION" else hem_rate,
                "hem_rain_rate_mmh": hem_rate,
                "imsra_rain_rate_mmh": imsra_rate,
                "tir1_brightness_temp_k": tir1_temp,
                "cloud_cover_pct": cloud_cover,
                "satellite_platform": "INSAT-3DS",
                "instrument": raw_record.get("instrument", "IMAGER"),
            },
            quality_state=raw_record.get("quality_state", "FRESH"),
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type=obs_type,
            acquisition_timestamp=ts,
            spatial_extent={"bbox": bbox, "crs": "EPSG:4326"},
            value=primary_val,
            unit=primary_unit,
            quality=quality_dict,
            source_status="ONLINE" if self.is_configured else "NOT_CONFIGURED",
            raw_reference=raw_ref,
        )
