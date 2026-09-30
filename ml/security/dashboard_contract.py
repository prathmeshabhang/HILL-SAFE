"""
ml/security/dashboard_contract.py
=================================
Stable API Data Contract for FLOODY SHIELD Dashboard and External Consumers.
Strictly requires every returned indicator, map layer, or prediction to declare its
truth status:
  - OBSERVATION: In-situ sensor or satellite measurement.
  - PREDICTED: Machine learning or statistical forecast.
  - MODELLED: Hydro-physical simulation or synthetic scenario.
  - DERIVED: Geometric or GIS spatial calculation.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValueTruthStatus(str, Enum):
    OBSERVED = "OBSERVED"        # Direct ground/remote measurement
    PREDICTED = "PREDICTED"      # ML / AI inference
    MODELLED = "MODELLED"        # Physics/hydrology simulation
    DERIVED = "DERIVED"          # GIS / topological transformation


@dataclass
class IndicatorContract:
    key: str
    value: Any
    unit: str
    truth_status: ValueTruthStatus
    timestamp: str               # ISO 8601 UTC
    model_or_source_id: str
    confidence: Optional[float] = None
    uncertainty_bounds: Optional[Dict[str, float]] = None
    data_quality_status: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["truth_status"] = self.truth_status.value
        return d


@dataclass
class DashboardPayloadContract:
    basin_name: str = "Upper Beas River Basin"
    generated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    system_version: str = "3.1.0"
    overall_alert_level: str = "ADVISORY"  # ADVISORY | WATCH | WARNING | EMERGENCY_EVACUATE
    indicators: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hazard_layers: List[Dict[str, Any]] = field(default_factory=list)
    safe_zones: List[Dict[str, Any]] = field(default_factory=list)
    evacuation_routes: List[Dict[str, Any]] = field(default_factory=list)
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_indicator(
        self,
        key: str,
        value: Any,
        unit: str,
        truth_status: ValueTruthStatus,
        source_id: str,
        confidence: Optional[float] = None,
        uncertainty: Optional[Dict[str, float]] = None,
        quality: str = "VALID",
    ) -> None:
        ind = IndicatorContract(
            key=key,
            value=value,
            unit=unit,
            truth_status=truth_status,
            timestamp=self.generated_at,
            model_or_source_id=source_id,
            confidence=confidence,
            uncertainty_bounds=uncertainty,
            data_quality_status=quality,
        )
        self.indicators[key] = ind.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
