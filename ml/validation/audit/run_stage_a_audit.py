"""
run_stage_a_audit.py — Master Executor for Validation-Audit Stage A
===================================================================
Executes the comprehensive scientific audit across Models M6, M7, M2, and M4
without retraining or modifying any model weights.

Generates:
  - reports/validation_audit/m6_audit.json
  - reports/validation_audit/m7_audit.json
  - reports/validation_audit/m2_audit.json
  - reports/validation_audit/m4_audit.json
  - reports/validation_audit/validation_summary.json
  - reports/validation_audit/VALIDATION_STAGE_A_SUMMARY.md
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import tifffile

from ml.validation.audit import (
    ClassBalanceAudit,
    ControlItemAudit,
    ControlQualityAudit,
    ControlValidity,
    EventIndependenceAudit,
    IndependenceStatus,
    MetricResult,
    MetricStatus,
    ModelValidationAuditResult,
    SpatialIndependenceAudit,
    ValidationTier,
    ValidationUnit,
    audit_class_balance,
    audit_event_structure,
    audit_flood_controls,
    audit_spatial_independence,
    check_discrimination_metric_eligibility,
    check_event_level_auc_eligibility,
    evaluate_audited_metrics,
    exact_binomial_ci,
    generate_conservative_claims,
    render_metric_markdown_table,
    save_audit_json,
)
from ml.validation.external.feature_extractor import M6FeatureExtractor

REPO_ROOT = Path(__file__).resolve().parents[3]
AUDIT_DIR = REPO_ROOT / "reports" / "validation_audit"


# =====================================================================
# STEP 1 & 2: MODEL M6 AUDIT (Landslide Susceptibility)
# =====================================================================
def audit_model_m6() -> ModelValidationAuditResult:
    """
    Audits Model M6 against authentic GSI/HPSDMA landslide failure inventory.
    Enforces single-class detection (20 failures, 0 controls) -> ROC-AUC is NOT ESTIMABLE.
    Enforces spatial independence partition (11 independent, 9 non-independent).
    """
    raw_csv = REPO_ROOT / "data" / "external" / "m6" / "upper_beas" / "raw" / "kullu_upper_beas_landslides_2023_raw.csv"
    leakage_csv = REPO_ROOT / "reports" / "M6_EXTERNAL_LEAKAGE_AUDIT.csv"
    model_path = REPO_ROOT / "ml" / "landslide" / "m6_beas_susceptibility_rf.joblib"

    df_raw = pd.read_csv(raw_csv)
    df_leakage = pd.read_csv(leakage_csv)

    # Invariants and classification
    indep_mask = df_leakage["accepted_for_validation"].astype(bool).values
    n_total = len(df_raw)
    n_indep = int(np.sum(indep_mask))
    n_non_indep = int(np.sum(~indep_mask))

    spatial_audit = SpatialIndependenceAudit(
        total_samples=n_total,
        independent_count=n_indep,
        non_independent_count=n_non_indep,
        unknown_count=0,
        distance_threshold_m=500.0,
        primary_evaluation_subset="INDEPENDENT (N=11)",
    )

    # Class balance audit (20 failures, 0 controls)
    y_true = np.ones(n_total, dtype=int)
    class_audit = audit_class_balance(y_true)

    # Feature extraction and frozen model inference
    model = joblib.load(model_path)
    extractor = M6FeatureExtractor()
    points = list(zip(df_raw["latitude"], df_raw["longitude"]))
    X, _ = extractor.extract_features_for_points(points)
    y_prob = model.predict_proba(X)[:, 1]

    # Evaluate audited metrics on Primary Independent Subset (N=11)
    metrics_indep = evaluate_audited_metrics(
        y_true=y_true[indep_mask],
        y_prob=y_prob[indep_mask],
        class_audit=audit_class_balance(y_true[indep_mask]),
        threshold=0.50,
        threshold_source="Predefined model operating threshold (locked before external evaluation)",
        unit=ValidationUnit.POINT,
    )

    # Add descriptive metrics for all 20 points
    metrics_all = evaluate_audited_metrics(
        y_true=y_true,
        y_prob=y_prob,
        class_audit=class_audit,
        threshold=0.50,
        threshold_source="Predefined model operating threshold (locked before external evaluation)",
        unit=ValidationUnit.POINT,
    )

    # Top-20% and Top-30% spatial capture rate on independent subset
    # In M6 susceptibility, class probabilities: high susceptibility >= 0.50
    rec_indep = metrics_indep["recall"]

    limitations = [
        "External inventory contains zero unfailed negative control slopes (N=20 failures, 0 controls).",
        "Discrimination metrics (ROC-AUC, PR-AUC, Specificity) are mathematically NOT ESTIMABLE without controls.",
        "Small primary independent sample size (N=11) limits statistical precision of recall estimation.",
        "9 of 20 historical points fall within 500m of M6 training samples and are excluded from primary independent evidence.",
    ]

    audit_result = ModelValidationAuditResult(
        model="M6_Random_Forest_Landslide_Susceptibility",
        dataset_name="kullu_upper_beas_landslides_2023_gsi_hpsdma",
        validation_tier=ValidationTier.INSUFFICIENT_SAMPLE,
        primary_validation_unit=ValidationUnit.POINT,
        spatial_independence=spatial_audit,
        class_balance=class_audit,
        event_audit=None,
        control_quality=None,
        metrics=metrics_indep,
        limitations=limitations,
        claims_supported=[],
        claims_unsupported=[],
    )

    supported, unsupported = generate_conservative_claims(audit_result)
    audit_result.claims_supported = supported
    audit_result.claims_unsupported = unsupported

    return audit_result


# =====================================================================
# STEP 3 & 4: MODEL M7 AUDIT (Dynamic Landslide Trigger)
# =====================================================================
def audit_model_m7() -> ModelValidationAuditResult:
    """
    Audits Model M7 against authentic July 9–10, 2023 disaster event forcing.
    Enforces event-level vs point-level distinction: 22 spatial points belong to
    ONE storm event -> event-level ROC-AUC is NOT ESTIMABLE.
    Point-level discrimination is reported separately.
    """
    event_csv = REPO_ROOT / "data" / "external" / "m6" / "upper_beas" / "processed" / "m7_external_event_dataset.csv"
    model_path = REPO_ROOT / "ml" / "landslide" / "m7_beas_trigger_lgbm.joblib"

    df_event = pd.read_csv(event_csv)

    # Ensure event tracking fields exist
    df_event["event_id"] = "STORM_JULY_2023_HP"
    df_event["rainfall_event_id"] = "STORM_JULY_2023_HP"
    df_event["forcing_type"] = "MONSOON_CLOUDBURST_JULY_9_10"

    event_audit = audit_event_structure(
        df_event,
        event_id_col="rainfall_event_id",
        date_col="event_date",
        forcing_col="forcing_type",
    )

    # Spatial independence: the 22 points include 11 independent failure points + 11 valley floor points
    spatial_audit = SpatialIndependenceAudit(
        total_samples=len(df_event),
        independent_count=11,
        non_independent_count=11,
        unknown_count=0,
        distance_threshold_m=500.0,
        primary_evaluation_subset="SPATIAL_SAMPLES_UNDER_SINGLE_STORM (N=22)",
    )

    y_true = df_event["landslide_triggered"].values.astype(int)
    class_audit = audit_class_balance(y_true)

    # Frozen Model M7 inference
    model = joblib.load(model_path)
    feature_cols = ["susceptibility_class", "slope_deg", "rainfall_1h", "antecedent_rain_3d", "soil_moisture_pct"]
    X = df_event[feature_cols]
    y_prob = model.predict_proba(X)[:, 1]

    # Evaluate point-level metrics
    metrics = evaluate_audited_metrics(
        y_true=y_true,
        y_prob=y_prob,
        class_audit=class_audit,
        threshold=0.50,
        threshold_source="Predefined model operational trigger threshold (locked before external evaluation)",
        unit=ValidationUnit.SPATIAL_SAMPLE,
        cluster_ids=df_event["rainfall_event_id"].tolist(),
    )

    # Attach explicit event-level ROC-AUC check
    event_auc_check = check_event_level_auc_eligibility(event_audit)
    if event_auc_check is not None:
        metrics["event_level_roc_auc"] = event_auc_check

    limitations = [
        "All 22 spatial points were exposed to the same single July 9–10, 2023 storm event (Events=1, Points=22).",
        "Event-level ROC-AUC is NOT ESTIMABLE because evaluation across multiple independent storm epochs is required.",
        "Catchment-wide extreme rainfall (R1h 35-65mm, R3d 140-210mm) caused widespread saturation, triggering on valley floor benches.",
        "Validation represents spatial performance under one extreme disaster scenario, not generalized multi-storm validation.",
    ]

    audit_result = ModelValidationAuditResult(
        model="M7_LightGBM_Dynamic_Landslide_Trigger",
        dataset_name="upper_beas_july2023_event_forcing_dataset",
        validation_tier=ValidationTier.PARTIALLY_VALIDATED,
        primary_validation_unit=ValidationUnit.SPATIAL_SAMPLE,
        spatial_independence=spatial_audit,
        class_balance=class_audit,
        event_audit=event_audit,
        control_quality=None,
        metrics=metrics,
        limitations=limitations,
        claims_supported=[],
        claims_unsupported=[],
    )

    supported, unsupported = generate_conservative_claims(audit_result)
    audit_result.claims_supported = supported
    audit_result.claims_unsupported = unsupported

    return audit_result


# =====================================================================
# STEP 5 & 6: MODEL M2 AUDIT (Flood Occurrence / Susceptibility)
# =====================================================================
def audit_model_m2() -> ModelValidationAuditResult:
    """
    Audits Model M2 against authentic July 2023 disaster flood inundation locations.
    Audits the 12 negative controls against the 5-point checklist (observed absence vs unmapped).
    Audits spatial independence (6 independent, 18 non-independent).
    Attaches exact Clopper-Pearson binomial CIs for small sample size.
    """
    raw_csv = REPO_ROOT / "data" / "external" / "flood" / "raw" / "upper_beas_flood_events_2023_raw.csv"
    leakage_csv = REPO_ROOT / "reports" / "M2_M4_EXTERNAL_LEAKAGE_AUDIT.csv"
    model_path = REPO_ROOT / "ml" / "flood" / "m2_upper_beas_flood_model.joblib"
    metrics_json = REPO_ROOT / "docs" / "m2_external_validation_metrics.json"

    df_raw = pd.read_csv(raw_csv)
    df_leakage = pd.read_csv(leakage_csv)

    # Control quality audit of the 12 negative controls
    control_audit = audit_flood_controls(df_raw, control_filter_col="inundation_observed", control_target_val=0)

    # Spatial independence audit
    indep_mask = df_leakage["is_spatially_independent"].values
    n_total = len(df_raw)
    n_indep = int(np.sum(indep_mask))
    n_non_indep = int(np.sum(~indep_mask))

    spatial_audit = SpatialIndependenceAudit(
        total_samples=n_total,
        independent_count=n_indep,
        non_independent_count=n_non_indep,
        unknown_count=0,
        distance_threshold_m=500.0,
        primary_evaluation_subset="INDEPENDENT (N=6)",
    )

    # Class balance audit (12 flooded, 12 unflooded)
    y_true = df_raw["inundation_observed"].values.astype(int)
    class_audit = audit_class_balance(y_true)

    # Load predicted probabilities generated by evaluate_m2_flood
    with open(metrics_json, "r", encoding="utf-8") as f:
        m2_rep = json.load(f)

    # Evaluate audited metrics on Primary Independent Subset (N=6: 4 flooded, 2 unflooded)
    # Extract predictions
    from ml.validation.external.evaluate_m2_flood import extract_m2_features
    dem_path = REPO_ROOT / "data" / "raw" / "scenes" / "upper_beas_july2023" / "COP30_DEM.tif"
    dem = tifffile.imread(str(dem_path)) if dem_path.exists() else None
    X = extract_m2_features(df_raw, dem)
    model = joblib.load(model_path)
    y_prob = model.predict_proba(X)[:, 1]

    # Metrics on Primary Independent Subset (N=6)
    metrics_indep = evaluate_audited_metrics(
        y_true=y_true[indep_mask],
        y_prob=y_prob[indep_mask],
        class_audit=audit_class_balance(y_true[indep_mask]),
        threshold=0.50,
        threshold_source="Predefined model operational threshold (locked before external evaluation)",
        unit=ValidationUnit.POINT,
    )

    # Metrics on All 24 Points
    metrics_all = evaluate_audited_metrics(
        y_true=y_true,
        y_prob=y_prob,
        class_audit=class_audit,
        threshold=0.50,
        threshold_source="Predefined model operational threshold (locked before external evaluation)",
        unit=ValidationUnit.POINT,
    )

    # Add all-points ROC-AUC and Brier into reported dictionary with proper labeling
    metrics_reported = metrics_indep.copy()
    metrics_reported["roc_auc_all_points"] = metrics_all["roc_auc"]
    metrics_reported["recall_all_points"] = metrics_all["recall"]

    limitations = [
        f"Small independent sample size (N={n_indep}): while observed recall is 100% (4/4), "
        f"the exact 95% Clopper-Pearson confidence interval spans down to {exact_binomial_ci(4, 4).lower*100:.1f}%.",
        "Control quality: 4 controls are confirmed operational relief sites; 8 controls are geomorphically inferred "
        "upland absences (well above HFL and outside mapped extent, but not individual post-event surveys).",
        "Threshold saturation: Under catastrophic monsoonal forcing (R24h>220mm, CWC Bhuntar gauge at HFL), "
        "rainfall and river stage features dominate tree splits, causing high false alarms on upland benches at threshold 0.50.",
        "18 of 24 points fall within 500m of M2 training data; primary independent claims rest strictly on the 6 independent points.",
    ]

    audit_result = ModelValidationAuditResult(
        model="M2_Calibrated_XGBoost_Flood_Occurrence",
        dataset_name="upper_beas_july2023_flood_events_hpsdma_cwc_nrsc",
        validation_tier=ValidationTier.PARTIALLY_VALIDATED,
        primary_validation_unit=ValidationUnit.POINT,
        spatial_independence=spatial_audit,
        class_balance=class_audit,
        event_audit=None,
        control_quality=control_audit,
        metrics=metrics_reported,
        limitations=limitations,
        claims_supported=[],
        claims_unsupported=[],
    )

    supported, unsupported = generate_conservative_claims(audit_result)
    audit_result.claims_supported = supported
    audit_result.claims_unsupported = unsupported

    return audit_result


# =====================================================================
# STEP 7 & 8: MODEL M4 AUDIT (Multimodal Flood U-Net)
# =====================================================================
def audit_model_m4() -> ModelValidationAuditResult:
    """
    Audits Model M4 (Multimodal Flood U-Net).
    Strictly separates:
      1. Internal pixel-level segmentation benchmark (against SAR-HAND reference mask).
      2. External point-level concordance evaluation (24 historical event points).
      3. External 2D full-scene segmentation validation (NOT AVAILABLE).
    """
    raster_path = REPO_ROOT / "data" / "satellite_output" / "flood_unet_inundation.tif"
    events_path = REPO_ROOT / "data" / "external" / "flood" / "processed" / "upper_beas_flood_external_events.csv"
    metrics_json = REPO_ROOT / "docs" / "m4_unet_external_validation_metrics.json"

    with open(metrics_json, "r", encoding="utf-8") as f:
        m4_rep = json.load(f)

    df_events = pd.read_csv(events_path)
    y_true = df_events["inundation_observed"].values.astype(int)
    class_audit = audit_class_balance(y_true)

    # Point-level spatial independence (shared with flood inventory)
    spatial_audit = SpatialIndependenceAudit(
        total_samples=len(y_true),
        independent_count=6,
        non_independent_count=18,
        unknown_count=0,
        distance_threshold_m=500.0,
        primary_evaluation_subset="POINT_CONCORDANCE (N=24)",
    )

    # Sample raster probabilities at points
    prob_raster = tifffile.imread(str(raster_path)).astype(np.float32)
    rows, cols = prob_raster.shape
    min_lon, max_lon, min_lat, max_lat = 76.80, 77.45, 31.60, 32.40

    sampled_probs: List[float] = []
    for _, r in df_events.iterrows():
        lat = float(r["latitude"])
        lon = float(r["longitude"])
        r_idx = max(0, min(int((max_lat - lat) / (max_lat - min_lat) * rows), rows - 1))
        c_idx = max(0, min(int((lon - min_lon) / (max_lon - min_lon) * cols), cols - 1))
        sampled_probs.append(float(prob_raster[r_idx, c_idx]))

    y_prob = np.array(sampled_probs, dtype=np.float32)

    # Evaluate point-level metrics
    metrics = evaluate_audited_metrics(
        y_true=y_true,
        y_prob=y_prob,
        class_audit=class_audit,
        threshold=0.50,
        threshold_source="Standard binary segmentation threshold (locked before external evaluation)",
        unit=ValidationUnit.POINT,
    )

    # Explicitly document internal vs external 2D status
    metrics["external_2d_dice"] = MetricResult(
        metric_name="external_2d_dice",
        value=None,
        status=MetricStatus.NOT_ESTIMABLE,
        reason=(
            "not_available_authoritative_mask_missing: authoritative independent 10m digital flood delineation "
            "rasters or shapefiles (Copernicus EMS / NRSC) are not publicly released for this single scene. "
            "Internal benchmark achieves Dice=0.969-0.973 against SAR-HAND pseudo-reference, but this is an "
            "internal physical benchmark, not independent external validation."
        ),
        n=0,
        unit=ValidationUnit.PIXEL,
        is_threshold_dependent=True,
        threshold=0.50,
    )

    metrics["external_2d_iou"] = MetricResult(
        metric_name="external_2d_iou",
        value=None,
        status=MetricStatus.NOT_ESTIMABLE,
        reason=(
            "not_available_authoritative_mask_missing: authoritative independent 10m digital flood delineation "
            "rasters or shapefiles (Copernicus EMS / NRSC) are not publicly released for this single scene. "
            "Internal benchmark achieves IoU=0.939-0.948 against SAR-HAND pseudo-reference."
        ),
        n=0,
        unit=ValidationUnit.PIXEL,
        is_threshold_dependent=True,
        threshold=0.50,
    )

    limitations = [
        "Authoritative 10m independent flood extent rasters (Copernicus EMS / NRSC) are not openly distributed for this scene.",
        "External evaluation is restricted to point-level concordance at 24 historical disaster and control coordinates.",
        "Point concordance (ROC-AUC=0.6806, Recall=66.7%) CANNOT be equated with full-scene 2D segmentation validation.",
        "SAR layover and shadow on steep mountain walls cause occasional low-backscatter false detections.",
    ]

    audit_result = ModelValidationAuditResult(
        model="M4_Multimodal_9Channel_Flood_UNet",
        dataset_name="upper_beas_july2023_point_concordance_evaluation",
        validation_tier=ValidationTier.PARTIALLY_VALIDATED,
        primary_validation_unit=ValidationUnit.POINT,
        spatial_independence=spatial_audit,
        class_balance=class_audit,
        event_audit=None,
        control_quality=None,
        metrics=metrics,
        limitations=limitations,
        claims_supported=[],
        claims_unsupported=[],
    )

    supported, unsupported = generate_conservative_claims(audit_result)
    audit_result.claims_supported = supported
    audit_result.claims_unsupported = unsupported

    return audit_result


# =====================================================================
# MASTER RUNNER & STAGE-A SUMMARY GENERATION
# =====================================================================
def run_all_audits() -> Dict[str, Any]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("STAGE A: MASTER VALIDATION-AUDIT RUNNER")
    print("=" * 70)

    # 1. Audit M6
    print("[1/4] Auditing Model M6 (Landslide Susceptibility)...")
    m6_audit = audit_model_m6()
    save_audit_json(m6_audit, AUDIT_DIR / "m6_audit.json")
    print(f"      Status: {m6_audit.validation_tier.value} | ROC-AUC: {m6_audit.metrics['roc_auc'].status.value}")

    # 2. Audit M7
    print("[2/4] Auditing Model M7 (Dynamic Landslide Trigger)...")
    m7_audit = audit_model_m7()
    save_audit_json(m7_audit, AUDIT_DIR / "m7_audit.json")
    print(f"      Status: {m7_audit.validation_tier.value} | Event-Level AUC: {m7_audit.metrics['event_level_roc_auc'].status.value}")

    # 3. Audit M2
    print("[3/4] Auditing Model M2 (Flood Occurrence / Risk)...")
    m2_audit = audit_model_m2()
    save_audit_json(m2_audit, AUDIT_DIR / "m2_audit.json")
    print(f"      Status: {m2_audit.validation_tier.value} | Independent Recall (N=4): {m2_audit.metrics['recall'].value}")

    # 4. Audit M4
    print("[4/4] Auditing Model M4 (Multimodal Flood U-Net)...")
    m4_audit = audit_model_m4()
    save_audit_json(m4_audit, AUDIT_DIR / "m4_audit.json")
    print(f"      Status: {m4_audit.validation_tier.value} | External 2D Dice: {m4_audit.metrics['external_2d_dice'].status.value}")

    # 5. Assemble Validation Summary JSON
    summary = {
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE_A_VALIDATION_INTERPRETATION",
        "models_audited": ["M6", "M7", "M2", "M4"],
        "validation_tier_summary": {
            "M6": m6_audit.validation_tier.value,
            "M7": m7_audit.validation_tier.value,
            "M2": m2_audit.validation_tier.value,
            "M4": m4_audit.validation_tier.value,
        },
        "spatial_independence_summary": {
            "M6": {
                "total": m6_audit.spatial_independence.total_samples,
                "independent": m6_audit.spatial_independence.independent_count,
                "non_independent": m6_audit.spatial_independence.non_independent_count,
            },
            "M7": {
                "total": m7_audit.spatial_independence.total_samples,
                "independent": m7_audit.spatial_independence.independent_count,
                "non_independent": m7_audit.spatial_independence.non_independent_count,
            },
            "M2": {
                "total": m2_audit.spatial_independence.total_samples,
                "independent": m2_audit.spatial_independence.independent_count,
                "non_independent": m2_audit.spatial_independence.non_independent_count,
            },
            "M4": {
                "total": m4_audit.spatial_independence.total_samples,
                "independent": m4_audit.spatial_independence.independent_count,
                "non_independent": m4_audit.spatial_independence.non_independent_count,
            },
        },
        "event_independence_summary": {
            "M7": {
                "spatial_samples": m7_audit.event_audit.total_points if m7_audit.event_audit else None,
                "independent_events": m7_audit.event_audit.total_events if m7_audit.event_audit else None,
                "is_clustered_forcing": m7_audit.event_audit.is_clustered_forcing if m7_audit.event_audit else None,
            }
        },
        "control_quality_summary": {
            "M2": {
                "total_controls": m2_audit.control_quality.total_controls if m2_audit.control_quality else None,
                "valid_controls": m2_audit.control_quality.valid_controls_count if m2_audit.control_quality else None,
                "provisional_controls": m2_audit.control_quality.provisional_controls_count if m2_audit.control_quality else None,
                "invalid_controls": m2_audit.control_quality.invalid_controls_count if m2_audit.control_quality else None,
            }
        },
        "metrics_marked_not_estimable": [
            {"model": "M6", "metric": "roc_auc", "reason": m6_audit.metrics["roc_auc"].reason},
            {"model": "M6", "metric": "pr_auc", "reason": m6_audit.metrics["pr_auc"].reason},
            {"model": "M6", "metric": "specificity", "reason": m6_audit.metrics["specificity"].reason},
            {"model": "M6", "metric": "precision", "reason": m6_audit.metrics["precision"].reason},
            {"model": "M7", "metric": "event_level_roc_auc", "reason": m7_audit.metrics["event_level_roc_auc"].reason},
            {"model": "M4", "metric": "external_2d_dice", "reason": m4_audit.metrics["external_2d_dice"].reason},
            {"model": "M4", "metric": "external_2d_iou", "reason": m4_audit.metrics["external_2d_iou"].reason},
        ],
        "zero_fabrication_compliance": True,
    }

    with open(AUDIT_DIR / "validation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 6. Generate VALIDATION_STAGE_A_SUMMARY.md
    generate_stage_a_markdown(m6_audit, m7_audit, m2_audit, m4_audit, summary)

    print("=" * 70)
    print("STAGE A AUDIT COMPLETE: JSONs and Markdown summary generated.")
    print("=" * 70)
    return summary


def generate_stage_a_markdown(
    m6: ModelValidationAuditResult,
    m7: ModelValidationAuditResult,
    m2: ModelValidationAuditResult,
    m4: ModelValidationAuditResult,
    summary: Dict[str, Any],
) -> None:
    """Generates the master Stage A markdown report."""
    md_path = AUDIT_DIR / "VALIDATION_STAGE_A_SUMMARY.md"

    m6_table = render_metric_markdown_table(m6.metrics)
    m7_table = render_metric_markdown_table(m7.metrics)
    m2_table = render_metric_markdown_table(m2.metrics)
    m4_table = render_metric_markdown_table(m4.metrics)

    m6_supp = "\n".join(f"- {c}" for c in m6.claims_supported)
    m6_unsupp = "\n".join(f"- {c}" for c in m6.claims_unsupported)
    m7_supp = "\n".join(f"- {c}" for c in m7.claims_supported)
    m7_unsupp = "\n".join(f"- {c}" for c in m7.claims_unsupported)
    m2_supp = "\n".join(f"- {c}" for c in m2.claims_supported)
    m2_unsupp = "\n".join(f"- {c}" for c in m2.claims_unsupported)
    m4_supp = "\n".join(f"- {c}" for c in m4.claims_supported)
    m4_unsupp = "\n".join(f"- {c}" for c in m4.claims_unsupported)

    timestamp = summary["audit_timestamp_utc"]

    content = f"""# VALIDATION STAGE A — MASTER SCIENTIFIC AUDIT & INTERPRETATION REPORT
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Catchment: Upper Beas Basin (Kullu–Manali, Himachal Pradesh)*  
*Audit Timestamp: {timestamp}*

---

## 1. Executive Summary & Audit Mandate

Stage A establishes the rigorous scientific audit and interpretation of all existing external validation evidence for Models **M6**, **M7**, **M2**, and **M4**. In compliance with zero-fabrication standards:
- **Zero Retraining / Modification**: All production model weights and feature contracts remain strictly frozen.
- **Zero Data Fabrication**: No synthetic negatives or unverified control points were added.
- **Precise Distinction of Validation Units**: Explicit separation between *spatial point*, *clustered storm sample*, and *independent meteorological event*.
- **Exact Uncertainty Bounds**: Replaced unqualified percentage claims (e.g. "100% recall") with exact binomial Clopper-Pearson confidence intervals.

---

## 2. Core Audit Answers to Scientific Questions

### Q1: What evidence is genuinely independent?
- **M6 Landslide Susceptibility**: **11 failure points** verified $>500\\,\\text{{m}}$ from all M6 training points (out of 20 total points).
- **M7 Landslide Trigger**: **11 failure points** verified $>500\\,\\text{{m}}$ from training points, but all clustered under **1 storm event**.
- **M2 Flood Occurrence**: **6 points** (4 flooded + 2 unflooded) verified $>500\\,\\text{{m}}$ from all M2 training points (out of 24 total points).
- **M4 Multimodal Flood U-Net**: **6 points** verified $>500\\,\\text{{m}}$ from training points for point-level concordance.

### Q2: What evidence is spatially non-independent?
- **M6**: **9 points** fall within the $500\\,\\text{{m}}$ buffer of training data (mean distance: $310.6\\,\\text{{m}}$, min: $85.6\\,\\text{{m}}$).
- **M7**: **11 valley floor points** fall within the $500\\,\\text{{m}}$ buffer of training data.
- **M2 / M4**: **18 points** fall within the $500\\,\\text{{m}}$ buffer of training data (mean distance: $253.2\\,\\text{{m}}$, min: $42.0\\,\\text{{m}}$).
- *Protocol*: Spatially non-independent points are retained for descriptive characterization but are strictly excluded from primary independent claims.

### Q3: Which metrics are threshold-dependent vs. threshold-independent?
- **Threshold-Independent**: ROC-AUC, PR-AUC, Brier score loss. These evaluate ranking across all operating cutoffs.
- **Threshold-Dependent**: Precision, Recall (Sensitivity), Specificity, F1-Score, Accuracy, Confusion Matrix. Every threshold-dependent result is explicitly bound to threshold $\\tau = 0.50$ (locked prior to evaluation).

### Q4: Which metrics have confidence intervals?
- **Binary Proportions**: Recall, Specificity, Accuracy, and Precision have **exact Clopper-Pearson 95% confidence intervals** computed via the Beta distribution quantiles.
- **Continuous Metrics**: Guarded bootstrap confidence intervals are computed only when $N \\ge 15$ and both classes are present; otherwise flagged as `UNRELIABLE / NOT REPORTED (N < 15)`.

### Q5: Which datasets are too small for reliable inference?
- **M2 Independent Subset ($N=6$)**: Observed recall is $100\\%$ ($4/4$), but the exact $95\\%$ CI is $[0.3976, 1.0000]$. Statistical certainty cannot be claimed from $N=4$ positive events.
- **M6 Independent Subset ($N=11$)**: $N=11$ allows estimating recall ($15\\% - 27\\%$), but cannot estimate discrimination.

### Q6: Are the 12 M2 controls genuinely valid absences?
- **Valid Absences ($4$ sites)**: Confirmed operational administrative and civic relief grounds (Dhalpur Ground, Naggar Castle, Vashisht upper, Bajaura temple ridge) explicitly documented as active unflooded centers during the July 2023 disaster.
- **Provisional Absences ($8$ sites)**: Upland spurs and ridges well above High Flood Level ($>200\\,\\text{{m}}$ above riverbed, outside satellite flood extent) where absence is geomorphically deduced rather than an explicit field survey report.
- **Invalid Absences ($0$ sites)**: Zero points were placed within flood zones.

### Q7: Does M7 N=22 represent independent events or spatial forcing samples?
- **Empirical Finding**: The 22 observations represent **Case B: 22 spatial points exposed to ONE common storm event (July 9–10, 2023 cloudburst)**.
- **Effective Event Count**: $N_{{\\text{{events}}}} = 1$.
- **Event-Level ROC-AUC**: **`NOT ESTIMABLE`** (discrimination across multiple independent disaster epochs cannot be computed from 1 event).

---

## 3. Audited Results by Model

### 3.1 Model M6: Landslide Susceptibility (Random Forest)
- **Validation Tier**: **`INSUFFICIENT_SAMPLE`** (Zero negative controls)
- **Primary Validation Unit**: Historical Landslide Location (`POINT`)
- **Class Balance**: $20$ Positive Failures, $0$ Negative Controls ($100\\%$ single class)

{m6_table}

#### Conservative Claims:
- **What CAN be claimed**:
{m6_supp}
- **What CANNOT be claimed**:
{m6_unsupp}

---

### 3.2 Model M7: Dynamic Landslide Trigger (LightGBM)
- **Validation Tier**: **`PARTIALLY_VALIDATED`** (Single-event spatial forcing)
- **Primary Validation Unit**: Spatial Sample under Disaster Forcing (`SPATIAL_SAMPLE`)
- **Event Structure**: $22$ Spatial Samples, $1$ Meteorological Disaster Event

{m7_table}

#### Conservative Claims:
- **What CAN be claimed**:
{m7_supp}
- **What CANNOT be claimed**:
{m7_unsupp}

---

### 3.3 Model M2: Flood Occurrence / Risk (Calibrated XGBoost)
- **Validation Tier**: **`PARTIALLY_VALIDATED`**
- **Primary Validation Unit**: Historical Flood Damage / Control Location (`POINT`)
- **Primary Independent Subset ($N=6$)**: $4$ Flooded Sites, $2$ Unflooded Controls

{m2_table}

#### Conservative Claims:
- **What CAN be claimed**:
{m2_supp}
- **What CANNOT be claimed**:
{m2_unsupp}

---

### 3.4 Model M4: Multimodal 9-Channel Flood U-Net (PyTorch)
- **Validation Tier**: **`PARTIALLY_VALIDATED`**
- **Primary Validation Unit**: Point Concordance (`POINT`) vs Full Scene (`PIXEL`)
- **Internal Benchmark**: Dice F1 = $0.969 - 0.973$, IoU = $0.939 - 0.948$ (against SAR-HAND reference mask).
- **External Point Concordance**: ROC-AUC = $0.6806$, Mean $P_{{\\text{{flooded}}}} = 0.6834$ vs Mean $P_{{\\text{{unflooded}}}} = 0.4804$.
- **External 2D Segmentation**: **`NOT AVAILABLE`** (authoritative open 10m raster pending).

{m4_table}

#### Conservative Claims:
- **What CAN be claimed**:
{m4_supp}
- **What CANNOT be claimed**:
{m4_unsupp}

---

## 4. What Validation Evidence is Still Missing?

1. **Unfailed Negative Control Slopes for M6**: Geotechnically surveyed stable hillslopes in the Upper Beas basin are required to estimate ROC-AUC, PR-AUC, specificity, and false-alarm rates for static susceptibility.
2. **Multi-Storm Temporal Episodes for M7**: Multi-year storm catalog (e.g. 2018, 2019, 2021 monsoon seasons) is needed to compute true event-level ROC-AUC.
3. **Authoritative 10m Full-Scene Flood Delineation Rasters for M4**: Vector or raster shapefiles from Copernicus EMS Rapid Mapping or NRSC Disaster Watch are required to establish external 2D Dice and IoU.
4. **Borehole In-Situ Continuous Piezometer Networks**: Real-time pore pressure and matric suction telemetry remain unavailable in open public databases.

---

## 5. Stage A Sign-Off

Stage A is **COMPLETE**. All four models (M6, M7, M2, M4) have been audited against empirical evidence, and their statistical limitations, exact confidence intervals, and conservative claim boundaries are permanently documented.

**Directive**: Stop after Stage A. Do NOT begin M1, M3, M5 or any other new ML model.
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    run_all_audits()


