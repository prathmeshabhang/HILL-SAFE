"""
registry.py — Authority Field Validation Registry & Ground-Truth Feedback Loop
==============================================================================
Maintains audit trail of field validations, responder inspections, and authoritative
sign-offs, transforming raw candidate detections into validated ground-truth data.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ValidationRecord:
    validation_id: str
    dam_id: str
    status: str              # "Confirmed", "Not a Natural Dam", "False Detection", "Needs Investigation", "Unable to Verify"
    validator_role: str      # e.g., "HPSDMA_District_Officer", "SDRF_Field_Engineer", "Geological_Survey_India"
    timestamp: str
    evidence_type: str       # "DRONE_AERIAL_SURVEY", "GROUND_INSPECTION", "SATELLITE_REANALYSIS"
    notes: str
    photo_url: Optional[str] = None


class ValidationRegistry:
    """In-memory and persistent ground-truth registry for authority validations."""

    def __init__(self):
        self._records: List[ValidationRecord] = []

    def record_validation(
        self,
        dam_id: str,
        status: str,
        validator_role: str,
        notes: str,
        evidence_type: str = "GROUND_INSPECTION",
        photo_url: Optional[str] = None,
    ) -> ValidationRecord:
        allowed_statuses = {
            "Confirmed",
            "Not a Natural Dam",
            "False Detection",
            "Needs Investigation",
            "Unable to Verify",
        }
        if status not in allowed_statuses:
            raise ValueError(f"Status '{status}' not recognized. Allowed: {allowed_statuses}")

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rec_id = f"VAL-{now_iso[:10]}-{uuid.uuid4().hex[:6].upper()}"

        rec = ValidationRecord(
            validation_id=rec_id,
            dam_id=dam_id,
            status=status,
            validator_role=validator_role,
            timestamp=now_iso,
            evidence_type=evidence_type,
            notes=notes,
            photo_url=photo_url,
        )
        self._records.append(rec)
        return rec

    def get_validations_for_dam(self, dam_id: str) -> List[ValidationRecord]:
        return [r for r in self._records if r.dam_id == dam_id]

    def get_latest_status(self, dam_id: str) -> Optional[str]:
        dam_records = self.get_validations_for_dam(dam_id)
        if dam_records:
            return dam_records[-1].status
        return None

    def get_all_records(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._records]
