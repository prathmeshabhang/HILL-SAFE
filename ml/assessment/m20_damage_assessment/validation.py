"""M20 — Validation report.

IMPORTANT: No authoritative external damage ground truth is available
for the Upper Beas corridor.  This file documents that limitation and
provides a reference to how validation would be conducted.

External damage data requirements (not yet available):
    - NDMA/HPSDMA post-disaster field survey records
    - National Remote Sensing Centre (NRSC) damage inventory
    - Revenue department khasra-wise loss reports
    - HP PWD damage assessment post July 2023 disaster

Without these, the model cannot be declared EXTERNALLY_VALIDATED.
"""

from __future__ import annotations

from typing import Any, Dict, List

EXTERNAL_VALIDATION_STATUS = "EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE"

VALIDATION_PLAN = {
    "status": EXTERNAL_VALIDATION_STATUS,
    "required_data": [
        "NDMA/HPSDMA post-disaster field survey (GPS + category)",
        "NRSC multi-temporal damage inventory (Sentinel-2 / Resourcesat-2)",
        "HP PWD damage assessment register (post July 2023)",
        "Revenue khasra-wise agricultural loss (HP Compensation records)",
    ],
    "planned_metrics": [
        "Per-class precision/recall vs field-surveyed labels",
        "Change-detection IoU vs NRSC damage polygon",
        "Asset-level damage-fraction RMSE vs PWD estimates",
    ],
    "note": (
        "Until authoritative ground truth is available, M20 outputs are "
        "labelled CHANGE_DETECTED_ONLY or MODELLED.  Do not report these "
        "as supervised classification results."
    ),
}


def generate_validation_report() -> Dict[str, Any]:
    """Return the current M20 validation status."""
    return {
        "model": "M20_DAMAGE_ASSESSMENT",
        "model_version": "1.0.0",
        "external_validation": EXTERNAL_VALIDATION_STATUS,
        "validation_plan": VALIDATION_PLAN,
        "change_detection_baseline": {
            "description": (
                "NDVI/NDWI/SAR coherence change detection fused with "
                "M10/M11 physics proxies.  No supervised labels."
            ),
            "indicator_thresholds": {
                "ndvi_change_min": 0.10,
                "ndwi_change_min": 0.08,
                "sar_coherence_drop_min": 0.15,
                "flood_depth_minor_m": 0.30,
            },
            "fusion_method": "weighted_average",
            "weights": {
                "physics": 0.40,
                "sar": 0.30,
                "ndwi": 0.18,
                "ndvi": 0.12,
            },
        },
    }
