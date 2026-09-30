"""
backend/app/websocket/manager.py
================================
Hardened WebSocket Connection Manager with Role-Based Access Control,
Topic Subscriptions, and Broadcast Filtering for FLOODY SHIELD v3.4.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Set, Optional
from fastapi import WebSocket

from backend.app.core.logging import get_logger
from backend.app.websocket.events import RealTimeEvent, RealTimeEventType

logger = get_logger("floody.websocket.manager")

ROLE_HIERARCHY = {
    "PUBLIC": 0,
    "OBSERVER": 1,
    "ANALYST": 2,
    "SENIOR_INCIDENT_COMMANDER": 3,
    "ADMIN": 4,
}

VALID_TOPICS = {"risk", "telemetry", "stations", "alerts", "system", "all"}


class ConnectionManager:
    def __init__(self):
        # Map websocket to client role
        self.active_connections: Dict[WebSocket, str] = {}
        # Map websocket to subscribed topics
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        self.lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        role: str = "OBSERVER",
        topics: Optional[List[str]] = None,
    ):
        await websocket.accept()
        async with self.lock:
            role_norm = role.upper()
            self.active_connections[websocket] = role_norm
            subs = set(topics) if topics else {"all", "alerts", "risk"}
            self.subscriptions[websocket] = subs
        logger.info(
            f"WebSocket client connected with role {role_norm}, subscriptions: {self.subscriptions[websocket]}. "
            f"Total active: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                del self.active_connections[websocket]
            if websocket in self.subscriptions:
                del self.subscriptions[websocket]
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, topic: str):
        if topic in VALID_TOPICS:
            if websocket in self.subscriptions:
                self.subscriptions[websocket].add(topic)

    def unsubscribe(self, websocket: WebSocket, topic: str):
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(topic)

    def _event_matches_topics(self, event_type: str, client_topics: Set[str]) -> bool:
        if "all" in client_topics:
            return True
        et = event_type.lower()
        if "telemetry" in client_topics and "telemetry" in et:
            return True
        if "stations" in client_topics and ("station" in et or "device" in et):
            return True
        if "risk" in client_topics and "risk" in et:
            return True
        if "alerts" in client_topics and "alert" in et:
            return True
        if "system" in client_topics and ("system" in et or "model" in et or "quality" in et):
            return True
        return False

    async def broadcast(self, event: RealTimeEvent):
        """Broadcasts event to clients with adequate RBAC role and matching topic subscription."""
        event_dict = event.model_dump()
        min_level = ROLE_HIERARCHY.get(event.min_role.upper(), 0)

        disconnected = []
        async with self.lock:
            for ws, client_role in self.active_connections.items():
                client_level = ROLE_HIERARCHY.get(client_role, 0)
                client_subs = self.subscriptions.get(ws, {"all"})

                if client_level >= min_level and self._event_matches_topics(event.event_type.value, client_subs):
                    try:
                        await ws.send_json(event_dict)
                    except Exception as exc:
                        logger.warning(f"Error delivering websocket event to client: {exc}")
                        disconnected.append(ws)

            for ws in disconnected:
                if ws in self.active_connections:
                    del self.active_connections[ws]
                if ws in self.subscriptions:
                    del self.subscriptions[ws]


ws_manager = ConnectionManager()
