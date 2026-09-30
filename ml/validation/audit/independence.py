"""
independence.py — Spatial Independence Audit Layer
===================================================
Audits spatial independence of external validation points against training data
using strict geodesic distance buffers. Enforces mathematical invariants.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.validation.audit.schema import IndependenceStatus, SpatialIndependenceAudit


def haversine_distance_m(lat1: float, lon1: float, lats2: np.ndarray, lons2: np.ndarray) -> np.ndarray:
    """Computes Haversine geodesic distance in meters from a point to an array of points."""
    R = 6371000.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lats2)
    delta_phi = np.radians(lats2 - lat1)
    delta_lambda = np.radians(lons2 - lon1)
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c


def audit_spatial_independence(
    eval_df: pd.DataFrame,
    train_lats: np.ndarray,
    train_lons: np.ndarray,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    buffer_threshold_m: float = 500.0,
) -> Tuple[SpatialIndependenceAudit, pd.DataFrame]:
    """
    Audits spatial independence for every external evaluation point.
    Returns:
      1. SpatialIndependenceAudit dataclass with rigorous invariant verification.
      2. Enriched DataFrame with distance_to_training_m and independence_status.
    """
    total = len(eval_df)
    indep_count = 0
    non_indep_count = 0
    unknown_count = 0

    statuses: List[str] = []
    min_distances: List[float] = []

    for _, row in eval_df.iterrows():
        lat_val = row.get(lat_col)
        lon_val = row.get(lon_col)

        if pd.isna(lat_val) or pd.isna(lon_val):
            statuses.append(IndependenceStatus.UNKNOWN.value)
            min_distances.append(float("nan"))
            unknown_count += 1
            continue

        try:
            lat = float(lat_val)
            lon = float(lon_val)
        except (ValueError, TypeError):
            statuses.append(IndependenceStatus.UNKNOWN.value)
            min_distances.append(float("nan"))
            unknown_count += 1
            continue

        dists = haversine_distance_m(lat, lon, train_lats, train_lons)
        min_d = float(np.min(dists))
        min_distances.append(min_d)

        if min_d > buffer_threshold_m:
            statuses.append(IndependenceStatus.INDEPENDENT.value)
            indep_count += 1
        else:
            statuses.append(IndependenceStatus.NON_INDEPENDENT.value)
            non_indep_count += 1

    # Invariant verification
    if (indep_count + non_indep_count + unknown_count) != total:
        raise AssertionError(
            f"Independence audit invariant broken: {indep_count} + {non_indep_count} + {unknown_count} != {total}"
        )
    if indep_count > total:
        raise AssertionError(f"Independent count {indep_count} cannot exceed total {total}")

    audit_result = SpatialIndependenceAudit(
        total_samples=total,
        independent_count=indep_count,
        non_independent_count=non_indep_count,
        unknown_count=unknown_count,
        distance_threshold_m=buffer_threshold_m,
        primary_evaluation_subset="INDEPENDENT",
    )

    df_out = eval_df.copy()
    df_out["nearest_training_dist_m"] = [round(d, 2) if not np.isnan(d) else None for d in min_distances]
    df_out["independence_status"] = statuses
    df_out["is_spatially_independent"] = [s == IndependenceStatus.INDEPENDENT.value for s in statuses]

    return audit_result, df_out
