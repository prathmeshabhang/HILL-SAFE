"""
metrics.py — Audited Metric Evaluation with Uncertainty & Threshold Disaggregation
===================================================================================
Computes threshold-independent and threshold-dependent metrics with:
  - Mandatory threshold recording and source provenance
  - Exact Clopper-Pearson binomial confidence intervals for binary proportions
  - Guarded bootstrap confidence intervals for ranking/calibration metrics
  - Rejection of single-class or inadequate samples
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

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

from ml.validation.audit.class_balance import ClassBalanceAudit, check_discrimination_metric_eligibility
from ml.validation.audit.confidence_intervals import (
    bootstrap_metric_ci,
    exact_binomial_ci,
    wilson_score_ci,
)
from ml.validation.audit.schema import (
    MetricResult,
    MetricStatus,
    ValidationUnit,
)


def evaluate_audited_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    class_audit: ClassBalanceAudit,
    threshold: float = 0.50,
    threshold_source: str = "Predefined model operating threshold (locked before external evaluation)",
    is_threshold_optimized_on_test: bool = False,
    unit: ValidationUnit = ValidationUnit.POINT,
    cluster_ids: Optional[List[str]] = None,
) -> Dict[str, MetricResult]:
    """
    Evaluates comprehensive threshold-independent and threshold-dependent metrics
    with full statistical uncertainty and eligibility auditing.
    """
    results: Dict[str, MetricResult] = {}
    n = len(y_true)

    # -------------------------------------------------------------
    # 1. Threshold-Independent Metrics
    # -------------------------------------------------------------
    # ROC-AUC
    roc_check = check_discrimination_metric_eligibility(class_audit, metric_name="roc_auc", unit=unit)
    if roc_check is not None:
        results["roc_auc"] = roc_check
    else:
        try:
            val = float(roc_auc_score(y_true, y_prob))
            ci = bootstrap_metric_ci(
                y_true, y_prob,
                metric_fn=lambda yt, yp: float(roc_auc_score(yt, yp)),
                cluster_ids=cluster_ids,
                unit=unit,
            )
            results["roc_auc"] = MetricResult(
                metric_name="roc_auc",
                value=val,
                status=MetricStatus.VALID,
                n=n,
                unit=unit,
                is_threshold_dependent=False,
                confidence_interval=ci,
            )
        except Exception as e:
            results["roc_auc"] = MetricResult(
                metric_name="roc_auc",
                value=None,
                status=MetricStatus.NOT_ESTIMABLE,
                reason=f"Calculation error: {str(e)}",
                n=n,
                unit=unit,
                is_threshold_dependent=False,
            )

    # PR-AUC
    pr_check = check_discrimination_metric_eligibility(class_audit, metric_name="pr_auc", unit=unit)
    if pr_check is not None:
        results["pr_auc"] = pr_check
    else:
        try:
            prec_arr, rec_arr, _ = precision_recall_curve(y_true, y_prob)
            val = float(auc(rec_arr, prec_arr))
            ci = bootstrap_metric_ci(
                y_true, y_prob,
                metric_fn=lambda yt, yp: float(auc(*precision_recall_curve(yt, yp)[:2][::-1])),
                cluster_ids=cluster_ids,
                unit=unit,
            )
            results["pr_auc"] = MetricResult(
                metric_name="pr_auc",
                value=val,
                status=MetricStatus.VALID,
                n=n,
                unit=unit,
                is_threshold_dependent=False,
                confidence_interval=ci,
            )
        except Exception as e:
            results["pr_auc"] = MetricResult(
                metric_name="pr_auc",
                value=None,
                status=MetricStatus.NOT_ESTIMABLE,
                reason=f"Calculation error: {str(e)}",
                n=n,
                unit=unit,
                is_threshold_dependent=False,
            )

    # Brier Score Loss
    try:
        brier_val = float(brier_score_loss(y_true, y_prob))
        brier_ci = bootstrap_metric_ci(
            y_true, y_prob,
            metric_fn=lambda yt, yp: float(brier_score_loss(yt, yp)),
            cluster_ids=cluster_ids,
            unit=unit,
        )
        results["brier_score"] = MetricResult(
            metric_name="brier_score",
            value=brier_val,
            status=MetricStatus.VALID,
            n=n,
            unit=unit,
            is_threshold_dependent=False,
            confidence_interval=brier_ci,
        )
    except Exception as e:
        results["brier_score"] = MetricResult(
            metric_name="brier_score",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason=f"Calculation error: {str(e)}",
            n=n,
            unit=unit,
            is_threshold_dependent=False,
        )

    # -------------------------------------------------------------
    # 2. Threshold-Dependent Metrics
    # -------------------------------------------------------------
    thresh_source_annotated = (
        f"{threshold_source} [FLAG: TEST_SET_OPTIMIZED]"
        if is_threshold_optimized_on_test
        else threshold_source
    )

    y_pred = (y_prob >= threshold).astype(int)

    # Contingency table
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    # Recall / Sensitivity (TP / (TP + FN))
    positives = class_audit.positive_count
    if positives > 0:
        rec_val = float(tp / positives)
        rec_ci = exact_binomial_ci(tp, positives, unit=unit)
        results["recall"] = MetricResult(
            metric_name="recall",
            value=rec_val,
            status=MetricStatus.VALID,
            n=positives,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
            confidence_interval=rec_ci,
        )
    else:
        results["recall"] = MetricResult(
            metric_name="recall",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason="not_estimable_due_to_zero_positives",
            n=0,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )

    # Specificity (TN / (TN + FP))
    negatives = class_audit.negative_count
    if negatives > 0:
        spec_val = float(tn / negatives)
        spec_ci = exact_binomial_ci(tn, negatives, unit=unit)
        results["specificity"] = MetricResult(
            metric_name="specificity",
            value=spec_val,
            status=MetricStatus.VALID,
            n=negatives,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
            confidence_interval=spec_ci,
        )
    else:
        results["specificity"] = MetricResult(
            metric_name="specificity",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason="not_estimable_due_to_zero_negative_controls: dataset contains no negative controls to evaluate true negatives.",
            n=0,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )

    # Precision (TP / (TP + FP))
    predicted_positives = tp + fp
    if predicted_positives > 0 and negatives > 0:
        prec_val = float(tp / predicted_positives)
        prec_ci = exact_binomial_ci(tp, predicted_positives, unit=unit)
        results["precision"] = MetricResult(
            metric_name="precision",
            value=prec_val,
            status=MetricStatus.VALID,
            n=predicted_positives,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
            confidence_interval=prec_ci,
        )
    elif negatives == 0:
        # If no negatives exist, precision is trivially 1.0 or non-informative
        results["precision"] = MetricResult(
            metric_name="precision",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason="not_estimable_due_to_zero_negative_controls: false positives cannot occur when dataset contains only positive cases.",
            n=predicted_positives,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )
    else:
        results["precision"] = MetricResult(
            metric_name="precision",
            value=0.0,
            status=MetricStatus.VALID,
            reason="zero_positive_predictions: model made zero positive predictions at chosen threshold.",
            n=0,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )

    # F1-Score
    if (
        results.get("precision")
        and results["precision"].value is not None
        and results.get("recall")
        and results["recall"].value is not None
    ):
        p = results["precision"].value
        r = results["recall"].value
        f1_val = float(2 * (p * r) / (p + r)) if (p + r) > 0 else 0.0
        results["f1_score"] = MetricResult(
            metric_name="f1_score",
            value=f1_val,
            status=MetricStatus.VALID,
            n=n,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )
    else:
        results["f1_score"] = MetricResult(
            metric_name="f1_score",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason="not_estimable_due_to_unestimable_precision_or_recall",
            n=n,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )

    # Accuracy ((TP + TN) / N)
    if negatives > 0:
        acc_val = float((tp + tn) / n)
        acc_ci = exact_binomial_ci(tp + tn, n, unit=unit)
        results["accuracy"] = MetricResult(
            metric_name="accuracy",
            value=acc_val,
            status=MetricStatus.VALID,
            n=n,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
            confidence_interval=acc_ci,
        )
    else:
        results["accuracy"] = MetricResult(
            metric_name="accuracy",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason="not_estimable_due_to_zero_negative_controls: accuracy on single-class data merely mirrors recall.",
            n=n,
            unit=unit,
            threshold=threshold,
            is_threshold_dependent=True,
            threshold_source=thresh_source_annotated,
        )

    return results
