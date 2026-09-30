"""
backend/app/core/event_bus.py
=============================
Asynchronous In-Memory Event Bus for FLOODY SHIELD v3.4.
Dispatches internal operational events across decoupled services and bridges to WebSockets.
"""

from __future__ import annotations

import asyncio
import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.core.logging import get_logger

logger = get_logger("floody.event_bus")


class SystemEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="e.g. telemetry.accepted, alert.authorized, station.offline")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field("FLOODY_SHIELD_CORE", description="Publishing service/component")
    entity_id: Optional[str] = Field(None, description="Primary affected entity ID")
    severity: str = Field("INFO", description="INFO, WARNING, HIGH, CRITICAL")
    payload: Dict[str, Any] = Field(default_factory=dict)

    def __getitem__(self, item: str) -> Any:
        if item in ("data", "payload"):
            return self.payload
        if item in self.payload:
            return self.payload[item]
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)



class EventBus:
    def __init__(self, redis_url: Optional[str] = None):
        self._subscribers: Dict[str, List[Callable[[SystemEvent], Any]]] = {}
        self._history: List[SystemEvent] = []
        self._max_history = 1000
        self._redis_url = redis_url
        self._mode = "in-memory"

        if self._redis_url:
            try:
                import redis.asyncio as aioredis  # type: ignore
                self._mode = "redis"
                logger.info(f"[EVENT_BUS] Initialized Redis Pub/Sub event bus at {self._redis_url}")
            except ImportError:
                logger.warning("[EVENT_BUS] redis package not installed. Falling back to in-memory event bus.")
                self._mode = "in-memory"
            except Exception as e:
                logger.warning(f"[EVENT_BUS] Could not connect to Redis at {self._redis_url} ({e}). Falling back to in-memory.")
                self._mode = "in-memory"
        else:
            logger.info("[EVENT_BUS] In-memory event bus active (single-worker mode). For multi-worker deployments, set REDIS_URL.")

    @property
    def mode(self) -> str:
        """Returns the active event bus distribution mode: 'in-memory' or 'redis'."""
        return self._mode

    def get_bus_mode(self) -> str:
        return self._mode

    def subscribe(self, event_pattern: str, handler: Callable[[SystemEvent], Any]) -> None:
        """Subscribe handler to an exact event_type or wildcard pattern (e.g. 'alert.*')."""
        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        self._subscribers[event_pattern].append(handler)

    def publish(self, event_or_type: Any, data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> SystemEvent:
        """Publishes an event to all matching subscribers."""
        if isinstance(event_or_type, SystemEvent):
            event = event_or_type
        else:
            event = SystemEvent(event_type=str(event_or_type), payload=data or kwargs)

        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Match exact and wildcards
        handlers_to_call = []
        for pattern, handlers in self._subscribers.items():
            if pattern == event.event_type or pattern == "*" or (pattern.endswith(".*") and event.event_type.startswith(pattern[:-2])):
                handlers_to_call.extend(handlers)

        for handler in handlers_to_call:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error executing event handler for {event.event_type}: {e}")

        return event

    def get_recent_events(self, limit: int = 50, event_type_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        events = self._history
        if event_type_prefix:
            events = [e for e in events if e.event_type.startswith(event_type_prefix)]
        events_slice = events[-limit:]
        return [e.model_dump() for e in reversed(events_slice)]


def get_event_bus() -> EventBus:
    from backend.app.core.config import settings
    return EventBus(redis_url=getattr(settings, "REDIS_URL", None))


event_bus = get_event_bus()
