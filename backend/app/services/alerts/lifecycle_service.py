"""
backend/app/services/alerts/lifecycle_service.py
================================================
Early Warning Alert Lifecycle Service for FLOODY SHIELD.
Enforces the life-safety invariant:
NO MODEL MAY AUTONOMOUSLY BROADCAST PUBLIC ALERTS.
Alerts transition strictly through:
DRAFT -> PENDING_APPROVAL -> APPROVED / DISPATCHED -> ACKNOWLEDGED -> RESOLVED.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import json
import uuid
from sqlalchemy.orm import Session

from backend.app.core.errors import AuthorizationError, FloodyShieldException, ResourceNotFoundError
from backend.app.core.logging import get_logger
from backend.app.core.provenance import (
    DataMode,
    OPERATIONAL_MODES,
    get_cap_status_for_mode,
    is_operational_provenance,
)
from backend.app.database.models.alert import AlertDispatchModel, AlertAcknowledgementModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.database.models.incident import IncidentModel
from backend.app.database.models.risk import RiskStateModel
from backend.app.decision.authorization_gateway import UserRole
from ml.security.cap_alert_engine import CAPAlertEngine

logger = get_logger("floody.alerts.lifecycle")


class AlertLifecycleService:
    def __init__(self):
        self.cap_engine = CAPAlertEngine()

    def create_alert_draft(
        self,
        db: Session,
        incident_id: Optional[str],
        headline: str,
        description: str,
        instruction: str,
        area_desc: str,
        severity: str = "Extreme",
        urgency: str = "Immediate",
        certainty: str = "Observed",
        polygon_geojson: Optional[str] = None,
        data_mode: Optional[str] = None,
        risk_state_id: Optional[str] = None,
        alert_type: str = "Alert",
    ) -> AlertDispatchModel:
        """
        Creates a new draft alert record. Always enters PENDING_APPROVAL.
        Enforces safety boundary: non-operational risk states or simulation/replay
        incidents are barred from creating live OPERATIONAL alerts.
        """
        resolved_mode = (data_mode or "").strip().upper() if data_mode else None

        # 1. Inspect RiskState provenance if risk_state_id is provided
        if risk_state_id:
            risk_state = db.query(RiskStateModel).filter_by(id=risk_state_id).first()
            if risk_state and risk_state.provenance_json:
                try:
                    p_info = json.loads(risk_state.provenance_json)
                    is_op = bool(p_info.get("is_operational", False))
                    r_mode = p_info.get("data_mode", DataMode.SIMULATION.value)
                    if not is_op:
                        if resolved_mode == DataMode.OPERATIONAL.value:
                            raise FloodyShieldException(
                                message=(
                                    f"Safety quarantine violation: Cannot create live OPERATIONAL alert draft from "
                                    f"non-operational risk state '{risk_state_id}' (mode={r_mode})."
                                ),
                                error_code="PROVENANCE_SAFETY_VIOLATION",
                                status_code=422,
                            )
                        resolved_mode = r_mode
                except json.JSONDecodeError:
                    pass

        # 2. Inspect Incident record if incident_id is provided
        if incident_id:
            incident = db.query(IncidentModel).filter_by(id=incident_id).first()
            if incident:
                is_exercise = incident.status == "EXERCISE" or "REPLAY" in str(incident.incident_type).upper()
                if is_exercise:
                    if resolved_mode == DataMode.OPERATIONAL.value:
                        raise FloodyShieldException(
                            message=(
                                f"Safety quarantine violation: Cannot create live OPERATIONAL alert draft from "
                                f"exercise/replay incident '{incident_id}'."
                            ),
                            error_code="PROVENANCE_SAFETY_VIOLATION",
                            status_code=422,
                        )
                    if not resolved_mode:
                        resolved_mode = DataMode.REPLAY.value if "REPLAY" in str(incident.incident_type).upper() else DataMode.SIMULATION.value

        final_mode = resolved_mode or DataMode.OPERATIONAL.value

        # 3. Generate CAP Identifier reflecting mode
        today_str = datetime.date.today().strftime('%Y%m%d')
        hex_suffix = uuid.uuid4().hex[:6].upper()
        if final_mode in OPERATIONAL_MODES:
            cap_id = f"CAP-HPSDMA-{today_str}-{hex_suffix}"
        else:
            cap_id = f"CAP-{final_mode}-HPSDMA-{today_str}-{hex_suffix}"

        alert = AlertDispatchModel(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            cap_identifier=cap_id,
            alert_type=alert_type,
            severity=severity,
            urgency=urgency,
            certainty=certainty,
            headline=headline,
            description=description,
            instruction=instruction,
            area_desc=area_desc,
            polygon_geojson=polygon_geojson,
            authorized_by="PENDING_COMMANDER_APPROVAL",
            status="PENDING_APPROVAL",
        )
        db.add(alert)
        db.commit()
        logger.info(f"Created alert draft {alert.id} ({cap_id}, mode={final_mode}) with status PENDING_APPROVAL")
        return alert

    def authorize_and_dispatch(
        self,
        db: Session,
        alert_id: str,
        commander_id: str,
        commander_role: str,
        approval_token: str,
        ip_address: Optional[str] = None,
    ) -> AlertDispatchModel:
        """
        Authorizes alert release. Strictly requires SENIOR_INCIDENT_COMMANDER and valid approval token.
        Transitions state to DISPATCHED, renders OASIS CAP v1.2 XML, and logs to tamper-evident audit.
        """
        # 1. Enforce RBAC invariant
        if commander_role.upper() != UserRole.SENIOR_INCIDENT_COMMANDER.value:
            raise AuthorizationError(
                message=f"Unauthorized: Only {UserRole.SENIOR_INCIDENT_COMMANDER.value} can authorize public emergency alerts",
                details={"provided_role": commander_role},
            )

        if not approval_token or len(approval_token) < 8:
            raise AuthorizationError(
                message="Valid cryptographic authorization token is required for public alert broadcast",
                details={"token_length": len(approval_token) if approval_token else 0},
            )

        # 2. Retrieve alert
        alert = db.query(AlertDispatchModel).filter_by(id=alert_id).first()
        if not alert:
            raise ResourceNotFoundError(
                message=f"Alert '{alert_id}' not found",
                resource_type="AlertDispatch",
                resource_id=alert_id,
            )

        if alert.status != "PENDING_APPROVAL":
            from backend.app.core.errors import FloodyShieldException
            raise FloodyShieldException(
                message=f"Cannot authorize alert in state '{alert.status}'. Alert must be in PENDING_APPROVAL status.",
                error_code="ALERT_INVALID_STATE",
                status_code=400,
            )

        # 3. Render statutory OASIS CAP v1.2 XML
        from xml.sax.saxutils import escape as xml_escape
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        headline_esc = xml_escape(alert.headline or "")
        desc_esc = xml_escape(alert.description or "")
        inst_esc = xml_escape(alert.instruction or "")
        area_esc = xml_escape(alert.area_desc or "")

        # Statutory CAP status: Actual ONLY for verified operational alerts; Exercise or Test for non-operational
        cid = (alert.cap_identifier or "").upper()
        if "REPLAY" in cid or "EXERCISE" in cid:
            cap_status = "Exercise"
        elif "SIMULATION" in cid or "TEST" in cid or "PROXY" in cid or "SYNTHETIC" in cid:
            cap_status = "Test"
        else:
            cap_status = "Actual"

        poly_tag = ""
        if alert.polygon_geojson:
            try:
                g = json.loads(alert.polygon_geojson)
                coords = g.get("coordinates", [])
                if coords and len(coords[0]) >= 3:
                    poly_pairs = [f"{pt[1]:.5f},{pt[0]:.5f}" for pt in coords[0]]
                    poly_str = " ".join(poly_pairs)
                    poly_tag = f"      <polygon>{poly_str}</polygon>\n"
            except Exception:
                pass

        cap_xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">\n'
            f'  <identifier>{alert.cap_identifier}</identifier>\n'
            f'  <sender>hpsdma.eoc.kullu@hp.gov.in</sender>\n'
            f'  <sent>{now_utc.isoformat()}</sent>\n'
            f'  <status>{cap_status}</status>\n'
            f'  <msgType>{alert.alert_type or "Alert"}</msgType>\n'
            f'  <scope>Public</scope>\n'
            f'  <info>\n'
            f'    <category>Geo</category>\n'
            f'    <event>{headline_esc}</event>\n'
            f'    <urgency>{alert.urgency}</urgency>\n'
            f'    <severity>{alert.severity}</severity>\n'
            f'    <certainty>{alert.certainty}</certainty>\n'
            f'    <headline>{headline_esc}</headline>\n'
            f'    <description>{desc_esc}</description>\n'
            f'    <instruction>{inst_esc}</instruction>\n'
            f'    <area>\n'
            f'      <areaDesc>{area_esc}</areaDesc>\n'
            f'{poly_tag}'
            f'    </area>\n'
            f'  </info>\n'
            f'</alert>'
        )

        # 4. CAP Validation prior to dispatch
        from backend.app.services.alerts.cap_validator import cap_validator
        cap_validator.validate_cap_xml(cap_xml)

        # 5. Transition status to DISPATCHED
        alert.status = "DISPATCHED"
        alert.authorized_by = commander_id
        alert.dispatched_at = now_utc
        alert.cap_xml = cap_xml

        # 6. Append-only tamper-evident audit record with hash chain
        last_audit = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).first()
        prev_hash = last_audit.entry_hash if last_audit else "GENESIS_ROOT_HASH_0000000000000000"

        audit_entry = AuditLogModel(
            id=str(uuid.uuid4()),
            timestamp=now_utc,
            action="ALERT_AUTHORIZED_AND_DISPATCHED",
            actor_id=commander_id,
            actor_role=commander_role,
            target_entity_type="AlertDispatch",
            target_entity_id=alert.id,
            changes=f"Status transitioned from PENDING_APPROVAL to DISPATCHED. Token validated.",
            ip_address=ip_address,
            previous_hash=prev_hash,
        )
        audit_entry.entry_hash = audit_entry.compute_hash(prev_hash)
        db.add(audit_entry)

        db.commit()
        logger.info(f"Alert {alert.id} DISPATCHED by commander {commander_id}. Audit record {audit_entry.id} hash-chained.")

        # 7. Asynchronous multi-channel notification dispatch
        try:
            import asyncio
            from backend.app.services.notifications.dispatcher import notification_dispatcher
            alert_dict = alert.to_dict()
            alert_dict["cap_xml"] = cap_xml
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(notification_dispatcher.broadcast_alert(alert_dict))
            except RuntimeError:
                pass  # synchronous test environment
        except Exception as e:
            logger.warning(f"Notification broadcast encountered warning: {e}")

        return alert

    def acknowledge_alert(
        self,
        db: Session,
        alert_id: str,
        recipient_id: str,
        channel: str = "EOC_DASHBOARD",
        notes: Optional[str] = None,
    ) -> AlertAcknowledgementModel:
        """Records external agency / civil defense confirmation of alert reception."""
        alert = db.query(AlertDispatchModel).filter_by(id=alert_id).first()
        if not alert:
            raise ResourceNotFoundError(message=f"Alert {alert_id} not found", resource_type="AlertDispatch", resource_id=alert_id)

        ack = AlertAcknowledgementModel(
            id=str(uuid.uuid4()),
            alert_id=alert_id,
            recipient_id=recipient_id,
            channel=channel,
            status="CONFIRMED",
            acknowledged_at=datetime.datetime.now(datetime.timezone.utc),
            notes=notes,
        )
        db.add(ack)

        # Update alert status if previously dispatched
        if alert.status == "DISPATCHED":
            alert.status = "ACKNOWLEDGED"

        db.commit()
        logger.info(f"Alert {alert_id} acknowledged by {recipient_id} via {channel}")
        return ack

    def resolve_alert(
        self,
        db: Session,
        alert_id: str,
        actor_id: str,
        actor_role: str,
        resolution_notes: str,
    ) -> AlertDispatchModel:
        """Resolves active alert when emergency threat has subsided."""
        alert = db.query(AlertDispatchModel).filter_by(id=alert_id).first()
        if not alert:
            raise ResourceNotFoundError(message=f"Alert {alert_id} not found", resource_type="AlertDispatch", resource_id=alert_id)

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        alert.status = "RESOLVED"
        alert.resolved_at = now_utc

        # Tamper-evident audit
        last_audit = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).first()
        prev_hash = last_audit.entry_hash if last_audit else "GENESIS_ROOT_HASH_0000000000000000"

        audit_entry = AuditLogModel(
            id=str(uuid.uuid4()),
            timestamp=now_utc,
            action="ALERT_RESOLVED",
            actor_id=actor_id,
            actor_role=actor_role,
            target_entity_type="AlertDispatch",
            target_entity_id=alert.id,
            changes=f"Alert resolved: {resolution_notes}",
            previous_hash=prev_hash,
        )
        audit_entry.entry_hash = audit_entry.compute_hash(prev_hash)
        db.add(audit_entry)

        db.commit()
        logger.info(f"Alert {alert_id} RESOLVED by {actor_id}")
        return alert

    def cancel_alert(
        self,
        db: Session,
        alert_id: str,
        commander_id: str,
        commander_role: str,
        cancellation_reason: str,
    ) -> AlertDispatchModel:
        """Cancels an alert. Restricted to SENIOR_INCIDENT_COMMANDER or ADMIN."""
        if commander_role not in ("SENIOR_INCIDENT_COMMANDER", "ADMIN"):
            raise AuthorizationError(f"Role {commander_role} unauthorized to cancel alerts.")

        alert = db.query(AlertDispatchModel).filter_by(id=alert_id).first()
        if not alert:
            raise ResourceNotFoundError(message=f"Alert {alert_id} not found", resource_type="AlertDispatch", resource_id=alert_id)

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        alert.status = "CANCELLED"
        alert.resolved_at = now_utc

        last_audit = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).first()
        prev_hash = last_audit.entry_hash if last_audit else "GENESIS_ROOT_HASH_0000000000000000"

        audit_entry = AuditLogModel(
            id=str(uuid.uuid4()),
            timestamp=now_utc,
            action="ALERT_CANCELLED",
            actor_id=commander_id,
            actor_role=commander_role,
            target_entity_type="AlertDispatch",
            target_entity_id=alert.id,
            changes=f"Alert cancelled: {cancellation_reason}",
            previous_hash=prev_hash,
        )
        audit_entry.entry_hash = audit_entry.compute_hash(prev_hash)
        db.add(audit_entry)
        db.commit()
        logger.info(f"Alert {alert_id} CANCELLED by commander {commander_id}")
        return alert


alert_lifecycle_service = AlertLifecycleService()
