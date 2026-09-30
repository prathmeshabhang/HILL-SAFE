"""
backend/app/services/alerts/hyperlocal_connector.py
===================================================
Hyperlocal Risk-to-Alert Lifecycle Connector for FLOODY SHIELD (Phase 04D).
Connects Ward and Gram Panchayat spatial risk units (Phase 04C) directly
into the statutory Early Warning Alert Lifecycle, CAP rendering, and Dispatcher.

Enforces:
1. Strict Human Authorization Gate (NO autonomous public broadcasts).
2. Phase 03 Provenance Isolation (operational vs non-operational/simulation/replay).
3. Grounded Actionable Semantics (WHAT, WHERE, WHEN, WHY, HOW SERIOUS, CONFIDENCE, WHAT TO DO).
4. Evidence-Grounded Trend Tracking (RISING, FALLING, STABLE, INSUFFICIENT_HISTORY).
5. Deduplication and Escalation Controls.
6. Fail-soft multi-channel notification dispatch.
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.core.provenance import (
    DataMode,
    OPERATIONAL_MODES,
    is_operational_provenance,
)
from backend.app.database.models.alert import AlertDispatchModel, AlertAcknowledgementModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.services.alerts.lifecycle_service import alert_lifecycle_service
from backend.app.services.notifications.dispatcher import notification_dispatcher

logger = get_logger("floody.alerts.hyperlocal_connector")


SEVERITY_RANK: Dict[str, int] = {
    "Minor": 1,
    "Moderate": 2,
    "Severe": 3,
    "Extreme": 4,
}


class HyperlocalAlertConnector:
    """
    Bridges Hyperlocal Spatial Risk Evaluations into Statutory Early Warning Alert Drafts.
    """

    # In-memory history cache to track hazard evolution across cycles for genuine trends
    _RECENT_RISK_SCORES: Dict[str, float] = {}

    @classmethod
    def clear_history(cls) -> None:
        """Clears the history cache (used in tests and state resets)."""
        cls._RECENT_RISK_SCORES.clear()

    @classmethod
    def compute_trend(cls, admin_id: str, current_score: float) -> str:
        """
        Computes genuine hazard trend based on actual historical comparison.
        Returns: RISING, FALLING, STABLE, or INSUFFICIENT_HISTORY.
        Never manufactures a trend from a single uncompared observation.
        """
        if admin_id not in cls._RECENT_RISK_SCORES:
            return "INSUFFICIENT_HISTORY"

        prev = cls._RECENT_RISK_SCORES[admin_id]
        diff = current_score - prev
        if diff > 0.04:
            return "RISING"
        elif diff < -0.04:
            return "FALLING"
        else:
            return "STABLE"

    def evaluate_candidate(
        self,
        unit: Dict[str, Any],
        previous_score: Optional[float] = None,
        risk_state_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates a single Ward or Gram Panchayat hyperlocal risk dict
        and generates an authoritative Alert Candidate contract.
        """
        admin_id = unit["admin_id"]
        name = unit.get("name", admin_id)
        unit_type = unit.get("unit_type", "ADMIN_UNIT")
        area_km2 = unit.get("area_km2", 10.0)
        centroid = unit.get("centroid", [77.18, 32.24])

        hazard_dict = unit.get("current_hazard", {})
        max_hazard = float(hazard_dict.get("max_hazard_score", 0.50))
        mean_hazard = float(hazard_dict.get("mean_hazard_score", 0.40))
        dominant_hazard = hazard_dict.get("dominant_hazard", "FLOOD")
        risk_level = hazard_dict.get("risk_level", "MODERATE")
        cascade_state = unit.get("cascade_state", "NOT_ESTABLISHED")

        exposure = unit.get("exposure", {})
        perm_pop = int(exposure.get("permanent_population", 1500))
        tour_pop = int(exposure.get("tourist_population", 0))
        total_pop = int(exposure.get("total_estimated_population", perm_pop + tour_pop))
        affected_pop = int(exposure.get("affected_population", 50))
        vulnerability = float(exposure.get("vulnerability_index", 0.50))
        infra_list = exposure.get("exposed_infrastructure", [])

        raw_conf = float(unit.get("confidence", 0.85))
        freshness_sec = float(unit.get("data_freshness_seconds", 120.0))
        timestamp = unit.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        provenance = unit.get("provenance", DataMode.REAL_FIELD_OBSERVATION.value)
        is_op = is_operational_provenance(provenance)

        # 1. Map Severity
        if risk_level == "CRITICAL" or cascade_state in ("CONFIRMED_BY_EVIDENCE", "SUSPECTED_BOTTLENECK"):
            severity = "Extreme"
        elif risk_level == "HIGH" or max_hazard >= 0.55:
            severity = "Severe"
        elif risk_level == "MODERATE" or max_hazard >= 0.30:
            severity = "Moderate"
        else:
            severity = "Minor"

        # 2. Map Urgency
        if severity == "Extreme" or dominant_hazard == "COMPOUND_CASCADE":
            urgency = "Immediate"
        elif severity == "Severe":
            urgency = "Expected"
        else:
            urgency = "Future"

        # 3. Compute Genuine Trend
        if previous_score is not None:
            diff = max_hazard - previous_score
            if diff > 0.04:
                trend = "RISING"
            elif diff < -0.04:
                trend = "FALLING"
            else:
                trend = "STABLE"
        else:
            trend = self.compute_trend(admin_id, max_hazard)

        # 4. Calibrate Confidence against source freshness and evidence
        freshness_discount = 1.0 if freshness_sec <= 300.0 else (0.90 if freshness_sec <= 900.0 else 0.75)
        evidence_boost = 0.05 if cascade_state in ("CONFIRMED_BY_EVIDENCE", "SUSPECTED_BOTTLENECK") else 0.0
        calibrated_conf = min(0.98, max(0.50, round((raw_conf * freshness_discount) + evidence_boost, 2)))

        # 5. Certainty
        if cascade_state == "CONFIRMED_BY_EVIDENCE" or (calibrated_conf >= 0.88 and is_op):
            certainty = "Observed"
        elif calibrated_conf >= 0.70:
            certainty = "Likely"
        else:
            certainty = "Possible"

        # 6. Build Evidence Metadata
        infra_names = [i["name"] for i in infra_list[:4]]
        infra_summary = f"{len(infra_list)} critical assets ({', '.join(infra_names)})" if infra_list else "No arterial assets directly bisected"
        evidence_summary = (
            f"Physical kinematic runoff & terrain AI. River obstruction: {cascade_state}. "
            f"Peak hazard: {max_hazard:.2f}, Vulnerability: {vulnerability:.2f}."
        )

        evidence_metadata = {
            "dominant_hazard": dominant_hazard,
            "max_hazard_score": max_hazard,
            "mean_hazard_score": mean_hazard,
            "cascade_state": cascade_state,
            "freshness_seconds": freshness_sec,
            "affected_population": affected_pop,
            "total_estimated_population": total_pop,
            "vulnerability_index": vulnerability,
            "exposed_infrastructure_count": len(infra_list),
            "exposed_infrastructure_names": infra_names,
            "trend": trend,
            "calibrated_confidence": calibrated_conf,
            "data_mode": provenance,
            "is_operational": is_op,
        }

        # 7. Actionable Alert Semantics (WHAT, WHERE, WHEN, WHY, HOW SERIOUS, CONFIDENCE, WHAT TO DO)
        if dominant_hazard == "COMPOUND_CASCADE":
            headline = f"[EMERGENCY WARNING] River Outburst & Flash Flood Threat for {name}"
            evacuation_instruction = (
                f"IMMEDIATE EVACUATION ORDER: Upstream river gorge blockage detected. "
                f"All residents and visitors in {name} must move to designated safe high ground immediately. "
                f"Do not attempt to cross Beas bridges or low-lying NH-3 sections."
            )
            protective_action = "EVACUATE_IMMEDIATELY_HIGH_GROUND"
        elif dominant_hazard == "LANDSLIDE":
            headline = f"[HAZARD ALERT] Severe Landslide & Debris Flow Risk for {name}"
            evacuation_instruction = (
                f"EVACUATION ADVISORY: Move away from steep hill-slopes, cut-slopes, and unreinforced buildings. "
                f"Assemble at designated civil defense points along arterial roads."
            )
            protective_action = "STAY_CLEAR_OF_SLOPES_AND_CUTS"
        else:
            headline = f"[FLOOD WARNING] Flash Flood Inundation Alert for {name}"
            evacuation_instruction = (
                f"FLOOD ADVISORY: Inundation threat along river corridor. "
                f"Stay clear of water channels, drainage nullahs, and culverts. Secure essential items."
            )
            protective_action = "MOVE_ABOVE_FLOOD_LEVEL"

        description = (
            f"WHAT: {dominant_hazard} emergency threat affecting {name} ({unit_type}).\n"
            f"WHERE: {name}, Upper Beas Catchment (Centroid: {centroid[1]:.4f}N, {centroid[0]:.4f}E, Area: {area_km2} sq km).\n"
            f"WHEN: Evaluated at {timestamp} (Sensor freshness: {freshness_sec:.0f}s).\n"
            f"WHY: {evidence_summary} Exposed infrastructure: {infra_summary}.\n"
            f"HOW SERIOUS: Risk Level: {risk_level} (Hazard Score: {max_hazard:.2f}, Severity: {severity}). "
            f"Trend: {trend}. Estimated Affected Population: ~{affected_pop:,} residents/visitors.\n"
            f"CONFIDENCE: {calibrated_conf*100:.0f}% based on terrain routing, satellite feeds, and hydrologic modeling."
        )

        area_desc = f"{name} ({admin_id}), Upper Beas River Basin, Kullu, Himachal Pradesh"
        geom = unit.get("geometry")
        polygon_geojson = json.dumps(geom) if geom else None

        return {
            "administrative_unit": {
                "admin_id": admin_id,
                "name": name,
                "unit_type": unit_type,
            },
            "location": centroid,
            "hazard": dominant_hazard,
            "severity": severity,
            "urgency": urgency,
            "certainty": certainty,
            "trend": trend,
            "confidence": calibrated_conf,
            "freshness": freshness_sec,
            "evidence": evidence_metadata,
            "risk_state_id": risk_state_id,
            "provenance": provenance,
            "is_operational": is_op,
            "headline": headline,
            "description": description,
            "instruction": evacuation_instruction,
            "recommended_action": protective_action,
            "area_desc": area_desc,
            "polygon_geojson": polygon_geojson,
            "timestamp": timestamp,
        }

    def draft_hyperlocal_alert(
        self,
        db: Session,
        candidate: Dict[str, Any],
        incident_id: Optional[str] = None,
    ) -> Tuple[str, Optional[AlertDispatchModel]]:
        """
        Drafts a formal early warning alert from an alert candidate.
        Enforces deduplication, escalation, and provenance isolation.

        Returns: (outcome_status, alert_model_or_none)
        Statuses:
          - DRAFT_CREATED: New alert draft in PENDING_APPROVAL
          - DUPLICATE_SUPPRESSED: Identical active alert already exists
          - ESCALATED: Higher severity detected; escalation update draft created
          - RESOLUTION_RECOMMENDED: Threat subsided; candidate indicates all-clear
          - ROUTINE_MONITORING: Below warning threshold; no alert required
        """
        admin_id = candidate["administrative_unit"]["admin_id"]
        candidate_severity = candidate["severity"]
        candidate_rank = SEVERITY_RANK.get(candidate_severity, 1)

        # 1. Search for existing active or pending alerts for this administrative unit
        existing_alerts = (
            db.query(AlertDispatchModel)
            .filter(
                AlertDispatchModel.area_desc.like(f"%{admin_id}%"),
                AlertDispatchModel.status.in_(["PENDING_APPROVAL", "APPROVED", "DISPATCHED", "ACKNOWLEDGED"]),
            )
            .order_by(AlertDispatchModel.created_at.desc())
            .all()
        )

        active_alert = existing_alerts[0] if existing_alerts else None

        # 2. Evaluate Deduplication & Escalation
        if active_alert:
            existing_rank = SEVERITY_RANK.get(active_alert.severity, 2)

            hazard_upper = candidate["hazard"].upper()
            headline_upper = (active_alert.headline or "").upper()
            desc_upper = (active_alert.description or "").upper()
            hazard_matches = (hazard_upper in headline_upper) or (hazard_upper in desc_upper)

            if candidate_rank == existing_rank and hazard_matches:
                # Suppress spam: identical severity and hazard already pending/active
                logger.info(
                    f"Alert deduplication: Active alert '{active_alert.cap_identifier}' ({active_alert.severity}) "
                    f"already exists for {admin_id}. Suppressing redundant candidate."
                )
                return ("DUPLICATE_SUPPRESSED", active_alert)

            elif candidate_rank > existing_rank:
                # Escalation: hazard severity increased (e.g. Severe -> Extreme)
                escalation_headline = f"[ESCALATION] {candidate['headline']}"
                escalation_desc = (
                    f"*** HAZARD ESCALATION NOTICE ***\n"
                    f"Supersedes prior alert: {active_alert.cap_identifier} (Severity: {active_alert.severity} -> {candidate_severity}).\n\n"
                    f"{candidate['description']}"
                )
                logger.warning(
                    f"Alert escalation: Escalating {admin_id} from {active_alert.severity} to {candidate_severity}."
                )
                draft = alert_lifecycle_service.create_alert_draft(
                    db=db,
                    incident_id=incident_id or active_alert.incident_id,
                    headline=escalation_headline,
                    description=escalation_desc,
                    instruction=candidate["instruction"],
                    area_desc=candidate["area_desc"],
                    severity=candidate_severity,
                    urgency=candidate["urgency"],
                    certainty=candidate["certainty"],
                    polygon_geojson=candidate["polygon_geojson"],
                    data_mode=candidate["provenance"],
                    risk_state_id=candidate.get("risk_state_id"),
                    alert_type="Update",
                )
                return ("ESCALATED", draft)

            elif candidate_rank <= 1 and existing_rank >= 3:
                # Hazard subsided to Minor; flag for commander resolution
                logger.info(f"Hazard subsided for {admin_id}. Recommending resolution of '{active_alert.cap_identifier}'.")
                return ("RESOLUTION_RECOMMENDED", active_alert)

        # 3. New Alert Evaluation (only draft if severity >= Severe or Urgency == Immediate)
        if candidate_rank >= 3 or candidate["urgency"] == "Immediate":
            draft = alert_lifecycle_service.create_alert_draft(
                db=db,
                incident_id=incident_id,
                headline=candidate["headline"],
                description=candidate["description"],
                instruction=candidate["instruction"],
                area_desc=candidate["area_desc"],
                severity=candidate_severity,
                urgency=candidate["urgency"],
                certainty=candidate["certainty"],
                polygon_geojson=candidate["polygon_geojson"],
                data_mode=candidate["provenance"],
                risk_state_id=candidate.get("risk_state_id"),
                alert_type="Alert",
            )
            return ("DRAFT_CREATED", draft)

        return ("ROUTINE_MONITORING", None)

    def process_hyperlocal_risks(
        self,
        db: Session,
        units: List[Dict[str, Any]],
        risk_state_id: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Processes a full batch of 12 hyperlocal administrative units:
        1. Updates historical score cache.
        2. Evaluates candidates.
        3. Drafts alerts where thresholds are breached.
        4. Applies deduplication & escalation.
        """
        results: List[Dict[str, Any]] = []

        for u in units:
            admin_id = u["admin_id"]
            curr_score = float(u.get("current_hazard", {}).get("max_hazard_score", 0.0))

            # Evaluate candidate with current cache
            candidate = self.evaluate_candidate(u, risk_state_id=risk_state_id)

            # Update cache after evaluation for next cycle comparison
            self._RECENT_RISK_SCORES[admin_id] = curr_score

            outcome, alert_model = self.draft_hyperlocal_alert(
                db=db,
                candidate=candidate,
                incident_id=incident_id,
            )

            results.append({
                "admin_id": admin_id,
                "unit_name": candidate["administrative_unit"]["name"],
                "unit_type": candidate["administrative_unit"]["unit_type"],
                "hazard": candidate["hazard"],
                "severity": candidate["severity"],
                "trend": candidate["trend"],
                "confidence": candidate["confidence"],
                "outcome": outcome,
                "alert_id": alert_model.id if alert_model else None,
                "cap_identifier": alert_model.cap_identifier if alert_model else None,
                "status": alert_model.status if alert_model else "NONE",
                "is_operational": candidate["is_operational"],
                "candidate": candidate,
            })

        return results

    def get_ddma_briefing(self, db: Session) -> Dict[str, Any]:
        """
        Compiles authoritative DDMA / EOC operational dashboard briefing:
        - Active dispatches
        - Pending commander sign-offs
        - Administrative risk overview
        - Channel readiness (WebSocket, SMS, IVR, Siren, NDMA Sachet)
        - Non-sensitive tamper-evident audit timeline
        """
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        # 1. Query Active Alerts (Dispatched / Acknowledged)
        active_dispatches = (
            db.query(AlertDispatchModel)
            .filter(AlertDispatchModel.status.in_(["DISPATCHED", "ACKNOWLEDGED"]))
            .order_by(AlertDispatchModel.dispatched_at.desc())
            .limit(20)
            .all()
        )

        # 2. Query Pending Approvals
        pending_drafts = (
            db.query(AlertDispatchModel)
            .filter_by(status="PENDING_APPROVAL")
            .order_by(AlertDispatchModel.created_at.desc())
            .limit(20)
            .all()
        )

        # 3. Query Recent Acknowledgements
        acks = (
            db.query(AlertAcknowledgementModel)
            .order_by(AlertAcknowledgementModel.acknowledged_at.desc())
            .limit(10)
            .all()
        )

        # 4. Non-sensitive Audit Timeline
        recent_audits = (
            db.query(AuditLogModel)
            .filter(AuditLogModel.target_entity_type == "AlertDispatch")
            .order_by(AuditLogModel.timestamp.desc())
            .limit(10)
            .all()
        )

        # 5. Multi-channel readiness
        statuses = notification_dispatcher.get_provider_statuses()

        return {
            "timestamp": now_utc.isoformat(),
            "ddma_station": "Kullu District Emergency Operations Centre (DEOC)",
            "jurisdiction": "Upper Beas River Basin, Himachal Pradesh",
            "active_alerts_count": len(active_dispatches),
            "pending_drafts_count": len(pending_drafts),
            "active_dispatches": [a.to_dict() for a in active_dispatches],
            "pending_drafts": [p.to_dict() for p in pending_drafts],
            "recent_acknowledgements": [ack.to_dict() for ack in acks],
            "channel_readiness": statuses,
            "audit_trail": [
                {
                    "audit_id": a.id,
                    "action": a.action,
                    "actor_role": a.actor_role,
                    "target_entity_id": a.target_entity_id,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                    "entry_hash_prefix": a.entry_hash[:12] if a.entry_hash else None,
                }
                for a in recent_audits
            ],
        }


# Global singleton instance
hyperlocal_alert_connector = HyperlocalAlertConnector()
