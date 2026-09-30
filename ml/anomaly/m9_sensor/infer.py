"""
ml/anomaly/m9_sensor/infer.py
=============================
Production inference entry point for Model M9.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from ml.anomaly.m9_sensor.model import M9SensorAnomalyModel

_default_model: Optional[M9SensorAnomalyModel] = None


def get_model() -> M9SensorAnomalyModel:
    global _default_model
    if _default_model is None:
        _default_model = M9SensorAnomalyModel()
    return _default_model


def predict(
    features: Dict[str, Any],
    recent_history: Optional[Sequence[Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """Universal prediction endpoint for Model M9."""
    model = get_model()
    return model.predict(features, recent_history)
