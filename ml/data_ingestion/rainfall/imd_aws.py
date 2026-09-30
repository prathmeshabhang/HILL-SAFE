"""
ml/data_ingestion/rainfall/imd_aws.py
====================================
India Meteorological Department (IMD) Automatic Weather Station (AWS) Ingestion Adapter.
Connects to IMD station feeds/CSVs for Upper Beas sites (Kullu, Manali, Bhuntar, etc.)
Enforces observation type OBSERVATION, sensor range validation, and missingness audits.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_sensor_range, check_spatial_bounds


# Known IMD AWS Stations in Upper Beas Basin
IMD_UPPER_BEAS_STATIONS: Dict[str, Dict[str, Any]] = {
    "IMD_KULLU": {"name": "Kullu", "lat": 31.9579, "lon": 77.1095, "elevation_m": 1279.0},
    "IMD_MANALI": {"name": "Manali", "lat": 32.2432, "lon": 77.1892, "elevation_m": 2050.0},
    "IMD_BHUNTAR": {"name": "Bhuntar Airport", "lat": 31.8764, "lon": 77.1542, "elevation_m": 1089.0},
    "IMD_SEOBAGH": {"name": "Seobagh Agro", "lat": 32.0167, "lon": 77.1333, "elevation_m": 1350.0},
    "IMD_BANJAR": {"name": "Banjar", "lat": 31.6367, "lon": 77.3456, "elevation_m": 1500.0},
    "IMD_KASOL": {"name": "Kasol Parbati", "lat": 32.0100, "lon": 77.3150, "elevation_m": 1580.0},
}


@dataclass
class IMDAWSRecord:
    station_id: str
    station_name: str
    timestamp: str          # ISO 8601 UTC
    latitude: float
    longitude: float
    elevation_m: float
    rainfall_1h_mm: float
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    quality_flag: str = "VALID"  # VALID | OUT_OF_BOUNDS | SENSOR_DROPOUT | RANGE_VIOLATION
    source: str = "IMD_MoES_AWS"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IMDAWSAdapter:
    """
    Ingests and validates ground-truth tipping-bucket rainfall observations
    from IMD Automatic Weather Stations in Himachal Pradesh.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.provenance = DatasetProvenance(
            dataset_id="rainfall_imd_aws",
            provenance_type=ProvenanceType.OBSERVATION,
            source_agency="India Meteorological Department (IMD) / MoES",
            geographic_aoi="Upper Beas Basin (Kullu District)",
            temporal_coverage="Monsoon In-Situ Telemetry (Hourly)",
            spatial_resolution="Point in-situ AWS station",
            license_type="Government Open Data Sharing Policy",
            doi_or_url="https://mausam.imd.gov.in",
            is_field_verified=True,
            citation="IMD Hydro-Meteorological Division, In-situ AWS Network Himachal Pradesh",
        )

    def parse_station_record(self, raw_data: Dict[str, Any]) -> Tuple[Optional[IMDAWSRecord], Optional[str]]:
        """Parses an IMD station record with spatial, station metadata, and rainfall bounds validation."""
        st_id = raw_data.get("station_id")
        ts = raw_data.get("timestamp")

        if not st_id or not ts:
            return None, "Missing station_id or timestamp"

        # Lookup known station or extract from payload
        meta = IMD_UPPER_BEAS_STATIONS.get(st_id, {})
        st_name = raw_data.get("station_name") or meta.get("name", "Unknown Station")
        lat = float(raw_data.get("latitude") or meta.get("lat", 0.0))
        lon = float(raw_data.get("longitude") or meta.get("lon", 0.0))
        elev = float(raw_data.get("elevation_m") or meta.get("elevation_m", 1200.0))

        # Spatial bounds check
        is_spatial_ok, spatial_err = check_spatial_bounds(lat, lon, elev)
        if not is_spatial_ok:
            return IMDAWSRecord(
                station_id=st_id,
                station_name=st_name,
                timestamp=ts,
                latitude=lat,
                longitude=lon,
                elevation_m=elev,
                rainfall_1h_mm=float(raw_data.get("rainfall_1h_mm", 0.0)),
                quality_flag="OUT_OF_BOUNDS",
            ), spatial_err

        # Check physical rainfall range
        rain_val = float(raw_data.get("rainfall_1h_mm", 0.0))
        is_range_ok, range_err = check_sensor_range("rainfall_1h_mm", rain_val)
        quality_flag = "VALID" if is_range_ok else "RANGE_VIOLATION"

        record = IMDAWSRecord(
            station_id=st_id,
            station_name=st_name,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            elevation_m=elev,
            rainfall_1h_mm=max(0.0, rain_val),
            temperature_c=raw_data.get("temperature_c"),
            humidity_pct=raw_data.get("humidity_pct"),
            wind_speed_kmh=raw_data.get("wind_speed_kmh"),
            quality_flag=quality_flag,
        )
        return record, None if is_range_ok else range_err

    def ingest_batch(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_records: List[IMDAWSRecord] = []
        errors: List[Dict[str, Any]] = []

        for idx, item in enumerate(raw_records):
            rec, err = self.parse_station_record(item)
            if rec and rec.quality_flag == "VALID":
                valid_records.append(rec)
            else:
                errors.append({"index": idx, "station_id": item.get("station_id"), "error": err})

        return {
            "dataset_id": self.provenance.dataset_id,
            "provenance": self.provenance.to_dict(),
            "total_records": len(raw_records),
            "valid_records_count": len(valid_records),
            "error_count": len(errors),
            "records": [r.to_dict() for r in valid_records],
            "errors": errors,
        }
