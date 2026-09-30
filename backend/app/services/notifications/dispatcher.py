"""
backend/app/services/notifications/dispatcher.py
================================================
Central Notification Dispatcher for FLOODY SHIELD v3.4.
Coordinates multi-channel alert delivery (WebSocket, Siren, SMS, Email, NDMA Sachet).
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from backend.app.services.notifications.base import NotificationProvider, NotificationResult
from backend.app.services.notifications.websocket_provider import WebSocketNotificationProvider
from backend.app.services.notifications.siren_provider import SirenProvider
from backend.app.services.notifications.sms_provider import SMSNotificationProvider
from backend.app.services.notifications.email_provider import EmailNotificationProvider
from backend.app.services.notifications.ivr_provider import IVRNotificationProvider
from backend.app.services.notifications.ndma_sachet_provider import NDMASachetProvider
from backend.app.core.logging import get_logger

logger = get_logger("floody.notifications.dispatcher")


class NotificationDispatcher:
    def __init__(self):
        self.providers: Dict[str, NotificationProvider] = {
            "WEBSOCKET": WebSocketNotificationProvider(),
            "SIREN": SirenProvider(),
            "SMS": SMSNotificationProvider(),
            "EMAIL": EmailNotificationProvider(),
            "IVR": IVRNotificationProvider(),
            "NDMA_SACHET": NDMASachetProvider(),
        }

    def get_provider_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Returns readiness status for every notification adapter."""
        return {
            name: {
                "channel": p.channel_name,
                "is_configured": p.is_configured,
            }
            for name, p in self.providers.items()
        }

    async def broadcast_alert(
        self,
        alert_payload: Dict[str, Any],
        channels: Optional[List[str]] = None,
    ) -> List[NotificationResult]:
        """
        Dispatches alert concurrently across requested or all available channels.
        """
        target_channels = channels or list(self.providers.keys())
        tasks = []
        for ch in target_channels:
            provider = self.providers.get(ch.upper())
            if provider:
                tasks.append(provider.dispatch(alert_payload))
            else:
                logger.warning(f"Unknown notification channel requested: {ch}")

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        final_results = []
        for r in results:
            if isinstance(r, NotificationResult):
                final_results.append(r)
            elif isinstance(r, Exception):
                final_results.append(
                    NotificationResult(
                        provider_name="DispatcherException",
                        channel="UNKNOWN",
                        status="FAILED",
                        error=str(r),
                    )
                )

        logger.info(
            f"Notification dispatch processed for alert {alert_payload.get('cap_identifier', alert_payload.get('alert_id'))} "
            f"across {len(final_results)} channels: {[(res.channel, res.status) for res in final_results]}"
        )
        return final_results


notification_dispatcher = NotificationDispatcher()
