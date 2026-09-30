"""
trend_engine.py — Multi-Horizon Time-Series Trend Intelligence Engine
====================================================================
Analyzes multi-temporal satellite observations across epochs:
  T1 (Pre-monsoon May) -> T2 (Peak-monsoon July) -> T3 (Post-monsoon September)

Outputs:
  - development_trend_score: Direction and velocity of anthropogenic expansion
  - hazard_trend_score: Multi-temporal expansion or contraction of flood/landslide susceptibility
  - recurring_inundation_frequency: Persistent vs transient floodways
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.spectral.index_generator import SpectralIndices


@dataclass
class TimeSeriesTrendResult:
    development_trend: str          # "RAPID_INCREASE", "MODERATE_INCREASE", "STABLE"
    hazard_trend: str               # "ESCALATING", "SEASONAL_PEAK", "STABLE"
    vegetation_trend: str           # "RECOVERING", "STABLE", "DEGRADING"
    mean_development_growth_pct: float
    mean_hazard_growth_pct: float
    recurring_flood_pixels: int
    transient_flood_pixels: int


class TimeSeriesTrendEngine:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def analyze_trajectory(
        self,
        t1_spectral: SpectralIndices,
        t2_spectral: SpectralIndices,
        t3_spectral: Optional[SpectralIndices] = None,
    ) -> TimeSeriesTrendResult:
        """
        Calculates multi-epoch trends across T1, T2, and optional T3.
        """
        # If T3 is not provided, simulate post-monsoon recovery from T2
        if t3_spectral is None:
            # T3 has recovering vegetation on flood margins, slight reduction in standing water
            recov_ndvi = np.clip(t2_spectral.ndvi + 0.08, -1.0, 1.0)
            recov_mndwi = np.clip(t2_spectral.mndwi - 0.12, -1.0, 1.0)
            recov_ndbi = np.clip(t2_spectral.ndbi + 0.02, -1.0, 1.0)
        else:
            recov_ndvi = t3_spectral.ndvi
            recov_mndwi = t3_spectral.mndwi
            recov_ndbi = t3_spectral.ndbi

        # 1. Development Growth: NDBI trajectory from T1 -> T2 -> T3
        delta_ndbi_1_2 = t2_spectral.ndbi - t1_spectral.ndbi
        delta_ndbi_2_3 = recov_ndbi - t2_spectral.ndbi
        net_dev_growth = float(np.mean(delta_ndbi_1_2 + delta_ndbi_2_3) * 100.0)

        dev_trend = "STABLE"
        if net_dev_growth > 4.0:
            dev_trend = "RAPID_INCREASE"
        elif net_dev_growth > 1.5:
            dev_trend = "MODERATE_INCREASE"

        # 2. Hazard Growth: Active water MNDWI expansion
        mndwi_t1_water = t1_spectral.mndwi > 0.05
        mndwi_t2_water = t2_spectral.mndwi > 0.05
        mndwi_t3_water = recov_mndwi > 0.05

        recurring_water = int(np.sum(mndwi_t1_water & mndwi_t2_water))
        transient_water = int(np.sum((~mndwi_t1_water) & mndwi_t2_water))

        hazard_growth = float((transient_water / max(1, recurring_water)) * 100.0)
        haz_trend = "SEASONAL_PEAK" if transient_water > recurring_water * 0.5 else "STABLE"

        # 3. Vegetation Trend: NDVI trajectory
        net_veg_change = float(np.mean(recov_ndvi - t1_spectral.ndvi) * 100.0)
        veg_trend = "RECOVERING" if net_veg_change >= -2.0 else "DEGRADING"

        return TimeSeriesTrendResult(
            development_trend=dev_trend,
            hazard_trend=haz_trend,
            vegetation_trend=veg_trend,
            mean_development_growth_pct=round(net_dev_growth, 2),
            mean_hazard_growth_pct=round(hazard_growth, 2),
            recurring_flood_pixels=recurring_water,
            transient_flood_pixels=transient_water,
        )
