"""
backend/app/services/ingestion/adapters/weather.py
==================================================
Ingestion adapters for IMD Automated Weather Stations (AWS) and NASA/JAXA GPM IMERG gridded rainfall.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation


class IMDAWSAdapter(DataSourceAdapter):
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(
            source_id="IMD_AWS",
            source_type="AGENCY_AWS",
            evidence_tier="DATA_ACQUIRED",
            data_mode=DataMode.REAL_AGENCY_DATA.value,
        )
        self.endpoint = endpoint or settings.IMD_AWS_ENDPOINT
        self.api_key = api_key or settings.IMD_AWS_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.endpoint.strip())

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes IMD AWS payload into canonical schema.
        Handles fields like 'station_code', 'obs_time', 'rain_rate_mm', 'accum_rain_24h'.
        """
        stn_id = raw_record.get("station_code") or raw_record.get("station_id") or "STN_KULLU_IMD"
        ts_raw = raw_record.get("obs_time") or raw_record.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        lat = float(raw_record.get("lat") or raw_record.get("latitude") or 31.95)
        lon = float(raw_record.get("lon") or raw_record.get("longitude") or 77.10)
        elev = float(raw_record.get("elevation_m") or 1250.0)

        rain_rate = float(raw_record.get("rain_rate_mm") or raw_record.get("rainfall_rate_mmh") or 0.0)
        accum_24h = float(raw_record.get("accum_rain_24h") or raw_record.get("accumulated_24h_mm") or 0.0)

        raw_ref = raw_record.get("record_id") or raw_record.get("packet_id")
        idem_hash = self.compute_idempotency_hash(stn_id, ts, raw_ref)

        return NormalizedObservation(
            station_id=stn_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=elev,
            values={
                "rainfall_rate_mmh": rain_rate,
                "accumulated_24h_mm": accum_24h,
                "temperature_c": raw_record.get("temp_c"),
                "humidity_pct": raw_record.get("humidity_pct"),
            },
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type="PRECIPITATION",
            acquisition_timestamp=ts,
            spatial_extent={"latitude": lat, "longitude": lon},
            value=rain_rate,
            unit="mm/h",
            quality={"qc_flag": raw_record.get("qc_flag", "PASS")},
            source_status="ONLINE" if self.is_configured else "NOT_CONFIGURED",
            raw_reference=raw_ref,
        )


class GPMIMERGAdapter(DataSourceAdapter):
    def __init__(self):
        super().__init__(
            source_id="GPM_IMERG",
            source_type="SATELLITE",
            evidence_tier="VALIDATION_GRADE_DATA",
            data_mode=DataMode.REMOTE_SENSING_OBSERVATION.value,
        )

    @property
    def is_configured(self) -> bool:
        return False

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes GPM IMERG 0.1° satellite precipitation product.
        """
        lat = float(raw_record.get("lat") or 32.0)
        lon = float(raw_record.get("lon") or 77.1)
        grid_id = raw_record.get("grid_cell_id") or f"GPM_{lat:.1f}_{lon:.1f}"
        ts_raw = raw_record.get("granule_time") or raw_record.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        rain_rate = float(raw_record.get("precipitation_cal_mmh") or raw_record.get("rainfall_rate_mmh") or 0.0)

        raw_ref = raw_record.get("granule_id")
        idem_hash = self.compute_idempotency_hash(grid_id, ts, raw_ref)

        return NormalizedObservation(
            station_id=grid_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=raw_record.get("elevation_m"),
            values={
                "rainfall_rate_mmh": rain_rate,
                "precipitation_quality_index": float(raw_record.get("quality_index", 0.9)),
            },
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type="PRECIPITATION",
            acquisition_timestamp=ts,
            spatial_extent={"latitude": lat, "longitude": lon},
            value=rain_rate,
            unit="mm/h",
            quality={"quality_index": float(raw_record.get("quality_index", 0.9))},
            source_status="ONLINE" if self.is_configured else "NOT_CONFIGURED",
            raw_reference=raw_ref,
        )
