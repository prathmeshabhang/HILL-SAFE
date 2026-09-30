"""
ml/validation/framework/__init__.py
===================================
Common validation framework public exports.
"""

from ml.validation.framework.schema import (
    ControlValidity,
    EvaluationSampleRecord,
    EventIndependenceSummary,
    IndependenceStatus,
    MetricStatus,
    SpatialIndependenceSummary,
    ValidationTier,
    ValidationUnit,
    audit_dataset_event_independence,
    audit_dataset_spatial_independence,
    determine_validation_status,
    haversine_distance_m,
)
from ml.validation.framework.uncertainty import (
    ConfidenceInterval,
    audit_spatial_difference_significance,
    cluster_aware_bootstrap_ci,
    exact_clopper_pearson_ci,
)

__all__ = [
    "ControlValidity",
    "EvaluationSampleRecord",
    "EventIndependenceSummary",
    "IndependenceStatus",
    "MetricStatus",
    "SpatialIndependenceSummary",
    "ValidationTier",
    "ValidationUnit",
    "audit_dataset_event_independence",
    "audit_dataset_spatial_independence",
    "determine_validation_status",
    "haversine_distance_m",
    "ConfidenceInterval",
    "audit_spatial_difference_significance",
    "cluster_aware_bootstrap_ci",
    "exact_clopper_pearson_ci",
]
