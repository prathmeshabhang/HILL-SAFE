"""
config.py — Configuration and Spatial Parameter Registry for Satellite Hazard Intelligence
===========================================================================================
Defines study area bounding boxes, sensor band mappings, physical thresholds,
and scientific disclaimers per FLOODY SHIELD specifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class StudyAreaConfig:
    name: str = "Upper Beas Basin (Kullu–Manali)"
    state: str = "Himachal Pradesh"
    country: str = "India"
    # Geographic Bounding Box (WGS84 EPSG:4326)
    min_lon: float = 76.80
    max_lon: float = 77.45
    min_lat: float = 31.60
    max_lat: float = 32.40
    # Projected CRS for accurate metric spatial measurements
    target_crs: str = "EPSG:32643"  # UTM Zone 43N
    display_crs: str = "EPSG:4326"
    # Grid dimensions for standardized test scenes and raster inference
    grid_rows: int = 500
    grid_cols: int = 400
    cell_size_m: float = 30.0  # Aligned with Copernicus 30m DEM


@dataclass(frozen=True)
class SatelliteProcessingConfig:
    study_area: StudyAreaConfig = field(default_factory=StudyAreaConfig)
    
    # Sentinel-2 Bands required
    bands_required: Tuple[str, ...] = (
        "B02",  # Blue (490 nm)
        "B03",  # Green (560 nm)
        "B04",  # Red (665 nm)
        "B08",  # NIR (842 nm)
        "B11",  # SWIR-1 (1610 nm)
        "B12",  # SWIR-2 (2190 nm)
        "SCL",  # Scene Classification Layer (Cloud / Shadow / Water)
    )

    # Cloud Masking (Sentinel-2 SCL Classes to Mask Out)
    cloud_scl_classes: Tuple[int, ...] = (
        3,  # Cloud shadows
        8,  # Cloud medium probability
        9,  # Cloud high probability
        10, # Thin cirrus
    )

    # Categorization Thresholds (Scientifically Documented)
    risk_bins: Tuple[float, ...] = (0.0, 0.20, 0.40, 0.60, 0.80, 1.0)
    risk_labels: Tuple[str, ...] = (
        "VERY_LOW",
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
    )

    # Thresholds for Decision Zones
    critical_dev_pressure_min: float = 0.60
    critical_hazard_susceptibility_min: float = 0.65

    candidate_safe_flood_max: float = 0.30
    candidate_safe_landslide_max: float = 0.30
    candidate_safe_slope_max_deg: float = 18.0
    candidate_safe_twi_max: float = 7.5

    # Statutory Disclaimer per Requirement
    safe_zone_disclaimer: str = (
        "Candidate zone identified from available geospatial evidence. "
        "This is not a substitute for field investigation, engineering assessment, "
        "environmental clearance, or statutory planning approval."
    )

    # Output paths
    output_dir: Path = Path("data/satellite_output")
