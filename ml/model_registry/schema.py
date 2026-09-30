"""
ml/model_registry/schema.py
==========================
Data structures and schema for FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ModelStatus(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    INTERNAL_VALIDATED = "INTERNAL_VALIDATED"
    EXTERNALLY_VALIDATED = "EXTERNALLY_VALIDATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FROZEN = "FROZEN"


@dataclass
class ModelMetadata:
    model_id: str
    model_name: str
    version: str
    artifact_path: str
    sha256: str
    training_dataset_id: str
    feature_schema_version: str
    training_period: Optional[str] = None
    validation_period: Optional[str] = None
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    status: ModelStatus = ModelStatus.DEVELOPMENT
    registered_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d
