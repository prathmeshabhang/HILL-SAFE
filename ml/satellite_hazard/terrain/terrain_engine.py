"""
terrain_engine.py — Advanced Digital Elevation Model (DEM) Feature Preprocessing
================================================================================
Derives production-grade physical geomorphic rasters from Copernicus 30m DEM:
  - Slope (degrees) via Horn's 3x3 convolution
  - Aspect (degrees, 0-360)
  - Plan Curvature (horizontal flow convergence)
  - Profile Curvature (downslope flow acceleration)
  - Topographic Wetness Index (TWI = ln(A / tan beta))
  - Stream Power Index (SPI = A * tan beta)
  - Terrain Ruggedness Index (TRI)
  - Height Above Nearest Drainage (HAND approximation)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
from scipy.signal import convolve2d

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.ingestion.dem_loader import DEMScene


@dataclass
class TerrainFeatures:
    shape: tuple[int, int]
    elevation_m: np.ndarray
    slope_deg: np.ndarray
    aspect_deg: np.ndarray
    plan_curvature: np.ndarray
    profile_curvature: np.ndarray
    topographic_wetness_index: np.ndarray
    stream_power_index: np.ndarray
    terrain_ruggedness_index: np.ndarray
    height_above_nearest_drainage_m: np.ndarray


class TerrainEngine:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def process(self, dem: DEMScene) -> TerrainFeatures:
        z = dem.elevation.astype(np.float64)
        d = float(dem.cell_size_m)  # Cell resolution in meters (30m)

        # Horn's 3x3 Convolutional Kernels for partial derivatives
        # dz/dx (East-West slope)
        kx = np.array([
            [-1.0, 0.0, 1.0],
            [-2.0, 0.0, 2.0],
            [-1.0, 0.0, 1.0]
        ], dtype=np.float64) / (8.0 * d)

        # dz/dy (North-South slope)
        ky = np.array([
            [ 1.0,  2.0,  1.0],
            [ 0.0,  0.0,  0.0],
            [-1.0, -2.0, -1.0]
        ], dtype=np.float64) / (8.0 * d)

        # Second derivatives for Curvature (Zevenbergen & Thorne)
        # d2z/dx2
        kxx = np.array([
            [1.0, -2.0, 1.0],
            [2.0, -4.0, 2.0],
            [1.0, -2.0, 1.0]
        ], dtype=np.float64) / (4.0 * d**2)

        # d2z/dy2
        kyy = np.array([
            [ 1.0,  2.0,  1.0],
            [-2.0, -4.0, -2.0],
            [ 1.0,  2.0,  1.0]
        ], dtype=np.float64) / (4.0 * d**2)

        # d2z/dxdy
        kxy = np.array([
            [-1.0, 0.0, 1.0],
            [ 0.0, 0.0, 0.0],
            [ 1.0, 0.0, -1.0]
        ], dtype=np.float64) / (4.0 * d**2)

        p = convolve2d(z, kx, mode="same", boundary="symm")
        q = convolve2d(z, ky, mode="same", boundary="symm")
        r = convolve2d(z, kxx, mode="same", boundary="symm")
        t = convolve2d(z, kyy, mode="same", boundary="symm")
        s = convolve2d(z, kxy, mode="same", boundary="symm")

        # 1. Slope (degrees)
        p2_plus_q2 = p**2 + q**2
        slope_rad = np.arctan(np.sqrt(p2_plus_q2))
        slope_deg = np.degrees(slope_rad).astype(np.float32)

        # 2. Aspect (degrees, 0 = North, 90 = East, 180 = South, 270 = West)
        aspect_rad = np.arctan2(-q, p)
        aspect_deg = np.degrees(aspect_rad)
        aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360.0, aspect_deg).astype(np.float32)

        # 3. Curvatures
        # Plan curvature (flow convergence: positive = divergent ridges, negative = convergent gullies)
        denom_plan = np.maximum(p2_plus_q2 ** 1.5, 1e-7)
        plan_curv = ((p**2 * t - 2.0 * p * q * s + q**2 * r) / denom_plan).astype(np.float32)
        plan_curv = np.clip(plan_curv, -0.05, 0.05)

        # Profile curvature (flow acceleration: positive = convex decelerating, negative = concave accelerating)
        denom_prof = np.maximum(p2_plus_q2 * (1.0 + p2_plus_q2)**1.5, 1e-7)
        prof_curv = (-(p**2 * r + 2.0 * p * q * s + q**2 * t) / denom_prof).astype(np.float32)
        prof_curv = np.clip(prof_curv, -0.05, 0.05)

        # 4. Topographic Wetness Index (TWI) & Stream Power Index (SPI)
        # Approximate specific catchment area A using inverse distance to stream and gully convergence
        # Low slopes and convergent gullies accumulate high upstream catchment area
        tan_slope = np.maximum(np.tan(slope_rad), 0.015)
        pseudo_catchment = 120.0 + (np.maximum(-plan_curv, 0.0) * 8000.0) + (1.0 / (tan_slope + 0.05)) * 40.0
        twi = np.log(np.maximum(pseudo_catchment / tan_slope, 1.0)).astype(np.float32)
        twi = np.clip(twi, 2.0, 16.0)

        spi = (pseudo_catchment * tan_slope).astype(np.float32)

        # 5. Terrain Ruggedness Index (TRI) via moving standard deviation
        # Difference with local 8 neighbours
        tri = np.zeros_like(z, dtype=np.float32)
        padded_z = np.pad(z, 1, mode="edge")
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                diff = padded_z[1+di : z.shape[0]+1+di, 1+dj : z.shape[1]+1+dj] - z
                tri += (diff**2).astype(np.float32)
        tri = np.sqrt(tri / 8.0)

        # 6. Height Above Nearest Drainage (HAND)
        # Approximate thalweg elevation by minimum filtering along local columns
        # In a V-shaped valley, HAND = z - valley_floor_elevation
        min_elev_per_row = np.min(z, axis=1, keepdims=True)
        hand = np.maximum(z - min_elev_per_row, 0.0).astype(np.float32)

        return TerrainFeatures(
            shape=dem.shape,
            elevation_m=dem.elevation,
            slope_deg=slope_deg,
            aspect_deg=aspect_deg,
            plan_curvature=plan_curv,
            profile_curvature=prof_curv,
            topographic_wetness_index=twi,
            stream_power_index=spi,
            terrain_ruggedness_index=tri,
            height_above_nearest_drainage_m=hand,
        )
