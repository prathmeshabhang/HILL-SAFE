"""M20 Post-Event Damage Assessment — schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DamageClass(str, Enum):
    NO_DAMAGE = "NO_DAMAGE"
    MINOR = "MINOR"                 # < 20% structural loss
    MODERATE = "MODERATE"           # 20–60% structural loss
    SEVERE = "SEVERE"               # > 60% structural loss / collapse
    CHANGE_DETECTED = "CHANGE_DETECTED"  # Change visible but unclassifiable (no labels)


class DamageEvidenceType(str, Enum):
    OBSERVED = "OBSERVED"              # Field-surveyed confirmed
    MODELLED = "MODELLED"              # Model-inferred from physics inputs
    CHANGE_DETECTED = "CHANGE_DETECTED"  # Remote sensing change only (no label)


class HazardType(str, Enum):
    FLOOD = "FLOOD"
    LANDSLIDE = "LANDSLIDE"
    DEBRIS_FLOW = "DEBRIS_FLOW"
    COMPOUND = "COMPOUND"


class AssessmentStatus(str, Enum):
    ASSESSED = "ASSESSED"
    CHANGE_DETECTED_ONLY = "CHANGE_DETECTED_ONLY"
    DEGRADED_INPUT = "DEGRADED_INPUT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class SatelliteObservation:
    """Pre/post image-derived change indicators (no raw imagery required)."""

    ndvi_pre: Optional[float] = None      # Pre-event NDVI
    ndvi_post: Optional[float] = None     # Post-event NDVI
    ndwi_pre: Optional[float] = None      # Pre-event NDWI (water index)
    ndwi_post: Optional[float] = None     # Post-event NDWI
    sar_coherence_pre: Optional[float] = None   # InSAR coherence pre
    sar_coherence_post: Optional[float] = None  # InSAR coherence post (drops on damage)
    inundation_depth_m: Optional[float] = None  # From M11
    debris_cover_fraction: Optional[float] = None  # 0–1


@dataclass
class M20DamageInput:
    """Input to M20 per asset."""

    asset_id: str
    hazard_type: str                            # HazardType
    satellite: SatelliteObservation = field(default_factory=SatelliteObservation)
    # Physics-based inputs
    flood_depth_m: Optional[float] = None       # From M11
    flow_velocity_ms: Optional[float] = None    # From M10
    peak_discharge_m3s: Optional[float] = None  # From M10/M12
    landslide_runout_m: Optional[float] = None  # Distance debris reached asset
    rainfall_mm_24h: float = 0.0
    # Asset metadata
    asset_category: str = "GENERIC"            # road, bridge, building, etc.
    asset_replacement_value_inr: float = 0.0
    data_quality: float = 1.0


@dataclass
class M20DamageOutput:
    """Per-asset damage assessment output."""

    asset_id: str
    hazard_type: str
    change_detected: bool
    damage_class: str                           # DamageClass
    damage_probability: float                   # 0–1
    damage_fraction: float                      # 0–1 structural loss fraction
    affected_area_m2: float
    evidence_type: str                          # DamageEvidenceType
    confidence: float
    data_quality: float
    status: str                                 # AssessmentStatus
    model: str = "M20_DAMAGE_ASSESSMENT"
    model_version: str = "1.0.0"
    applicability: str = "UPPER_BEAS_KULLU_MANALI_CORRIDOR"
    provenance: str = "M20_CHANGE_DETECTION_BASELINE"
    notes: str = ""
    external_validation_note: str = "EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE"
