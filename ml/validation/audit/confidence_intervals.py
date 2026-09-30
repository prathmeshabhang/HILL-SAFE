"""
confidence_intervals.py — Statistical Uncertainty & Confidence Intervals
========================================================================
Implements exact binomial confidence intervals (Clopper-Pearson, Wilson)
and guarded bootstrap resampling for scientific validation metrics.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

from ml.validation.audit.schema import ConfidenceInterval, ConfidenceIntervalMethod, ValidationUnit


def exact_binomial_ci(
    count: int,
    nobs: int,
    alpha: float = 0.05,
    unit: ValidationUnit = ValidationUnit.POINT,
) -> ConfidenceInterval:
    """
    Computes exact Clopper-Pearson binomial confidence interval for proportions.
    Uses Beta distribution quantiles to guarantee exact coverage for any N.
    """
    if nobs <= 0:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            alpha=alpha,
            method=ConfidenceIntervalMethod.EXACT_CLOPPER_PEARSON,
            sample_size=0,
            unit=unit,
            is_reliable=False,
            reason="Sample size nobs <= 0",
        )

    count = int(np.clip(count, 0, nobs))

    # Clopper-Pearson exact bounds via Beta distribution
    lower = 0.0 if count == 0 else float(stats.beta.ppf(alpha / 2.0, count, nobs - count + 1))
    upper = 1.0 if count == nobs else float(stats.beta.ppf(1.0 - alpha / 2.0, count + 1, nobs - count))

    return ConfidenceInterval(
        lower=lower,
        upper=upper,
        alpha=alpha,
        method=ConfidenceIntervalMethod.EXACT_CLOPPER_PEARSON,
        sample_size=nobs,
        unit=unit,
        is_reliable=True,
    )


def wilson_score_ci(
    count: int,
    nobs: int,
    alpha: float = 0.05,
    unit: ValidationUnit = ValidationUnit.POINT,
) -> ConfidenceInterval:
    """Computes Wilson score interval for proportions."""
    if nobs <= 0:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            alpha=alpha,
            method=ConfidenceIntervalMethod.WILSON_SCORE,
            sample_size=0,
            unit=unit,
            is_reliable=False,
            reason="Sample size nobs <= 0",
        )

    count = int(np.clip(count, 0, nobs))
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    p = count / float(nobs)

    denom = 1.0 + (z**2) / float(nobs)
    center = (p + (z**2) / (2.0 * float(nobs))) / denom
    spread = (z * np.sqrt((p * (1.0 - p) + (z**2) / (4.0 * float(nobs))) / float(nobs))) / denom

    lower = max(0.0, float(center - spread))
    upper = min(1.0, float(center + spread))

    return ConfidenceInterval(
        lower=lower,
        upper=upper,
        alpha=alpha,
        method=ConfidenceIntervalMethod.WILSON_SCORE,
        sample_size=nobs,
        unit=unit,
        is_reliable=True,
    )


def bootstrap_metric_ci(
    y_true: np.ndarray,
    y_score: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    cluster_ids: Optional[List[str]] = None,
    n_bootstraps: int = 1000,
    alpha: float = 0.05,
    min_sample_size: int = 15,
    random_state: int = 42,
    unit: ValidationUnit = ValidationUnit.POINT,
) -> ConfidenceInterval:
    """
    Computes bootstrap confidence interval for continuous/ranking metrics.
    Guarded rule: if sample size or cluster count < min_sample_size, rejects bootstrapping
    to prevent degenerate or statistically misleading intervals.
    """
    n = len(y_true)
    if n < min_sample_size:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            alpha=alpha,
            method=ConfidenceIntervalMethod.NOT_ESTIMABLE,
            sample_size=n,
            unit=unit,
            is_reliable=False,
            reason=f"Bootstrap CI not reliable: sample size N={n} < predefined minimum {min_sample_size}.",
        )

    rng = np.random.RandomState(random_state)
    boot_vals: List[float] = []

    if cluster_ids is not None:
        unique_clusters = np.unique(cluster_ids)
        n_clusters = len(unique_clusters)
        if n_clusters < min_sample_size:
            return ConfidenceInterval(
                lower=None,
                upper=None,
                alpha=alpha,
                method=ConfidenceIntervalMethod.NOT_ESTIMABLE,
                sample_size=n_clusters,
                unit=ValidationUnit.EVENT,
                is_reliable=False,
                reason=f"Event bootstrap CI not reliable: unique events count ({n_clusters}) < {min_sample_size}.",
            )

        cluster_map = {c: np.where(np.array(cluster_ids) == c)[0] for c in unique_clusters}
        for _ in range(n_bootstraps):
            sampled_clusters = rng.choice(unique_clusters, size=n_clusters, replace=True)
            sampled_indices = np.concatenate([cluster_map[c] for c in sampled_clusters])
            if len(np.unique(y_true[sampled_indices])) < 2:
                continue
            val = metric_fn(y_true[sampled_indices], y_score[sampled_indices])
            if val is not None and not np.isnan(val):
                boot_vals.append(val)
    else:
        indices = np.arange(n)
        for _ in range(n_bootstraps):
            b_idx = rng.choice(indices, size=n, replace=True)
            if len(np.unique(y_true[b_idx])) < 2:
                continue
            val = metric_fn(y_true[b_idx], y_score[b_idx])
            if val is not None and not np.isnan(val):
                boot_vals.append(val)

    if len(boot_vals) < 50:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            alpha=alpha,
            method=ConfidenceIntervalMethod.NOT_ESTIMABLE,
            sample_size=n,
            unit=unit,
            is_reliable=False,
            reason="Degenerate bootstrap: fewer than 50 resamples contained both classes.",
        )

    lower = float(np.percentile(boot_vals, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_vals, 100.0 * (1.0 - alpha / 2.0)))

    method_type = ConfidenceIntervalMethod.BOOTSTRAP_EVENT if cluster_ids is not None else ConfidenceIntervalMethod.BOOTSTRAP_POINT

    return ConfidenceInterval(
        lower=lower,
        upper=upper,
        alpha=alpha,
        method=method_type,
        sample_size=n,
        unit=unit,
        is_reliable=True,
    )
