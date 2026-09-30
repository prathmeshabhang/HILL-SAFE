"""
ml/flood/m12_cascade
====================
Model M12: Hazard Cascade & Landslide Dam Breach Engine.
"""

from ml.flood.m12_cascade.infer import get_model, predict
from ml.flood.m12_cascade.model import CompoundCascadeEngine, M12HazardCascadeModel
from ml.flood.m12_cascade.physics import (
    compute_costa_peak_outflow,
    compute_froehlich_breach_parameters,
)
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
    "M12HazardCascadeModel",
    "compute_costa_peak_outflow",
    "compute_froehlich_breach_parameters",
    "get_model",
    "predict",
    "CascadeSeverity",
    "DownstreamReachImpact",
    "EvacuationUrgency",
    "LandslideDamBreachResult",
    "M12CascadeInput",
    "M12PredictionOutput",
]
