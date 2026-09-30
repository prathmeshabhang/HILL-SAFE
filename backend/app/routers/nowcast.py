"""
nowcast.py — Model M1 Short-Term Extreme Rainfall Nowcasting API Router
========================================================================
Exposes endpoints for:
  - pySTEPS semi-Lagrangian advection precipitation forecasts (+15m, +30m, +60m, +120m).
  - Cloudburst probability (>60 mm/hr) and impacted tributary gorges.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.rainfall.nowcast_service import ShortTermNowcastService

router = APIRouter(prefix="/api/v1/nowcast", tags=["Atmospheric Nowcasting (M1)"])
nowcast_service = ShortTermNowcastService()


class NowcastQueryRequest(BaseModel):
    catchment_name: str = Field("Upper_Beas_Catchment", description="Mountain catchment name")
    current_max_rain_mmh: float = Field(78.5, ge=0.0, le=350.0, description="Observed peak rainfall rate mm/hr")
    storm_motion_dx_kmh: float = Field(14.0, description="Zonal motion km/h (+ East, - West)")
    storm_motion_dy_kmh: float = Field(-8.0, description="Meridional motion km/h (+ North, - South)")


@router.post("/forecast", summary="Generate Lagrangian short-term precipitation nowcast")
def generate_precipitation_nowcast(req: NowcastQueryRequest) -> Dict[str, Any]:
    """Generates 15-minute to 120-minute lead time spatial precipitation nowcast."""
    res = nowcast_service.generate_nowcast(
        catchment_name=req.catchment_name,
        current_max_rain_mmh=req.current_max_rain_mmh,
        storm_motion_dx_kmh=req.storm_motion_dx_kmh,
        storm_motion_dy_kmh=req.storm_motion_dy_kmh,
    )
    return {
        "status": "success",
        "nowcast": asdict(res),
    }


@router.get("/latest", summary="Get latest active atmospheric cloudburst forecast")
def get_latest_nowcast() -> Dict[str, Any]:
    """Returns the most recent nowcast cycle for the Upper Beas mountain basin."""
    res = nowcast_service.generate_nowcast()
    return {
        "status": "success",
        "nowcast": asdict(res),
    }
