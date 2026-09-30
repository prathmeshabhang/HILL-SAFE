"""
ml/rainfall/m1_nowcast/infer.py
===============================
Inference interface for Model M1 Extreme Rainfall Nowcasting.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from ml.rainfall.m1_nowcast.model import M1RainfallNowcastModel

_default_model: Optional[M1RainfallNowcastModel] = None


def get_model() -> M1RainfallNowcastModel:
    global _default_model
    if _default_model is None:
        _default_model = M1RainfallNowcastModel()
    return _default_model


def predict(
    features: Dict[str, Any],
    rainfall_history: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Universal prediction endpoint for Model M1."""
    model = get_model()
    return model.predict(features, rainfall_history)
