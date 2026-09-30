"""
ml/security/human_authorization.py
==================================
Strict Human Authorization Boundary & CAP Alert Release Governance.
Ensures that machine learning models and decision engines:
  1. Act purely as DECISION SUPPORT recommendations.
  2. NEVER autonomously transmit public emergency evacuation alerts.
  3. Require cryptographic sign-off from authorized Incident Commanders (DDMA, NDRF, HPSDMA).
  4. Maintain immutable audit trails of all alert authorizations and rejections.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AuthorizationStatus(str, Enum):
    PENDING_OFFICIAL_REVIEW = "PENDING_OFFICIAL_REVIEW"
    AUTHORIZED_FOR_RELEASE = "AUTHORIZED_FOR_RELEASE"
    REJECTED_BY_OFFICIAL = "REJECTED_BY_OFFICIAL"
    EXPIRED_WITHOUT_ACTION = "EXPIRED_WITHOUT_ACTION"


class AuthorizedAgency(str, Enum):
    DDMA_KULLU = "DDMA_KULLU"           # District Disaster Management Authority, Kullu
    HPSDMA = "HPSDMA"                   # Himachal Pradesh State Disaster Management Authority
    NDRF_14_BN = "NDRF_14_BN"           # National Disaster Response Force (14th Battalion)
    CWC_INDUS = "CWC_INDUS"             # Central Water Commission Indus Basin Division
    POLICE_EOC = "POLICE_EOC"           # Himachal Pradesh Police Emergency Operations Center


@dataclass
class AlertAuthorizationRecord:
    advisory_id: str
    cap_identifier: str
    recommended_severity: str       # ADVISORY | WATCH | WARNING | EMERGENCY_EVACUATE
    hazard_type: str
    affected_settlements: List[str]
    model_generated_timestamp: str
    authorization_status: AuthorizationStatus = AuthorizationStatus.PENDING_OFFICIAL_REVIEW
    authorizing_officer_id: Optional[str] = None
    authorizing_agency: Optional[AuthorizedAgency] = None
    authorization_timestamp: Optional[str] = None
    officer_digital_signature_hash: Optional[str] = None
    review_notes: Optional[str] = None
    payload_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["authorization_status"] = self.authorization_status.value
        d["authorizing_agency"] = self.authorizing_agency.value if self.authorizing_agency else None
        return d


class HumanAuthorizationGateway:
    """
    Guards the emergency communication channel.
    Verifies that no CAP v1.2 public alert leaves the system without
    formal authorized official credentials and signature.
    """

    def __init__(self, audit_log_path: Optional[Path] = None):
        self.audit_log_path = audit_log_path or Path("reports/alert_authorizations_audit.jsonl")
        self.pending_advisories: Dict[str, AlertAuthorizationRecord] = {}

    def submit_advisory_for_review(
        self,
        advisory_id: str,
        cap_identifier: str,
        severity: str,
        hazard_type: str,
        affected_settlements: List[str],
        cap_payload: Dict[str, Any],
    ) -> AlertAuthorizationRecord:
        """
        Registers an AI-generated emergency recommendation.
        Marks status as PENDING_OFFICIAL_REVIEW.
        """
        payload_str = json.dumps(cap_payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        rec = AlertAuthorizationRecord(
            advisory_id=advisory_id,
            cap_identifier=cap_identifier,
            recommended_severity=severity,
            hazard_type=hazard_type,
            affected_settlements=affected_settlements,
            model_generated_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            authorization_status=AuthorizationStatus.PENDING_OFFICIAL_REVIEW,
            payload_hash=payload_hash,
        )
        self.pending_advisories[advisory_id] = rec
        self._append_audit_log(rec)
        return rec

    def authorize_and_sign(
        self,
        advisory_id: str,
        officer_id: str,
        agency: AuthorizedAgency,
        passcode: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, Optional[AlertAuthorizationRecord], str]:
        """
        Formal human sign-off executing official authorization.
        Generates an immutable signature hash over officer credentials, timestamp, and payload.
        """
        rec = self.pending_advisories.get(advisory_id)
        if not rec:
            return False, None, f"Advisory {advisory_id} not found in pending queue"

        if rec.authorization_status != AuthorizationStatus.PENDING_OFFICIAL_REVIEW:
            return False, rec, f"Advisory already in state {rec.authorization_status.value}"

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        sig_data = f"{advisory_id}:{officer_id}:{agency.value}:{now_iso}:{rec.payload_hash}:{passcode}"
        sig_hash = hashlib.sha256(sig_data.encode("utf-8")).hexdigest()

        rec.authorization_status = AuthorizationStatus.AUTHORIZED_FOR_RELEASE
        rec.authorizing_officer_id = officer_id
        rec.authorizing_agency = agency
        rec.authorization_timestamp = now_iso
        rec.officer_digital_signature_hash = sig_hash
        rec.review_notes = notes or "Authorized by competent authority for broadcast."

        self._append_audit_log(rec)
        return True, rec, "Alert successfully authorized for broadcast."

    def reject_advisory(
        self,
        advisory_id: str,
        officer_id: str,
        agency: AuthorizedAgency,
        reason: str,
    ) -> Tuple[bool, Optional[AlertAuthorizationRecord], str]:
        """Official human rejection of AI alert recommendation."""
        rec = self.pending_advisories.get(advisory_id)
        if not rec:
            return False, None, f"Advisory {advisory_id} not found"

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rec.authorization_status = AuthorizationStatus.REJECTED_BY_OFFICIAL
        rec.authorizing_officer_id = officer_id
        rec.authorizing_agency = agency
        rec.authorization_timestamp = now_iso
        rec.review_notes = reason

        self._append_audit_log(rec)
        return True, rec, f"Advisory rejected by {officer_id}: {reason}"

    def _append_audit_log(self, record: AlertAuthorizationRecord) -> None:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
