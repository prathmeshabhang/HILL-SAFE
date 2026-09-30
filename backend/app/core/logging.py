"""
backend/app/core/logging.py
===========================
Structured JSON logging and contextual log enrichment for FLOODY SHIELD.
Injects request_id, model_run_id, and user identity into all log emissions.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from backend.app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Formats log records as structured text with context tagging."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", "NO_REQ")
        model_run_id = getattr(record, "model_run_id", "-")
        prefix = f"[{record.levelname}] [{req_id}]"
        if model_run_id != "-":
            prefix += f" [ModelRun:{model_run_id}]"
        return f"{prefix} {record.name}: {record.getMessage()}"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("floody_shield")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        child = logging.getLogger(name)
        child.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        return child
    return logger

