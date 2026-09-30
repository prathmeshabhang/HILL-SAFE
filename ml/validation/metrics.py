"""
metrics.py — Statistical & Machine Learning Validation Metrics
===============================================================
Computes rigorous classification, probability calibration, and discrimination
metrics for binary and multi-class disaster risk models:
  - Accuracy, Precision, Recall, Specificity
  - F1-Score, F1-Macro
  - ROC-AUC (Receiver Operating Characteristic)
  - PR-AUC (Precision-Recall Area Under Curve - vital for imbalanced disasters)
  - Brier Score Loss (Mean squared probability error)
  - Confusion Matrix (TP, FP, TN, FN)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    auc,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class BinaryClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    specificity: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    brier_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    false_alarm_rate: float
    miss_rate: float


@dataclass
class MulticlassClassificationMetrics:
    accuracy: float
    f1_macro: float
    f1_weighted: float
    precision_macro: float
    recall_macro: float
    class_wise_f1: Dict[int, float]
    confusion_matrix: list[list[int]]


def evaluate_binary_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.50,
) -> BinaryClassificationMetrics:
    """Computes full evaluation suite for binary risk probabilities."""
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=np.float32)
    y_pred = (y_prob >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        roc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc = 0.0

    p_curve, r_curve, _ = precision_recall_curve(y_true, y_prob)
    pr_auc_val = float(auc(r_curve, p_curve))
    brier = float(brier_score_loss(y_true, y_prob))

    far = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    miss = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    return BinaryClassificationMetrics(
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        specificity=round(spec, 4),
        f1_score=round(f1, 4),
        roc_auc=round(roc, 4),
        pr_auc=round(pr_auc_val, 4),
        brier_score=round(brier, 4),
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        false_alarm_rate=round(far, 4),
        miss_rate=round(miss, 4),
    )


def evaluate_multiclass_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: list[int] = [0, 1, 2],
) -> MulticlassClassificationMetrics:
    """Computes evaluation metrics for multiclass susceptibility predictions."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    acc = float(accuracy_score(y_true, y_pred))
    f1_m = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_w = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    p_m = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    r_m = float(recall_score(y_true, y_pred, average="macro", zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=classes).tolist()
    class_f1s = f1_score(y_true, y_pred, labels=classes, average=None, zero_division=0)
    class_dict = {int(c): round(float(f), 4) for c, f in zip(classes, class_f1s)}

    return MulticlassClassificationMetrics(
        accuracy=round(acc, 4),
        f1_macro=round(f1_m, 4),
        f1_weighted=round(f1_w, 4),
        precision_macro=round(p_m, 4),
        recall_macro=round(r_m, 4),
        class_wise_f1=class_dict,
        confusion_matrix=cm,
    )
