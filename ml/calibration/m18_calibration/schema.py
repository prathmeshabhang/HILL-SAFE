"""M18 Risk Calibration — schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CalibrationMethod(str, Enum):
    PLATT_SCALING = "platt_scaling"
    ISOTONIC_REGRESSION = "isotonic_regression"
    UNCALIBRATED = "uncalibrated"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class CalibrationStatus(str, Enum):
    CALIBRATED = "CALIBRATED"
    UNCALIBRATED_PASSTHROUGH = "UNCALIBRATED_PASSTHROUGH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DEGRADED_INPUT = "DEGRADED_INPUT"


class SourceModel(str, Enum):
    M2_FLOOD_RISK = "M2_FLOOD_RISK"
    M6_LANDSLIDE_SUSCEPTIBILITY = "M6_LANDSLIDE_SUSCEPTIBILITY"
    M7_LANDSLIDE_TRIGGER = "M7_LANDSLIDE_TRIGGER"
    M1_RAINFALL = "M1_RAINFALL"
    M10_WATER_LEVEL = "M10_WATER_LEVEL"
    M11_FLOOD_DEPTH = "M11_FLOOD_DEPTH"
    GENERIC = "GENERIC"


@dataclass
class M18CalibrationInput:
    """Input to the M18 calibration layer."""

    source_model: str                            # SourceModel value
    raw_probability: float                       # 0–1 raw score from source model
    event_label: Optional[int] = None           # 0 or 1 ground-truth (for fitting); None for inference
    additional_features: Dict[str, Any] = field(default_factory=dict)
    data_quality: float = 1.0                   # 0–1; below 0.5 → DEGRADED_INPUT


@dataclass
class M18CalibrationOutput:
    """Output contract for M18."""

    model: str                           # "M18_RISK_CALIBRATION"
    source_model: str
    raw_probability: float
    calibrated_probability: float
    calibration_method: str              # CalibrationMethod value
    confidence: float                    # 0–1 internal confidence
    data_quality: float
    status: str                          # CalibrationStatus value
    metrics: Dict[str, Any] = field(default_factory=dict)
    model_version: str = "1.0.0"
    applicability: str = "UPPER_BEAS_KULLU_MANALI_CORRIDOR"
    provenance: str = "M18_PROBABILITY_CALIBRATION_LAYER"
    notes: str = ""
