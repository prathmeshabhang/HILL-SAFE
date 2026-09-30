"""
ml/data_ingestion/rainfall/gpm_imerg.py
======================================
NASA GPM IMERG Precipitation Ingestion Adapter.
Parses GPM IMERG HDF5/GeoTIFF/JSON products, filters to Upper Beas AOI,
and enforces observation type DERIVED with provenance & quality flags.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import UPPER_BEAS_BOUNDS, check_sensor_range, check_spatial_bounds


@dataclass
class GPMRecord:
    timestamp: str          # ISO 8601 UTC
    latitude: float
    longitude: float
    rainfall_mm: float
    source: str = "NASA_GES_DISC"
    product: str = "3IMERGHHE_07B"
    version: str = "V07B"
    quality_flag: str = "VALID"  # VALID | OUT_OF_BOUNDS | MISSING | UNCALIBRATED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GPMIMERGAdapter:
    """
    Ingests and validates NASA GPM IMERG 30-minute precipitation estimates
    for the Upper Beas Basin.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.provenance = DatasetProvenance(
            dataset_id="rainfall_gpm_imerg",
            provenance_type=ProvenanceType.DERIVED,
            source_agency="NASA / JAXA",
            geographic_aoi="Upper Beas Basin (31.40-32.45N, 76.80-77.45E)",
            temporal_coverage="2018-Present (30-minute)",
            spatial_resolution="0.1 deg (~10 km)",
            license_type="NASA Open Science Policy",
            doi_or_url="https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHHE_06/summary",
            is_field_verified=False,
            citation="Huffman et al., NASA Global Precipitation Measurement (GPM) IMERG V07B",
        )

    def parse_record(self, raw_data: Dict[str, Any]) -> Tuple[Optional[GPMRecord], Optional[str]]:
        """
        Parses and validates a single GPM IMERG precipitation reading.
        Enforces Upper Beas spatial bounding and physical rainfall thresholds.
        """
        lat = float(raw_data.get("latitude", 0.0))
        lon = float(raw_data.get("longitude", 0.0))
        rainfall_mm = float(raw_data.get("rainfall_mm", -1.0))
        ts = raw_data.get("timestamp")

        if not ts:
            return None, "Missing timestamp"

        # Spatial bounds check
        is_spatial_ok, spatial_err = check_spatial_bounds(lat, lon)
        if not is_spatial_ok:
            return GPMRecord(
                timestamp=ts,
                latitude=lat,
                longitude=lon,
                rainfall_mm=rainfall_mm,
                quality_flag="OUT_OF_BOUNDS",
            ), spatial_err

        # Physical bounds check
        is_range_ok, range_err = check_sensor_range("rainfall_rate_mmh", rainfall_mm * 2.0)  # 30-min to mm/h
        quality_flag = "VALID" if is_range_ok else "RANGE_VIOLATION"

        record = GPMRecord(
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            rainfall_mm=max(0.0, rainfall_mm),
            product=raw_data.get("product", "3IMERGHHE_07B"),
            version=raw_data.get("version", "V07B"),
            quality_flag=quality_flag,
        )
        return record, None if is_range_ok else range_err

    def ingest_batch(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processes a batch of raw records returning valid items and audit metrics."""
        valid_records: List[GPMRecord] = []
        errors: List[Dict[str, Any]] = []

        for idx, item in enumerate(raw_records):
            rec, err = self.parse_record(item)
            if rec and rec.quality_flag == "VALID":
                valid_records.append(rec)
            else:
                errors.append({"index": idx, "record": item, "error": err})

        return {
            "dataset_id": self.provenance.dataset_id,
            "provenance": self.provenance.to_dict(),
            "total_records": len(raw_records),
            "valid_records_count": len(valid_records),
            "error_count": len(errors),
            "records": [r.to_dict() for r in valid_records],
            "errors": errors,
        }
