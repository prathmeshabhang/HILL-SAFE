"""
ml/landslide/m8_deformation/preprocessing.py
============================================
Input sanitation, quality auditing, and missing value imputation for Model M8.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.data_quality.validator import DataQualityValidator


class M8Preprocessor:
    def __init__(self):
        self.validator = DataQualityValidator()

    def process_and_audit(
        self,
        features: Dict[str, Any],
        pixel_id: str = "PIXEL_UNKNOWN",
    ) -> Tuple[Dict[str, float], float, str, List[str]]:
        """
        Audits data quality and cleans deformation features.
        Returns: (sanitized_features, quality_score, applicability, flags)
        """
        report = self.validator.validate_record(sample_id=pixel_id, features=features)
        flags = [f.message for f in report.flags]

        cleaned: Dict[str, float] = {}
        for k, v in features.items():
            if isinstance(v, (int, float)):
                if np.isnan(v):
                    cleaned[k] = 0.0
                else:
                    cleaned[k] = float(v)

        # InSAR coherence sanity
        if "insar_coherence" in cleaned:
            cleaned["insar_coherence"] = float(np.clip(cleaned["insar_coherence"], 0.0, 1.0))

        status_str = "VALID" if report.is_usable else "DEGRADED"
        return cleaned, report.quality_score, status_str, flags
