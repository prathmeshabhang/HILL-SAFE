"""
ml/data_quality/provenance.py
============================
Provenance tracking and classification for datasets, features, and model inputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProvenanceType(str, Enum):
    OBSERVATION = "OBSERVATION"        # Real physical in-situ or remote sensor measurement
    DERIVED = "DERIVED"                # Topographic derivative (slope, curvature, HAND)
    MODELLED = "MODELLED"              # Hydro-physical or numerical simulation output
    PREDICTION = "PREDICTION"          # Machine learning model inference
    SYNTHETIC = "SYNTHETIC"            # Smoke test, controlled simulation experiment


@dataclass
class DatasetProvenance:
    dataset_id: str
    provenance_type: ProvenanceType
    source_agency: str
    geographic_aoi: str
    temporal_coverage: str
    spatial_resolution: str
    license_type: str
    doi_or_url: str
    is_field_verified: bool
    citation: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "provenance_type": self.provenance_type.value,
            "source_agency": self.source_agency,
            "geographic_aoi": self.geographic_aoi,
            "temporal_coverage": self.temporal_coverage,
            "spatial_resolution": self.spatial_resolution,
            "license_type": self.license_type,
            "doi_or_url": self.doi_or_url,
            "is_field_verified": self.is_field_verified,
            "citation": self.citation,
            "notes": self.notes,
        }
