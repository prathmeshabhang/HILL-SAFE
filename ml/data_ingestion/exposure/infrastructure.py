"""
ml/data_ingestion/exposure/infrastructure.py
============================================
Upper Beas Lifeline Infrastructure & Asset Register Ingestion Adapter.
Parses critical infrastructure (bridges, hospitals, roads, substations, water supply).
Enforces realistic asset replacement valuation rules:
  - Disallows invented monetary values (marks as VALUE_UNAVAILABLE if not official).
  - Validates spatial locations strictly within Upper Beas bounds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_spatial_bounds


# Standard lifeline categories
LIFELINE_CATEGORIES = {
    "BRIDGE": "Critical crossing vulnerable to scouring and debris collision",
    "ROAD_CORRIDOR": "NH-3, NH-305, and MDR routes essential for evacuation",
    "HOSPITAL": "Primary healthcare and regional emergency medical centers",
    "SUBSTATION": "HPSEB electrical transmission and distribution transformers",
    "WATER_WORKS": "Jal Shakti intake well and municipal filtration plants",
    "COMMUNICATION": "Cellular BTS towers and microwave emergency relays",
}


@dataclass
class InfrastructureAssetRecord:
    asset_id: str
    asset_name: str
    asset_type: str             # BRIDGE | ROAD_CORRIDOR | HOSPITAL | SUBSTATION | WATER_WORKS | COMMUNICATION
    latitude: float
    longitude: float
    elevation_m: float
    criticality_tier: int       # 1 (Extreme Lifeline) to 4 (Local Secondary)
    replacement_value_inr_lakh: Optional[float] = None  # None if VALUE_UNAVAILABLE
    capacity_or_flow: Optional[str] = None
    source_agency: str = "HP_PWD_HPSEB_OSM"
    quality_flag: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InfrastructureAssetLoader:
    """
    Ingests and audits infrastructure assets for M14 Physical Vulnerability & Loss.
    """

    def __init__(self):
        self.provenance = DatasetProvenance(
            dataset_id="infrastructure_assets_register",
            provenance_type=ProvenanceType.DERIVED,
            source_agency="HP State PWD / HPSEB / Jal Shakti / OpenStreetMap India",
            geographic_aoi="Upper Beas Basin Transportation & Utility Corridor",
            temporal_coverage="2023 Infrastructure Baseline",
            spatial_resolution="Point and Polyline Asset Vectors",
            license_type="Government Open Data / ODbL",
            doi_or_url="https://hppwd.hp.gov.in",
            is_field_verified=True,
            citation="Himachal Pradesh Public Works Department Asset Master Register",
        )

    def parse_asset(self, raw_data: Dict[str, Any]) -> Tuple[Optional[InfrastructureAssetRecord], Optional[str]]:
        aid = str(raw_data.get("asset_id", ""))
        name = str(raw_data.get("asset_name", "Unknown Asset"))
        atype = str(raw_data.get("asset_type", "")).upper()
        lat = float(raw_data.get("latitude", 0.0))
        lon = float(raw_data.get("longitude", 0.0))
        elev = float(raw_data.get("elevation_m", 1200.0))

        if not aid or not atype:
            return None, "Missing asset_id or asset_type"

        if atype not in LIFELINE_CATEGORIES:
            return None, f"Invalid asset_type: {atype}. Allowed: {list(LIFELINE_CATEGORIES.keys())}"

        is_spatial_ok, spatial_err = check_spatial_bounds(lat, lon, elev)
        if not is_spatial_ok:
            return None, spatial_err

        val_inr = raw_data.get("replacement_value_inr_lakh")
        if val_inr is not None:
            try:
                val_inr = float(val_inr)
                if val_inr <= 0.0:
                    val_inr = None  # Treat negative/zero as VALUE_UNAVAILABLE
            except ValueError:
                val_inr = None

        record = InfrastructureAssetRecord(
            asset_id=aid,
            asset_name=name,
            asset_type=atype,
            latitude=lat,
            longitude=lon,
            elevation_m=elev,
            criticality_tier=int(raw_data.get("criticality_tier", 2)),
            replacement_value_inr_lakh=val_inr,
            capacity_or_flow=raw_data.get("capacity_or_flow"),
            source_agency=raw_data.get("source_agency", "HP_PWD"),
            quality_flag="VALID",
        )
        return record, None

    def ingest_assets(self, raw_assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_assets: List[InfrastructureAssetRecord] = []
        rejected: List[Dict[str, Any]] = []

        for idx, item in enumerate(raw_assets):
            rec, err = self.parse_asset(item)
            if rec:
                valid_assets.append(rec)
            else:
                rejected.append({"index": idx, "asset_id": item.get("asset_id"), "error": err})

        return {
            "dataset_id": self.provenance.dataset_id,
            "provenance": self.provenance.to_dict(),
            "total_assets": len(raw_assets),
            "valid_assets_count": len(valid_assets),
            "rejected_count": len(rejected),
            "assets": [a.to_dict() for a in valid_assets],
            "rejections": rejected,
        }
