"""M18 — Calibration model: Platt scaling + isotonic regression."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Minimum number of labelled samples required to fit a calibrator.
MIN_CALIBRATION_SAMPLES = 50
MINIMUM_POSITIVE_SAMPLES = 5


def _expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() == 0:
            continue
        acc = y_true[mask].mean()
        conf = y_prob[mask].mean()
        ece += (mask.sum() / n) * abs(acc - conf)
    return float(ece)


def _brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Mean squared error between probabilities and binary labels."""
    return float(np.mean((y_prob - y_true) ** 2))


def _calibration_slope_intercept(
    y_true: np.ndarray, y_prob: np.ndarray
) -> Tuple[float, float]:
    """Logistic calibration slope/intercept via simple linear regression on log-odds."""
    eps = 1e-6
    log_odds = np.log(np.clip(y_prob, eps, 1 - eps) / (1 - np.clip(y_prob, eps, 1 - eps)))
    # OLS: slope and intercept of logit-y_prob → y_true
    X = np.column_stack([log_odds, np.ones_like(log_odds)])
    try:
        coeffs, _, _, _ = np.linalg.lstsq(X, y_true, rcond=None)
        slope, intercept = float(coeffs[0]), float(coeffs[1])
    except Exception:
        slope, intercept = 1.0, 0.0
    return slope, intercept


class PlattCalibrator:
    """Logistic (Platt) calibration via sklearn LogisticRegression."""

    def __init__(self) -> None:
        self._lr: Any = None
        self.fitted = False

    def fit(self, y_true: np.ndarray, y_score: np.ndarray) -> "PlattCalibrator":
        from sklearn.linear_model import LogisticRegression

        X = y_score.reshape(-1, 1)
        self._lr = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
        self._lr.fit(X, y_true)
        self.fitted = True
        return self

    def predict_proba(self, y_score: np.ndarray) -> np.ndarray:
        if not self.fitted:
            return y_score
        return self._lr.predict_proba(y_score.reshape(-1, 1))[:, 1]


class IsotonicCalibrator:
    """Isotonic regression calibration (non-parametric monotone)."""

    def __init__(self) -> None:
        self._iso: Any = None
        self.fitted = False

    def fit(self, y_true: np.ndarray, y_score: np.ndarray) -> "IsotonicCalibrator":
        from sklearn.isotonic import IsotonicRegression

        self._iso = IsotonicRegression(out_of_bounds="clip")
        self._iso.fit(y_score, y_true)
        self.fitted = True
        return self

    def predict_proba(self, y_score: np.ndarray) -> np.ndarray:
        if not self.fitted:
            return y_score
        return np.clip(self._iso.predict(y_score), 0.0, 1.0)


class M18CalibrationModel:
    """
    Probability calibration layer for Floody Shield hazard models.

    Wraps Platt scaling and isotonic regression.  Selects the method with
    the lower Brier score on the calibration holdout.  Never touches the
    external validation split.
    """

    MODEL_ID = "M18"
    MODEL_VERSION = "1.0.0"

    def __init__(self) -> None:
        self.platt = PlattCalibrator()
        self.isotonic = IsotonicCalibrator()
        self._best_method: str = "insufficient_evidence"
        self._platt_brier: Optional[float] = None
        self._iso_brier: Optional[float] = None
        self._fitted = False
        self._n_train: int = 0
        self._n_pos: int = 0

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        y_true: np.ndarray,
        y_score: np.ndarray,
        val_fraction: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Fit calibrators on a train split; evaluate on internal val split.

        Parameters
        ----------
        y_true   : binary labels (0/1) — calibration set ONLY, NOT external validation
        y_score  : raw probabilities from source model
        val_fraction : fraction of provided data used as internal calibration-holdout

        Returns
        -------
        dict with fitting report
        """
        y_true = np.asarray(y_true, dtype=float)
        y_score = np.asarray(y_score, dtype=float)

        n = len(y_true)
        n_pos = int(y_true.sum())
        self._n_train = n
        self._n_pos = n_pos

        if n < MIN_CALIBRATION_SAMPLES:
            logger.warning(
                "M18: INSUFFICIENT_EVIDENCE — only %d samples (need ≥ %d)",
                n,
                MIN_CALIBRATION_SAMPLES,
            )
            self._best_method = "insufficient_evidence"
            return {"status": "INSUFFICIENT_EVIDENCE", "n_samples": n}

        if n_pos < MINIMUM_POSITIVE_SAMPLES:
            logger.warning(
                "M18: INSUFFICIENT_EVIDENCE — only %d positive samples (need ≥ %d)",
                n_pos,
                MINIMUM_POSITIVE_SAMPLES,
            )
            self._best_method = "insufficient_evidence"
            return {"status": "INSUFFICIENT_EVIDENCE", "n_pos": n_pos}

        # Stratified split
        from sklearn.model_selection import train_test_split

        idx_pos = np.where(y_true == 1)[0]
        idx_neg = np.where(y_true == 0)[0]

        rng = np.random.default_rng(42)

        def _split(idx: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
            n_val = max(1, int(len(idx) * val_fraction))
            val_idx = rng.choice(idx, n_val, replace=False)
            train_idx = np.setdiff1d(idx, val_idx)
            return train_idx, val_idx

        tr_pos, va_pos = _split(idx_pos)
        tr_neg, va_neg = _split(idx_neg)
        tr_idx = np.concatenate([tr_pos, tr_neg])
        va_idx = np.concatenate([va_pos, va_neg])

        y_tr, s_tr = y_true[tr_idx], y_score[tr_idx]
        y_va, s_va = y_true[va_idx], y_score[va_idx]

        # Fit both calibrators on train
        self.platt.fit(y_tr, s_tr)
        self.isotonic.fit(y_tr, s_tr)

        # Evaluate on val
        p_platt = self.platt.predict_proba(s_va)
        p_iso = self.isotonic.predict_proba(s_va)

        self._platt_brier = _brier_score(y_va, p_platt)
        self._iso_brier = _brier_score(y_va, p_iso)
        uncal_brier = _brier_score(y_va, s_va)

        # Pick best
        if self._platt_brier <= self._iso_brier:
            self._best_method = "platt_scaling"
        else:
            self._best_method = "isotonic_regression"

        self._fitted = True

        logger.info(
            "M18 fit: platt_brier=%.4f  iso_brier=%.4f  uncal_brier=%.4f  best=%s",
            self._platt_brier,
            self._iso_brier,
            uncal_brier,
            self._best_method,
        )

        return {
            "status": "OK",
            "n_train": len(y_tr),
            "n_val": len(y_va),
            "platt_brier": self._platt_brier,
            "iso_brier": self._iso_brier,
            "uncalibrated_brier": uncal_brier,
            "best_method": self._best_method,
        }

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def calibrate(self, raw_probability: float) -> Tuple[float, str]:
        """
        Return (calibrated_probability, method_used).

        If model is not fitted or has insufficient evidence, passes through
        the raw probability with method = 'uncalibrated'.
        """
        if not self._fitted or self._best_method == "insufficient_evidence":
            return float(np.clip(raw_probability, 0.0, 1.0)), "uncalibrated"

        s = np.array([raw_probability], dtype=float)
        if self._best_method == "platt_scaling":
            cal = float(self.platt.predict_proba(s)[0])
        else:
            cal = float(self.isotonic.predict_proba(s)[0])

        return float(np.clip(cal, 0.0, 1.0)), self._best_method

    # ------------------------------------------------------------------
    # Evaluation helpers
    # ------------------------------------------------------------------

    def evaluate(
        self, y_true: np.ndarray, y_score_raw: np.ndarray
    ) -> Dict[str, Any]:
        """Full evaluation report on an external holdout (for reporting only)."""
        y_true = np.asarray(y_true, dtype=float)
        y_score_raw = np.asarray(y_score_raw, dtype=float)

        if not self._fitted:
            return {"status": "INSUFFICIENT_EVIDENCE"}

        cal_probs = np.array(
            [self.calibrate(p)[0] for p in y_score_raw], dtype=float
        )
        slope, intercept = _calibration_slope_intercept(y_true, cal_probs)

        report = {
            "n_eval": len(y_true),
            "brier_uncalibrated": _brier_score(y_true, y_score_raw),
            "brier_calibrated": _brier_score(y_true, cal_probs),
            "ece_uncalibrated": _expected_calibration_error(y_true, y_score_raw),
            "ece_calibrated": _expected_calibration_error(y_true, cal_probs),
            "calibration_slope": slope,
            "calibration_intercept": intercept,
            "method": self._best_method,
        }

        try:
            from sklearn.metrics import roc_auc_score, average_precision_score

            if len(np.unique(y_true)) == 2:
                report["roc_auc"] = float(roc_auc_score(y_true, cal_probs))
                report["pr_auc"] = float(average_precision_score(y_true, cal_probs))
        except Exception:
            pass

        return report
