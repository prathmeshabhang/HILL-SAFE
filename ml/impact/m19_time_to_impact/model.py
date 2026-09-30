"""M19 — ML quantile regression model (event-level holdout).

This module implements a quantile regression layer for time-to-impact
when event-level labelled timestamps are available.

DATA CONSTRAINT
---------------
At project time, no real event-level time-to-impact observations are
available for the Upper Beas corridor.  This module therefore:

1. Declares `INSUFFICIENT_EVIDENCE` for ML validation.
2. Provides the full ML infrastructure for when real data becomes available.
3. Uses SYNTHETIC scenario data for unit tests only — clearly labelled.

Event-level holdout split
--------------------------
When real event data is available, observations from the SAME event
must NOT be split across train and test sets.  The `fit()` method
enforces GroupShuffleSplit on event_id to prevent leakage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Quantile levels predicted
QUANTILES = [0.10, 0.50, 0.90]

# Minimum number of distinct events required for ML validation
MIN_EVENTS = 10
MIN_SAMPLES = 30


class M19QuantileModel:
    """
    Quantile regression for time-to-impact (minutes).

    Features (7):
        distance_km, wave_speed_kmh, slope_pct, peak_discharge_m3s,
        soil_saturation_ratio, rainfall_mm_1h, debris_depth_m
    """

    MODEL_ID = "M19"
    MODEL_VERSION = "1.0.0"
    FEATURE_NAMES = [
        "distance_km",
        "wave_speed_kmh",
        "slope_pct",
        "peak_discharge_m3s",
        "soil_saturation_ratio",
        "rainfall_mm_1h",
        "debris_depth_m",
    ]

    def __init__(self) -> None:
        self._models: Dict[float, Any] = {}  # quantile → fitted regressor
        self._fitted = False
        self._n_events = 0
        self._n_samples = 0
        self._val_report: Dict[str, Any] = {}

    def fit(
        self,
        X: np.ndarray,
        y_minutes: np.ndarray,
        event_ids: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Fit quantile regressors with event-level holdout.

        Parameters
        ----------
        X          : Feature matrix (n_samples × 7)
        y_minutes  : Target (travel time in minutes)
        event_ids  : Array of event identifiers; used for group-split.
                     If None, regular random split is used (sub-optimal).
        """
        from sklearn.ensemble import GradientBoostingRegressor

        n = len(y_minutes)
        self._n_samples = n

        if n < MIN_SAMPLES:
            logger.warning(
                "M19 ML: INSUFFICIENT_EVIDENCE — only %d samples (need ≥ %d). "
                "Kinematic baseline will be used.",
                n, MIN_SAMPLES,
            )
            return {"status": "INSUFFICIENT_EVIDENCE", "n_samples": n}

        # Event-level holdout
        if event_ids is not None:
            unique_events = np.unique(event_ids)
            self._n_events = len(unique_events)
            if self._n_events < MIN_EVENTS:
                logger.warning(
                    "M19 ML: INSUFFICIENT_EVIDENCE — only %d distinct events "
                    "(need ≥ %d) — using kinematic baseline.",
                    self._n_events, MIN_EVENTS,
                )
                return {
                    "status": "INSUFFICIENT_EVIDENCE",
                    "n_events": self._n_events,
                }

            # Hold out 20% of events
            rng = np.random.default_rng(42)
            n_val_events = max(1, int(len(unique_events) * 0.2))
            val_events = rng.choice(unique_events, n_val_events, replace=False)
            val_mask = np.isin(event_ids, val_events)
            tr_mask = ~val_mask
        else:
            from sklearn.model_selection import train_test_split
            idx = np.arange(n)
            tr_idx, va_idx = train_test_split(idx, test_size=0.2, random_state=42)
            tr_mask = np.zeros(n, dtype=bool)
            val_mask = np.zeros(n, dtype=bool)
            tr_mask[tr_idx] = True
            val_mask[va_idx] = True

        X_tr, y_tr = X[tr_mask], y_minutes[tr_mask]
        X_va, y_va = X[val_mask], y_minutes[val_mask]

        for q in QUANTILES:
            reg = GradientBoostingRegressor(
                loss="quantile",
                alpha=q,
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=42,
            )
            reg.fit(X_tr, y_tr)
            self._models[q] = reg

        self._fitted = True

        # Validation on holdout
        p50_pred = self._models[0.50].predict(X_va)
        mae = float(np.mean(np.abs(p50_pred - y_va)))
        self._val_report = {
            "status": "ML_VALIDATED",
            "n_train": int(tr_mask.sum()),
            "n_val": int(val_mask.sum()),
            "p50_mae_minutes": round(mae, 2),
            "holdout_type": "event_level" if event_ids is not None else "random",
        }
        logger.info("M19 ML fit: %s", self._val_report)
        return self._val_report

    def predict(self, x: np.ndarray) -> Tuple[float, float, float]:
        """Return (p10, p50, p90) in minutes for a single feature vector."""
        if not self._fitted:
            raise RuntimeError("M19QuantileModel not fitted.")
        p10 = float(max(1.0, self._models[0.10].predict(x.reshape(1, -1))[0]))
        p50 = float(max(1.0, self._models[0.50].predict(x.reshape(1, -1))[0]))
        p90 = float(max(1.0, self._models[0.90].predict(x.reshape(1, -1))[0]))
        return p10, p50, p90
