"""
backend/app/services/ingestion/adapters/iot.py
=============================================
Ingestion adapter for slope and riverbed IoT sensor arrays (extensometers, piezometers, geophones).
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.core.provenance import DataMode
from backend.app.services.ingestion.adapters.base import DataSourceAdapter, NormalizedObservation


class IoTTelemetryAdapter(DataSourceAdapter):
    def __init__(self):
        super().__init__(
            source_id="UPPER_BEAS_IOT",
            source_type="IOT_EXTENSOMETER",
            evidence_tier="DATA_ACQUIRED",
            data_mode=DataMode.REAL_FIELD_OBSERVATION.value,
        )

    @property
    def is_configured(self) -> bool:
        # Ingestion endpoint for LoRa gateway packets is natively active within FLOODY SHIELD
        return True

    def normalize(self, raw_record: Dict[str, Any]) -> NormalizedObservation:
        """
        Normalizes geotechnical sensor package.
        """
        stn_id = raw_record.get("station_id") or "IOT_SLOPE_AUT_01"
        ts_raw = raw_record.get("timestamp") or raw_record.get("time")
        if isinstance(ts_raw, str):
            ts = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        elif isinstance(ts_raw, datetime.datetime):
            ts = ts_raw
        else:
            ts = datetime.datetime.now(datetime.timezone.utc)

        lat = float(raw_record.get("latitude") or 31.75)
        lon = float(raw_record.get("longitude") or 77.20)
        elev = float(raw_record.get("elevation_m") or 1100.0)

        pwp = float(raw_record.get("pore_pressure_kpa") or 0.0)
        disp = float(raw_record.get("displacement_mm") or 0.0)
        ae = float(raw_record.get("acoustic_emission_db") or 0.0)
        rain = float(raw_record.get("rainfall_rate_mmh") or 0.0)
        stage = float(raw_record.get("water_level_m") or 0.0)

        raw_ref = raw_record.get("packet_id") or raw_record.get("seq_no")
        idem_hash = self.compute_idempotency_hash(stn_id, ts, str(raw_ref) if raw_ref is not None else None)

        # Primary value selection based on sensor focus
        if disp > 0.0:
            primary_val = disp
            unit = "mm"
            obs_type = "DISPLACEMENT"
        elif pwp > 0.0:
            primary_val = pwp
            unit = "kPa"
            obs_type = "PORE_WATER_PRESSURE"
        elif rain > 0.0:
            primary_val = rain
            unit = "mm/h"
            obs_type = "PRECIPITATION"
        elif stage > 0.0:
            primary_val = stage
            unit = "m"
            obs_type = "WATER_LEVEL"
        else:
            primary_val = 0.0
            unit = "none"
            obs_type = "GEOTECHNICAL_MULTI"

        return NormalizedObservation(
            station_id=stn_id,
            source_id=self.source_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=elev,
            values={
                "pore_pressure_kpa": pwp,
                "displacement_mm": disp,
                "acoustic_emission_db": ae,
                "rainfall_rate_mmh": rain,
                "water_level_m": stage,
            },
            idempotency_hash=idem_hash,
            provenance=self.provenance(),
            source_type=self.source_type,
            observation_type=obs_type,
            acquisition_timestamp=ts,
            spatial_extent={"latitude": lat, "longitude": lon},
            value=primary_val,
            unit=unit,
            quality={"battery_volts": float(raw_record.get("battery_volts", 3.7)), "rssi": float(raw_record.get("rssi", -80.0))},
            source_status="ONLINE",
            raw_reference=str(raw_ref) if raw_ref is not None else None,
        )
