"""
surface_change.py — Multi-Temporal Satellite Change Detection Engine
===================================================================
Compares T1 (Pre-event baseline) vs T2 (Post-event or current observation):
  - delta_ndvi: Vegetation Loss (< -0.15 indicates deforestation, slope cutting, debris scouring)
  - delta_mndwi: Water expansion (> +0.15 indicates newly inundated floodways)
  - delta_ndbi: Construction expansion (> +0.10 indicates new roads, concrete, quarries)
  - surface_disturbance_index: Overall compound geomorphic alteration [0.0, 1.0]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from ml.satellite_hazard.spectral.index_generator import SpectralIndices


@dataclass
class TemporalChangeResult:
    shape: Tuple[int, int]
    delta_ndvi: np.ndarray                 # T2 - T1
    delta_mndwi: np.ndarray                # T2 - T1
    delta_ndbi: np.ndarray                 # T2 - T1
    vegetation_loss_mask: np.ndarray       # Significant vegetation drop
    flood_inundation_expansion: np.ndarray # Newly flooded land
    construction_expansion_mask: np.ndarray
    surface_disturbance_score: np.ndarray  # [0.0, 1.0] compound change


class SurfaceChangeEngine:
    def compare(self, t1_indices: SpectralIndices, t2_indices: SpectralIndices) -> TemporalChangeResult:
        shape = t1_indices.shape

        d_ndvi = (t2_indices.ndvi - t1_indices.ndvi).astype(np.float32)
        d_mndwi = (t2_indices.mndwi - t1_indices.mndwi).astype(np.float32)
        d_ndbi = (t2_indices.ndbi - t1_indices.ndbi).astype(np.float32)

        # Detect specific change phenomena
        veg_loss = d_ndvi < -0.18
        flood_exp = (d_mndwi > 0.15) & (t2_indices.mndwi > 0.0)
        const_exp = (d_ndbi > 0.12) & (d_ndvi < 0.0)

        # Compound Surface Disturbance Score [0.0, 1.0]
        disturbance = (
            np.maximum(-d_ndvi, 0.0) * 0.40 +
            np.maximum(d_mndwi, 0.0) * 0.35 +
            np.maximum(d_ndbi, 0.0) * 0.25
        )
        disturbance = np.clip(disturbance * 2.2, 0.0, 1.0).astype(np.float32)

        return TemporalChangeResult(
            shape=shape,
            delta_ndvi=d_ndvi,
            delta_mndwi=d_mndwi,
            delta_ndbi=d_ndbi,
            vegetation_loss_mask=veg_loss,
            flood_inundation_expansion=flood_exp,
            construction_expansion_mask=const_exp,
            surface_disturbance_score=disturbance,
        )
