"""
backend/app/services/notifications/email_provider.py
====================================================
EOC Emergency Operations Center Email Dispatch Provider.
Enforces the Notification Sandbox Invariant:
In SANDBOX mode (default), all emails are simulated in-memory;
zero outbound network traffic or SMTP socket connections are made.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DeliveryStatus, NotificationMode
from backend.app.services.notifications.base import NotificationProvider, NotificationResult

logger = get_logger("floody.notifications.email")


class EmailNotificationProvider(NotificationProvider):
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST")
        self.smtp_user = os.environ.get("SMTP_USER")
        self.smtp_pass = os.environ.get("SMTP_PASSWORD")

    @property
    def channel_name(self) -> str:
        return "EMAIL"

    @property
    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_pass)

    @property
    def notification_mode(self) -> str:
        return os.environ.get("NOTIFICATION_MODE", settings.NOTIFICATION_MODE).strip().upper()

    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        target_recipient = recipient or "EOC_COMMAND_STAFF"

        # In SANDBOX mode (default in dev/test/staging), strictly simulate in-memory
        if self.notification_mode == NotificationMode.SANDBOX.value:
            sim_id = f"sandbox-sim-email-{uuid.uuid4().hex[:8]}"
            logger.info(
                f"EMAIL SIMULATED [SANDBOX]: Alert {alert_payload.get('cap_identifier', 'UNKNOWN')} "
                f"for {target_recipient}. Simulated ID: {sim_id}. Zero SMTP network traffic."
            )
            return NotificationResult(
                provider_name="EmailNotificationProvider",
                channel="EMAIL",
                status=DeliveryStatus.SIMULATED.value,
                recipient=target_recipient,
                message_id=sim_id,
                details={
                    "mode": "SANDBOX",
                    "transmission": "SIMULATED_IN_MEMORY",
                    "is_simulated": True,
                    "subject": f"EMERGENCY ADVISORY: {alert_payload.get('headline', 'FLOODY SHIELD ALERT')}",
                },
            )

        if not self.is_configured:
            return NotificationResult(
                provider_name="EmailNotificationProvider",
                channel="EMAIL",
                status=DeliveryStatus.NOT_CONFIGURED.value,
                recipient=target_recipient,
                details={"reason": "SMTP credentials not configured in environment."},
            )

        # Non-sandbox but external SMTP client reserved for future authenticated phase
        logger.info(f"SANDBOX DISPATCH: Email simulated for {target_recipient}")
        return NotificationResult(
            provider_name="EmailNotificationProvider",
            channel="EMAIL",
            status=DeliveryStatus.SIMULATED.value,
            recipient=target_recipient,
            message_id=f"sandbox-email-{uuid.uuid4().hex[:8]}",
            details={"mode": "SANDBOX", "transmission": "MOCK_PROVIDER"},
        )
