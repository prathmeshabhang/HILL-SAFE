"""
ml/flood/m10_water_level/preprocessing.py
=========================================
Input sanitation, quality auditing, and missing data handling for Model M10.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.data_quality.validator import DataQualityValidator


class M10Preprocessor:
    def __init__(self):
        self.validator = DataQualityValidator()

    def process_and_audit(
        self,
        features: Dict[str, Any],
        station_id: str = "STATION_UNKNOWN",
    ) -> Tuple[Dict[str, float], float, str, List[str]]:
        """
        Audits data quality and cleans hydrological features.
        Returns: (sanitized_features, quality_score, applicability, flags)
        """
        report = self.validator.validate_record(sample_id=station_id, features=features)
        flags = [f.message for f in report.flags]

        cleaned: Dict[str, float] = {}
        for k, v in features.items():
            if isinstance(v, (int, float)):
                if np.isnan(v):
                    cleaned[k] = 0.0
                else:
                    cleaned[k] = float(v)

        # Force positive water levels
        if "water_level_m" in cleaned:
            cleaned["water_level_m"] = max(0.0, cleaned["water_level_m"])
        if "current_stage_m" in cleaned:
            cleaned["current_stage_m"] = max(0.0, cleaned["current_stage_m"])

        status_str = "VALID" if report.is_usable else "DEGRADED"
        return cleaned, report.quality_score, status_str, flags
