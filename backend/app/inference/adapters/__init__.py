"""
backend/app/inference/adapters/__init__.py
==========================================
Exports and initializes all model adapters across the FLOODY SHIELD hazard chain.
"""

from typing import Dict, Type

from backend.app.inference.base import ModelAdapter
from backend.app.inference.adapters.hazard_adapters import (
    M1NowcastAdapter,
    M2FloodRiskAdapter,
    M4FloodSegmentationAdapter,
    M6SusceptibilityAdapter,
    M7TriggerAdapter,
    M8DeformationAdapter,
    M9AnomalyAdapter,
    M10WaterLevelAdapter,
    M11FloodDepthAdapter,
    M12CascadeAdapter,
    PWPSlopeStabilityAdapter,
)
from backend.app.inference.adapters.decision_adapters import (
    M13VulnerabilityAdapter,
    M14InfrastructureAdapter,
    M15SafeZoneAdapter,
    M16EvacuationRoutingAdapter,
    M17WarningGatingAdapter,
    M18CalibrationAdapter,
    M19TimeToImpactAdapter,
    M20DamageAssessmentAdapter,
)

ADAPTER_CLASSES: Dict[str, Type[ModelAdapter]] = {
    "M1": M1NowcastAdapter,
    "M2": M2FloodRiskAdapter,
    "M4": M4FloodSegmentationAdapter,
    "M6": M6SusceptibilityAdapter,
    "M7": M7TriggerAdapter,
    "M8": M8DeformationAdapter,
    "M9": M9AnomalyAdapter,
    "PWP_SSI": PWPSlopeStabilityAdapter,
    "M10": M10WaterLevelAdapter,
    "M11": M11FloodDepthAdapter,
    "M12": M12CascadeAdapter,
    "M13": M13VulnerabilityAdapter,
    "M14": M14InfrastructureAdapter,
    "M15": M15SafeZoneAdapter,
    "M16": M16EvacuationRoutingAdapter,
    "M17": M17WarningGatingAdapter,
    "M18": M18CalibrationAdapter,
    "M19": M19TimeToImpactAdapter,
    "M20": M20DamageAssessmentAdapter,
}

_ADAPTER_INSTANCES: Dict[str, ModelAdapter] = {}


def get_model_adapter(model_id: str) -> ModelAdapter:
    """Retrieves or instantiates the singleton adapter for a given model ID."""
    key = model_id.upper()
    if key not in _ADAPTER_INSTANCES:
        adapter_cls = ADAPTER_CLASSES.get(key)
        if not adapter_cls:
            raise ValueError(f"No adapter registered for model '{model_id}'")
        _ADAPTER_INSTANCES[key] = adapter_cls()
    return _ADAPTER_INSTANCES[key]
