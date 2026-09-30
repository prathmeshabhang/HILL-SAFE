"""
backend/app/core/config.py
==========================
Global application settings and environment-driven configuration for FLOODY SHIELD v3.2+.
Strictly manages secrets via environment variables with safe defaults for local/test environments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseModel):
    REPO_ROOT: Path = REPO_ROOT

    # Core Application Info
    APP_NAME: str = Field(default="HILL-SAFE — Predict • Protect • Preserve")
    APP_VERSION: str = Field(default="4.0.0")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Target Geographic Bounds (Upper Beas River Basin)
    AOI_NAME: str = "Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)"
    MIN_LATITUDE: float = 31.40
    MAX_LATITUDE: float = 32.45
    MIN_LONGITUDE: float = 76.80
    MAX_LONGITUDE: float = 77.45
    MIN_ELEVATION_M: float = 700.0
    MAX_ELEVATION_M: float = 6000.0

    # Database Configuration (PostgreSQL + PostGIS target; SQLite in-memory fallback for tests)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/floody_shield",
        description="Async SQLAlchemy database connection URI",
    )
    SYNC_DATABASE_URL: Optional[str] = Field(
        default="postgresql://postgres:postgres@localhost:5432/floody_shield",
        description="Synchronous database connection URI for Alembic migrations",
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Distributed Event Bus Configuration (Redis Pub/Sub fallback; defaults to In-Memory)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL for multi-worker distributed event bus",
    )

    # Security & JWT Tokens
    SECRET_KEY: str = Field(
        default="floody-shield-insecure-dev-secret-key-32-bytes-minimum-replace-in-prod",
        description="Cryptographic secret key for signing JWTs",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Model Registry & Data Paths
    DATA_ROOT: Path = REPO_ROOT / "data"
    MODEL_REGISTRY_PATH: Path = REPO_ROOT / "reports" / "model_registry.json"

    # Notification & Operational Safety Modes
    NOTIFICATION_MODE: str = Field(
        default="SANDBOX",
        description="Notification dispatch mode: SANDBOX (mock/in-memory) or LIVE (authenticated gateways)",
    )
    DEFAULT_DATA_MODE: str = Field(
        default="SIMULATED",
        description="Default data mode when unspecified for non-field inputs: REAL_FIELD_OBSERVATION, SIMULATED, etc.",
    )

    # Multi-Source Observation Endpoints & Polling (Phase 04A)
    INSAT3DS_MOSDAC_ENDPOINT: Optional[str] = Field(default=None, description="MOSDAC API endpoint for INSAT-3DS")
    INSAT3DS_API_KEY: Optional[str] = Field(default=None, description="MOSDAC API authentication key")
    INSAT3DS_FRESHNESS_MINUTES: int = Field(default=60, description="Freshness threshold for INSAT-3DS products in minutes")

    SMAP_EARTHDATA_ENDPOINT: Optional[str] = Field(default=None, description="NASA Earthdata / NSIDC endpoint for SMAP")
    SMAP_API_KEY: Optional[str] = Field(default=None, description="NASA Earthdata Bearer Token")
    SMAP_FRESHNESS_HOURS: int = Field(default=12, description="Freshness threshold for SMAP soil moisture in hours")

    IMD_AWS_ENDPOINT: Optional[str] = Field(default=None, description="IMD API / AWS FTP endpoint")
    IMD_AWS_API_KEY: Optional[str] = Field(default=None, description="IMD API token")
    IMD_AWS_FRESHNESS_MINUTES: int = Field(default=30, description="Freshness threshold for IMD AWS in minutes")

    CWC_RIVER_ENDPOINT: Optional[str] = Field(default=None, description="CWC river gauge endpoint")
    CWC_RIVER_API_KEY: Optional[str] = Field(default=None, description="CWC API token")
    CWC_RIVER_FRESHNESS_MINUTES: int = Field(default=60, description="Freshness threshold for CWC gauge telemetry in minutes")

    SENTINEL_COPERNICUS_ENDPOINT: Optional[str] = Field(default=None, description="Copernicus Data Space Ecosystem endpoint")
    SENTINEL_COPERNICUS_API_KEY: Optional[str] = Field(default=None, description="CDSE OAuth token or API key")
    SENTINEL_FRESHNESS_HOURS: int = Field(default=72, description="Freshness threshold for Sentinel scenes in hours")

    IOT_FIELD_FRESHNESS_MINUTES: int = Field(default=15, description="Freshness threshold for field IoT telemetry in minutes")
    MULTI_SOURCE_POLL_INTERVAL_SECONDS: int = Field(default=300, description="Default polling interval across sources")
    MULTI_SOURCE_HTTP_TIMEOUT_SECONDS: int = Field(default=15, description="Network timeout for external agency requests")


settings = Settings()
