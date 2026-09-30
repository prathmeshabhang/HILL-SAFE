"""
datasets.py — Dataset Loader & Schema Auditor for Scientific Validation
========================================================================
Loads and validates training/evaluation tabular datasets and spatial rasters
for FLOODY SHIELD machine learning models:
  - Model M2 (Upper Beas Flood Occurrence)
  - Model M6 (Static Landslide Susceptibility)
  - Model M7 (Dynamic Landslide Triggering)
  - Multimodal Flood U-Net (Satellite Rasters)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

BEAS_FLOOD_CSV = DATA_DIR / "processed" / "upper_beas" / "upper_beas_flood_dataset.csv"
BEAS_LANDSLIDE_CSV = DATA_DIR / "processed" / "upper_beas" / "upper_beas_landslide_dataset.csv"

M2_EXPECTED_FEATURES = [
    "elevation_m", "slope_deg", "aspect_deg", "plan_curvature", "profile_curvature",
    "twi", "spi", "dist_to_river_m", "lulc_code", "soil_clay_pct", "rainfall_15m",
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_24h", "antecedent_rain_3d",
    "soil_moisture_pct", "cwc_river_level_m", "cwc_rate_of_rise_m_hr"
]
M2_TARGET = "flash_flood_occurred"

M6_EXPECTED_FEATURES = [
    "elevation_m", "slope_deg", "aspect_deg", "profile_curvature",
    "lithology_code", "dist_to_road_m", "dist_to_river_m", "lulc_code"
]
M6_TARGET = "susceptibility_class"

M7_EXPECTED_FEATURES = [
    "susceptibility_class", "slope_deg", "rainfall_1h",
    "antecedent_rain_3d", "soil_moisture_pct"
]
M7_TARGET = "landslide_triggered"


@dataclass
class DatasetAuditRecord:
    dataset_name: str
    file_path: str
    sha256_hash: str
    row_count: int
    column_count: int
    features: List[str]
    target_column: str
    has_coordinates: bool
    has_timestamps: bool
    has_event_ids: bool
    missing_values_count: int
    target_distribution: Dict[str, Any]


def compute_file_sha256(path: Path) -> str:
    """Computes SHA-256 checksum for audit traceability."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_and_audit_flood_dataset(path: Optional[Path] = None) -> Tuple[pd.DataFrame, DatasetAuditRecord]:
    """Loads Upper Beas flood dataset and generates scientific audit record."""
    target_path = path or BEAS_FLOOD_CSV
    if not target_path.exists():
        raise FileNotFoundError(f"Flood dataset not found at {target_path}")

    df = pd.read_csv(target_path)
    sha = compute_file_sha256(target_path)

    has_coords = "lat" in df.columns and "lon" in df.columns
    has_time = any(c in df.columns for c in ["timestamp", "datetime", "date", "time"])
    has_events = any(c in df.columns for c in ["event_id", "storm_id", "event_name"])

    missing = int(df.isna().sum().sum())
    dist = {str(k): int(v) for k, v in df[M2_TARGET].value_counts().items()}

    audit = DatasetAuditRecord(
        dataset_name="upper_beas_flood_dataset",
        file_path=str(target_path),
        sha256_hash=sha,
        row_count=len(df),
        column_count=len(df.columns),
        features=M2_EXPECTED_FEATURES,
        target_column=M2_TARGET,
        has_coordinates=has_coords,
        has_timestamps=has_time,
        has_event_ids=has_events,
        missing_values_count=missing,
        target_distribution=dist,
    )
    return df, audit


def load_and_audit_landslide_dataset(path: Optional[Path] = None) -> Tuple[pd.DataFrame, DatasetAuditRecord]:
    """Loads Upper Beas landslide dataset and generates scientific audit record."""
    target_path = path or BEAS_LANDSLIDE_CSV
    if not target_path.exists():
        raise FileNotFoundError(f"Landslide dataset not found at {target_path}")

    df = pd.read_csv(target_path)
    sha = compute_file_sha256(target_path)

    has_coords = "lat" in df.columns and "lon" in df.columns
    has_time = any(c in df.columns for c in ["timestamp", "datetime", "date", "time"])
    has_events = any(c in df.columns for c in ["event_id", "storm_id", "event_name"])

    missing = int(df.isna().sum().sum())
    dist_m6 = {str(k): int(v) for k, v in df[M6_TARGET].value_counts().items()}
    dist_m7 = {str(k): int(v) for k, v in df[M7_TARGET].value_counts().items()}

    audit = DatasetAuditRecord(
        dataset_name="upper_beas_landslide_dataset",
        file_path=str(target_path),
        sha256_hash=sha,
        row_count=len(df),
        column_count=len(df.columns),
        features=M6_EXPECTED_FEATURES + M7_EXPECTED_FEATURES,
        target_column=f"{M6_TARGET} / {M7_TARGET}",
        has_coordinates=has_coords,
        has_timestamps=has_time,
        has_event_ids=has_events,
        missing_values_count=missing,
        target_distribution={"m6_classes": dist_m6, "m7_triggers": dist_m7},
    )
    return df, audit
