"""
backend/app/core/errors.py
==========================
Consistent, structured error handling and custom exceptions for FLOODY SHIELD.
Guarantees:
  1. Never return internal stack traces in production HTTP responses.
  2. All errors contain standardized error code, message, request_id, and details.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class FloodyShieldException(Exception):
    """Base exception for all domain errors within FLOODY SHIELD."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = error_code or code
        self.error_code = self.code
        self.status_code = status_code
        self.details = details or {}


class DataQualityError(FloodyShieldException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATA_QUALITY_ERROR",
            status_code=422,
            details=details,
        )


class ModelInferenceError(FloodyShieldException):
    def __init__(self, message: str, model_id: str, details: Optional[Dict[str, Any]] = None):
        d = details or {}
        d["model_id"] = model_id
        super().__init__(
            message=message,
            code="MODEL_INFERENCE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=d,
        )


class UnauthorizedAlertError(FloodyShieldException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED_ALERT_DISPATCH",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


AuthorizationError = UnauthorizedAlertError


class ResourceNotFoundError(FloodyShieldException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


async def floody_exception_handler(request: Request, exc: FloodyShieldException) -> JSONResponse:
    req_id = getattr(request.state, "request_id", "NO_REQ")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": f"[{exc.code}] {exc.message}",
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": req_id,
                "details": exc.details,
            }
        },
    )
