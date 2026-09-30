"""
ml/flood/m12_cascade/preprocessing.py
=====================================
Input auditing and physical sanity checking for Model M12.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ml.data_quality.validator import DataQualityValidator


class M12Preprocessor:
    def __init__(self):
        self.validator = DataQualityValidator()

    def process_and_audit(
        self,
        features: Dict[str, Any],
        dam_id: str = "DAM_CANDIDATE_01",
    ) -> Tuple[Dict[str, Any], float, str, List[str]]:
        """Audits data quality and cleans cascade features."""
        report = self.validator.validate_record(sample_id=dam_id, features=features)
        flags = [f.message for f in report.flags]

        cleaned = dict(features)
        h = float(cleaned.get("dam_height_m", 35.0))
        v = float(cleaned.get("impounded_volume_m3", 8_500_000.0))

        if h < 2.0 or h > 200.0:
            flags.append(f"Dam height {h}m is outside typical landslide dam range [2, 200m]")
        if v < 1000.0:
            flags.append(f"Impounded volume {v}m3 is below minimum threshold")

        cleaned["dam_height_m"] = max(2.0, min(200.0, h))
        cleaned["impounded_volume_m3"] = max(1000.0, v)

        status_str = "VALID" if report.is_usable and len(flags) == 0 else "DEGRADED"
        dq_score = report.quality_score if len(flags) == 0 else min(report.quality_score, 0.75)
        return cleaned, dq_score, status_str, flags
