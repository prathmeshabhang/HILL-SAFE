"""
ml/flood/m11_flood_depth/preprocessing.py
=========================================
Input sanitation, quality auditing, and missing data handling for Model M11.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.data_quality.validator import DataQualityValidator


class M11Preprocessor:
    def __init__(self):
        self.validator = DataQualityValidator()

    def process_and_audit(
        self,
        features: Dict[str, Any],
        sample_id: str = "REACH_SAMPLE_01",
    ) -> Tuple[Dict[str, float], float, str, List[str]]:
        """
        Audits data quality and cleans hydrological/terrain features.
        Returns: (sanitized_features, quality_score, applicability, flags)
        """
        report = self.validator.validate_record(sample_id=sample_id, features=features)
        flags = [f.message for f in report.flags]

        cleaned: Dict[str, float] = {}
        for k, v in features.items():
            if isinstance(v, (int, float)):
                if np.isnan(v):
                    cleaned[k] = 0.0
                else:
                    cleaned[k] = float(v)

        # Force positive HAND and river stage
        if "hand_m" in cleaned:
            cleaned["hand_m"] = max(0.0, cleaned["hand_m"])
        if "source_stage_m" in cleaned:
            cleaned["source_stage_m"] = max(0.0, cleaned["source_stage_m"])
        if "source_discharge_m3s" in cleaned:
            cleaned["source_discharge_m3s"] = max(0.0, cleaned["source_discharge_m3s"])

        status_str = "VALID" if report.is_usable else "DEGRADED"
        return cleaned, report.quality_score, status_str, flags
