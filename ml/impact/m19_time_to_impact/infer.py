"""M19 — Inference: combine physics baseline with optional ML layer."""

from __future__ import annotations

import logging
from typing import Optional

from .physics import estimate_travel_time
from .schema import (
    ImpactType,
    TTIPredictionMethod,
    TTIStatus,
    M19TimeToImpactInput,
    M19TimeToImpactOutput,
)

logger = logging.getLogger(__name__)


def predict(inp: M19TimeToImpactInput) -> M19TimeToImpactOutput:
    """
    Estimate time-to-impact window using kinematic physics baseline.

    ML quantile regression is declared INSUFFICIENT_EVIDENCE because
    no real event-level timestamps exist for the Upper Beas corridor
    at this project stage.

    Returns P10/P50/P90 quantiles in minutes.
    """
    if inp.data_quality < 0.3:
        return M19TimeToImpactOutput(
            model="M19_TIME_TO_IMPACT",
            impact_type=inp.impact_type,
            p10_minutes=float("nan"),
            p50_minutes=float("nan"),
            p90_minutes=float("nan"),
            confidence=0.1,
            data_quality=inp.data_quality,
            status=TTIStatus.DEGRADED_INPUT,
            method=TTIPredictionMethod.KINEMATIC_BASELINE,
            notes="Data quality critically low — cannot produce reliable estimate.",
        )

    result = estimate_travel_time(
        impact_type=inp.impact_type,
        distance_km=inp.distance_km,
        channel_slope_pct=inp.channel_slope_pct,
        peak_discharge_m3s=inp.peak_discharge_m3s,
        floodplain_width_m=inp.floodplain_width_m,
        wave_speed_kmh=inp.wave_speed_kmh,
        slope_angle_deg=inp.slope_angle_deg,
        debris_depth_m=inp.debris_depth_m,
        soil_saturation_ratio=inp.soil_saturation_ratio,
    )

    # Confidence: degrades with uncertainty band and data quality
    # Base confidence 0.70 (physics only) × data_quality
    confidence = round(0.70 * inp.data_quality, 4)

    uncertainty_note = (
        "Time-to-impact estimated via kinematic baseline only. "
        "ML quantile regression marked INSUFFICIENT_EVIDENCE — "
        "no event-level time-to-impact observations available for "
        "the Upper Beas corridor at this project stage. "
        f"P10/P90 spread = ±30% parametric uncertainty on wave speed."
    )

    return M19TimeToImpactOutput(
        model="M19_TIME_TO_IMPACT",
        impact_type=inp.impact_type,
        p10_minutes=result["p10_min"],
        p50_minutes=result["p50_min"],
        p90_minutes=result["p90_min"],
        confidence=confidence,
        data_quality=inp.data_quality,
        status=TTIStatus.PREDICTED,
        method=TTIPredictionMethod.KINEMATIC_BASELINE,
        uncertainty_note=uncertainty_note,
        provenance="M19_KINEMATIC_BASELINE + MANNING_HUNGR1995",
        physics=result["physics"],
        notes=(
            f"Speed source: {result['speed_source']}. "
            f"Estimated speed: {result['speed_kmh']} km/h."
        ),
    )
