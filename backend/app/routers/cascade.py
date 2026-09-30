"""
cascade.py — Compound Cascade & Landslide Dam Breach API Router
================================================================
Exposes endpoints for simulating landslide dam breaches using Froehlich (2008)
and Costa (1985) hydro-geotechnical formulations along the Beas River corridor.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.flood.m12_compound_cascade import CompoundCascadeEngine

router = APIRouter(prefix="/api/v1/cascade", tags=["Cascade & Dam Breach"])
cascade_engine = CompoundCascadeEngine()


class DamBreachRequest(BaseModel):
    dam_location: str = Field("Larji_Sainj_Confluence", description="Geographic name of landslide dam formation")
    dam_height_m: float = Field(35.0, ge=5.0, le=200.0, description="Height of landslide dam blockage in meters")
    impounded_volume_m3: float = Field(
        8_500_000.0,
        ge=100_000.0,
        le=500_000_000.0,
        description="Total impounded reservoir volume behind dam in cubic meters",
    )
    normal_river_discharge_m3s: float = Field(
        450.0,
        ge=10.0,
        le=10_000.0,
        description="Ambient river discharge prior to breach in m3/s",
    )


@router.post("/simulate", summary="Simulate landslide dam overtopping breach and downstream wave arrival")
def simulate_dam_breach(req: DamBreachRequest) -> Dict[str, Any]:
    """
    Computes breach outflow hydrograph (peak discharge Q_p and breach formation time t_f)
    and downstream attenuation along Beas River corridor reaches (Aut, Thalout, Pandoh Dam, Mandi).
    """
    result = cascade_engine.simulate_dam_breach(
        dam_location=req.dam_location,
        dam_height_m=req.dam_height_m,
        impounded_volume_m3=req.impounded_volume_m3,
        normal_river_discharge_m3s=req.normal_river_discharge_m3s,
    )
    return {
        "status": "success",
        "simulation": asdict(result),
    }


@router.get("/historical-scenarios", summary="List historical Himalayan dam breach benchmarks")
def list_historical_scenarios() -> Dict[str, Any]:
    """Returns historical benchmarks for validation (e.g. Pareechu 2005, Rishiganga 2021)."""
    return {
        "scenarios": [
            {
                "event_name": "Pareechu River Landslide Dam (Tibet / Sutlej)",
                "year": 2005,
                "dam_height_m": 60.0,
                "impounded_volume_m3": 64_000_000.0,
                "peak_discharge_m3s": 5200.0,
                "lead_time_to_indian_border_hours": 8.5,
            },
            {
                "event_name": "Rishiganga Chamoli Rock-Ice Avalanche & Dam Breach",
                "year": 2021,
                "dam_height_m": 45.0,
                "impounded_volume_m3": 1_600_000.0,
                "peak_discharge_m3s": 2800.0,
                "lead_time_to_tapovan_min": 14.0,
            },
            {
                "event_name": "Upper Beas Sainj-Larji Landslide Dam Scenario",
                "year": 2023,
                "dam_height_m": 35.0,
                "impounded_volume_m3": 8_500_000.0,
                "peak_discharge_m3s": 3500.0,
                "lead_time_to_aut_min": 12.0,
            },
        ]
    }
