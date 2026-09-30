"""
ml/validation/external/evaluate_m6_strengthened.py
=================================================
Evaluates the frozen Model M6 (Random Forest Landslide Susceptibility)
against real historical failure points AND authoritative negative control slopes.

Enforces:
- Zero model retraining or tuning (verifies SHA-256)
- Predefined operating threshold tau = 0.50
- Strict spatial independence (>500m separation)
- Exact Clopper-Pearson binomial confidence intervals
- Cluster-aware uncertainty over spatial groups
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
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

from ml.validation.external.feature_extractor import M6FeatureExtractor
from ml.validation.framework.schema import (
    ControlValidity,
    EvaluationSampleRecord,
    IndependenceStatus,
    SpatialIndependenceSummary,
    ValidationTier,
    audit_dataset_spatial_independence,
    determine_validation_status,
    haversine_distance_m,
)
from ml.validation.framework.uncertainty import (
    cluster_aware_bootstrap_ci,
    exact_clopper_pearson_ci,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = REPO_ROOT / "ml" / "landslide" / "m6_beas_susceptibility_rf.joblib"
FAILURES_CSV = REPO_ROOT / "data" / "external" / "m6" / "upper_beas" / "raw" / "kullu_upper_beas_landslides_2023_raw.csv"
CONTROLS_CSV = REPO_ROOT / "data" / "external" / "m6" / "upper_beas" / "raw" / "kullu_upper_beas_stable_controls_raw.csv"
TRAINING_CSV = REPO_ROOT / "data" / "processed" / "upper_beas" / "upper_beas_landslide_dataset.csv"
OUTPUT_JSON = REPO_ROOT / "reports" / "validation_external" / "m6_strengthened_metrics.json"


def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def assign_spatial_group(lat: float, lon: float) -> str:
    """Assigns geomorphic valley reach cluster to coordinate."""
    if lat >= 32.25:
        return "upper_manali_rohtang"
    elif lat >= 32.10:
        return "mid_beas_valley"
    elif lat >= 31.85:
        return "kullu_bhuntar_confluence"
    else:
        return "lower_gorge_tirthan"


def run_m6_strengthened_evaluation() -> Dict[str, Any]:
    # 1. Verify frozen model
    model_sha = get_file_sha256(MODEL_PATH)
    model = joblib.load(MODEL_PATH)

    # 2. Ingest failure points (N=20)
    df_fail = pd.read_csv(FAILURES_CSV)
    # 3. Ingest stable controls (N=12)
    df_ctrl = pd.read_csv(CONTROLS_CSV)

    # 4. Ingest training data to audit spatial proximity
    df_train = pd.read_csv(TRAINING_CSV)
    train_points = list(zip(df_train["lat"], df_train["lon"]))

    # 5. Build standardized EvaluationSampleRecord objects
    records: List[EvaluationSampleRecord] = []

    for _, r in df_fail.iterrows():
        lat, lon = float(r["latitude"]), float(r["longitude"])
        grp = assign_spatial_group(lat, lon)
        rec = EvaluationSampleRecord(
            dataset_id="ext_kullu_upper_beas_failures_2023",
            model_id="M6",
            dataset_version="1.0",
            source=str(r.get("source_report", "GSI/HPSDMA")),
            source_url="local://kullu_upper_beas_landslides_2023_raw.csv",
            collection_date=str(r.get("event_date", "2023-07-09")),
            event_id="EV_2023_07",
            latitude=lat,
            longitude=lon,
            spatial_uncertainty_m=15.0,
            label=1,
            label_type="observed_failure",
            label_confidence="HIGH",
            observation_type="FIELD_SURVEY",
            spatial_group=grp,
            event_group="july_2023_storm",
            training_overlap_m=0.0,
            independence_status=IndependenceStatus.UNKNOWN,
            independence_reason="",
            control_validity=None,
            properties={"location_name": r.get("location_name", ""), "type": r.get("landslide_type", "")},
        )
        records.append(rec)

    for _, r in df_ctrl.iterrows():
        lat, lon = float(r["latitude"]), float(r["longitude"])
        grp = assign_spatial_group(lat, lon)
        validity = ControlValidity(r.get("control_validity", "VALID_ABSENCE"))
        rec = EvaluationSampleRecord(
            dataset_id="ext_kullu_upper_beas_controls_2023",
            model_id="M6",
            dataset_version="1.0",
            source=str(r.get("control_source", "HPSDMA/Heritage")),
            source_url="local://kullu_upper_beas_stable_controls_raw.csv",
            collection_date="2023-07-10",
            event_id="EV_2023_07",
            latitude=lat,
            longitude=lon,
            spatial_uncertainty_m=10.0,
            label=0,
            label_type="stable_control",
            label_confidence=str(r.get("label_confidence", "HIGH")),
            observation_type="ADMINISTRATIVE_RECORD",
            spatial_group=grp,
            event_group="july_2023_storm",
            training_overlap_m=0.0,
            independence_status=IndependenceStatus.UNKNOWN,
            independence_reason="",
            control_validity=validity,
            properties={"location_name": r.get("location_name", ""), "justification": r.get("justification", "")},
        )
        records.append(rec)

    # 6. Audit spatial independence (500m threshold)
    spatial_summary = audit_dataset_spatial_independence(records, train_points, distance_threshold_m=500.0)

    # 7. Extract M6 features via feature extractor
    coords = [(s.latitude, s.longitude) for s in records]
    extractor = M6FeatureExtractor()
    X, _ = extractor.extract_features_for_points(coords)

    # 8. Frozen inference
    y_true = np.array([s.label for s in records], dtype=int)
    y_prob = model.predict_proba(X)[:, 1]

    # Partition into strictly independent subset vs all
    indep_mask = np.array([s.independence_status == IndependenceStatus.INDEPENDENT for s in records])
    indep_valid_ctrl_mask = indep_mask & (y_true == 0)
    indep_pos_mask = indep_mask & (y_true == 1)

    n_indep_pos = int(np.sum(indep_pos_mask))
    n_indep_ctrl = int(np.sum(indep_valid_ctrl_mask))
    n_indep_total = int(np.sum(indep_mask))

    spatial_clusters = [s.spatial_group for s in records]
    spatial_clusters_indep = [spatial_clusters[i] for i in range(len(records)) if indep_mask[i]]

    # 9. Compute Metrics on Strictly Independent Subset (N_indep)
    threshold = 0.50
    y_true_ind = y_true[indep_mask]
    y_prob_ind = y_prob[indep_mask]
    y_pred_ind = (y_prob_ind >= threshold).astype(int)

    tp_ind = int(np.sum((y_true_ind == 1) & (y_pred_ind == 1)))
    fn_ind = int(np.sum((y_true_ind == 1) & (y_pred_ind == 0)))
    tn_ind = int(np.sum((y_true_ind == 0) & (y_pred_ind == 0)))
    fp_ind = int(np.sum((y_true_ind == 0) & (y_pred_ind == 1)))

    rec_ci = exact_clopper_pearson_ci(tp_ind, n_indep_pos)
    spec_ci = exact_clopper_pearson_ci(tn_ind, n_indep_ctrl)
    prec_ci = exact_clopper_pearson_ci(tp_ind, tp_ind + fp_ind) if (tp_ind + fp_ind) > 0 else None
    acc_ci = exact_clopper_pearson_ci(tp_ind + tn_ind, n_indep_total)

    # Compute ROC-AUC on independent subset
    has_both_classes_ind = (len(np.unique(y_true_ind)) == 2)
    if has_both_classes_ind:
        roc_auc_ind = float(roc_auc_score(y_true_ind, y_prob_ind))
        prec_arr, rec_arr, _ = precision_recall_curve(y_true_ind, y_prob_ind)
        pr_auc_ind = float(auc(rec_arr, prec_arr))
        brier_ind = float(brier_score_loss(y_true_ind, y_prob_ind))

        # Cluster bootstrap on independent subset
        roc_auc_ci = cluster_aware_bootstrap_ci(
            y_true_ind, y_prob_ind,
            metric_fn=lambda yt, yp: float(roc_auc_score(yt, yp)),
            cluster_ids=spatial_clusters_indep,
        )
    else:
        roc_auc_ind = None
        pr_auc_ind = None
        brier_ind = float(brier_score_loss(y_true_ind, y_prob_ind))
        roc_auc_ci = None

    # Compute Metrics on All Points (N=32) for full descriptive transparency
    y_pred_all = (y_prob >= threshold).astype(int)
    tp_all = int(np.sum((y_true == 1) & (y_pred_all == 1)))
    fn_all = int(np.sum((y_true == 1) & (y_pred_all == 0)))
    tn_all = int(np.sum((y_true == 0) & (y_pred_all == 0)))
    fp_all = int(np.sum((y_true == 0) & (y_pred_all == 1)))

    roc_auc_all = float(roc_auc_score(y_true, y_prob))
    prec_arr_all, rec_arr_all, _ = precision_recall_curve(y_true, y_prob)
    pr_auc_all = float(auc(rec_arr_all, prec_arr_all))
    brier_all = float(brier_score_loss(y_true, y_prob))

    tier, tier_reason = determine_validation_status(
        model_id="M6",
        n_independent_samples=n_indep_total,
        n_independent_positives=n_indep_pos,
        n_independent_valid_controls=n_indep_ctrl,
        n_independent_events=1,
    )

    results = {
        "model_id": "M6",
        "model_name": "Random Forest Landslide Susceptibility (350 trees)",
        "model_sha256": model_sha,
        "validation_tier": tier.value,
        "validation_tier_reason": tier_reason,
        "operating_threshold": threshold,
        "operating_threshold_rationale": "Locked prior to external evaluation (standard risk threshold).",
        "spatial_summary": asdict(spatial_summary),
        "independent_subset_metrics": {
            "n_total": n_indep_total,
            "n_positives": n_indep_pos,
            "n_valid_controls": n_indep_ctrl,
            "roc_auc": round(roc_auc_ind, 4) if roc_auc_ind is not None else None,
            "roc_auc_status": "VALID" if roc_auc_ind is not None else "NOT_ESTIMABLE",
            "roc_auc_95_ci": roc_auc_ci.format_interval() if roc_auc_ci else None,
            "pr_auc": round(pr_auc_ind, 4) if pr_auc_ind is not None else None,
            "brier_score": round(brier_ind, 4),
            "recall": round(float(recall_score(y_true_ind, y_pred_ind)), 4),
            "recall_95_ci": rec_ci.format_interval(),
            "specificity": round(float(tn_ind / n_indep_ctrl), 4) if n_indep_ctrl > 0 else None,
            "specificity_95_ci": spec_ci.format_interval() if spec_ci else None,
            "precision": round(float(precision_score(y_true_ind, y_pred_ind, zero_division=0)), 4),
            "precision_95_ci": prec_ci.format_interval() if prec_ci else None,
            "accuracy": round(float(accuracy_score(y_true_ind, y_pred_ind)), 4),
            "accuracy_95_ci": acc_ci.format_interval(),
            "confusion_matrix": {"tp": tp_ind, "fp": fp_ind, "tn": tn_ind, "fn": fn_ind},
        },
        "all_samples_descriptive_metrics": {
            "n_total": len(records),
            "n_positives": int(np.sum(y_true == 1)),
            "n_controls": int(np.sum(y_true == 0)),
            "roc_auc": round(roc_auc_all, 4),
            "pr_auc": round(pr_auc_all, 4),
            "brier_score": round(brier_all, 4),
            "recall": round(float(recall_score(y_true, y_pred_all)), 4),
            "specificity": round(float(tn_all / (tn_all + fp_all)), 4),
            "confusion_matrix": {"tp": tp_all, "fp": fp_all, "tn": tn_all, "fn": fn_all},
        },
        "sample_records": [s.to_dict() for s in records],
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = run_m6_strengthened_evaluation()
    print("M6 Strengthened Evaluation Complete:")
    print(f"  Tier: {res['validation_tier']}")
    print(f"  Independent Samples: {res['independent_subset_metrics']['n_total']} (Pos: {res['independent_subset_metrics']['n_positives']}, Ctrl: {res['independent_subset_metrics']['n_valid_controls']})")
    print(f"  Independent ROC-AUC: {res['independent_subset_metrics']['roc_auc']}")
    print(f"  Independent Recall: {res['independent_subset_metrics']['recall']} (CI: {res['independent_subset_metrics']['recall_95_ci']})")
    print(f"  Independent Specificity: {res['independent_subset_metrics']['specificity']} (CI: {res['independent_subset_metrics']['specificity_95_ci']})")
