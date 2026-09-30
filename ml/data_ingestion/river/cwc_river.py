"""
ml/data_ingestion/river/cwc_river.py
===================================
Central Water Commission (CWC) & State Water Resources Telemetry Ingestion Adapter.
Parses river gauge stage (water level in meters) and discharge (m3/s) along the Beas River.
Enforces statutory CWC danger and warning thresholds, sensor rate-of-change, and quality flags.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_sensor_range, check_spatial_bounds


# Authoritative CWC Hydrological Stations on Beas River (Upper Basin)
CWC_BEAS_STATIONS: Dict[str, Dict[str, Any]] = {
    "CWC_MANALI": {
        "name": "Manali (Old Bridge)",
        "lat": 32.2396,
        "lon": 77.1887,
        "warning_level_m": 4.5,
        "danger_level_m": 5.8,
        "hfl_m": 7.2,
        "zero_gauge_rl_m": 1920.5,
    },
    "CWC_PATLIKUHAL": {
        "name": "Patlikuhal",
        "lat": 32.1245,
        "lon": 77.1528,
        "warning_level_m": 6.0,
        "danger_level_m": 7.5,
        "hfl_m": 9.1,
        "zero_gauge_rl_m": 1420.0,
    },
    "CWC_KULLU": {
        "name": "Kullu (Akhara Bazar)",
        "lat": 31.9610,
        "lon": 77.1120,
        "warning_level_m": 8.0,
        "danger_level_m": 10.0,
        "hfl_m": 12.8,
        "zero_gauge_rl_m": 1180.2,
    },
    "CWC_BHUNTAR": {
        "name": "Bhuntar (Beas-Parbati Confluence)",
        "lat": 31.8742,
        "lon": 77.1489,
        "warning_level_m": 9.5,
        "danger_level_m": 11.5,
        "hfl_m": 14.2,
        "zero_gauge_rl_m": 1055.0,
    },
    "CWC_THALOUT": {
        "name": "Thalout (Larji Reservoir Inflow)",
        "lat": 31.7144,
        "lon": 77.2185,
        "warning_level_m": 12.0,
        "danger_level_m": 14.5,
        "hfl_m": 18.0,
        "zero_gauge_rl_m": 940.0,
    },
}


@dataclass
class CWCRiverRecord:
    station_id: str
    station_name: str
    timestamp: str          # ISO 8601 UTC
    latitude: float
    longitude: float
    water_level_m: float
    discharge_m3s: Optional[float] = None
    rate_of_rise_mh: Optional[float] = None
    warning_level_m: float = 0.0
    danger_level_m: float = 0.0
    hfl_m: float = 0.0
    status_indicator: str = "NORMAL"  # NORMAL | ABOVE_WARNING | ABOVE_DANGER | ABOVE_HFL
    quality_flag: str = "VALID"       # VALID | SENSOR_FAULT | RATE_EXCEEDED | OUT_OF_BOUNDS
    source: str = "CWC_WRIS"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CWCRiverAdapter:
    """
    Ingests, audits, and formats Central Water Commission stage and discharge observations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.provenance = DatasetProvenance(
            dataset_id="river_cwc_telemetry",
            provenance_type=ProvenanceType.OBSERVATION,
            source_agency="Central Water Commission (CWC) / Ministry of Jal Shakti",
            geographic_aoi="Upper Beas River Basin (Manali to Thalout)",
            temporal_coverage="Monsoon Hydrographic Telemetry (Hourly)",
            spatial_resolution="Point in-situ telemetric gauge",
            license_type="National Water Data Sharing Policy",
            doi_or_url="https://indiawris.gov.in",
            is_field_verified=True,
            citation="CWC Indus Basin Organization, Hydrological Observation Circle Shimla",
        )

    def parse_gauge_reading(
        self,
        raw_data: Dict[str, Any],
        previous_reading: Optional[CWCRiverRecord] = None,
    ) -> Tuple[Optional[CWCRiverRecord], Optional[str]]:
        """Parses a single gauge reading, checks physical limits and statutory marks."""
        st_id = raw_data.get("station_id")
        ts = raw_data.get("timestamp")
        level_m = float(raw_data.get("water_level_m", -1.0))

        if not st_id or not ts:
            return None, "Missing station_id or timestamp"

        meta = CWC_BEAS_STATIONS.get(st_id, {})
        st_name = raw_data.get("station_name") or meta.get("name", "Unknown CWC Station")
        lat = float(raw_data.get("latitude") or meta.get("lat", 0.0))
        lon = float(raw_data.get("longitude") or meta.get("lon", 0.0))
        warn_lvl = float(raw_data.get("warning_level_m") or meta.get("warning_level_m", 5.0))
        dang_lvl = float(raw_data.get("danger_level_m") or meta.get("danger_level_m", 7.0))
        hfl = float(raw_data.get("hfl_m") or meta.get("hfl_m", 10.0))

        # Spatial check
        is_spatial_ok, spatial_err = check_spatial_bounds(lat, lon)
        if not is_spatial_ok:
            return CWCRiverRecord(
                station_id=st_id,
                station_name=st_name,
                timestamp=ts,
                latitude=lat,
                longitude=lon,
                water_level_m=level_m,
                quality_flag="OUT_OF_BOUNDS",
            ), spatial_err

        # Physical range check
        is_range_ok, range_err = check_sensor_range("water_level_m", level_m)
        quality_flag = "VALID" if is_range_ok else "RANGE_VIOLATION"

        # Rate of rise check if previous reading exists
        rate_of_rise = None
        if previous_reading and previous_reading.station_id == st_id:
            try:
                t1 = datetime.datetime.fromisoformat(previous_reading.timestamp)
                t2 = datetime.datetime.fromisoformat(ts)
                dt_hours = (t2 - t1).total_seconds() / 3600.0
                if 0.1 <= dt_hours <= 6.0:
                    rate_of_rise = (level_m - previous_reading.water_level_m) / dt_hours
                    # Physical rule: flash-flood rate > 4.0 m/h triggers warning
                    if rate_of_rise > 4.0:
                        quality_flag = "RATE_EXCEEDED"
            except Exception:
                pass

        # Statutory status
        if level_m >= hfl:
            status = "ABOVE_HFL"
        elif level_m >= dang_lvl:
            status = "ABOVE_DANGER"
        elif level_m >= warn_lvl:
            status = "ABOVE_WARNING"
        else:
            status = "NORMAL"

        record = CWCRiverRecord(
            station_id=st_id,
            station_name=st_name,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            water_level_m=level_m,
            discharge_m3s=raw_data.get("discharge_m3s"),
            rate_of_rise_mh=round(rate_of_rise, 3) if rate_of_rise is not None else None,
            warning_level_m=warn_lvl,
            danger_level_m=dang_lvl,
            hfl_m=hfl,
            status_indicator=status,
            quality_flag=quality_flag,
        )
        return record, None if is_range_ok else range_err

    def ingest_timeseries(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingests a chronological list of gauge readings preserving rate-of-rise context."""
        valid_records: List[CWCRiverRecord] = []
        errors: List[Dict[str, Any]] = []
        prev_map: Dict[str, CWCRiverRecord] = {}

        # Sort chronologically
        sorted_records = sorted(raw_records, key=lambda x: str(x.get("timestamp", "")))

        for idx, item in enumerate(sorted_records):
            st_id = str(item.get("station_id", ""))
            prev = prev_map.get(st_id)
            rec, err = self.parse_gauge_reading(item, previous_reading=prev)
            if rec and rec.quality_flag in ("VALID", "RATE_EXCEEDED"):
                valid_records.append(rec)
                prev_map[st_id] = rec
            else:
                errors.append({"index": idx, "station_id": st_id, "error": err})

        return {
            "dataset_id": self.provenance.dataset_id,
            "provenance": self.provenance.to_dict(),
            "total_records": len(raw_records),
            "valid_records_count": len(valid_records),
            "error_count": len(errors),
            "records": [r.to_dict() for r in valid_records],
            "errors": errors,
        }
