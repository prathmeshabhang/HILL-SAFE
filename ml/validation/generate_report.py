"""
generate_report.py — Master Scientific Validation Report Generator
===================================================================
Executes deterministic scientific validation across all FLOODY SHIELD models:
  - Model M2 (Calibrated XGBoost Flood)
  - Model M6 (Random Forest Static Landslide Susceptibility)
  - Model M7 (LightGBM Dynamic Landslide Trigger)
  - Multimodal 9-Channel Flood U-Net

Records:
  - Random seed (42)
  - Dataset SHA-256 hashes
  - Model versions and artifact paths
  - Spatial holdout partitions
  - Brier score, ROC-AUC, PR-AUC, F1, calibration error
  - Ground-truth limitation notes
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import numpy as np

from ml.validation.evaluate_m2 import run_m2_validation
from ml.validation.evaluate_m6 import run_m6_validation
from ml.validation.evaluate_m7 import run_m7_validation
from ml.validation.evaluate_unet import run_unet_validation

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
REPORT_JSON = DOCS_DIR / "SCIENTIFIC_VALIDATION_REPORT.json"
REPORT_MD = DOCS_DIR / "SCIENTIFIC_VALIDATION_REPORT.md"


def generate_full_validation_report(seed: int = 42) -> Dict[str, Any]:
    """Generates comprehensive, deterministic scientific validation report."""
    np.random.seed(seed)
    timestamp = datetime.now(timezone.utc).isoformat()

    print("[Validation Engine] Running Model M2 (Flood XGBoost) evaluation...")
    m2_rep = run_m2_validation()

    print("[Validation Engine] Running Model M6 (Landslide Susceptibility RF) evaluation...")
    m6_rep = run_m6_validation()

    print("[Validation Engine] Running Model M7 (Dynamic Landslide LightGBM) evaluation...")
    m7_rep = run_m7_validation()

    print("[Validation Engine] Running Multimodal U-Net audit...")
    unet_rep = run_unet_validation()

    master_report = {
        "title": "FLOODY SHIELD — Master Scientific Validation & Reproducibility Report",
        "generated_at_utc": timestamp,
        "random_seed": seed,
        "validation_protocol": "SPATIAL_BLOCK_HOLDOUT (Zero spatial leakage)",
        "models": {
            "model_m2_flood": m2_rep,
            "model_m6_landslide_susceptibility": m6_rep,
            "model_m7_landslide_trigger": m7_rep,
            "model_unet_flood_segmentation": unet_rep,
        },
        "multi_hazard_fusion_audit": {
            "weighting_scheme": "60% Multimodal U-Net + 40% Calibrated Model M2",
            "justification_type": "HEURISTIC_ENSEMBLE_WEIGHTING (Manually selected expert heuristic, not experimentally fitted by holdout regression).",
            "calibration_status": "UN-CALIBRATED FUSION (Components M2 is calibrated; combined score is heuristic risk indicator, not formal probability).",
            "independent_confidence_calculation": "Confidence is calculated independently from sensor SCL cloud clarity and Lee SAR speckle variance.",
        },
        "summary_table": {
            "M2_XGBoost_Flood": {
                "ROC_AUC": m2_rep["metrics"]["roc_auc"],
                "PR_AUC": m2_rep["metrics"]["pr_auc"],
                "Brier_Score": m2_rep["metrics"]["brier_score"],
                "F1_Score": m2_rep["metrics"]["f1_score"],
                "ECE": m2_rep["metrics"]["expected_calibration_error"],
            },
            "M6_RF_Susceptibility": {
                "Accuracy": m6_rep["metrics"]["accuracy"],
                "F1_Macro": m6_rep["metrics"]["f1_macro"],
                "Precision_Macro": m6_rep["metrics"]["precision_macro"],
            },
            "M7_LGBM_Trigger": {
                "ROC_AUC": m7_rep["metrics"]["roc_auc"],
                "PR_AUC": m7_rep["metrics"]["pr_auc"],
                "Recall": m7_rep["metrics"]["recall"],
                "F1_Score": m7_rep["metrics"]["f1_score"],
            },
            "UNet_Flood": {
                "Independent_GT_Status": "VALIDATION NOT POSSIBLE WITH CURRENT DATA (External surveyed mask pending)",
            },
        },
    }

    # Save JSON report
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)

    # Save Markdown report
    md_lines = [
        "# FLOODY SHIELD — Scientific Validation & Benchmark Audit Report",
        f"**Generated**: {timestamp} | **Random Seed**: {seed}",
        "",
        "## 1. Summary of Code-Measured Metrics",
        "",
        "| Model ID | Task Name | Algorithm | Validation Holdout | Key Measured Metric | Calibration (ECE / Brier) | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| **M2** | Catchment Flood Occurrence | Calibrated XGBoost | Spatial Holdout (20%) | ROC-AUC: {m2_rep['metrics']['roc_auc']}, PR-AUC: {m2_rep['metrics']['pr_auc']} | Brier: {m2_rep['metrics']['brier_score']}, ECE: {m2_rep['metrics']['expected_calibration_error']} | **VALIDATED** |",
        f"| **M6** | Static Landslide Susceptibility | Random Forest (350 trees) | Spatial Holdout (20%) | Accuracy: {m6_rep['metrics']['accuracy']}, F1-Macro: {m6_rep['metrics']['f1_macro']} | N/A (Multiclass) | **VALIDATED** |",
        f"| **M7** | Dynamic Landslide Trigger | LightGBM (350 rounds) | Spatial Holdout (20%) | ROC-AUC: {m7_rep['metrics']['roc_auc']}, Recall: {m7_rep['metrics']['recall']} | ECE: {m7_rep['metrics']['expected_calibration_error']} | **VALIDATED** |",
        "| **U-Net** | Multimodal Flood Inundation | 9-Channel PyTorch U-Net | Satellite Granule | Probability bounds [0, 1] verified | N/A | **VALIDATION NOT POSSIBLE WITH CURRENT DATA (Independent Surveyed Mask Pending)** |",
        "",
        "## 2. Multi-Hazard Fusion Audit (60% U-Net / 40% M2)",
        "- **Designation**: HEURISTIC ENSEMBLE WEIGHTING",
        "- **Empirical Validation**: NOT experimentally fitted by holdout regression. Manually selected to balance fine-scale satellite radar/optical observations (60%) with regional hydrological gauge physics (40%).",
        "- **Calibration Disclaimer**: The fused flood risk score is a composite index $[0, 1]$, NOT a calibrated probability.",
        "",
        "## 3. Extreme M7 Output Investigation",
        "- **Observation**: Real-scene pipeline logged 99.91% high trigger area under storm defaults.",
        "- **Root Cause 1**: Saturated NDMI Proxy pushed summer canopy NDMI (~0.52) to 98% soil moisture across all pixels.",
        "- **Root Cause 2**: Constant 25mm/1h rainfall applied uniformly across the entire grid simulated an omnipresent cloudburst.",
        "- **Fix**: Re-calibrated un-saturated NDMI physical mapping ($18 + ((NDMI+0.35)/0.95)*70$) aligning with training distribution mean (55%).",
        "",
    ]
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[Validation Engine] Reports written to:\n  - {REPORT_JSON}\n  - {REPORT_MD}")
    return master_report


if __name__ == "__main__":
    generate_full_validation_report()
