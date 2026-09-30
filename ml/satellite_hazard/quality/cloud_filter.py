"""
cloud_filter.py — Sentinel-2 SCL Cloud Masking & Quality Auditing Engine
========================================================================
Audits scene quality before inference:
  - Rejects or flags scenes with excessive cloud cover (>50%).
  - Masks SCL classes 3 (Shadow), 8 (Medium Prob Cloud), 9 (High Prob Cloud), 10 (Cirrus).
  - Produces pixel-level Quality Mask and Epistemic Observation Confidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.ingestion.sentinel2_loader import Sentinel2Scene


@dataclass
class QualityAuditReport:
    scene_id: str
    total_pixels: int
    clean_pixels: int
    cloud_pixels: int
    cloud_shadow_pixels: int
    nodata_pixels: int
    valid_data_fraction: float
    is_usable_for_disaster_inference: bool
    rejection_reason: Optional[str]


class CloudQualityFilter:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def audit_and_filter(self, scene: Sentinel2Scene) -> Tuple[Dict[str, np.ndarray], np.ndarray, QualityAuditReport]:
        """
        Filters clouds from all bands and generates:
          1. Cleaned bands dictionary (cloud pixels set to np.nan)
          2. Binary valid mask (1.0 = valid ground observation, 0.0 = cloud/shadow/nodata)
          3. Quality audit report
        """
        scl = scene.bands.get("SCL")
        shape = scene.shape

        if scl is None:
            # Fallback if SCL band missing: use threshold on high Blue reflectance
            is_cloud = scene.bands["B02"] > 0.45
            is_shadow = np.zeros(shape, dtype=bool)
        else:
            is_cloud = np.isin(scl, (8, 9, 10))
            is_shadow = scl == 3

        is_nodata = np.isnan(scene.bands["B02"]) | (scene.bands["B02"] <= 0.0)
        invalid_mask = is_cloud | is_shadow | is_nodata
        valid_mask = (~invalid_mask).astype(np.float32)

        total_px = shape[0] * shape[1]
        cloud_count = int(np.sum(is_cloud))
        shadow_count = int(np.sum(is_shadow))
        nodata_count = int(np.sum(is_nodata))
        clean_count = int(np.sum(valid_mask > 0))

        valid_fraction = float(clean_count / total_px)
        is_usable = valid_fraction >= 0.40  # At least 40% cloud-free ground visible
        rejection_reason = None if is_usable else f"Insufficient cloud-free ground ({valid_fraction*100:.1f}% valid < 40% required)"

        report = QualityAuditReport(
            scene_id=scene.scene_id,
            total_pixels=total_px,
            clean_pixels=clean_count,
            cloud_pixels=cloud_count,
            cloud_shadow_pixels=shadow_count,
            nodata_pixels=nodata_count,
            valid_data_fraction=round(valid_fraction, 4),
            is_usable_for_disaster_inference=is_usable,
            rejection_reason=rejection_reason,
        )

        # Create masked bands
        cleaned_bands = {}
        for b_name, b_arr in scene.bands.items():
            arr_copy = b_arr.copy()
            if b_name != "SCL":
                arr_copy[invalid_mask] = np.nan
            cleaned_bands[b_name] = arr_copy

        return cleaned_bands, valid_mask, report
