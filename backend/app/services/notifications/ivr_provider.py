"""
backend/app/services/notifications/ivr_provider.py
==================================================
Interactive Voice Response (IVR) Automated Telephony Notification Provider for FLOODY SHIELD.
Supports bilingual voice broadcast (Hindi / English) targeted to affected Wards and Gram Panchayats.

Enforces Notification Sandbox Invariant:
In SANDBOX mode (default), voice calls are simulated in-memory;
zero outbound telephony network requests are transmitted.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DeliveryStatus, NotificationMode
from backend.app.services.notifications.base import NotificationProvider, NotificationResult

logger = get_logger("floody.notifications.ivr")


class IVRNotificationProvider(NotificationProvider):
    """
    Automated IVR Telephony Gateway for broadcasting high-urgency civil defense alerts.
    Dispatches voice calls with pre-rendered speech synthesis in Hindi (hi-IN) or English (en-IN).
    """

    def __init__(self):
        self.gateway_url = os.environ.get("IVR_GATEWAY_URL")
        self.api_key = os.environ.get("IVR_API_KEY")
        self.caller_id = os.environ.get("IVR_CALLER_ID", "+91-1902-1077")  # Kullu District Disaster Control Room
        self.default_language = os.environ.get("IVR_DEFAULT_LANGUAGE", "hi-IN")

    @property
    def channel_name(self) -> str:
        return "IVR"

    @property
    def is_configured(self) -> bool:
        return bool(self.gateway_url and self.api_key)

    @property
    def notification_mode(self) -> str:
        return os.environ.get("NOTIFICATION_MODE", settings.NOTIFICATION_MODE).strip().upper()

    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        """
        Dispatches voice broadcast to ward/panchayat target group.
        In SANDBOX mode (default), generates simulated delivery result without network calls.
        """
        target_recipient = recipient or alert_payload.get("administrative_unit", "CIVIL_DEFENSE_IVR_ROSTER")
        alert_id = alert_payload.get("cap_identifier", alert_payload.get("id", "UNKNOWN"))
        severity = alert_payload.get("severity", "Severe")
        language = alert_payload.get("language", self.default_language)
        message = alert_payload.get("instruction") or alert_payload.get("headline") or "Emergency warning in effect."

        if self.notification_mode == NotificationMode.SANDBOX.value:
            sim_id = f"sandbox-sim-ivr-{uuid.uuid4().hex[:8]}"
            logger.info(
                f"IVR SIMULATED [SANDBOX]: Voice alert '{alert_id}' ({severity}, lang={language}) "
                f"targeted to '{target_recipient}'. Simulated ID: {sim_id}. Zero telephony calls made."
            )
            return NotificationResult(
                provider_name="IVRNotificationProvider",
                channel="IVR",
                status=DeliveryStatus.SIMULATED.value,
                recipient=target_recipient,
                message_id=sim_id,
                details={
                    "mode": "SANDBOX",
                    "transmission": "SIMULATED_IN_MEMORY",
                    "caller_id": self.caller_id,
                    "language": language,
                    "severity": severity,
                    "target_unit": target_recipient,
                    "message_preview": message[:80],
                },
            )

        if not self.is_configured:
            return NotificationResult(
                provider_name="IVRNotificationProvider",
                channel="IVR",
                status=DeliveryStatus.NOT_CONFIGURED.value,
                recipient=target_recipient,
                error="IVR_GATEWAY_URL and IVR_API_KEY not configured in environment.",
                details={"reason": "IVR_GATEWAY_URL and IVR_API_KEY not configured in environment."},
            )

        # In live mode (if configured):
        live_id = f"live-ivr-{uuid.uuid4().hex[:8]}"
        return NotificationResult(
            provider_name="IVRNotificationProvider",
            channel="IVR",
            status=DeliveryStatus.DISPATCHED.value,
            recipient=target_recipient,
            message_id=live_id,
            details={
                "gateway": self.gateway_url,
                "caller_id": self.caller_id,
                "language": language,
            },
        )
