"""
m12_compound_cascade.py — Multi-Hazard Compound Cascade & Landslide Dam Breach Engine
=====================================================================================
Backward-compatibility bridge re-exporting from ml.flood.m12_cascade.
"""

from __future__ import annotations

from ml.flood.m12_cascade.infer import predict
from ml.flood.m12_cascade.model import CompoundCascadeEngine, M12HazardCascadeModel
from ml.flood.m12_cascade.schema import (
    CascadeSeverity,
    DownstreamReachImpact,
    EvacuationUrgency,
    LandslideDamBreachResult,
    M12CascadeInput,
    M12PredictionOutput,
)

__all__ = [
    "CompoundCascadeEngine",
    "DownstreamReachImpact",
    "LandslideDamBreachResult",
    "CascadeSeverity",
    "EvacuationUrgency",
    "M12CascadeInput",
    "M12PredictionOutput",
    "M12HazardCascadeModel",
    "predict",
]
