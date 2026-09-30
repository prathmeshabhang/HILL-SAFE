"""
index_generator.py — Multispectral Index Calculation Engine
===========================================================
Computes standardized remote sensing indices for disaster and land analysis:
  - NDVI (Normalized Difference Vegetation Index)
  - NDWI (Normalized Difference Water Index, McFeeters)
  - MNDWI (Modified Normalized Difference Water Index, Xu)
  - NDBI (Normalized Difference Built-up Index)
  - NDMI (Normalized Difference Moisture Index)
  - SAVI (Soil-Adjusted Vegetation Index)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig


@dataclass
class SpectralIndices:
    shape: tuple[int, int]
    ndvi: np.ndarray
    ndwi: np.ndarray
    mndwi: np.ndarray
    ndbi: np.ndarray
    ndmi: np.ndarray
    savi: np.ndarray


class SpectralIndexGenerator:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def calculate_all(self, bands: Dict[str, np.ndarray]) -> SpectralIndices:
        """
        Calculates all 6 standardized indices from calibrated reflectance bands.
        """
        blue = bands["B02"].astype(np.float32)
        green = bands["B03"].astype(np.float32)
        red = bands["B04"].astype(np.float32)
        nir = bands["B08"].astype(np.float32)
        swir1 = bands["B11"].astype(np.float32)

        eps = 1e-6
        shape = red.shape

        # 1. NDVI = (NIR - Red) / (NIR + Red)
        ndvi = (nir - red) / (nir + red + eps)
        ndvi = np.clip(ndvi, -1.0, 1.0)

        # 2. NDWI = (Green - NIR) / (Green + NIR)
        ndwi = (green - nir) / (green + nir + eps)
        ndwi = np.clip(ndwi, -1.0, 1.0)

        # 3. MNDWI = (Green - SWIR1) / (Green + SWIR1)
        mndwi = (green - swir1) / (green + swir1 + eps)
        mndwi = np.clip(mndwi, -1.0, 1.0)

        # 4. NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)
        ndbi = (swir1 - nir) / (swir1 + nir + eps)
        ndbi = np.clip(ndbi, -1.0, 1.0)

        # 5. NDMI = (NIR - SWIR1) / (NIR + SWIR1)
        ndmi = (nir - swir1) / (nir + swir1 + eps)
        ndmi = np.clip(ndmi, -1.0, 1.0)

        # 6. SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L), L = 0.5
        L = 0.5
        savi = ((nir - red) / (nir + red + L)) * (1.0 + L)
        savi = np.clip(savi, -1.0, 1.0)

        return SpectralIndices(
            shape=shape,
            ndvi=ndvi,
            ndwi=ndwi,
            mndwi=mndwi,
            ndbi=ndbi,
            ndmi=ndmi,
            savi=savi,
        )
