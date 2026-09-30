"""M19 Time-to-Impact — schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ImpactType(str, Enum):
    FLOOD_INUNDATION = "FLOOD_INUNDATION"         # River / flash flood reaching asset
    LANDSLIDE_RUNOUT = "LANDSLIDE_RUNOUT"          # Debris / rotational slide reaching road
    DAM_BREACH_OUTBURST = "DAM_BREACH_OUTBURST"    # GLOFs / landslide-dam outburst
    DEBRIS_FLOW = "DEBRIS_FLOW"                    # Channelized debris flow
    COMBINED = "COMBINED"                          # Composite hazard front


class TTIPredictionMethod(str, Enum):
    KINEMATIC_BASELINE = "KINEMATIC_BASELINE"      # Physics-based wave travel time
    QUANTILE_REGRESSION = "QUANTILE_REGRESSION"    # ML quantile regression (if real data)
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class TTIStatus(str, Enum):
    PREDICTED = "PREDICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DEGRADED_INPUT = "DEGRADED_INPUT"
    BELOW_DETECTION = "BELOW_DETECTION"


@dataclass
class M19TimeToImpactInput:
    """
    Inputs for time-to-impact estimation.

    All distances in km, speeds in km/h, depths in m, discharges in m³/s.
    """

    impact_type: str                          # ImpactType value
    distance_km: float                        # Source-to-asset distance
    # -- Flood / outburst specific --
    wave_speed_kmh: Optional[float] = None    # If known (e.g. from M12)
    peak_discharge_m3s: Optional[float] = None
    channel_slope_pct: Optional[float] = None # Channel slope (%)
    floodplain_width_m: Optional[float] = None
    # -- Landslide specific --
    slope_angle_deg: Optional[float] = None
    debris_depth_m: Optional[float] = None
    # -- Context --
    upstream_rainfall_mm_1h: float = 0.0
    soil_saturation_ratio: float = 0.5        # 0–1
    data_quality: float = 1.0


@dataclass
class M19TimeToImpactOutput:
    """Time-to-impact output with P10/P50/P90 quantiles."""

    model: str                       # "M19_TIME_TO_IMPACT"
    impact_type: str
    p10_minutes: float               # Earliest credible impact (optimistic)
    p50_minutes: float               # Best estimate (median)
    p90_minutes: float               # Latest credible impact (conservative)
    confidence: float                # 0–1
    data_quality: float
    status: str                      # TTIStatus
    method: str                      # TTIPredictionMethod
    uncertainty_note: str = ""
    model_version: str = "1.0.0"
    applicability: str = "UPPER_BEAS_KULLU_MANALI_CORRIDOR"
    provenance: str = "M19_KINEMATIC_BASELINE"
    notes: str = ""
    physics: Dict[str, Any] = field(default_factory=dict)
