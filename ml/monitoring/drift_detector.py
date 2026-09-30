"""
ml/monitoring/drift_detector.py
===============================
Distribution Drift, Concept Shift & Data Integrity Monitor.
Computes:
  - Population Stability Index (PSI) between baseline and production streaming distributions.
  - Two-sample Kolmogorov-Smirnov (KS) statistic for continuous telemetry.
  - Missingness drift tracking over rolling operational windows.

Rule:
  DO NOT AUTOMATICALLY RETRAIN.
  When drift exceeds threshold, generate DRIFT_DETECTED status and flag for scientific human review.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class DriftMetricResult:
    feature_name: str
    psi_score: float
    ks_statistic: float
    ks_pvalue: float
    baseline_missing_rate: float
    streaming_missing_rate: float
    drift_status: str           # NO_DRIFT | MODERATE_DRIFT | DRIFT_DETECTED
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DistributionDriftMonitor:
    """
    Monitors input feature distributions (rainfall, river level, sensor values)
    against baseline training/calibration reference sets.
    """

    def __init__(self, psi_warning_threshold: float = 0.1, psi_critical_threshold: float = 0.25):
        self.psi_warning = psi_warning_threshold
        self.psi_critical = psi_critical_threshold

    def calculate_psi(
        self,
        baseline: np.ndarray,
        target: np.ndarray,
        num_buckets: int = 10,
    ) -> float:
        """
        Calculates Population Stability Index (PSI) between two 1D numerical arrays.
        """
        b_clean = baseline[~np.isnan(baseline)]
        t_clean = target[~np.isnan(target)]

        if len(b_clean) < 10 or len(t_clean) < 10:
            return 0.0

        # Create quantile buckets based on baseline
        quantiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(b_clean, quantiles)
        bins[0] -= 1e-5
        bins[-1] += 1e-5

        b_counts, _ = np.histogram(b_clean, bins=bins)
        t_counts, _ = np.histogram(t_clean, bins=bins)

        b_pct = np.maximum(b_counts / len(b_clean), 1e-4)
        t_pct = np.maximum(t_counts / len(t_clean), 1e-4)

        psi_val = np.sum((t_pct - b_pct) * np.log(t_pct / b_pct))
        return float(psi_val)

    def calculate_ks_stat(self, baseline: np.ndarray, target: np.ndarray) -> Tuple[float, float]:
        """
        Simplified Kolmogorov-Smirnov 2-sample test statistic.
        """
        from scipy.stats import ks_2samp
        b_clean = baseline[~np.isnan(baseline)]
        t_clean = target[~np.isnan(target)]

        if len(b_clean) < 5 or len(t_clean) < 5:
            return 0.0, 1.0

        res = ks_2samp(b_clean, t_clean)
        return float(res.statistic), float(res.pvalue)

    def evaluate_feature(
        self,
        feature_name: str,
        baseline_values: Sequence[float],
        streaming_values: Sequence[float],
    ) -> DriftMetricResult:
        b_arr = np.array(baseline_values, dtype=float)
        t_arr = np.array(streaming_values, dtype=float)

        b_missing = float(np.mean(np.isnan(b_arr)))
        t_missing = float(np.mean(np.isnan(t_arr)))

        psi = self.calculate_psi(b_arr, t_arr)
        ks_stat, ks_pval = self.calculate_ks_stat(b_arr, t_arr)

        if psi >= self.psi_critical or ks_pval < 0.001:
            status = "DRIFT_DETECTED"
            rec = "CRITICAL: Distribution drift detected. Halt automated trust; require scientific human audit."
        elif psi >= self.psi_warning or ks_pval < 0.05:
            status = "MODERATE_DRIFT"
            rec = "WARNING: Moderate distribution shift. Log alert and monitor upcoming 24h rolling window."
        else:
            status = "NO_DRIFT"
            rec = "Distribution is stable within expected variation."

        return DriftMetricResult(
            feature_name=feature_name,
            psi_score=round(psi, 4),
            ks_statistic=round(ks_stat, 4),
            ks_pvalue=round(ks_pval, 6),
            baseline_missing_rate=round(b_missing, 4),
            streaming_missing_rate=round(t_missing, 4),
            drift_status=status,
            recommendation=rec,
        )

    def audit_batch(
        self,
        baseline_df: Dict[str, Sequence[float]],
        streaming_df: Dict[str, Sequence[float]],
    ) -> Dict[str, Any]:
        """Audits multiple features returning aggregate drift assessment."""
        results = {}
        drift_count = 0

        for col in baseline_df:
            if col in streaming_df:
                res = self.evaluate_feature(col, baseline_df[col], streaming_df[col])
                results[col] = res.to_dict()
                if res.drift_status == "DRIFT_DETECTED":
                    drift_count += 1

        overall_status = "DRIFT_DETECTED" if drift_count > 0 else "STABLE"

        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "overall_status": overall_status,
            "drifted_features_count": drift_count,
            "total_features_monitored": len(results),
            "features": results,
        }
