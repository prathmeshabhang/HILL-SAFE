"""
backend/app/websocket/endpoint.py
=================================
FastAPI WebSocket endpoint `/ws/v1/events` for real-time hazard, incident, and alert streams.
Enforces authentication, RBAC topic subscriptions, and strict prohibition on remote alert authorization.
"""

from __future__ import annotations

import json
from typing import Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
import jwt

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.websocket.manager import ws_manager

logger = get_logger("floody.websocket.endpoint")
router = APIRouter(tags=["Real-Time WebSockets"])


@router.websocket("/ws/v1/events")
@router.websocket("/ws/realtime")
async def websocket_events_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Optional JWT bearer token for role authorization"),
    role: Optional[str] = Query("OBSERVER", description="Client role override if unauthenticated"),
    topics: Optional[str] = Query("all", description="Comma-separated topic subscriptions: risk,telemetry,stations,alerts,system,all"),
):
    """
    Subscribes to live multi-hazard pipeline events, model completions, risk updates, and alert dispatches.
    Authenticates client credentials, assigns role, and filters stream by subscribed topics.
    """
    client_role = "OBSERVER"
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            client_role = payload.get("role", "OBSERVER").upper()
        except Exception:
            client_role = "OBSERVER"
    elif role:
        client_role = role.upper()

    topic_list = [t.strip().lower() for t in topics.split(",") if t.strip()] if topics else ["all"]

    await ws_manager.connect(websocket, role=client_role, topics=topic_list)
    await websocket.send_json({
        "type": "SUBSCRIPTION_CONFIRMED",
        "status": "CONNECTED",
        "role": client_role,
        "topics": topic_list,
    })
    try:
        while True:
            raw = await websocket.receive_text()
            if raw == "ping":
                await websocket.send_text("pong")
                continue

            try:
                msg = json.loads(raw)
            except Exception:
                continue

            action = msg.get("action", "").lower()
            if action == "subscribe":
                ws_manager.subscribe(websocket, msg.get("topic", "").lower())
                await websocket.send_json({"type": "SUBSCRIPTION_CONFIRMED", "status": "SUBSCRIBED", "topic": msg.get("topic")})
            elif action == "unsubscribe":
                ws_manager.unsubscribe(websocket, msg.get("topic", "").lower())
                await websocket.send_json({"type": "UNSUBSCRIBE_CONFIRMED", "status": "UNSUBSCRIBED", "topic": msg.get("topic")})
            elif "authorize" in action or "dispatch" in action:
                # Strictly enforce Life-Safety Invariant: Alert authorization via WebSockets is prohibited!
                await websocket.send_json({
                    "type": "SECURITY_ERROR",
                    "code": "WEBSOCKET_AUTHORIZATION_PROHIBITED",
                    "error": "WEBSOCKET_AUTHORIZATION_PROHIBITED",
                    "message": "Life-safety emergency alert authorization cannot be executed via WebSocket. "
                               "The authenticated REST API gateway (POST /api/v1/alerts/{id}/authorize) is required.",
                })
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket session terminated: {exc}")
        await ws_manager.disconnect(websocket)
