"""
spatial_aligner.py — Multi-Sensor Grid Alignment & 3D Geomorphic Terrain Processor
===================================================================================
Handles:
  1. Multi-resolution spatial grid alignment (10m Sentinel-2, 20m Sentinel-1, 30m DEM).
  2. Lee Adaptive Speckle Filtering on Sentinel-1 SAR VV and VH bands.
  3. Derivation of 3D geomorphic terrain features via Horn's finite-difference formulations:
     - Slope gradient (degrees)
     - Aspect (degrees)
     - Plan and profile curvatures
     - Topographic Wetness Index (TWI) / Flow accumulation proxy
     - Height Above Nearest Drainage (HAND) proxy
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from scipy.ndimage import uniform_filter, zoom

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.ingestion.real_scene_loader import RealSceneBundle
from ml.satellite_hazard.sar.sar_loader import lee_speckle_filter


@dataclass
class AlignedSceneBundle:
    scene_id: str
    shape: Tuple[int, int]
    s2_bands: Dict[str, np.ndarray]
    sar_vv_filtered_db: np.ndarray
    sar_vh_filtered_db: np.ndarray
    dem_elevation_m: np.ndarray
    slope_deg: np.ndarray
    aspect_deg: np.ndarray
    plan_curvature: np.ndarray
    profile_curvature: np.ndarray
    flow_accumulation: np.ndarray
    hand_m: np.ndarray
    scl: np.ndarray
    valid_data_pct: float


class SpatialAligner:
    def __init__(self, config: SatelliteProcessingConfig | None = None):
        self.config = config or SatelliteProcessingConfig()
        self.target_rows = self.config.study_area.grid_rows
        self.target_cols = self.config.study_area.grid_cols
        self.cell_size_m = self.config.study_area.cell_size_m

    def align_and_process(self, bundle: RealSceneBundle) -> AlignedSceneBundle:
        """
        Resamples all bands onto reference spatial grid, filters SAR speckle,
        and computes Horn's 3D geomorphic terrain suite.
        """
        # 1. Resample Sentinel-2 bands to target grid if needed
        aligned_s2: Dict[str, np.ndarray] = {}
        for b_name, arr in bundle.s2_bands.items():
            if arr.shape != (self.target_rows, self.target_cols):
                zf = (self.target_rows / arr.shape[0], self.target_cols / arr.shape[1])
                aligned_s2[b_name] = zoom(arr, zf, order=1).astype(np.float32)
            else:
                aligned_s2[b_name] = arr.copy()

        # Resample SCL
        if bundle.scl.shape != (self.target_rows, self.target_cols):
            zf = (self.target_rows / bundle.scl.shape[0], self.target_cols / bundle.scl.shape[1])
            scl_aligned = zoom(bundle.scl, zf, order=0).astype(np.uint8)
        else:
            scl_aligned = bundle.scl.copy()

        # 2. Resample & Lee-Filter Sentinel-1 SAR Bands
        vv_raw = bundle.sar_bands["VV"]
        vh_raw = bundle.sar_bands["VH"]

        if vv_raw.shape != (self.target_rows, self.target_cols):
            zf = (self.target_rows / vv_raw.shape[0], self.target_cols / vv_raw.shape[1])
            vv_raw = zoom(vv_raw, zf, order=1).astype(np.float32)
            vh_raw = zoom(vh_raw, zf, order=1).astype(np.float32)

        sar_vv_filt = lee_speckle_filter(vv_raw, window_size=5)
        sar_vh_filt = lee_speckle_filter(vh_raw, window_size=5)

        # 3. Resample DEM & Derive 3D Geomorphic Terrain Suite
        dem = bundle.dem
        if dem.shape != (self.target_rows, self.target_cols):
            zf = (self.target_rows / dem.shape[0], self.target_cols / dem.shape[1])
            dem = zoom(dem, zf, order=1).astype(np.float32)

        slope_deg, aspect_deg, plan_curv, prof_curv = self._compute_horns_curvature(dem, self.cell_size_m)
        flow_acc, hand = self._compute_hydrological_proxies(dem, slope_deg)

        return AlignedSceneBundle(
            scene_id=bundle.scene_id,
            shape=(self.target_rows, self.target_cols),
            s2_bands=aligned_s2,
            sar_vv_filtered_db=sar_vv_filt,
            sar_vh_filtered_db=sar_vh_filt,
            dem_elevation_m=dem,
            slope_deg=slope_deg,
            aspect_deg=aspect_deg,
            plan_curvature=plan_curv,
            profile_curvature=prof_curv,
            flow_accumulation=flow_acc,
            hand_m=hand,
            scl=scl_aligned,
            valid_data_pct=bundle.valid_data_pct,
        )

    def _compute_horns_curvature(
        self, dem: np.ndarray, cell_size: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Implements Horn's 3x3 finite-difference convolution for slope, aspect,
        and Zevenbergen-Thorne plan/profile curvatures.
        """
        # Padded dem for boundary preservation
        pad_dem = np.pad(dem, 1, mode="edge")

        # 3x3 neighbors:
        # [z1, z2, z3]
        # [z4, z5, z6]
        # [z7, z8, z9]
        z1 = pad_dem[:-2, :-2]
        z2 = pad_dem[:-2, 1:-1]
        z3 = pad_dem[:-2, 2:]
        z4 = pad_dem[1:-1, :-2]
        z6 = pad_dem[1:-1, 2:]
        z7 = pad_dem[2:, :-2]
        z8 = pad_dem[2:, 1:-1]
        z9 = pad_dem[2:, 2:]

        # Horn's partial derivatives
        dz_dx = ((z3 + 2.0 * z6 + z9) - (z1 + 2.0 * z4 + z7)) / (8.0 * cell_size)
        dz_dy = ((z7 + 2.0 * z8 + z9) - (z1 + 2.0 * z2 + z3)) / (8.0 * cell_size)

        rise_run = np.sqrt(dz_dx ** 2 + dz_dy ** 2)
        slope_rad = np.arctan(rise_run)
        slope_deg = np.degrees(slope_rad).astype(np.float32)

        # Aspect
        aspect_rad = np.arctan2(-dz_dy, -dz_dx)
        aspect_deg = (np.degrees(aspect_rad) + 360.0) % 360.0

        # Curvatures (second partial derivatives)
        d2z_dx2 = ((z4 + z6) - 2.0 * pad_dem[1:-1, 1:-1]) / (cell_size ** 2)
        d2z_dy2 = ((z2 + z8) - 2.0 * pad_dem[1:-1, 1:-1]) / (cell_size ** 2)
        d2z_dxdy = ((z3 - z1) - (z9 - z7)) / (4.0 * cell_size ** 2)

        p = dz_dx
        q = dz_dy
        p2_q2 = p ** 2 + q ** 2
        p2_q2_safe = np.maximum(p2_q2, 1e-6)

        # Plan curvature (contour curvature)
        plan_curv = -((q ** 2) * d2z_dx2 - 2.0 * p * q * d2z_dxdy + (p ** 2) * d2z_dy2) / (p2_q2_safe ** 1.5)
        # Profile curvature (downhill slope curvature)
        prof_curv = -((p ** 2) * d2z_dx2 + 2.0 * p * q * d2z_dxdy + (q ** 2) * d2z_dy2) / (p2_q2_safe * (1.0 + p2_q2_safe) ** 1.5)

        return slope_deg, aspect_deg.astype(np.float32), np.clip(plan_curv, -0.2, 0.2).astype(np.float32), np.clip(prof_curv, -0.2, 0.2).astype(np.float32)

    def _compute_hydrological_proxies(
        self, dem: np.ndarray, slope_deg: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Derives Topographic Wetness Index (TWI) / Flow accumulation proxy
        and Height Above Nearest Drainage (HAND) proxy.
        """
        # Valley floor proxy: low elevation compared to local 15x15 mean
        local_mean = uniform_filter(dem, size=15)
        elevation_relief = dem - local_mean

        # HAND proxy: elevation relief above local drainage channel
        hand = np.maximum(0.0, elevation_relief + 15.0).astype(np.float32)

        # Flow accumulation proxy: inverse of slope in valley troughs
        tan_slope = np.tan(np.radians(np.maximum(1.0, slope_deg)))
        flow_acc = np.clip(1.0 / (tan_slope * (hand + 1.0) * 0.1), 0.1, 100.0).astype(np.float32)

        return flow_acc, hand
