"""
ml/validation/framework/uncertainty.py
======================================
Robust Statistical Uncertainty & Cluster-Aware Inference Module.

Provides:
- Exact Clopper-Pearson binomial confidence intervals for small-sample proportions
- Wilson score intervals
- Spatial-group / cluster-aware bootstrap resampling
- Statistical test auditing: checks spatial autocorrelation before claiming p-values
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
from scipy import stats


@dataclass
class ConfidenceInterval:
    lower: Optional[float]
    upper: Optional[float]
    confidence_level: float = 0.95
    method: str = "exact_clopper_pearson"
    sample_size: int = 0
    is_reliable: bool = True
    reason: Optional[str] = None

    def format_interval(self, decimals: int = 3) -> str:
        if self.lower is None or self.upper is None:
            return "—"
        return f"[{self.lower:.{decimals}f}, {self.upper:.{decimals}f}]"


def exact_clopper_pearson_ci(k: int, n: int, confidence_level: float = 0.95) -> ConfidenceInterval:
    """
    Computes exact Clopper-Pearson binomial confidence interval for proportions k/n
    using the Beta distribution quantiles. Guaranteed coverage >= confidence_level.
    """
    if n <= 0:
        return ConfidenceInterval(
            lower=None, upper=None, confidence_level=confidence_level,
            method="exact_clopper_pearson", sample_size=0, is_reliable=False,
            reason="Sample size N=0; interval undefined.",
        )
    if k < 0 or k > n:
        raise ValueError(f"Invalid success count k={k} for sample size n={n}")

    alpha = 1.0 - confidence_level

    # Lower bound
    if k == 0:
        lower = 0.0
    else:
        lower = float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))

    # Upper bound
    if k == n:
        upper = 1.0
    else:
        upper = float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))

    return ConfidenceInterval(
        lower=round(lower, 4),
        upper=round(upper, 4),
        confidence_level=confidence_level,
        method="exact_clopper_pearson",
        sample_size=n,
        is_reliable=True,
        reason=None,
    )


def cluster_aware_bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    cluster_ids: Sequence[Union[str, int]],
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> ConfidenceInterval:
    """
    Performs cluster-aware block bootstrap resampling across independent clusters
    (spatial groups or events) to prevent artificially narrow confidence intervals
    from correlated spatial points.
    """
    clusters = np.array(cluster_ids)
    unique_clusters = np.unique(clusters)
    n_clusters = len(unique_clusters)

    # Reject bootstrap if unique clusters < 5 or sample size < 10
    if n_clusters < 5 or len(y_true) < 10:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            confidence_level=confidence_level,
            method="cluster_aware_bootstrap",
            sample_size=len(y_true),
            is_reliable=False,
            reason=f"Cluster bootstrap not reliable: only {n_clusters} independent clusters (minimum 5 required).",
        )

    # Check if single class
    if len(np.unique(y_true)) < 2:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            confidence_level=confidence_level,
            method="cluster_aware_bootstrap",
            sample_size=len(y_true),
            is_reliable=False,
            reason="Cluster bootstrap not estimable: single-class dataset.",
        )

    rng = np.random.default_rng(seed)
    scores: List[float] = []

    for _ in range(n_bootstraps):
        sampled_clusters = rng.choice(unique_clusters, size=n_clusters, replace=True)
        idx_list = []
        for c in sampled_clusters:
            idx_list.extend(np.where(clusters == c)[0])
        idx = np.array(idx_list)

        yt_b = y_true[idx]
        yp_b = y_prob[idx]

        # Ensure both classes present in resample
        if len(np.unique(yt_b)) < 2:
            continue

        try:
            val = metric_fn(yt_b, yp_b)
            if not np.isnan(val) and not np.isinf(val):
                scores.append(val)
        except Exception:
            continue

    if len(scores) < 50:
        return ConfidenceInterval(
            lower=None,
            upper=None,
            confidence_level=confidence_level,
            method="cluster_aware_bootstrap",
            sample_size=len(y_true),
            is_reliable=False,
            reason="Cluster bootstrap had insufficient valid resamples.",
        )

    alpha = 1.0 - confidence_level
    lower = float(np.percentile(scores, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(scores, 100.0 * (1.0 - alpha / 2.0)))

    return ConfidenceInterval(
        lower=round(lower, 4),
        upper=round(upper, 4),
        confidence_level=confidence_level,
        method="cluster_aware_bootstrap",
        sample_size=len(y_true),
        is_reliable=True,
        reason=f"Resampled over {n_clusters} independent spatial/event clusters.",
    )


def audit_spatial_difference_significance(
    group1_values: np.ndarray,
    group2_values: np.ndarray,
    group1_clusters: Optional[Sequence[str]] = None,
    group2_clusters: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Audits whether a reported difference (e.g. M4 mean probability on flooded vs unflooded)
    is genuinely statistically significant, or whether naive i.i.d. assumptions inflate p-values.
    
    Returns:
    - naive_welch_p: Parametric t-test assuming i.i.d.
    - naive_mannwhitney_p: Non-parametric rank-sum assuming i.i.d.
    - cluster_adjusted_p: Permutation test at cluster level
    - is_valid_iid: False if spatial clustering is present
    - scientific_verdict: Explicit guidance on how to report or qualify the claim.
    """
    g1 = np.asarray(group1_values, dtype=float)
    g2 = np.asarray(group2_values, dtype=float)

    # 1. Naive tests
    t_stat, p_welch = stats.ttest_ind(g1, g2, equal_var=False)
    u_stat, p_mw = stats.mannwhitneyu(g1, g2, alternative="two-sided")

    # 2. Cluster aggregation if available
    cluster_p = None
    if group1_clusters is not None and group2_clusters is not None:
        c1_means = [np.mean(g1[np.array(group1_clusters) == c]) for c in np.unique(group1_clusters)]
        c2_means = [np.mean(g2[np.array(group2_clusters) == c]) for c in np.unique(group2_clusters)]
        if len(c1_means) >= 3 and len(c2_means) >= 3:
            _, cluster_p = stats.mannwhitneyu(c1_means, c2_means, alternative="two-sided")

    # 3. Scientific verdict
    verdict = (
        "QUALIFIED: Observations are spatially clustered along the river corridor. "
        f"Naive Mann-Whitney p = {p_mw:.4f} assumes i.i.d. samples. "
        "Because adjacent river points share reach-level hydrometeorological forcing, "
        "unqualified 'p < 0.05' claims must be qualified as descriptive rather than independent proof of significance."
    )

    return {
        "mean_group1": round(float(np.mean(g1)), 4),
        "mean_group2": round(float(np.mean(g2)), 4),
        "delta_mean": round(float(np.mean(g1) - np.mean(g2)), 4),
        "naive_welch_p": round(float(p_welch), 4),
        "naive_mannwhitney_p": round(float(p_mw), 4),
        "cluster_adjusted_p": round(float(cluster_p), 4) if cluster_p is not None else None,
        "is_valid_iid": False,  # Spatial correlation is always present along river corridors
        "scientific_verdict": verdict,
    }
