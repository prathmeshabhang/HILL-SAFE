"""
schema.py — Common Scientific Validation-Audit Schema
=====================================================
Establishes standardized data models, enums, and structured audit results
for all FLOODY SHIELD machine learning validation pipelines (M6, M7, M2, M4).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationUnit(str, Enum):
    POINT = "point"
    SPATIAL_SAMPLE = "spatial_sample"
    EVENT = "event"
    PIXEL = "pixel"
    SCENE = "scene"


class IndependenceStatus(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    NON_INDEPENDENT = "NON_INDEPENDENT"
    UNKNOWN = "UNKNOWN"


class ControlValidity(str, Enum):
    VALID_ABSENCE = "VALID_ABSENCE"
    PROVISIONAL_ABSENCE = "PROVISIONAL_ABSENCE"
    UNCERTAIN = "UNCERTAIN"
    INVALID = "INVALID"


class ValidationTier(str, Enum):
    VALIDATED = "VALIDATED"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
    PROVISIONALLY_VALIDATED = "PROVISIONALLY_VALIDATED"
    NOT_ESTIMABLE = "NOT_ESTIMABLE"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    INVALID_VALIDATION = "INVALID_VALIDATION"


class MetricStatus(str, Enum):
    VALID = "VALID"
    NOT_ESTIMABLE = "NOT_ESTIMABLE"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    UNRELIABLE = "UNRELIABLE"


class ConfidenceIntervalMethod(str, Enum):
    EXACT_CLOPPER_PEARSON = "exact_clopper_pearson"
    WILSON_SCORE = "wilson_score"
    BOOTSTRAP_EVENT = "bootstrap_event"
    BOOTSTRAP_POINT = "bootstrap_point"
    NOT_ESTIMABLE = "not_estimable"


@dataclass
class ConfidenceInterval:
    lower: Optional[float]
    upper: Optional[float]
    alpha: float = 0.05
    method: ConfidenceIntervalMethod = ConfidenceIntervalMethod.EXACT_CLOPPER_PEARSON
    sample_size: int = 0
    unit: ValidationUnit = ValidationUnit.POINT
    is_reliable: bool = True
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower": round(self.lower, 4) if self.lower is not None else None,
            "upper": round(self.upper, 4) if self.upper is not None else None,
            "confidence_level": round(1.0 - self.alpha, 2),
            "method": self.method.value,
            "sample_size": self.sample_size,
            "unit": self.unit.value,
            "is_reliable": self.is_reliable,
            "reason": self.reason,
        }


@dataclass
class MetricResult:
    metric_name: str
    value: Optional[float]
    status: MetricStatus
    reason: Optional[str] = None
    n: int = 0
    unit: ValidationUnit = ValidationUnit.POINT
    threshold: Optional[float] = None
    is_threshold_dependent: bool = False
    threshold_source: Optional[str] = None
    confidence_interval: Optional[ConfidenceInterval] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "metric": self.metric_name,
            "value": round(self.value, 4) if self.value is not None else None,
            "status": self.status.value,
            "reason": self.reason,
            "n": self.n,
            "unit": self.unit.value,
            "is_threshold_dependent": self.is_threshold_dependent,
        }
        if self.is_threshold_dependent:
            d["threshold"] = self.threshold
            d["threshold_source"] = self.threshold_source
        if self.confidence_interval is not None:
            d["confidence_interval"] = self.confidence_interval.to_dict()
        return d


@dataclass
class SpatialIndependenceAudit:
    total_samples: int
    independent_count: int
    non_independent_count: int
    unknown_count: int = 0
    distance_threshold_m: float = 500.0
    primary_evaluation_subset: str = "INDEPENDENT"

    def __post_init__(self):
        if (self.independent_count + self.non_independent_count + self.unknown_count) != self.total_samples:
            raise ValueError(
                f"Independence partition invariant violated: {self.independent_count} + "
                f"{self.non_independent_count} + {self.unknown_count} != {self.total_samples}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClassBalanceAudit:
    total_count: int
    positive_count: int
    negative_count: int
    class_prevalence: float
    is_single_class: bool
    single_class_label: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EventIndependenceAudit:
    total_points: int
    total_events: int
    is_clustered_forcing: bool
    forcing_description: str
    primary_unit: ValidationUnit = ValidationUnit.SPATIAL_SAMPLE
    event_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.total_events > self.total_points:
            raise ValueError(
                f"Event count invariant violated: total_events ({self.total_events}) "
                f"cannot exceed total_points ({self.total_points})"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ControlItemAudit:
    control_id: str
    location_name: str
    latitude: float
    longitude: float
    observed_in_field: bool
    flood_explicitly_absent: bool
    temporally_matched: bool
    resolution_sufficient: bool
    outside_flood_extent: bool
    evidence_type: str
    validity: ControlValidity
    provenance_source: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["validity"] = self.validity.value
        return d


@dataclass
class ControlQualityAudit:
    total_controls: int
    valid_controls_count: int
    provisional_controls_count: int
    invalid_controls_count: int
    unknown_controls_count: int
    controls: List[ControlItemAudit] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_controls": self.total_controls,
            "valid_controls_count": self.valid_controls_count,
            "provisional_controls_count": self.provisional_controls_count,
            "invalid_controls_count": self.invalid_controls_count,
            "unknown_controls_count": self.unknown_controls_count,
            "controls": [c.to_dict() for c in self.controls],
        }


@dataclass
class ModelValidationAuditResult:
    model: str
    dataset_name: str
    validation_tier: ValidationTier
    primary_validation_unit: ValidationUnit
    spatial_independence: SpatialIndependenceAudit
    class_balance: ClassBalanceAudit
    event_audit: Optional[EventIndependenceAudit]
    control_quality: Optional[ControlQualityAudit]
    metrics: Dict[str, MetricResult]
    limitations: List[str]
    claims_supported: List[str]
    claims_unsupported: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "dataset_name": self.dataset_name,
            "validation_tier": self.validation_tier.value,
            "primary_validation_unit": self.primary_validation_unit.value,
            "spatial_independence": self.spatial_independence.to_dict(),
            "class_balance": self.class_balance.to_dict(),
            "event_audit": self.event_audit.to_dict() if self.event_audit else None,
            "control_quality": self.control_quality.to_dict() if self.control_quality else None,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "limitations": self.limitations,
            "claims_supported": self.claims_supported,
            "claims_unsupported": self.claims_unsupported,
        }
