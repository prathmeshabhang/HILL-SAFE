"""
class_balance.py — Class Balance & Single-Class Audit Layer
============================================================
Audits label distribution and enforces strict metric eligibility.
Detects single-class datasets (e.g. M6 landslide-only inventory) and
blocks calculation of discrimination metrics (ROC-AUC, PR-AUC).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from ml.validation.audit.schema import ClassBalanceAudit, MetricResult, MetricStatus, ValidationUnit


def audit_class_balance(y: np.ndarray, target_name: str = "target") -> ClassBalanceAudit:
    """
    Audits the binary class balance of an evaluation ground-truth vector.
    Enforces strict detection of single-class datasets.
    """
    total = len(y)
    if total == 0:
        return ClassBalanceAudit(
            total_count=0,
            positive_count=0,
            negative_count=0,
            class_prevalence=0.0,
            is_single_class=True,
            single_class_label=None,
        )

    unique_vals = np.unique(y)
    pos_count = int(np.sum(y == 1))
    neg_count = int(np.sum(y == 0))
    prevalence = float(pos_count / total)

    is_single = len(unique_vals) < 2
    single_label = int(unique_vals[0]) if is_single else None

    return ClassBalanceAudit(
        total_count=total,
        positive_count=pos_count,
        negative_count=neg_count,
        class_prevalence=round(prevalence, 4),
        is_single_class=is_single,
        single_class_label=single_label,
    )


def check_discrimination_metric_eligibility(
    class_audit: ClassBalanceAudit,
    metric_name: str = "roc_auc",
    unit: ValidationUnit = ValidationUnit.POINT,
) -> Optional[MetricResult]:
    """
    Verifies whether discrimination metrics (ROC-AUC, PR-AUC) can be estimated.
    If single-class, returns a structured NOT_ESTIMABLE MetricResult.
    If eligible, returns None (allowing calculation to proceed).
    """
    if class_audit.is_single_class:
        label_desc = "positives (failures/floods) only" if class_audit.single_class_label == 1 else "negatives only"
        return MetricResult(
            metric_name=metric_name,
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason=f"not_estimable_due_to_single_class: external dataset contains {label_desc} (N={class_audit.total_count}). "
                   f"Discrimination metrics require both positive and negative observation controls.",
            n=class_audit.total_count,
            unit=unit,
            is_threshold_dependent=False,
        )

    if class_audit.positive_count < 2 or class_audit.negative_count < 2:
        return MetricResult(
            metric_name=metric_name,
            value=None,
            status=MetricStatus.INSUFFICIENT_SAMPLE,
            reason=f"insufficient_class_samples: dataset has {class_audit.positive_count} positive and "
                   f"{class_audit.negative_count} negative samples, which is statistically insufficient for ranking.",
            n=class_audit.total_count,
            unit=unit,
            is_threshold_dependent=False,
        )

    return None
