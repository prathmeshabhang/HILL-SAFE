"""
backend/app/websocket/events.py
===============================
Standardized, typed event schemas for FLOODY SHIELD Real-Time WebSocket Streaming.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RealTimeEventType(str, Enum):
    OBSERVATION_INGESTED = "OBSERVATION_INGESTED"
    QUALITY_CHANGED = "QUALITY_CHANGED"
    MODEL_STARTED = "MODEL_STARTED"
    MODEL_COMPLETED = "MODEL_COMPLETED"
    MODEL_FAILED = "MODEL_FAILED"
    RISK_UPDATED = "RISK_UPDATED"
    SAFE_ZONE_UPDATED = "SAFE_ZONE_UPDATED"
    ROUTE_UPDATED = "ROUTE_UPDATED"
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_APPROVED = "ALERT_APPROVED"
    ALERT_DISPATCHED = "ALERT_DISPATCHED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"


class RealTimeEvent(BaseModel):
    event_type: RealTimeEventType
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    incident_id: Optional[str] = None
    risk_state_id: Optional[str] = None
    min_role: str = "OBSERVER"  # PUBLIC, OBSERVER, ANALYST, SENIOR_INCIDENT_COMMANDER
    data: Dict[str, Any] = Field(default_factory=dict)
