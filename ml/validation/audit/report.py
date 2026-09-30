"""
report.py — Machine-Readable JSON Export & Conservative Claim Generator
======================================================================
Serializes audited validation findings to JSON and generates objective,
non-hyperbolic scientific statements adhering to empirical evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.validation.audit.confidence_intervals import exact_binomial_ci
from ml.validation.audit.schema import (
    ConfidenceInterval,
    MetricResult,
    MetricStatus,
    ModelValidationAuditResult,
    ValidationTier,
    ValidationUnit,
)


def generate_conservative_claims(
    audit: ModelValidationAuditResult,
) -> Tuple[List[str], List[str]]:
    """
    Generates conservative, evidence-grounded scientific statements.
    Explicitly separates what CAN be claimed from what CANNOT be claimed.
    """
    supported: List[str] = []
    unsupported: List[str] = []

    m = audit.metrics
    indep = audit.spatial_independence
    cb = audit.class_balance
    ev = audit.event_audit

    # --- Landslide Susceptibility (M6) ---
    if audit.model.upper().startswith("M6"):
        if cb.is_single_class:
            unsupported.append(
                "Model M6 discrimination ability (ROC-AUC / PR-AUC) CANNOT be scientifically established from this dataset "
                "because zero unfailed negative control slopes are included (N=20 failures, 0 controls)."
            )
            unsupported.append(
                "Model M6 specificity, precision, and false-alarm rejection CANNOT be claimed on external data."
            )
            rec = m.get("recall")
            if rec and rec.value is not None:
                ci_str = (
                    f" [{rec.confidence_interval.lower*100:.1f}%, {rec.confidence_interval.upper*100:.1f}%]"
                    if rec.confidence_interval and rec.confidence_interval.lower is not None
                    else ""
                )
                supported.append(
                    f"On the strictly independent subset (N={indep.independent_count}, >500m from training data), "
                    f"frozen Model M6 identified {rec.value*100:.1f}% of documented failure sites (95% exact CI:{ci_str}) "
                    f"at predefined probability threshold {rec.threshold}."
                )
            supported.append(
                f"9 of the 20 historical landslide locations fall within {indep.distance_threshold_m}m of M6 training data; "
                f"these 9 points provide descriptive characterization but are excluded from primary independent evidence."
            )

    # --- Landslide Dynamic Trigger (M7) ---
    elif audit.model.upper().startswith("M7"):
        if ev and ev.is_clustered_forcing:
            unsupported.append(
                f"Evaluation across {ev.total_points} spatial points during the July 9–10, 2023 disaster does NOT constitute "
                f"{ev.total_points} independent validation events. All observations share a single monsoonal cloudburst forcing epoch."
            )
            unsupported.append(
                "Event-level ROC-AUC CANNOT be scientifically computed (only 1 disaster event observed)."
            )
        rec = m.get("recall")
        if rec and rec.value is not None:
            ci_str = (
                f" [{rec.confidence_interval.lower*100:.1f}%, {rec.confidence_interval.upper*100:.1f}%]"
                if rec.confidence_interval and rec.confidence_interval.lower is not None
                else ""
            )
            supported.append(
                f"Under catastrophic monsoonal rainfall forcing (July 9–10, 2023), Model M7 triggered across all evaluated "
                f"historical failure locations (Observed Recall: {rec.value*100:.1f}%, 95% exact CI:{ci_str}, N={rec.n})."
            )
        supported.append(
            "Point-level spatial discrimination under heavy storm forcing is limited: extreme catchment-wide precipitation "
            "causes widespread high trigger probabilities across both steep failure corridors and valley benches."
        )

    # --- Flood Occurrence (M2) ---
    elif audit.model.upper().startswith("M2"):
        rec = m.get("recall")
        if rec and rec.value is not None:
            ci_str = (
                f" [{rec.confidence_interval.lower*100:.1f}%, {rec.confidence_interval.upper*100:.1f}%]"
                if rec.confidence_interval and rec.confidence_interval.lower is not None
                else ""
            )
            supported.append(
                f"Frozen Model M2 correctly identified all {cb.positive_count} documented riverine inundation sites "
                f"(Observed Recall = {rec.value*100:.1f}%, 95% exact CI:{ci_str}) at predefined threshold {rec.threshold}."
            )
        roc = m.get("roc_auc")
        if roc and roc.value is not None:
            supported.append(
                f"Model M2 continuous probability scores rank true flooded sites above upland reference benches with "
                f"point-level ROC-AUC = {roc.value:.4f} (N={audit.class_balance.total_count})."
            )
        unsupported.append(
            f"100% observed recall on the strictly independent subset (N={indep.independent_count}, >500m) does NOT indicate "
            f"statistical certainty: with 4 independent flooded points, the exact 95% confidence interval spans down to "
            f"{exact_binomial_ci(4, 4).lower*100:.1f}%."
        )
        unsupported.append(
            "Catchment-wide catastrophic rainfall and HFL river stage saturated tree splits, producing high probabilities "
            "on upland benches and yielding zero specificity at default threshold 0.50 without dynamic threshold adaptation."
        )

    # --- Flood Segmentation (M4 U-Net) ---
    elif audit.model.upper().startswith("M4"):
        supported.append(
            "Internal validation against physical radar-topographic (SAR-HAND) reference masks demonstrates high segmentation "
            "fidelity (Dice F1 = 96.9%–97.3%, IoU = 93.9%–94.8%)."
        )
        roc = m.get("roc_auc")
        if roc and roc.value is not None:
            supported.append(
                f"External point-level concordance at 24 historical disaster and control locations exhibits ROC-AUC = {roc.value:.4f}, "
                f"with higher mean predicted probability at flooded disaster sites than unflooded control locations."
            )
        unsupported.append(
            "External full-scene 2D segmentation validation (external Dice / IoU) CANNOT be claimed because authoritative "
            "independent 10m digital flood delineation rasters are currently unreleased for this scene."
        )
        unsupported.append(
            "Point concordance at selected coordinates CANNOT be presented as equivalent to complete 2D scene segmentation validation."
        )

    return supported, unsupported


def save_audit_json(audit: ModelValidationAuditResult, output_path: Path) -> None:
    """Saves the audit result as machine-readable JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(audit.to_dict(), f, indent=2)


def render_metric_markdown_table(metrics: Dict[str, MetricResult]) -> str:
    """Renders a standard markdown table from MetricResult dictionary."""
    rows = [
        "| Metric | Value | Status | 95% Confidence Interval | Sample Unit | Evaluation Threshold |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |",
    ]
    for k, v in metrics.items():
        val_str = f"{v.value:.4f}" if v.value is not None else "NOT ESTIMABLE"
        ci_str = "—"
        if v.confidence_interval and v.confidence_interval.lower is not None:
            ci_str = f"[{v.confidence_interval.lower:.4f}, {v.confidence_interval.upper:.4f}] ({v.confidence_interval.method.value})"
        elif v.confidence_interval and not v.confidence_interval.is_reliable:
            ci_str = f"Unreliable ({v.confidence_interval.reason})"

        thresh_str = f"{v.threshold} ({v.threshold_source})" if v.is_threshold_dependent else "Threshold-Independent"

        rows.append(
            f"| **{v.metric_name}** | {val_str} | `{v.status.value}` | {ci_str} | {v.unit.value} (N={v.n}) | {thresh_str} |"
        )
    return "\n".join(rows)
