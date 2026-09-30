"""
backend/app/decision/authorization_gateway.py
=============================================
Human-in-the-Loop Safety & Authorization Gateway for FLOODY SHIELD.
Enforces Role-Based Access Control (RBAC) and prevents autonomous emergency broadcast.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.orm import Session

from backend.app.core.errors import AuthorizationError, ResourceNotFoundError
from backend.app.core.logging import get_logger
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.audit import AuditLogModel

logger = get_logger("floody.decision.auth_gateway")


class UserRole(str, Enum):
    OBSERVER = "OBSERVER"
    ANALYST = "ANALYST"
    SENIOR_INCIDENT_COMMANDER = "SENIOR_INCIDENT_COMMANDER"


class HumanAuthorizationGateway:
    """
    Statutory safety gateway enforcing human authorization invariants.
    System CANNOT dispatch public CAP alerts without explicit Commander sign-off.
    """

    def verify_role_permission(self, actor_role: str, required_role: UserRole) -> bool:
        """Checks whether the actor's role meets or exceeds the required privilege level."""
        hierarchy = {
            UserRole.OBSERVER: 1,
            UserRole.ANALYST: 2,
            UserRole.SENIOR_INCIDENT_COMMANDER: 3,
        }
        actor_enum = getattr(UserRole, actor_role.upper(), None)
        if not actor_enum:
            raise AuthorizationError(
                message=f"Invalid or unrecognized actor role: {actor_role}",
                details={"provided_role": actor_role},
            )

        if hierarchy[actor_enum] < hierarchy[required_role]:
            raise AuthorizationError(
                message=(
                    f"Insufficient permissions: Action requires {required_role.value}, "
                    f"but actor has role {actor_enum.value}."
                ),
                details={"required_role": required_role.value, "actor_role": actor_enum.value},
            )
        return True

    def authorize_alert_dispatch(
        self,
        db: Session,
        alert_id: str,
        actor_id: str,
        actor_role: str,
        approval_token: str,
        ip_address: Optional[str] = None,
    ) -> AlertDispatchModel:
        """
        Authorizes and transitions an alert from PENDING_APPROVAL to DISPATCHED.
        Strictly requires SENIOR_INCIDENT_COMMANDER authority.
        """
        # 1. Enforce Commander-only authorization invariant
        self.verify_role_permission(actor_role, UserRole.SENIOR_INCIDENT_COMMANDER)

        if not approval_token or len(approval_token) < 8:
            raise AuthorizationError(
                message="Valid cryptographic authorization token is required for public alert broadcast",
                details={"provided_token_length": len(approval_token) if approval_token else 0},
            )

        # 2. Retrieve target alert
        alert = db.query(AlertDispatchModel).filter_by(id=alert_id).first()
        if not alert:
            raise ResourceNotFoundError(
                message=f"Alert dispatch record '{alert_id}' not found",
                resource_type="AlertDispatch",
                resource_id=alert_id,
            )

        if alert.status == "DISPATCHED":
            return alert

        # 3. Transition status and record timestamp
        previous_status = alert.status
        alert.status = "DISPATCHED"
        alert.authorized_by = actor_id
        alert.dispatched_at = datetime.datetime.now(datetime.timezone.utc)

        # 4. Immutable Audit Trail
        audit = AuditLogModel(
            id=str(uuid.uuid4()),
            action="PUBLIC_ALERT_DISPATCH_AUTHORIZATION",
            actor_id=actor_id,
            actor_role=actor_role,
            target_entity_type="AlertDispatch",
            target_entity_id=alert.id,
            changes=f'{{"previous_status": "{previous_status}", "new_status": "DISPATCHED", "cap_id": "{alert.cap_identifier}"}}',
            ip_address=ip_address or "127.0.0.1",
        )
        db.add(audit)
        db.commit()
        db.refresh(alert)

        logger.info(
            f"Alert {alert.cap_identifier} DISPATCH AUTHORIZED by {actor_id} ({actor_role}). Audit ID: {audit.id}"
        )
        return alert


authorization_gateway = HumanAuthorizationGateway()
