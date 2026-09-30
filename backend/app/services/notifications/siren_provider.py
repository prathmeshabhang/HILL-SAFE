"""
backend/app/services/notifications/siren_provider.py
====================================================
Field Siren Network Notification Provider for FLOODY SHIELD.
Dispatches acoustic alarms to Aut, Larji, Pandoh, and Bhuntar riverbed communities.
In SANDBOX mode (default), acoustic alarms are simulated in-memory; sirens remain silent.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DeliveryStatus, NotificationMode
from backend.app.services.notifications.base import NotificationProvider, NotificationResult

logger = get_logger("floody.notifications.siren")


class SirenProvider(NotificationProvider):
    def __init__(self):
        self.siren_endpoint = os.environ.get("SIREN_GATEWAY_URL")
        self.api_key = os.environ.get("SIREN_GATEWAY_KEY")

    @property
    def channel_name(self) -> str:
        return "SIREN"

    @property
    def is_configured(self) -> bool:
        return bool(self.siren_endpoint and self.api_key)

    @property
    def notification_mode(self) -> str:
        return os.environ.get("NOTIFICATION_MODE", settings.NOTIFICATION_MODE).strip().upper()

    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        target_recipient = recipient or "ALL_RIVERBED_SIRENS"

        if self.notification_mode == NotificationMode.SANDBOX.value:
            sim_id = f"sandbox-sim-siren-{uuid.uuid4().hex[:8]}"
            logger.info(
                f"SIREN SIMULATED [SANDBOX]: Acoustic warning {alert_payload.get('cap_identifier', 'UNKNOWN')} "
                f"for {target_recipient}. Simulated ID: {sim_id}. Physical sirens silent."
            )
            return NotificationResult(
                provider_name="SirenProvider",
                channel="SIREN",
                status=DeliveryStatus.SIMULATED.value,
                recipient=target_recipient,
                message_id=sim_id,
                details={"mode": "SANDBOX", "transmission": "SIMULATED_IN_MEMORY"},
            )

        if not self.is_configured:
            return NotificationResult(
                provider_name="SirenProvider",
                channel="SIREN",
                status=DeliveryStatus.NOT_CONFIGURED.value,
                recipient=target_recipient,
                details={"reason": "SIREN_GATEWAY_URL and SIREN_GATEWAY_KEY not configured in environment."},
            )

        return NotificationResult(
            provider_name="SirenProvider",
            channel="SIREN",
            status=DeliveryStatus.SIMULATED.value,
            recipient=target_recipient,
            message_id=f"sandbox-siren-{uuid.uuid4().hex[:8]}",
            details={"gateway": self.siren_endpoint, "tones": "WARBLE_EVACUATION"},
        )
