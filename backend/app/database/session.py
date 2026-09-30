"""
backend/app/database/session.py
================================
SQLAlchemy engine, session factory, and FastAPI dependency.
Supports PostgreSQL (production) and SQLite (testing/development).
"""

from __future__ import annotations

import os
from typing import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("floody.db.session")

Base = declarative_base()


def resolve_database_url() -> str:
    """
    Determines database connection string. If postgresql is requested
    but not available in local test env, safely falls back to sqlite.
    """
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    # Check if a dedicated DB URL is set in settings
    configured = getattr(settings, "DATABASE_URL", "")
    if "sqlite" in configured:
        return configured

    # If no external PostgreSQL instance is explicitly forced, use sqlite in data root
    data_dir = settings.DATA_ROOT
    data_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = data_dir / "floody_shield.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


DATABASE_URL = resolve_database_url()
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a scoped database session,
    with automatic commit/rollback and cleanup.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Database session rolled back due to error: {exc}")
        raise
    finally:
        db.close()


def init_db(target_engine=None) -> None:
    """Initializes tables for all registered models."""
    import backend.app.database.models  # noqa: F401
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    logger.info("Database schema initialized successfully.")


# Initialize tables on application startup
try:
    init_db()
except Exception as exc:
    logger.warning(f"Deferred database initialization: {exc}")

