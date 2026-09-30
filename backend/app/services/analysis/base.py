"""
backend/app/services/analysis/base.py
======================================
Common Analysis Interface for FLOODY SHIELD Physics and AI Intelligence Pipelines.
Enforces decoupled execution, explicit execution status, input requirement tracking,
provenance preservation, and structured evidence metadata.
"""

from __future__ import annotations

import abc
import datetime
from enum import Enum
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.provenance import (
    DataMode,
    classify_provenance_mode,
    is_operational_provenance,
    normalize_provenance,
)


class AnalysisStatus(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    ERROR = "ERROR"
    UNAVAILABLE = "UNAVAILABLE"


class AnalysisResult(BaseModel):
    """
    Uniform result schema produced by any FLOODY SHIELD analytical component
    (physics simulator, hydrologic model, AI booster, or terrain router).
    """
    component_name: str = Field(..., description="Technical identifier of analytical component")
    capability_name: str = Field(..., description="Operational capability name (e.g. Flood Intelligence)")
    execution_status: AnalysisStatus = Field(..., description="Component execution status")
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="UTC completion timestamp",
    )
    data_mode: str = Field(
        default=DataMode.REAL_FIELD_OBSERVATION.value,
        description="Effective provenance mode conforming to Phase 03 safety rules",
    )
    input_provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Breakdown of input sources and their respective data modes",
    )
    confidence_score: float = Field(
        1.0, ge=0.0, le=1.0, description="Calibrated confidence or uncertainty score (0.0 to 1.0)"
    )
    evidence_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scientific evidence tier, algorithm version, dataset citations, limitations",
    )
    processing_duration_ms: float = Field(
        0.0, ge=0.0, description="Server-side compute duration in milliseconds"
    )
    warnings: List[str] = Field(default_factory=list, description="Non-fatal operational warnings")
    errors: List[str] = Field(default_factory=list, description="Diagnostic error descriptions if failed")
    output_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Primary domain calculation metrics and spatial/temporal indicators",
    )

    def is_operational(self) -> bool:
        """Indicates whether this result is safe for live operational decision-support."""
        return is_operational_provenance(self.data_mode) and self.execution_status in (
            AnalysisStatus.READY,
            AnalysisStatus.DEGRADED,
        )


class AnalysisComponent(abc.ABC):
    """
    Abstract Base Class for decoupled analytical components.
    Guarantees that component failures remain strictly isolated and do not crash the risk engine.
    """

    def __init__(
        self,
        component_name: str,
        capability_name: str,
        input_requirements: List[str],
        output_type: str,
    ):
        self.component_name = component_name
        self.capability_name = capability_name
        self.input_requirements = input_requirements
        self.output_type = output_type
        self.status = AnalysisStatus.READY

    @abc.abstractmethod
    def _run_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Internal computation hook implemented by specific physics or AI models."""
        pass

    def evaluate_provenance(self, inputs: Dict[str, Any]) -> str:
        """
        Preserves Phase 03 provenance safety rules.
        Conservative Tainting: If any input is synthetic, simulated, or replay,
        the composite result is marked with that non-operational classification.
        """
        provenances = []
        # Check explicit provenance list
        if "provenance_list" in inputs and isinstance(inputs["provenance_list"], list):
            provenances.extend(inputs["provenance_list"])
        elif "input_provenances" in inputs and isinstance(inputs["input_provenances"], list):
            provenances.extend(inputs["input_provenances"])

        # Check top-level provenance tags
        for key in ("provenance", "data_mode", "mode", "rainfall_provenance", "soil_provenance"):
            if key in inputs and inputs[key]:
                provenances.append(str(inputs[key]))

        # Inspect nested dictionary provenance tags
        for v in inputs.values():
            if isinstance(v, dict) and "provenance" in v:
                prov_val = v["provenance"]
                if isinstance(prov_val, dict) and "data_mode" in prov_val:
                    provenances.append(str(prov_val["data_mode"]))
                elif isinstance(prov_val, str):
                    provenances.append(prov_val)

        mode_str, _ = classify_provenance_mode(provenances)
        return mode_str

    def execute(self, inputs: Dict[str, Any]) -> AnalysisResult:
        """
        Executes analysis with fail-soft isolation, timing, and strict provenance enforcement.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []
        errors: List[str] = []
        output_payload: Dict[str, Any] = {}
        status = AnalysisStatus.READY
        confidence = 1.0

        # 1. Check for missing critical inputs
        missing_inputs = [req for req in self.input_requirements if req not in inputs or inputs[req] is None]
        if missing_inputs:
            status = AnalysisStatus.DEGRADED
            warnings.append(f"Missing recommended inputs: {', '.join(missing_inputs)}")
            confidence = max(0.2, 1.0 - (len(missing_inputs) * 0.25))

        # 2. Evaluate composite provenance
        data_mode = self.evaluate_provenance(inputs)

        # 3. Execute isolated analysis
        try:
            output_payload = self._run_analysis(inputs)
            if "warnings" in output_payload:
                warnings.extend(output_payload.pop("warnings"))
            if "status_override" in output_payload:
                status = AnalysisStatus(output_payload.pop("status_override"))
            if "confidence" in output_payload:
                confidence = float(output_payload.pop("confidence"))
        except Exception as exc:
            status = AnalysisStatus.ERROR
            errors.append(f"{self.component_name} execution failed: {str(exc)}")
            confidence = 0.0
            output_payload = {"error": str(exc)}

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return AnalysisResult(
            component_name=self.component_name,
            capability_name=self.capability_name,
            execution_status=status,
            data_mode=data_mode,
            input_provenance={
                "effective_mode": data_mode,
                "is_operational": is_operational_provenance(data_mode),
                "inspected_keys": list(inputs.keys()),
            },
            confidence_score=round(confidence, 3),
            evidence_metadata=self.get_evidence_metadata(),
            processing_duration_ms=round(duration_ms, 2),
            warnings=warnings,
            errors=errors,
            output_payload=output_payload,
        )

    def get_evidence_metadata(self) -> Dict[str, Any]:
        """Provides transparency regarding underlying algorithms, datasets, and limitations."""
        return {
            "component": self.component_name,
            "capability": self.capability_name,
            "scientific_method": "Unspecified",
            "disclaimer": "Analytical output represents computational estimation; not direct physical measurement.",
        }
