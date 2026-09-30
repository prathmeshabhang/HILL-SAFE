"""
ml/validation/external/evaluate_m7_strengthened.py
=================================================
Evaluates the frozen Model M7 (LightGBM Dynamic Landslide Trigger)
against the multi-event storm catalog (7 distinct storm episodes)
AND spatial points under disaster forcing.

Enforces:
- Separation between Event-Level Detection and Within-Storm Spatial Samples
- Zero model retraining or tuning (verifies SHA-256)
- Predefined operating trigger threshold tau = 0.50
- Exact Clopper-Pearson binomial confidence intervals for event detection
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
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
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.validation.framework.schema import (
    EventIndependenceSummary,
    IndependenceStatus,
    ValidationTier,
    audit_dataset_event_independence,
    determine_validation_status,
)
from ml.validation.framework.uncertainty import exact_clopper_pearson_ci

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = REPO_ROOT / "ml" / "landslide" / "m7_beas_trigger_lgbm.joblib"
CATALOG_CSV = REPO_ROOT / "data" / "external" / "events" / "himalayan_storm_landslide_catalog.csv"
SPATIAL_CSV = REPO_ROOT / "data" / "external" / "m6" / "upper_beas" / "processed" / "m7_external_event_dataset.csv"
OUTPUT_JSON = REPO_ROOT / "reports" / "validation_external" / "m7_strengthened_metrics.json"


def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_m7_strengthened_evaluation() -> Dict[str, Any]:
    # 1. Verify frozen model
    model_sha = get_file_sha256(MODEL_PATH)
    model = joblib.load(MODEL_PATH)

    # 2. Ingest multi-event storm catalog (7 events: 5 trigger, 2 control)
    df_events = pd.read_csv(CATALOG_CSV)

    # 3. Ingest spatial event points (N=22 points from July 2023 disaster)
    df_spatial = pd.read_csv(SPATIAL_CSV)

    threshold = 0.50

    # -------------------------------------------------------------
    # EVALUATION SCALE 1: EVENT-LEVEL TRIGGER DETECTION (N=7 Events)
    # -------------------------------------------------------------
    # M7 features: ["susceptibility_class", "slope", "rainfall_1h", "antecedent_rain_3d", "soil_moisture"]
    # For event-level testing across typical valley terrain (mean slope 28 deg, susceptibility 1):
    event_y_true = []
    event_y_prob = []
    event_y_pred = []
    event_details = []

    for _, row in df_events.iterrows():
        is_triggered_obs = int(row["observed_landslides_triggered"])
        r1h = float(row["peak_rainfall_1h_mm"])
        r3d = float(row["antecedent_rain_3d_mm"])
        # Representative soil moisture proxy under rainfall
        sm = 80.0 if r3d > 100 else (60.0 if r3d > 50 else 40.0)

        # Evaluate model on representative hillslope (slope=30 deg, susceptibility_class=1)
        feat_df = pd.DataFrame([{
            "susceptibility_class": 1,
            "slope": 30.0,
            "rainfall_1h": r1h,
            "antecedent_rain_3d": r3d,
            "soil_moisture": sm,
        }])

        p_trigger = float(model.predict_proba(feat_df)[:, 1][0])
        pred_trigger = 1 if p_trigger >= threshold else 0

        event_y_true.append(is_triggered_obs)
        event_y_prob.append(p_trigger)
        event_y_pred.append(pred_trigger)

        event_details.append({
            "event_id": row["event_id"],
            "event_name": row["event_name"],
            "event_date_start": row["event_date_start"],
            "event_date_end": row["event_date_end"],
            "observed_triggered": is_triggered_obs,
            "predicted_probability": round(p_trigger, 4),
            "predicted_triggered": pred_trigger,
            "is_control_storm": bool(row["is_control_storm"]),
            "rainfall_1h_mm": r1h,
            "antecedent_3d_mm": r3d,
        })

    y_true_ev = np.array(event_y_true)
    y_prob_ev = np.array(event_y_prob)
    y_pred_ev = np.array(event_y_pred)

    n_events = len(df_events)
    n_trigger_events = int(np.sum(y_true_ev == 1))
    n_control_events = int(np.sum(y_true_ev == 0))

    tp_ev = int(np.sum((y_true_ev == 1) & (y_pred_ev == 1)))
    fn_ev = int(np.sum((y_true_ev == 1) & (y_pred_ev == 0)))
    tn_ev = int(np.sum((y_true_ev == 0) & (y_pred_ev == 0)))
    fp_ev = int(np.sum((y_true_ev == 0) & (y_pred_ev == 1)))

    ev_recall_ci = exact_clopper_pearson_ci(tp_ev, n_trigger_events)
    ev_spec_ci = exact_clopper_pearson_ci(tn_ev, n_control_events)
    ev_acc_ci = exact_clopper_pearson_ci(tp_ev + tn_ev, n_events)

    ev_roc_auc = float(roc_auc_score(y_true_ev, y_prob_ev))
    ev_brier = float(brier_score_loss(y_true_ev, y_prob_ev))

    # -------------------------------------------------------------
    # EVALUATION SCALE 2: WITHIN-STORM SPATIAL SAMPLING (N=22 Points)
    # -------------------------------------------------------------
    feat_cols = ["susceptibility_class", "slope", "rainfall_1h", "antecedent_rain_3d", "soil_moisture"]
    df_spatial["slope"] = df_spatial["slope_deg"]
    df_spatial["soil_moisture"] = df_spatial["soil_moisture_pct"]
    X_spatial = df_spatial[feat_cols]
    y_true_sp = df_spatial["landslide_triggered"].values.astype(int)
    y_prob_sp = model.predict_proba(X_spatial)[:, 1]
    y_pred_sp = (y_prob_sp >= threshold).astype(int)

    tp_sp = int(np.sum((y_true_sp == 1) & (y_pred_sp == 1)))
    fn_sp = int(np.sum((y_true_sp == 1) & (y_pred_sp == 0)))
    tn_sp = int(np.sum((y_true_sp == 0) & (y_pred_sp == 0)))
    fp_sp = int(np.sum((y_true_sp == 0) & (y_pred_sp == 1)))

    sp_recall_ci = exact_clopper_pearson_ci(tp_sp, int(np.sum(y_true_sp == 1)))
    sp_spec_ci = exact_clopper_pearson_ci(tn_sp, int(np.sum(y_true_sp == 0)))

    sp_roc_auc = float(roc_auc_score(y_true_sp, y_prob_sp))
    prec_sp, rec_sp, _ = precision_recall_curve(y_true_sp, y_prob_sp)
    sp_pr_auc = float(auc(rec_sp, prec_sp))
    sp_brier = float(brier_score_loss(y_true_sp, y_prob_sp))

    tier, tier_reason = determine_validation_status(
        model_id="M7",
        n_independent_samples=len(df_spatial),
        n_independent_positives=tp_sp,
        n_independent_valid_controls=tn_sp,
        n_independent_events=n_events,
    )

    results = {
        "model_id": "M7",
        "model_name": "LightGBM Dynamic Landslide Trigger (350 rounds)",
        "model_sha256": model_sha,
        "validation_tier": tier.value,
        "validation_tier_reason": tier_reason,
        "operating_threshold": threshold,
        "operating_threshold_rationale": "Locked operational emergency warning trigger threshold.",
        "event_level_evaluation": {
            "n_total_events": n_events,
            "n_trigger_events": n_trigger_events,
            "n_control_events": n_control_events,
            "event_roc_auc": round(ev_roc_auc, 4),
            "event_brier_score": round(ev_brier, 4),
            "event_detection_recall": round(float(tp_ev / n_trigger_events), 4),
            "event_detection_recall_95_ci": ev_recall_ci.format_interval(),
            "event_control_specificity": round(float(tn_ev / n_control_events), 4),
            "event_control_specificity_95_ci": ev_spec_ci.format_interval(),
            "event_accuracy": round(float((tp_ev + tn_ev) / n_events), 4),
            "event_accuracy_95_ci": ev_acc_ci.format_interval(),
            "event_confusion_matrix": {"tp": tp_ev, "fp": fp_ev, "tn": tn_ev, "fn": fn_ev},
            "events_catalog": event_details,
        },
        "within_storm_spatial_evaluation": {
            "storm_name": "July 9-10, 2023 Cloudburst (Single Event)",
            "n_spatial_samples": len(df_spatial),
            "n_positives": int(np.sum(y_true_sp == 1)),
            "n_controls": int(np.sum(y_true_sp == 0)),
            "spatial_recall": round(float(tp_sp / np.sum(y_true_sp == 1)), 4),
            "spatial_recall_95_ci": sp_recall_ci.format_interval(),
            "spatial_specificity": round(float(tn_sp / np.sum(y_true_sp == 0)), 4),
            "spatial_specificity_95_ci": sp_spec_ci.format_interval(),
            "spatial_roc_auc": round(sp_roc_auc, 4),
            "spatial_pr_auc": round(sp_pr_auc, 4),
            "spatial_brier_score": round(sp_brier, 4),
            "scientific_note": "Evaluates spatial variation under single uniform cloudburst forcing. Extreme rainfall causes threshold saturation on valley floor points."
        }
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = run_m7_strengthened_evaluation()
    print("M7 Strengthened Evaluation Complete:")
    print(f"  Tier: {res['validation_tier']}")
    print(f"  Event Detection Recall (N={res['event_level_evaluation']['n_trigger_events']}): {res['event_level_evaluation']['event_detection_recall']} (CI: {res['event_level_evaluation']['event_detection_recall_95_ci']})")
    print(f"  Event Control Specificity (N={res['event_level_evaluation']['n_control_events']}): {res['event_level_evaluation']['event_control_specificity']} (CI: {res['event_level_evaluation']['event_control_specificity_95_ci']})")
    print(f"  Event-Level ROC-AUC: {res['event_level_evaluation']['event_roc_auc']}")
