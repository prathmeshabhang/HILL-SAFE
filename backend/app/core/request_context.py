"""
backend/app/core/request_context.py
===================================
Request ID generation, validation, and propagation middleware.
Ensures every request has an X-Request-ID attached to response headers and request state.
"""

from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Accept client-supplied X-Request-ID or generate new UUID4
        client_req_id = request.headers.get("X-Request-ID")
        if client_req_id and len(client_req_id) <= 64:
            request_id = client_req_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
