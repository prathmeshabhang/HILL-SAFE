"""
ml/data_ingestion/landslide/inventory_loader.py
==============================================
Geological Survey of India (GSI) & HPSDMA Landslide Inventory Ingestion Pipeline.
Loads verified landslide scarp points, debris flow paths, and polygon outlines
for the Upper Beas Basin with strict source document tracking and duplicate auditing.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_spatial_bounds


@dataclass
class LandslideInventoryRecord:
    event_id: str
    date: str                # YYYY-MM-DD or ISO 8601
    latitude: float
    longitude: float
    elevation_m: float
    location_name: str
    failure_type: str        # DEBRIS_FLOW | ROCKFALL | TRANSLATIONAL_SLIDE | ROTATIONAL_SLUMP | COMPLEX
    estimated_volume_m3: Optional[float] = None
    trigger_mechanism: str = "EXTREME_RAINFALL"  # EXTREME_RAINFALL | TOE_EROSION | ANTHROPIC_CUT | UNKNOWN
    source: str = "GSI_BHUKOSH"
    source_document: str = "GSI Post-Disaster Geological Assessment Report 2023"
    confidence: str = "HIGH"  # HIGH (Field GPS) | MEDIUM (Satellite Photo-interpretation) | LOW (Local Media)
    quality_flag: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LandslideInventoryLoader:
    """
    Ingests, de-duplicates, and validates Geological Survey of India and HPSDMA
    historical and event-based landslide inventory datasets.
    """

    def __init__(self):
        self.provenance = DatasetProvenance(
            dataset_id="landslide_gsi_beas_inventory",
            provenance_type=ProvenanceType.OBSERVATION,
            source_agency="Geological Survey of India (GSI) / HPSDMA",
            geographic_aoi="Upper Beas Basin (Kullu District)",
            temporal_coverage="1995-2023 Historical + July-Aug 2023 Disaster",
            spatial_resolution="Point scarp and failure polygons",
            license_type="Government Open Data Sharing Policy",
            doi_or_url="https://bhukosh.gsi.gov.in",
            is_field_verified=True,
            citation="GSI Northern Region Landslide Division, National Landslide Susceptibility Mapping (NLSM)",
        )

    def parse_record(self, raw_data: Dict[str, Any]) -> Tuple[Optional[LandslideInventoryRecord], Optional[str]]:
        ev_id = str(raw_data.get("event_id", ""))
        date_str = str(raw_data.get("date", ""))
        lat = float(raw_data.get("latitude", 0.0))
        lon = float(raw_data.get("longitude", 0.0))
        elev = float(raw_data.get("elevation_m", 1500.0))

        if not ev_id or not date_str:
            return None, "Missing event_id or date"

        is_spatial_ok, spatial_err = check_spatial_bounds(lat, lon, elev)
        if not is_spatial_ok:
            return LandslideInventoryRecord(
                event_id=ev_id,
                date=date_str,
                latitude=lat,
                longitude=lon,
                elevation_m=elev,
                location_name=raw_data.get("location_name", "Unknown"),
                failure_type=raw_data.get("failure_type", "COMPLEX"),
                quality_flag="OUT_OF_BOUNDS",
            ), spatial_err

        record = LandslideInventoryRecord(
            event_id=ev_id,
            date=date_str,
            latitude=lat,
            longitude=lon,
            elevation_m=elev,
            location_name=raw_data.get("location_name", "Upper Beas Reach"),
            failure_type=raw_data.get("failure_type", "DEBRIS_FLOW"),
            estimated_volume_m3=raw_data.get("estimated_volume_m3"),
            trigger_mechanism=raw_data.get("trigger_mechanism", "EXTREME_RAINFALL"),
            source=raw_data.get("source", "GSI_BHUKOSH"),
            source_document=raw_data.get("source_document", "GSI Post-Disaster Report 2023"),
            confidence=raw_data.get("confidence", "HIGH"),
            quality_flag="VALID",
        )
        return record, None

    def ingest_inventory(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_records: List[LandslideInventoryRecord] = []
        errors: List[Dict[str, Any]] = []
        seen_coords: set = set()

        for idx, item in enumerate(raw_records):
            rec, err = self.parse_record(item)
            if rec and rec.quality_flag == "VALID":
                # Spatial de-duplication within ~10m (round lat/lon to 4 decimal places)
                coord_key = (round(rec.latitude, 4), round(rec.longitude, 4), rec.date)
                if coord_key in seen_coords:
                    errors.append({"index": idx, "event_id": rec.event_id, "error": "Duplicate observation point"})
                    continue
                seen_coords.add(coord_key)
                valid_records.append(rec)
            else:
                errors.append({"index": idx, "event_id": item.get("event_id"), "error": err})

        return {
            "dataset_id": self.provenance.dataset_id,
            "provenance": self.provenance.to_dict(),
            "total_records": len(raw_records),
            "valid_records_count": len(valid_records),
            "error_count": len(errors),
            "records": [r.to_dict() for r in valid_records],
            "errors": errors,
        }
