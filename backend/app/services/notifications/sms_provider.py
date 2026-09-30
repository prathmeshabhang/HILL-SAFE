"""
backend/app/services/notifications/sms_provider.py
==================================================
Civil Defense SMS Gateway Notification Provider for FLOODY SHIELD.
Enforces the Notification Sandbox Invariant:
In SANDBOX mode (default), all SMS alerts are simulated in-memory;
zero outbound SMS gateway HTTP calls are made.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DeliveryStatus, NotificationMode
from backend.app.services.notifications.base import NotificationProvider, NotificationResult

logger = get_logger("floody.notifications.sms")


class SMSNotificationProvider(NotificationProvider):
    def __init__(self):
        self.gateway_url = os.environ.get("SMS_GATEWAY_URL")
        self.api_key = os.environ.get("SMS_API_KEY")
        self.sender_id = os.environ.get("SMS_SENDER_ID", "HPSDMA")

    @property
    def channel_name(self) -> str:
        return "SMS"

    @property
    def is_configured(self) -> bool:
        return bool(self.gateway_url and self.api_key)

    @property
    def notification_mode(self) -> str:
        return os.environ.get("NOTIFICATION_MODE", settings.NOTIFICATION_MODE).strip().upper()

    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        target_recipient = recipient or "CIVIL_DEFENSE_ROSTER"

        if self.notification_mode == NotificationMode.SANDBOX.value:
            sim_id = f"sandbox-sim-sms-{uuid.uuid4().hex[:8]}"
            logger.info(
                f"SMS SIMULATED [SANDBOX]: Alert {alert_payload.get('cap_identifier', 'UNKNOWN')} "
                f"to {target_recipient}. Simulated ID: {sim_id}. Zero SMS gateway traffic."
            )
            return NotificationResult(
                provider_name="SMSNotificationProvider",
                channel="SMS",
                status=DeliveryStatus.SIMULATED.value,
                recipient=target_recipient,
                message_id=sim_id,
                details={
                    "mode": "SANDBOX",
                    "transmission": "SIMULATED_IN_MEMORY",
                    "sender_id": self.sender_id,
                },
            )

        if not self.is_configured:
            return NotificationResult(
                provider_name="SMSNotificationProvider",
                channel="SMS",
                status=DeliveryStatus.NOT_CONFIGURED.value,
                recipient=target_recipient,
                details={"reason": "SMS_GATEWAY_URL and SMS_API_KEY not configured in environment."},
            )

        return NotificationResult(
            provider_name="SMSNotificationProvider",
            channel="SMS",
            status=DeliveryStatus.SIMULATED.value,
            recipient=target_recipient,
            message_id=f"sandbox-sms-{uuid.uuid4().hex[:8]}",
            details={"gateway": self.gateway_url, "sender_id": self.sender_id},
        )
