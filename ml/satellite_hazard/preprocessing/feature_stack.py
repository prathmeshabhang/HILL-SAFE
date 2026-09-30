"""
feature_stack.py — 9-Channel Multimodal Feature Stack & Tensor Constructor
==========================================================================
Constructs standardized 9-Channel Multimodal Tensor (B, 9, H, W) for PyTorch U-Net
and downstream hazard analysis:
  Ch 1: Sentinel-1 SAR VV (Lee filtered, standardized)
  Ch 2: Sentinel-1 SAR VH (Lee filtered, standardized)
  Ch 3: Sentinel-2 B04 (Red)
  Ch 4: Sentinel-2 B03 (Green)
  Ch 5: Sentinel-2 B08 (NIR)
  Ch 6: Sentinel-2 B11 (SWIR-1)
  Ch 7: DEM Elevation (meters ASL, standardized)
  Ch 8: Slope Gradient (degrees / 90.0)
  Ch 9: Flow Accumulation / HAND proxy

Also computes standardized spectral indices (NDWI, MNDWI, NDVI, NDBI).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import torch

from ml.satellite_hazard.preprocessing.spatial_aligner import AlignedSceneBundle


@dataclass
class FeatureStack:
    array_9ch: np.ndarray             # (9, rows, cols) float32 in [0, 1]
    tensor_9ch: torch.Tensor           # (1, 9, rows, cols) float32 PyTorch tensor
    channel_names: List[str]
    indices: Dict[str, np.ndarray]    # NDWI, MNDWI, NDVI, NDBI
    shape: tuple[int, int]


class FeatureStackConstructor:
    CHANNEL_NAMES = [
        "SAR_VV_Filtered",
        "SAR_VH_Filtered",
        "S2_B04_Red",
        "S2_B03_Green",
        "S2_B08_NIR",
        "S2_B11_SWIR1",
        "DEM_Elevation_Standardized",
        "Slope_Gradient_Normalized",
        "HAND_Hydrology_Proxy",
    ]

    def construct(self, aligned: AlignedSceneBundle) -> FeatureStack:
        """
        Synthesizes normalized 9-channel array and tensor.
        """
        rows, cols = aligned.shape

        # 1. Normalize SAR VV [-25 dB, 0 dB] -> [0.0, 1.0]
        vv_norm = np.clip((aligned.sar_vv_filtered_db + 25.0) / 25.0, 0.0, 1.0).astype(np.float32)

        # 2. Normalize SAR VH [-32 dB, -5 dB] -> [0.0, 1.0]
        vh_norm = np.clip((aligned.sar_vh_filtered_db + 32.0) / 27.0, 0.0, 1.0).astype(np.float32)

        # 3. Sentinel-2 Optical Reflectances (clip to [0.0, 1.0])
        b04 = np.clip(aligned.s2_bands["B04"], 0.0, 1.0).astype(np.float32)
        b03 = np.clip(aligned.s2_bands["B03"], 0.0, 1.0).astype(np.float32)
        b08 = np.clip(aligned.s2_bands["B08"], 0.0, 1.0).astype(np.float32)
        b11 = np.clip(aligned.s2_bands["B11"], 0.0, 1.0).astype(np.float32)

        # 4. Standardized DEM Elevation [800m, 3800m] -> [0.0, 1.0]
        dem_norm = np.clip((aligned.dem_elevation_m - 800.0) / 3000.0, 0.0, 1.0).astype(np.float32)

        # 5. Normalized Slope [0 deg, 90 deg] -> [0.0, 1.0]
        slope_norm = np.clip(aligned.slope_deg / 90.0, 0.0, 1.0).astype(np.float32)

        # 6. Normalized HAND Hydrology Proxy [0m, 100m] -> [0.0, 1.0]
        hand_norm = np.clip(aligned.hand_m / 100.0, 0.0, 1.0).astype(np.float32)

        # Stack into (9, rows, cols)
        stack_arr = np.stack([
            vv_norm,
            vh_norm,
            b04,
            b03,
            b08,
            b11,
            dem_norm,
            slope_norm,
            hand_norm,
        ], axis=0)

        # PyTorch Tensor (1, 9, rows, cols)
        tensor = torch.from_numpy(stack_arr).unsqueeze(0).float()

        # Compute Standardized Spectral Indices
        eps = 1e-6
        ndwi = (b03 - b08) / (b03 + b08 + eps)
        mndwi = (b03 - b11) / (b03 + b11 + eps)
        ndvi = (b08 - b04) / (b08 + b04 + eps)
        ndbi = (b11 - b08) / (b11 + b08 + eps)

        indices = {
            "NDWI": np.clip(ndwi, -1.0, 1.0).astype(np.float32),
            "MNDWI": np.clip(mndwi, -1.0, 1.0).astype(np.float32),
            "NDVI": np.clip(ndvi, -1.0, 1.0).astype(np.float32),
            "NDBI": np.clip(ndbi, -1.0, 1.0).astype(np.float32),
        }

        return FeatureStack(
            array_9ch=stack_arr,
            tensor_9ch=tensor,
            channel_names=self.CHANNEL_NAMES,
            indices=indices,
            shape=(rows, cols),
        )
