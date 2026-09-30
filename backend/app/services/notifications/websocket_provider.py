"""
backend/app/services/notifications/websocket_provider.py
========================================================
Real-Time WebSocket Notification Provider for FLOODY SHIELD.
Broadcasts dispatches to connected EOC dashboards, mobile clients, and sirens.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
import uuid

from backend.app.services.notifications.base import NotificationProvider, NotificationResult
from backend.app.websocket.manager import ws_manager
from backend.app.websocket.events import RealTimeEvent, RealTimeEventType


class WebSocketNotificationProvider(NotificationProvider):
    @property
    def channel_name(self) -> str:
        return "WEBSOCKET"

    @property
    def is_configured(self) -> bool:
        return True

    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        try:
            event = RealTimeEvent(
                event_type=RealTimeEventType.ALERT_DISPATCHED,
                incident_id=alert_payload.get("incident_id"),
                min_role="OBSERVER",
                data=alert_payload,
            )
            await ws_manager.broadcast(event)
            return NotificationResult(
                provider_name="WebSocketNotificationProvider",
                channel="WEBSOCKET",
                status="DISPATCHED",
                recipient="BROADCAST_ACTIVE_SUBSCRIBERS",
                message_id=str(uuid.uuid4()),
                details={"active_connections": len(ws_manager.active_connections)},
            )
        except Exception as exc:
            return NotificationResult(
                provider_name="WebSocketNotificationProvider",
                channel="WEBSOCKET",
                status="FAILED",
                error=str(exc),
            )
