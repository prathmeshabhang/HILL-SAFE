"""M18 — Validation report generation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np

from .model import (
    M18CalibrationModel,
    _brier_score,
    _expected_calibration_error,
    _calibration_slope_intercept,
    MIN_CALIBRATION_SAMPLES,
)

logger = logging.getLogger(__name__)


def generate_validation_report(
    model: M18CalibrationModel,
    y_true: np.ndarray,
    y_score_raw: np.ndarray,
    source_model_id: str = "GENERIC",
) -> Dict[str, Any]:
    """
    Generate a scientifically rigorous validation report for M18.

    Parameters
    ----------
    model          : Fitted M18CalibrationModel
    y_true         : Binary ground-truth labels (0/1) — EXTERNAL holdout
    y_score_raw    : Raw probabilities from the source model
    source_model_id: E.g. 'M2_FLOOD_RISK'

    Returns
    -------
    dict with full metric breakdown
    """
    y_true = np.asarray(y_true, dtype=float)
    y_score_raw = np.asarray(y_score_raw, dtype=float)
    n = len(y_true)

    report: Dict[str, Any] = {
        "source_model": source_model_id,
        "n_eval": n,
        "n_positive": int(y_true.sum()),
        "n_negative": int((1 - y_true).sum()),
    }

    if n < MIN_CALIBRATION_SAMPLES or not model._fitted:
        report["validation_status"] = "INSUFFICIENT_EVIDENCE"
        report["note"] = (
            "External validation skipped — fewer than "
            f"{MIN_CALIBRATION_SAMPLES} labelled samples available."
        )
        return report

    # Calibrated probabilities
    cal_probs = np.array([model.calibrate(p)[0] for p in y_score_raw], dtype=float)

    # Metrics — uncalibrated
    report["uncalibrated"] = {
        "brier_score": _brier_score(y_true, y_score_raw),
        "ece": _expected_calibration_error(y_true, y_score_raw),
    }

    # Metrics — calibrated
    slope, intercept = _calibration_slope_intercept(y_true, cal_probs)
    report["calibrated"] = {
        "brier_score": _brier_score(y_true, cal_probs),
        "ece": _expected_calibration_error(y_true, cal_probs),
        "calibration_slope": slope,
        "calibration_intercept": intercept,
        "method": model._best_method,
    }

    try:
        from sklearn.metrics import roc_auc_score, average_precision_score

        if len(np.unique(y_true)) == 2:
            report["calibrated"]["roc_auc"] = float(roc_auc_score(y_true, cal_probs))
            report["calibrated"]["pr_auc"] = float(
                average_precision_score(y_true, cal_probs)
            )
    except Exception as exc:
        logger.debug("ROC/PR-AUC computation skipped: %s", exc)

    brier_improve = (
        report["uncalibrated"]["brier_score"] - report["calibrated"]["brier_score"]
    )
    report["brier_improvement"] = round(brier_improve, 6)
    report["validation_status"] = "CALIBRATION_EVALUATED"
    report["external_ground_truth_note"] = (
        "If y_true is derived from synthetic/proxy data, "
        "mark validation as PROXY_VALIDATED not EXTERNALLY_VALIDATED."
    )

    return report
