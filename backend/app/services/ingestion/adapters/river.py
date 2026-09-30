"""
backend/app/services/ingestion/adapters/river.py
================================================
Ingestion adapter for Central Water Commission (CWC) and Himachal Jal Shakti river stage/discharge gauges.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation


class CWCRiverAdapter(DataSourceAdapter):
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(
            source_id="CWC_RIVER",
            source_type="RIVER_GAUGE",
            evidence_tier="DATA_ACQUIRED",
            data_mode=DataMode.REAL_AGENCY_DATA.value,
        )
        self.endpoint = endpoint or settings.CWC_RIVER_ENDPOINT
        self.api_key = api_key or settings.CWC_RIVER_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.endpoint.strip())

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes CWC gauge telemetry.
        """
        stn_id = raw_record.get("site_id") or raw_record.get("station_id") or "CWC_BHUNTAR_01"
        ts_raw = raw_record.get("measurement_time") or raw_record.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        lat = float(raw_record.get("latitude") or 31.89)
        lon = float(raw_record.get("longitude") or 77.15)
        water_level = float(raw_record.get("water_level_m") or raw_record.get("stage_m") or 0.0)
        discharge = float(raw_record.get("discharge_m3s") or 0.0)

        raw_ref = raw_record.get("record_id")
        idem_hash = self.compute_idempotency_hash(stn_id, ts, raw_ref)

        return NormalizedObservation(
            station_id=stn_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=raw_record.get("elevation_m", 1080.0),
            values={
                "water_level_m": water_level,
                "discharge_m3s": discharge,
                "warning_level_m": float(raw_record.get("warning_level_m", 5.0)),
                "danger_level_m": float(raw_record.get("danger_level_m", 7.0)),
                "hfl_m": float(raw_record.get("hfl_m", 9.5)),
            },
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type="WATER_LEVEL",
            acquisition_timestamp=ts,
            spatial_extent={"latitude": lat, "longitude": lon},
            value=water_level,
            unit="m",
            quality={"qc_status": raw_record.get("qc_status", "VALIDATED")},
            source_status="ONLINE" if self.is_configured else "NOT_CONFIGURED",
            raw_reference=raw_ref,
        )
