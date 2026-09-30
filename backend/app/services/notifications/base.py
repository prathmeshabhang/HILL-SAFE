"""
backend/app/services/notifications/base.py
==========================================
Notification Provider abstraction and data structures for FLOODY SHIELD v3.4.
Enforces honest delivery statuses: unconfigured providers return NOT_CONFIGURED, never fake success.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class NotificationResult(BaseModel):
    provider_name: str
    channel: str  # WEBSOCKET, EMAIL, SMS, SIREN, NDMA_SACHET
    status: str  # DISPATCHED, CONFIRMED, FAILED, NOT_CONFIGURED
    recipient: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    @property
    def error_message(self) -> Optional[str]:
        return self.error



class NotificationProvider(ABC):
    """Abstract interface for emergency notification channels."""

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Returns the channel code (e.g. WEBSOCKET, NDMA_SACHET)."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Indicates whether production credentials and endpoints are available."""
        pass

    @abstractmethod
    async def dispatch(self, alert_payload: Dict[str, Any], recipient: Optional[str] = None) -> NotificationResult:
        """Sends or broadcasts alert to downstream receivers."""
        pass
