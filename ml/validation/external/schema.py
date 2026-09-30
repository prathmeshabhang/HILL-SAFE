"""
schema.py — Machine-Readable Data Contracts for M6 External Validation
======================================================================
Defines schemas, frozen model contracts, sample tracking dataclasses,
and validation metadata for independent real-world landslide evaluation.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ExternalValidationState(str, Enum):
    EXTERNALLY_VALIDATED = "EXTERNALLY VALIDATED"
    PARTIALLY_VALIDATED = "PARTIALLY VALIDATED"
    EXTERNAL_VALIDATION_PENDING = "EXTERNAL VALIDATION PENDING"
    NOT_POSSIBLE = "VALIDATION NOT POSSIBLE WITH CURRENT EXTERNAL DATA"


@dataclass(frozen=True)
class FrozenModelContract:
    """
    Immutable specification of the Model M6 architecture and feature expectations.
    Enforces that M6 cannot be retrained, fine-tuned, or re-calibrated.
    """
    model_id: str = "M6"
    model_name: str = "Random Forest Landslide Susceptibility Model"
    model_version: str = "v1.0-rf350"
    algorithm: str = "RandomForestClassifier(n_estimators=350, max_depth=9, min_samples_split=4)"
    feature_names: Tuple[str, ...] = (
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "profile_curvature",
        "lithology_code",
        "dist_to_road_m",
        "dist_to_river_m",
        "lulc_code",
    )
    feature_order: Tuple[str, ...] = (
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "profile_curvature",
        "lithology_code",
        "dist_to_road_m",
        "dist_to_river_m",
        "lulc_code",
    )
    classes: Tuple[int, ...] = (0, 1, 2)
    class_labels: Tuple[str, ...] = ("LOW", "MODERATE", "HIGH")
    training_data_description: str = (
        "Upper Beas Catchment landslide dataset (10,000 samples, lat: 31.60–32.40, lon: 76.80–77.45). "
        "Topography, lithology bands, distance to roads/river, and LULC."
    )
    preprocessing_version: str = "v1.0-standard-geomorphic"
    output_semantics: str = (
        "STATIC_GEOMORPHIC_SUSCEPTIBILITY_PROBABILITY: Continuous probability in [0.0, 1.0] "
        "calculated as expected susceptibility score (p1*0.50 + p2*1.00). "
        "Represents permanent terrain failure predisposition, NOT instantaneous storm trigger."
    )
    model_path: str = "ml/landslide/m6_beas_susceptibility_rf.joblib"
    is_frozen: bool = True

    def verify_integrity(self, repo_root: Path) -> str:
        """Computes and returns SHA-256 hash of the frozen artifact."""
        p = repo_root / self.model_path
        if not p.exists():
            raise FileNotFoundError(f"Frozen M6 model artifact missing at {p}")
        sha = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()


@dataclass
class ExternalDatasetRecord:
    """
    Provenance record for an independently sourced historical landslide dataset.
    """
    dataset_id: str
    dataset_name: str
    provider: str
    source_url: str
    license_or_access_terms: str
    download_date: str
    publication_date: str
    geographic_extent: Tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    temporal_extent: str
    geometry_type: str                                    # Point, Polygon, or Mixed
    coordinate_reference_system: str                      # e.g., "EPSG:4326"
    event_date_available: bool
    source_description: str
    validation_role: str                                  # "INDEPENDENT_EXTERNAL_OBSERVATION"
    file_path: Optional[str] = None
    sha256_hash: Optional[str] = None
    raw_event_count: int = 0
    aoi_event_count: int = 0


@dataclass
class ExternalValidationSample:
    """
    Sample record combining observed status with frozen M6 model prediction.
    """
    sample_id: str
    latitude: float
    longitude: float
    observed_label: int          # 1 = landslide event, 0 = non-landslide / stable terrain
    m6_probability: float        # Continuous susceptibility score in [0.0, 1.0]
    m6_class: int                # Argmax class: 0 (Low), 1 (Moderate), 2 (High)
    model_id: str = "M6"
    model_version: str = "v1.0-rf350"
    inference_timestamp: str = ""
    dataset_id: str = ""
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not (0.0 <= self.m6_probability <= 1.0):
            raise ValueError(
                f"m6_probability out of bounds [0.0, 1.0]: {self.m6_probability:.6f}"
            )
        if self.m6_class not in (0, 1, 2):
            raise ValueError(f"m6_class must be 0, 1, or 2, got: {self.m6_class}")
