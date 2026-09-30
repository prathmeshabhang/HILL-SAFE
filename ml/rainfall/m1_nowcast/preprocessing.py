"""
ml/rainfall/m1_nowcast/preprocessing.py
======================================
Input sanitation, quality auditing, and missing data handling for Model M1.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.data_quality.validator import DataQualityValidator


class M1Preprocessor:
    def __init__(self):
        self.validator = DataQualityValidator()

    def process_and_audit(
        self,
        features: Dict[str, Any],
        station_id: str = "STATION_UNKNOWN",
    ) -> Tuple[Dict[str, float], float, str, List[str]]:
        """
        Audits data quality and cleans features.
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

        # Force non-negative rainfall values
        for r_key in ["r_15m", "r_30m", "r_1h", "r_3h", "r_6h", "r_12h", "r_24h", "r_72h", "rolling_intensity_mmh"]:
            if r_key in cleaned:
                cleaned[r_key] = max(0.0, cleaned[r_key])

        status_str = "VALID" if report.is_usable else "DEGRADED"
        return cleaned, report.quality_score, status_str, flags
