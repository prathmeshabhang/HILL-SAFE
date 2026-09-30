"""
alerts.py — Common Alerting Protocol (CAP v1.2) Early Warning API Router
========================================================================
Exposes endpoints for generating ITU-T X.1303 / NDMA Sachet compliant bilingual
CAP alerts for sirens, mobile broadcast, SMS gateway, and emergency operations centers.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ml.flood.m12_compound_cascade import CompoundCascadeEngine
from ml.security.cap_alert_engine import CAPAlertEngine

router = APIRouter(prefix="/api/v1/alerts", tags=["Emergency Alerts & CAP"])
cap_engine = CAPAlertEngine()
cascade_engine = CompoundCascadeEngine()


class TriggerCascadeAlertRequest(BaseModel):
    dam_location: str = Field("Larji_Sainj_Confluence", description="Location of the landslide dam")
    dam_height_m: float = Field(35.0, description="Height of dam in meters")
    impounded_volume_m3: float = Field(8_500_000.0, description="Impounded reservoir volume in m3")
    status: Literal["Actual", "Exercise", "Test", "Draft"] = Field("Exercise", description="CAP alert status (defaults to Exercise for non-operational simulation)")
    format: Literal["json", "xml"] = Field("json", description="Response serialization format")


class ZoneHazardAlertRequest(BaseModel):
    zone_name: str = Field("NH-3 Aut-Larji Riverbed Ribbon", description="Designated hazard zone name")
    hazard_type: str = Field("Compound Flood & Debris Flow", description="Type of hazard")
    coordinates_polygon: List[List[float]] = Field(
        [[31.7150, 77.1450], [31.7600, 77.1700], [31.7500, 77.1950], [31.7150, 77.1450]],
        description="List of [lat, lon] polygon vertices",
    )
    format: Literal["json", "xml"] = Field("json", description="Response format")


@router.post("/cascade-breach", summary="Generate bilingual CAP v1.2 alert for landslide dam breach")
def generate_cascade_alert(req: TriggerCascadeAlertRequest) -> Any:
    """
    Simulates dam breach hydrograph and produces an ITU-T X.1303 / NDMA Sachet
    bilingual CAP v1.2 alert payload (English and Hindi).
    """
    breach_sim = cascade_engine.simulate_dam_breach(
        dam_location=req.dam_location,
        dam_height_m=req.dam_height_m,
        impounded_volume_m3=req.impounded_volume_m3,
    )

    alert = cap_engine.generate_cascade_breach_alert(
        breach_result_dict=asdict(breach_sim),
        status=req.status,
    )

    if req.format == "xml":
        xml_content = alert.to_xml_string()
        return Response(content=xml_content, media_type="application/xml")

    return {
        "status": "success",
        "format": "json",
        "cap_alert": alert.to_dict(),
    }


@router.post("/hazard-zone", summary="Generate targeted CAP v1.2 alert for critical hazard zone")
def generate_zone_alert(req: ZoneHazardAlertRequest) -> Any:
    """
    Generates targeted Section 36 high-hazard warning for sirens and local geofenced push notifications.
    """
    poly_tuples = [(p[0], p[1]) for p in req.coordinates_polygon]
    alert = cap_engine.generate_high_hazard_zone_alert(
        zone_name=req.zone_name,
        hazard_type=req.hazard_type,
        coordinates_polygon=poly_tuples,
    )

    if req.format == "xml":
        xml_content = alert.to_xml_string()
        return Response(content=xml_content, media_type="application/xml")

    return {
        "status": "success",
        "format": "json",
        "cap_alert": alert.to_dict(),
    }
