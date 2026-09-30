"""
pressure_engine.py — Observed Development Pressure Detection Engine
====================================================================
Identifies areas where human infrastructure and anthropogenic activities
are expanding into mountainous terrain:
  - Normalized Difference Built-up Index (NDBI)
  - Disturbed ground / lack of dense vegetation (1 - NDVI)
  - Proximity to primary transport corridors (NH-3, bypasses)
  - Riverbank encroachment within active floodways

NOTE: In accordance with scientific specifications, this output is designated
"Observed Development / Development Pressure", not an assertion of legality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.spectral.index_generator import SpectralIndices
from ml.satellite_hazard.terrain.terrain_engine import TerrainFeatures


@dataclass
class DevelopmentPressureResult:
    shape: Tuple[int, int]
    development_pressure_score: np.ndarray  # [0.0, 1.0]
    high_pressure_mask: np.ndarray          # Pressure >= 0.60
    river_corridor_encroachment: np.ndarray # High pressure inside active HAND buffer
    mean_pressure: float
    high_pressure_area_pct: float


class DevelopmentPressureEngine:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def evaluate(self, spectral: SpectralIndices, terrain: TerrainFeatures) -> DevelopmentPressureResult:
        ndbi = spectral.ndbi
        ndvi = spectral.ndvi
        hand = terrain.height_above_nearest_drainage_m
        slope = terrain.slope_deg

        # 1. Built-up spectral signal: NDBI > -0.05 indicates concrete, metal, or compacted soil
        built_signal = np.clip((ndbi + 0.15) / 0.50, 0.0, 1.0)

        # 2. Vegetation clearing signal: 1 - NDVI
        clearing_signal = np.clip(1.0 - ((ndvi + 0.20) / 0.80), 0.0, 1.0)

        # 3. Transport corridor accessibility:
        # Development clusters in valley bottoms (slope < 25 deg, near roads)
        slope_accessibility = np.clip(1.0 - (slope / 35.0), 0.0, 1.0)

        # 4. Multi-factor development pressure formulation
        # P_dev = 0.45 * Built_up + 0.25 * Clearing + 0.30 * Accessibility
        raw_pressure = (
            0.45 * built_signal +
            0.25 * clearing_signal +
            0.30 * slope_accessibility
        )
        pressure = np.clip(raw_pressure, 0.0, 1.0).astype(np.float32)

        # 5. Critical Encroachment: Development within immediate river active corridor (HAND < 15m)
        encroachment = (pressure >= 0.50) & (hand < 15.0)

        high_pressure = pressure >= self.config.critical_dev_pressure_min
        high_pct = float(np.mean(high_pressure) * 100.0)
        mean_p = float(np.mean(pressure))

        return DevelopmentPressureResult(
            shape=spectral.shape,
            development_pressure_score=pressure,
            high_pressure_mask=high_pressure,
            river_corridor_encroachment=encroachment,
            mean_pressure=round(mean_p, 4),
            high_pressure_area_pct=round(high_pct, 2),
        )
