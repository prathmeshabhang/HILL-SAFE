"""
temporal_river_change.py — Multi-Temporal River Width & Water Extent Change Engine
==================================================================================
Compares pre-event and post-event observation timestamps (T-30d to T+7d) to identify:
  1. River channel narrowing / sudden cross-sectional constriction.
  2. Upstream water body expansion.
  3. Downstream channel drying or flow signature reduction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class TemporalObservation:
    timestamp: str          # e.g., "2023-07-01", "2023-07-09", "2023-07-10"
    relative_day: str       # "T-15d", "T-1d", "T0", "T+1d"
    water_mask: np.ndarray
    water_area_km2: float
    sar_vv_db: Optional[np.ndarray] = None


@dataclass
class TemporalChangeResult:
    upstream_expansion_pct: float
    downstream_reduction_pct: float
    width_narrowing_pct: float
    expansion_rate_km2_day: float
    is_expanding_upstream: bool
    is_constricted_downstream: bool
    water_diff_grid: np.ndarray  # +1 = new water, -1 = lost water, 0 = unchanged


class TemporalRiverChangeEngine:
    """Detects hydraulic anomalies indicating rapid impoundment or channel cutoff."""

    def compare_observations(
        self,
        obs_baseline: TemporalObservation,
        obs_current: TemporalObservation,
        reach_center_row: int,
        days_between: float = 1.0,
    ) -> TemporalChangeResult:
        """
        Calculates differential changes partitioned into upstream (rows < reach_center_row)
        and downstream (rows > reach_center_row) sections of the river channel.
        """
        w_base = obs_baseline.water_mask
        w_curr = obs_current.water_mask

        # Water difference grid: +1 new water, -1 dried water
        diff = w_curr.astype(np.int16) - w_base.astype(np.int16)

        # Split into upstream and downstream partitions
        rows = w_curr.shape[0]
        split_idx = max(5, min(rows - 5, reach_center_row))

        up_base = float(np.sum(w_base[:split_idx, :]))
        up_curr = float(np.sum(w_curr[:split_idx, :]))

        down_base = float(np.sum(w_base[split_idx:, :]))
        down_curr = float(np.sum(w_curr[split_idx:, :]))

        # Percentage expansions / reductions
        up_change_pct = ((up_curr - up_base) / max(up_base, 1.0)) * 100.0
        down_change_pct = ((down_curr - down_base) / max(down_base, 1.0)) * 100.0

        # Narrowing at the blockage latitude (center row +/- 2 rows)
        ch_width_base = float(np.sum(w_base[split_idx - 2 : split_idx + 2, :]))
        ch_width_curr = float(np.sum(w_curr[split_idx - 2 : split_idx + 2, :]))
        width_reduction_pct = max(0.0, ((ch_width_base - ch_width_curr) / max(ch_width_base, 1.0)) * 100.0)

        # Expansion rate in km2 / day
        pixel_km2 = (30.0 * 30.0) / 1_000_000.0
        area_diff_km2 = (up_curr - up_base) * pixel_km2
        rate_km2_day = area_diff_km2 / max(days_between, 0.1)

        return TemporalChangeResult(
            upstream_expansion_pct=round(float(up_change_pct), 1),
            downstream_reduction_pct=round(float(-down_change_pct), 1),
            width_narrowing_pct=round(float(width_reduction_pct), 1),
            expansion_rate_km2_day=round(float(rate_km2_day), 3),
            is_expanding_upstream=bool(up_change_pct >= 20.0),
            is_constricted_downstream=bool(down_change_pct <= -15.0 or width_reduction_pct >= 40.0),
            water_diff_grid=diff,
        )
