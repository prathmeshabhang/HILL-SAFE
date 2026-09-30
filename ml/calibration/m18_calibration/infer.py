"""M18 — Inference (calibrate a raw probability)."""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from .model import M18CalibrationModel
from .schema import (
    CalibrationMethod,
    CalibrationStatus,
    M18CalibrationInput,
    M18CalibrationOutput,
)
from .train import ARTIFACT_PATH, train

logger = logging.getLogger(__name__)

_MODEL_CACHE: Optional[M18CalibrationModel] = None


def _load_model() -> M18CalibrationModel:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if ARTIFACT_PATH.exists():
        with open(ARTIFACT_PATH, "rb") as f:
            _MODEL_CACHE = pickle.load(f)
        logger.info("M18: loaded calibration model from %s", ARTIFACT_PATH)
    else:
        logger.warning("M18: no artifact found — training on synthetic data now.")
        train(save=True)
        if ARTIFACT_PATH.exists():
            with open(ARTIFACT_PATH, "rb") as f:
                _MODEL_CACHE = pickle.load(f)
        else:
            _MODEL_CACHE = M18CalibrationModel()

    return _MODEL_CACHE


def calibrate(inp: M18CalibrationInput) -> M18CalibrationOutput:
    """
    Calibrate a raw probability from a source hazard model.

    Returns full M18CalibrationOutput including calibration method and status.
    """
    raw = float(np.clip(inp.raw_probability, 0.0, 1.0))

    # Data-quality gate
    if inp.data_quality < 0.3:
        return M18CalibrationOutput(
            model="M18_RISK_CALIBRATION",
            source_model=inp.source_model,
            raw_probability=raw,
            calibrated_probability=raw,
            calibration_method=CalibrationMethod.UNCALIBRATED,
            confidence=0.2,
            data_quality=inp.data_quality,
            status=CalibrationStatus.DEGRADED_INPUT,
            notes="Data quality below threshold — passthrough only.",
        )

    model = _load_model()

    if not model._fitted or model._best_method == "insufficient_evidence":
        return M18CalibrationOutput(
            model="M18_RISK_CALIBRATION",
            source_model=inp.source_model,
            raw_probability=raw,
            calibrated_probability=raw,
            calibration_method=CalibrationMethod.INSUFFICIENT_EVIDENCE,
            confidence=0.3,
            data_quality=inp.data_quality,
            status=CalibrationStatus.INSUFFICIENT_EVIDENCE,
            notes="Calibration model not fitted — INSUFFICIENT_EVIDENCE.",
        )

    cal_prob, method = model.calibrate(raw)

    # Confidence: degrades with distance from calibration interior
    confidence = float(np.clip(1.0 - abs(raw - 0.5) * 0.4, 0.6, 1.0))
    if inp.data_quality < 0.7:
        confidence *= inp.data_quality

    return M18CalibrationOutput(
        model="M18_RISK_CALIBRATION",
        source_model=inp.source_model,
        raw_probability=raw,
        calibrated_probability=cal_prob,
        calibration_method=method,
        confidence=round(confidence, 4),
        data_quality=inp.data_quality,
        status=CalibrationStatus.CALIBRATED,
        metrics={
            "platt_brier": model._platt_brier,
            "iso_brier": model._iso_brier,
        },
    )
