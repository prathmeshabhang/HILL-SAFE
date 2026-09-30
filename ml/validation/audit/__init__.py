"""
ml.validation.audit — Common Scientific Validation-Audit Layer
==============================================================
Standardized schemas, independence auditing, class-balance verification,
confidence intervals, event-level checks, and conservative reporting.
"""

from ml.validation.audit.class_balance import (
    audit_class_balance,
    check_discrimination_metric_eligibility,
)
from ml.validation.audit.confidence_intervals import (
    bootstrap_metric_ci,
    exact_binomial_ci,
    wilson_score_ci,
)
from ml.validation.audit.control_quality import audit_flood_controls
from ml.validation.audit.event_level import (
    audit_event_structure,
    check_event_level_auc_eligibility,
)
from ml.validation.audit.independence import (
    audit_spatial_independence,
    haversine_distance_m,
)
from ml.validation.audit.metrics import evaluate_audited_metrics
from ml.validation.audit.report import (
    generate_conservative_claims,
    render_metric_markdown_table,
    save_audit_json,
)
from ml.validation.audit.schema import (
    ClassBalanceAudit,
    ConfidenceInterval,
    ConfidenceIntervalMethod,
    ControlItemAudit,
    ControlQualityAudit,
    ControlValidity,
    EventIndependenceAudit,
    IndependenceStatus,
    MetricResult,
    MetricStatus,
    ModelValidationAuditResult,
    SpatialIndependenceAudit,
    ValidationTier,
    ValidationUnit,
)

__all__ = [
    "ValidationUnit",
    "IndependenceStatus",
    "ControlValidity",
    "ValidationTier",
    "MetricStatus",
    "ConfidenceIntervalMethod",
    "ConfidenceInterval",
    "MetricResult",
    "SpatialIndependenceAudit",
    "ClassBalanceAudit",
    "EventIndependenceAudit",
    "ControlItemAudit",
    "ControlQualityAudit",
    "ModelValidationAuditResult",
    "haversine_distance_m",
    "audit_spatial_independence",
    "audit_class_balance",
    "check_discrimination_metric_eligibility",
    "exact_binomial_ci",
    "wilson_score_ci",
    "bootstrap_metric_ci",
    "audit_event_structure",
    "check_event_level_auc_eligibility",
    "audit_flood_controls",
    "evaluate_audited_metrics",
    "generate_conservative_claims",
    "save_audit_json",
    "render_metric_markdown_table",
]
