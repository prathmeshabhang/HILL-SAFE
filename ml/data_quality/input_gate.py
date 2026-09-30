"""
ml/data_quality/input_gate.py
=============================
Shared Model Input Validation Gate for FLOODY SHIELD.
Enforces the mandatory pipeline order:
  RAW DATA -> SCHEMA VALIDATION -> PROVENANCE -> QUALITY CHECK -> FRESHNESS CHECK -> SPATIAL/TEMPORAL CHECK -> MODEL

Inference Invariants:
  - If QualityStatus == CRITICAL_ERROR: BLOCK INFERENCE.
  - If QualityStatus == DEGRADED: PASS THROUGH WITH REDUCED CONFIDENCE AND EXPLICIT WARNING.
  - If QualityStatus == VALID: NORMAL INFERENCE.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.schema import DataQualityReport, QualityStatus
from ml.data_quality.validator import DataQualityValidator


@dataclass
class InputGateResult:
    allowed: bool
    status: QualityStatus
    quality_report: DataQualityReport
    adjusted_confidence_multiplier: float  # 1.0 for VALID, 0.65 for DEGRADED, 0.0 for CRITICAL
    blocking_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "status": self.status.value,
            "adjusted_confidence_multiplier": self.adjusted_confidence_multiplier,
            "blocking_reasons": self.blocking_reasons,
            "warnings": self.warnings,
            "quality_report": self.quality_report.to_dict(),
        }


class ModelInputGate:
    """
    Guards model inference entry points, preventing models from silently
    consuming corrupt, stale, out-of-bounds, or unphysical inputs.
    """

    def __init__(
        self,
        validator: Optional[DataQualityValidator] = None,
        block_on_degraded: bool = False,
    ):
        self.validator = validator or DataQualityValidator()
        self.block_on_degraded = block_on_degraded

    def evaluate(
        self,
        sample_id: str,
        features: Dict[str, Any],
        provenance: Optional[DatasetProvenance] = None,
        observation_time_iso: Optional[str] = None,
        reference_now_iso: Optional[str] = None,
    ) -> InputGateResult:
        """
        Audits raw record across all quality gates before permitting inference.
        """
        report = self.validator.validate_record(
            sample_id=sample_id,
            features=features,
            provenance=provenance,
            observation_time_iso=observation_time_iso,
            reference_now_iso=reference_now_iso,
        )

        blocking_reasons = []
        warnings = []
        allowed = True
        confidence_multiplier = 1.0

        if report.status == QualityStatus.CRITICAL_ERROR:
            allowed = False
            confidence_multiplier = 0.0
            for flag in report.flags:
                if flag.severity.value == "CRITICAL":
                    blocking_reasons.append(f"[{flag.code}] {flag.message}")

        elif report.status == QualityStatus.DEGRADED:
            if self.block_on_degraded:
                allowed = False
                confidence_multiplier = 0.0
                blocking_reasons.append("ModelInputGate configured to block on DEGRADED inputs.")
            else:
                allowed = True
                confidence_multiplier = 0.65
                for flag in report.flags:
                    warnings.append(f"[{flag.code}] {flag.message}")

        elif report.status == QualityStatus.INSUFFICIENT_DATA:
            allowed = False
            confidence_multiplier = 0.0
            blocking_reasons.append("Insufficient data provided to perform valid inference.")

        return InputGateResult(
            allowed=allowed,
            status=report.status,
            quality_report=report,
            adjusted_confidence_multiplier=confidence_multiplier,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    def guard_inference(
        self,
        sample_id: str,
        features: Dict[str, Any],
        inference_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        provenance: Optional[DatasetProvenance] = None,
        observation_time_iso: Optional[str] = None,
        reference_now_iso: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes model inference safely wrapped inside the input gate.
        If blocked, returns a structured rejected response.
        If degraded, applies confidence multiplier and attaches warning.
        """
        gate_res = self.evaluate(
            sample_id=sample_id,
            features=features,
            provenance=provenance,
            observation_time_iso=observation_time_iso,
            reference_now_iso=reference_now_iso,
        )

        if not gate_res.allowed:
            return {
                "inference_status": "BLOCKED_BY_QUALITY_GATE",
                "sample_id": sample_id,
                "blocking_reasons": gate_res.blocking_reasons,
                "data_quality": gate_res.quality_report.to_dict(),
                "prediction": None,
                "confidence": 0.0,
            }

        # Run model inference
        raw_pred = inference_fn(features)

        # Scale confidence if degraded
        if gate_res.status == QualityStatus.DEGRADED and "confidence" in raw_pred:
            raw_pred["confidence"] = round(raw_pred["confidence"] * gate_res.adjusted_confidence_multiplier, 4)
            raw_pred["gate_warnings"] = gate_res.warnings

        raw_pred["data_quality"] = gate_res.quality_report.to_dict()
        return raw_pred
