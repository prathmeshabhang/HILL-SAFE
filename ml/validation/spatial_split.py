"""
spatial_split.py — Spatial Holdout Partitioning for Preventing Spatial Leakage
=============================================================================
Splits geospatial observations into geographically isolated spatial partitions
(e.g., Northern Upper Beas Catchment vs Southern Beas Catchment) based on
latitude/longitude boundaries.

Prevents spatial auto-correlation leakage where random train/test splits
test on pixels immediately adjacent to training pixels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class SpatialSplitResult:
    train_indices: np.ndarray
    test_indices: np.ndarray
    train_count: int
    test_count: int
    train_lat_range: Tuple[float, float]
    test_lat_range: Tuple[float, float]
    train_lon_range: Tuple[float, float]
    test_lon_range: Tuple[float, float]
    split_method: str
    buffer_deg: float


def create_spatial_block_holdout(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    test_fraction: float = 0.20,
    buffer_deg: float = 0.01,  # ~1.1 km buffer to prevent border leakage
) -> SpatialSplitResult:
    """
    Creates a spatial holdout partition by geographic latitude cutoff.
    Points in the buffer zone between train and test boundaries are excluded
    from training to eliminate edge leakage.
    """
    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(f"Spatial coordinates '{lat_col}' and '{lon_col}' required for spatial split.")

    lats = df[lat_col].values
    cutoff = np.quantile(lats, 1.0 - test_fraction)

    # Test set: northernmost 20%
    test_mask = lats >= cutoff
    # Train set: southernmost area minus buffer
    train_mask = lats < (cutoff - buffer_deg)

    test_idx = np.where(test_mask)[0]
    train_idx = np.where(train_mask)[0]

    train_lat_range = (float(np.min(lats[train_idx])), float(np.max(lats[train_idx])))
    test_lat_range = (float(np.min(lats[test_idx])), float(np.max(lats[test_idx])))
    train_lon_range = (float(np.min(df[lon_col].iloc[train_idx])), float(np.max(df[lon_col].iloc[train_idx])))
    test_lon_range = (float(np.min(df[lon_col].iloc[test_idx])), float(np.max(df[lon_col].iloc[test_idx])))

    return SpatialSplitResult(
        train_indices=train_idx,
        test_indices=test_idx,
        train_count=len(train_idx),
        test_count=len(test_idx),
        train_lat_range=train_lat_range,
        test_lat_range=test_lat_range,
        train_lon_range=train_lon_range,
        test_lon_range=test_lon_range,
        split_method="LATITUDE_BLOCK_WITH_BUFFER",
        buffer_deg=buffer_deg,
    )
