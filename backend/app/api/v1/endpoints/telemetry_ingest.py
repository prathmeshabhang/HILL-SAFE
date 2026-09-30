"""
backend/app/api/v1/endpoints/telemetry_ingest.py
================================================
REST API endpoints for real-time telemetry ingestion with quality gating.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.services.ingestion.schemas import RainGaugeReading, RiverWaterLevelReading
from backend.app.services.ingestion.ingestion_service import ingestion_service

router = APIRouter(prefix="/api/v1/ingest", tags=["Telemetry Ingestion & Quality Gating"])


@router.post("/rain-gauge", summary="Ingest rainfall telemetry with M9 quality gating")
def ingest_rainfall_reading(
    reading: RainGaugeReading,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Ingests AWS/IMD rain gauge telemetry, runs quality checks, and saves to database."""
    return ingestion_service.ingest_rainfall(db, reading)


@router.post("/river-stage", summary="Ingest CWC river stage telemetry with M9 quality gating")
def ingest_river_stage_reading(
    reading: RiverWaterLevelReading,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Ingests CWC river gauge telemetry, runs quality checks, and saves to database."""
    return ingestion_service.ingest_river_stage(db, reading)
