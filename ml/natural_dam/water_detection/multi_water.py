"""
multi_water.py — Multi-Sensor Optical (NDWI/MNDWI) & SAR Specular Water Detection
==================================================================================
Extracts high-fidelity water surface probability and binary masks fusing Sentinel-2
multispectral indices with all-weather Sentinel-1 C-Band SAR radar backscatter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np


@dataclass
class WaterDetectionResult:
    water_mask: np.ndarray          # Binary mask (1 = water, 0 = non-water)
    water_probability: np.ndarray   # Calibrated float (0.0 to 1.0)
    water_confidence: np.ndarray    # Epistemic sensor confidence (0.0 to 1.0)
    optical_available: bool
    sar_available: bool
    water_area_km2: float


class MultiSensorWaterDetector:
    """
    Robust water extraction engine engineered for narrow mountain river corridors.
    Works under heavy monsoon clouds using Sentinel-1 C-Band SAR specular reflection.
    """

    def detect_water(
        self,
        ndwi: Optional[np.ndarray] = None,
        mndwi: Optional[np.ndarray] = None,
        sar_vv_db: Optional[np.ndarray] = None,
        sar_delta_db: Optional[np.ndarray] = None,
        cloud_mask: Optional[np.ndarray] = None,
        cell_size_m: float = 30.0,
    ) -> WaterDetectionResult:
        """
        Fuses available optical and SAR observation layers.
        """
        shape = None
        for arr in (ndwi, mndwi, sar_vv_db, sar_delta_db):
            if arr is not None:
                shape = arr.shape
                break

        if shape is None:
            raise ValueError("At least one optical or SAR array must be provided")

        prob_grid = np.zeros(shape, dtype=np.float32)
        conf_grid = np.zeros(shape, dtype=np.float32)
        weight_sum = np.zeros(shape, dtype=np.float32)

        has_optical = False
        has_sar = False

        # 1. Optical Water Evidence (NDWI / MNDWI)
        if mndwi is not None and ndwi is not None:
            # Cloud valid mask: 1 = clear, 0 = obscured
            clear_mask = (cloud_mask == 0) if cloud_mask is not None else np.ones(shape, dtype=bool)
            has_optical = np.mean(clear_mask) > 0.30

            # Logistic transform of MNDWI: water signature typically MNDWI > 0.0
            opt_prob = 1.0 / (1.0 + np.exp(-7.0 * (mndwi - 0.05)))
            opt_conf = np.where(clear_mask, 0.95, 0.10)

            prob_grid += (opt_prob * opt_conf * clear_mask.astype(np.float32))
            weight_sum += (opt_conf * clear_mask.astype(np.float32))

        # 2. SAR C-Band Radar Evidence (All-Weather Cloud Penetration)
        if sar_vv_db is not None:
            has_sar = True
            # Calm open water has specular reflection: VV backscatter drops drastically (<-15.5 dB)
            sar_prob = 1.0 / (1.0 + np.exp(0.65 * (sar_vv_db + 15.5)))

            # If temporal backscatter anomaly is available, boost confidence where delta < -4.0 dB
            if sar_delta_db is not None:
                flood_delta_prob = np.clip((-sar_delta_db - 2.0) / 4.0, 0.0, 1.0)
                sar_prob = np.maximum(sar_prob, flood_delta_prob)

            sar_conf = 0.90  # SAR radar is unaffected by monsoon clouds or night
            prob_grid += (sar_prob * sar_conf)
            weight_sum += sar_conf

        # Normalize probability
        valid_weights = weight_sum > 0
        final_prob = np.zeros(shape, dtype=np.float32)
        final_prob[valid_weights] = prob_grid[valid_weights] / weight_sum[valid_weights]
        final_conf = np.clip(weight_sum / 1.85, 0.1, 1.0)

        # Binary water mask (decision threshold at 0.50 probability)
        water_mask = (final_prob >= 0.50).astype(np.uint8)

        # Total detected water surface area
        pixel_area_km2 = (cell_size_m * cell_size_m) / 1_000_000.0
        total_area_km2 = float(np.sum(water_mask) * pixel_area_km2)

        return WaterDetectionResult(
            water_mask=water_mask,
            water_probability=final_prob,
            water_confidence=final_conf,
            optical_available=has_optical,
            sar_available=has_sar,
            water_area_km2=round(total_area_km2, 3),
        )
