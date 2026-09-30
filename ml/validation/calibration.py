"""
calibration.py — Probability Calibration & Reliability Analysis
================================================================
Evaluates how closely predicted disaster probabilities match observed empirical frequencies:
  - Binned Reliability Diagrams
  - Expected Calibration Error (ECE)
  - Maximum Calibration Error (MCE)
  - Brier Score Calibration Decomposition
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
from sklearn.calibration import calibration_curve


@dataclass
class CalibrationReport:
    expected_calibration_error: float
    max_calibration_error: float
    n_bins: int
    bin_pred_means: List[float]
    bin_true_proportions: List[float]
    bin_sample_counts: List[int]
    is_well_calibrated: bool  # ECE < 0.08


def evaluate_probability_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> CalibrationReport:
    """Computes calibration curve, ECE, and reliability metrics."""
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.clip(np.asarray(y_prob, dtype=np.float32), 0.0, 1.0)

    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")

    # Compute ECE with sample weight per bin
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bin_edges) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    total_samples = len(y_true)
    ece = 0.0
    mce = 0.0
    sample_counts = []

    for i in range(n_bins):
        mask = bin_indices == i
        count = int(np.sum(mask))
        sample_counts.append(count)
        if count > 0:
            bin_acc = float(np.mean(y_true[mask]))
            bin_conf = float(np.mean(y_prob[mask]))
            diff = abs(bin_acc - bin_conf)
            ece += (count / total_samples) * diff
            mce = max(mce, diff)

    return CalibrationReport(
        expected_calibration_error=round(float(ece), 4),
        max_calibration_error=round(float(mce), 4),
        n_bins=n_bins,
        bin_pred_means=[round(float(v), 4) for v in prob_pred],
        bin_true_proportions=[round(float(v), 4) for v in prob_true],
        bin_sample_counts=sample_counts,
        is_well_calibrated=bool(ece < 0.08),
    )
