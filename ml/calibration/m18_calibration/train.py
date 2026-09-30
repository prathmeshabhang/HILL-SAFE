"""M18 — Training pipeline.

Trains Platt and isotonic calibrators on synthetic labelled probability
samples that reflect realistic source-model score distributions for the
Upper Beas hazard corridor.

DATA PROVENANCE
---------------
Training data is SYNTHETIC — generated from known score/label distributions.
This is used only for unit tests and pipeline validation.
Do NOT use these calibrators as externally validated evidence.
All synthetic records are labelled: SYNTHETIC — PIPELINE TEST ONLY
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from .model import M18CalibrationModel

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).parent
ARTIFACT_PATH = ARTIFACT_DIR / "m18_calibration.pkl"


def _generate_synthetic_dataset(
    n_pos: int = 300,
    n_neg: int = 700,
    rng_seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    SYNTHETIC — PIPELINE TEST ONLY.

    Generate synthetic (raw_probability, label) pairs mimicking a biased but
    imperfect model.  Positive class scores are beta(5,2)-distributed (high);
    negative class scores are beta(2,5)-distributed (low).
    """
    rng = np.random.default_rng(rng_seed)
    s_pos = rng.beta(5, 2, n_pos)
    s_neg = rng.beta(2, 5, n_neg)
    y_score = np.concatenate([s_pos, s_neg])
    y_true = np.concatenate([np.ones(n_pos), np.zeros(n_neg)])
    # Shuffle
    idx = rng.permutation(len(y_true))
    return y_true[idx], y_score[idx]


def train(
    y_true: np.ndarray | None = None,
    y_score: np.ndarray | None = None,
    save: bool = True,
) -> Dict[str, Any]:
    """
    Fit M18 calibrators.

    If y_true/y_score are not provided, use SYNTHETIC data (pipeline test).
    """
    if y_true is None or y_score is None:
        logger.warning(
            "M18 train: No real calibration data supplied. "
            "Using SYNTHETIC dataset — PIPELINE TEST ONLY."
        )
        y_true, y_score = _generate_synthetic_dataset()

    model = M18CalibrationModel()
    report = model.fit(y_true, y_score)

    if save and report.get("status") != "INSUFFICIENT_EVIDENCE":
        with open(ARTIFACT_PATH, "wb") as f:
            pickle.dump(model, f)

        sha256 = hashlib.sha256(ARTIFACT_PATH.read_bytes()).hexdigest()
        logger.info("M18 artifact saved: %s  sha256=%s", ARTIFACT_PATH, sha256)
        report["artifact_path"] = str(ARTIFACT_PATH)
        report["sha256"] = sha256

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = train()
    print(json.dumps(result, indent=2))
