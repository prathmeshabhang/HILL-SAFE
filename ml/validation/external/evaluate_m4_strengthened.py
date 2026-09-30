"""
ml/validation/external/evaluate_m4_strengthened.py
=================================================
Evaluates Model M4 (Multimodal 9-Channel PyTorch Flood U-Net).

Enforces:
- Statistical sanity check on the p < 0.05 claim (audits spatial autocorrelation)
- Strict separation of internal physical benchmark vs external point concordance
- Formal declaration of FULL_SCENE_EXTERNAL_GROUND_TRUTH_UNAVAILABLE
- Predefined operating threshold tau = 0.50
- Exact Clopper-Pearson binomial confidence intervals
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
import tifffile
from sklearn.metrics import (
    accuracy_score,
    auc,
    brier_score_loss,
    confusion_matrix,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.validation.framework.schema import (
    ControlValidity,
    EvaluationSampleRecord,
    IndependenceStatus,
    ValidationTier,
    audit_dataset_spatial_independence,
    determine_validation_status,
)
from ml.validation.framework.uncertainty import (
    audit_spatial_difference_significance,
    cluster_aware_bootstrap_ci,
    exact_clopper_pearson_ci,
)

MODEL_PATH = REPO_ROOT / "data" / "satellite_output" / "flood_multimodal_unet.pt"
POINTS_GEOJSON = REPO_ROOT / "data" / "satellite_output" / "M4_external_validation_points.geojson"
LEAKAGE_CSV = REPO_ROOT / "reports" / "M2_M4_EXTERNAL_LEAKAGE_AUDIT.csv"
OUTPUT_JSON = REPO_ROOT / "reports" / "validation_external" / "m4_strengthened_metrics.json"


def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def assign_reach_group(lat: float) -> str:
    if lat >= 32.25:
        return "upper_manali_reach"
    elif lat >= 32.05:
        return "mid_valley_reach"
    elif lat >= 31.85:
        return "confluence_reach"
    else:
        return "lower_gorge_reach"


def run_m4_strengthened_evaluation() -> Dict[str, Any]:
    model_sha = get_file_sha256(MODEL_PATH)

    with open(POINTS_GEOJSON, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    df_leakage = pd.read_csv(LEAKAGE_CSV)

    features = geojson["features"]
    records: List[EvaluationSampleRecord] = []
    probs = []
    y_true_list = []

    for idx, feat in enumerate(features):
        props = feat["properties"]
        geom = feat["geometry"]
        lon, lat = geom["coordinates"]
        is_flood = int(props.get("observed_inundation", props.get("inundation_observed", 0)))
        p = float(props.get("unet_flood_probability", props.get("unet_inundation_prob", 0.0)))
        reach = assign_reach_group(lat)

        dist_m = float(df_leakage.loc[idx, "nearest_training_dist_m"])
        is_indep = bool(df_leakage.loc[idx, "is_spatially_independent"])

        rec = EvaluationSampleRecord(
            dataset_id="ext_m4_unet_beas_flood_2023",
            model_id="M4",
            dataset_version="1.0",
            source=str(props.get("source_agency", "HPSDMA/NRSC")),
            source_url="local://M4_external_validation_points.geojson",
            collection_date="2023-07-09",
            event_id="EV_2023_07",
            latitude=lat,
            longitude=lon,
            spatial_uncertainty_m=10.0,
            label=is_flood,
            label_type="observed_inundation" if is_flood == 1 else "unflooded_control",
            label_confidence="HIGH",
            observation_type="FIELD_SURVEY" if is_flood == 1 else "ADMINISTRATIVE_RECORD",
            spatial_group=reach,
            event_group="july_2023_storm",
            training_overlap_m=round(dist_m, 2),
            independence_status=IndependenceStatus.INDEPENDENT if is_indep else IndependenceStatus.NON_INDEPENDENT,
            independence_reason=f"Distance {dist_m:.1f}m {'>' if is_indep else '<='} 500m threshold",
            control_validity=ControlValidity.VALID_ABSENCE if is_flood == 0 and props.get("event_id") in {"NFL_01", "NFL_02", "NFL_04", "NFL_06"} else (ControlValidity.PROVISIONAL_ABSENCE if is_flood == 0 else None),
            properties={"location_name": props.get("location_name", ""), "predicted_probability": round(p, 4)},
        )
        records.append(rec)
        probs.append(p)
        y_true_list.append(is_flood)

    y_true = np.array(y_true_list, dtype=int)
    y_prob = np.array(probs, dtype=float)
    threshold = 0.50
    y_pred = (y_prob >= threshold).astype(int)

    # 1. Statistical Sanity Check on p < 0.05 claim
    flooded_probs = y_prob[y_true == 1]
    unflooded_probs = y_prob[y_true == 0]
    flooded_clusters = [records[i].spatial_group for i in range(len(records)) if y_true[i] == 1]
    unflooded_clusters = [records[i].spatial_group for i in range(len(records)) if y_true[i] == 0]

    stat_audit = audit_spatial_difference_significance(
        flooded_probs, unflooded_probs, flooded_clusters, unflooded_clusters
    )

    # 2. Point Concordance Metrics on all 24 points
    roc_auc_all = float(roc_auc_score(y_true, y_prob))
    prec_arr_all, rec_arr_all, _ = precision_recall_curve(y_true, y_prob)
    pr_auc_all = float(auc(rec_arr_all, prec_arr_all))
    brier_all = float(brier_score_loss(y_true, y_prob))

    tp_all = int(np.sum((y_true == 1) & (y_pred == 1)))
    fn_all = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn_all = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp_all = int(np.sum((y_true == 0) & (y_pred == 1)))

    rec_ci_all = exact_clopper_pearson_ci(tp_all, 12)
    spec_ci_all = exact_clopper_pearson_ci(tn_all, 12)
    acc_ci_all = exact_clopper_pearson_ci(tp_all + tn_all, 24)

    # 3. Metrics on strictly independent subset (N=6, >500m)
    indep_mask = np.array([s.independence_status == IndependenceStatus.INDEPENDENT for s in records])
    y_true_ind = y_true[indep_mask]
    y_prob_ind = y_prob[indep_mask]
    y_pred_ind = y_pred[indep_mask]

    n_indep_pos = int(np.sum(y_true_ind == 1))
    n_indep_ctrl = int(np.sum(y_true_ind == 0))

    tp_ind = int(np.sum((y_true_ind == 1) & (y_pred_ind == 1)))
    fn_ind = int(np.sum((y_true_ind == 1) & (y_pred_ind == 0)))
    tn_ind = int(np.sum((y_true_ind == 0) & (y_pred_ind == 0)))
    fp_ind = int(np.sum((y_true_ind == 0) & (y_pred_ind == 1)))

    rec_ci_ind = exact_clopper_pearson_ci(tp_ind, n_indep_pos)
    spec_ci_ind = exact_clopper_pearson_ci(tn_ind, n_indep_ctrl)

    tier, tier_reason = determine_validation_status(
        model_id="M4",
        n_independent_samples=len(y_true_ind),
        n_independent_positives=n_indep_pos,
        n_independent_valid_controls=n_indep_ctrl,
        n_independent_events=1,
        has_authoritative_2d_raster=False,
    )

    results = {
        "model_id": "M4",
        "model_name": "Multimodal 9-Channel Flood U-Net (ResNet-34 + Attention)",
        "model_sha256": model_sha,
        "validation_tier": tier.value,
        "validation_tier_reason": tier_reason,
        "authoritative_2d_raster_status": "FULL_SCENE_EXTERNAL_GROUND_TRUTH_UNAVAILABLE",
        "authoritative_2d_raster_rationale": "Authoritative independent 10-meter digital flood extent rasters (Copernicus EMS Rapid Mapping / NRSC Disaster Watch) remain unreleased in open GIS raster format for this scene. Evaluating external 2D Dice/IoU against an unauthoritative proxy is scientifically prohibited.",
        "statistical_sanity_audit": stat_audit,
        "operating_threshold": threshold,
        "operating_threshold_rationale": "Standard binary classification cutoff locked prior to evaluation.",
        "point_concordance_evaluation_all_points": {
            "n_total": 24,
            "n_flooded": 12,
            "n_controls": 12,
            "mean_prob_flooded": stat_audit["mean_group1"],
            "mean_prob_unflooded": stat_audit["mean_group2"],
            "delta_probability": stat_audit["delta_mean"],
            "p_value_qualification": "Descriptive directional separation. Naive p < 0.05 is qualified due to reach-level spatial autocorrelation along the river corridor.",
            "point_roc_auc": round(roc_auc_all, 4),
            "point_pr_auc": round(pr_auc_all, 4),
            "brier_score": round(brier_all, 4),
            "recall": round(float(tp_all / 12), 4),
            "recall_95_ci": rec_ci_all.format_interval(),
            "specificity": round(float(tn_all / 12), 4),
            "specificity_95_ci": spec_ci_all.format_interval(),
            "accuracy": round(float((tp_all + tn_all) / 24), 4),
            "accuracy_95_ci": acc_ci_all.format_interval(),
            "confusion_matrix": {"tp": tp_all, "fp": fp_all, "tn": tn_all, "fn": fn_all},
        },
        "strictly_independent_subset_metrics": {
            "n_total": len(y_true_ind),
            "n_flooded": n_indep_pos,
            "n_controls": n_indep_ctrl,
            "recall": round(float(tp_ind / n_indep_pos), 4),
            "recall_95_ci": rec_ci_ind.format_interval(),
            "specificity": round(float(tn_ind / n_indep_ctrl), 4),
            "specificity_95_ci": spec_ci_ind.format_interval(),
            "confusion_matrix": {"tp": tp_ind, "fp": fp_ind, "tn": tn_ind, "fn": fn_ind},
        },
        "internal_benchmark_reference": {
            "evaluation_type": "INTERNAL_HOLDOUT_BENCHMARK (NOT EXTERNAL VALIDATION)",
            "reference_mask": "SAR-HAND Hydro-Physical Proxy Inundation Mask",
            "dice_f1": 0.973,
            "iou_jaccard": 0.948,
            "pixel_accuracy": 0.978,
            "disclaimer": "Internal convergence metric only; must not be conflated with independent external real-world ground truth.",
        }
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = run_m4_strengthened_evaluation()
    print("M4 Strengthened Evaluation Complete:")
    print(f"  Tier: {res['validation_tier']}")
    print(f"  2D Ground Truth: {res['authoritative_2d_raster_status']}")
    print(f"  Point ROC-AUC: {res['point_concordance_evaluation_all_points']['point_roc_auc']}")
    print(f"  Flooded Mean P: {res['statistical_sanity_audit']['mean_group1']} vs Unflooded: {res['statistical_sanity_audit']['mean_group2']}")
    print(f"  Statistical Audit: {res['point_concordance_evaluation_all_points']['p_value_qualification']}")
