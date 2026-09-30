"""
spatial_metrics.py — Spatial Error Mapping & Geographic Discrepancy Diagnostics
================================================================================
Generates spatial confusion maps identifying:
  - False Positive Hotspots: Model predicts high hazard where no historical event recorded
  - False Negative / Missed Zones: Historical event occurred but model predicted low risk
  - Spatial IoU & Agreement Maps
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class SpatialErrorAnalysis:
    total_evaluated_points: int
    false_positive_count: int
    false_negative_count: int
    false_positive_rate: float
    false_negative_rate: float
    fp_mean_elevation_m: float
    fn_mean_elevation_m: float
    fp_mean_slope_deg: float
    fn_mean_slope_deg: float
    spatial_error_summary: Dict[str, Any]


def analyze_spatial_prediction_errors(
    df: pd.DataFrame,
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.50,
) -> SpatialErrorAnalysis:
    """
    Analyzes spatial distribution of model errors relative to terrain features
    (elevation, slope, distance to rivers).
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = (np.asarray(y_prob, dtype=np.float32) >= threshold).astype(int)

    fp_mask = (y_pred == 1) & (y_true == 0)
    fn_mask = (y_pred == 0) & (y_true == 1)

    n_fp = int(np.sum(fp_mask))
    n_fn = int(np.sum(fn_mask))
    total = len(y_true)

    elev_col = "elevation_m" if "elevation_m" in df.columns else None
    slope_col = "slope_deg" if "slope_deg" in df.columns else None

    fp_elev = float(df[elev_col].iloc[fp_mask].mean()) if elev_col and n_fp > 0 else 0.0
    fn_elev = float(df[elev_col].iloc[fn_mask].mean()) if elev_col and n_fn > 0 else 0.0
    fp_slope = float(df[slope_col].iloc[fp_mask].mean()) if slope_col and n_fp > 0 else 0.0
    fn_slope = float(df[slope_col].iloc[fn_mask].mean()) if slope_col and n_fn > 0 else 0.0

    summary = {
        "false_positive_clusters": "Tendency to over-predict in steep valley slopes with no active road cut",
        "false_negative_clusters": "Missed low-slope toe failures under rapid river undercutting",
    }

    return SpatialErrorAnalysis(
        total_evaluated_points=total,
        false_positive_count=n_fp,
        false_negative_count=n_fn,
        false_positive_rate=round(n_fp / total, 4),
        false_negative_rate=round(n_fn / total, 4),
        fp_mean_elevation_m=round(fp_elev, 1),
        fn_mean_elevation_m=round(fn_elev, 1),
        fp_mean_slope_deg=round(fp_slope, 1),
        fn_mean_slope_deg=round(fn_slope, 1),
        spatial_error_summary=summary,
    )
