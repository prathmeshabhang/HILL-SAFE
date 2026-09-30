"""
ml/decision/m17_warning_gating/infer.py
=======================================
Inference utilities and multi-reach early warning evaluation for Model M17.
"""

from __future__ import annotations

from typing import List, Optional
from ml.decision.m17_warning_gating.model import M17WarningGatingModel
from ml.decision.m17_warning_gating.schema import M17WarningInput, M17WarningOutput, WarningAlertLevel


_GLOBAL_MODEL: Optional[M17WarningGatingModel] = None


def get_m17_model() -> M17WarningGatingModel:
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is None:
        _GLOBAL_MODEL = M17WarningGatingModel()
    return _GLOBAL_MODEL


def issue_early_warning_and_evacuation(inp: M17WarningInput) -> M17WarningOutput:
    """Evaluates multi-hazard gating and issues warning / evacuation guidance for a reach/settlement."""
    return get_m17_model().predict(inp)


def evaluate_basin_alert_matrix(
    reach_inputs: List[M17WarningInput],
) -> List[M17WarningOutput]:
    """
    Evaluates warning levels across a list of reaches or settlements.
    Sorted with RED_EVACUATE first, then ORANGE, then YELLOW, then GREEN.
    """
    model = get_m17_model()
    outputs = [model.predict(inp) for inp in reach_inputs]

    level_order = {
        WarningAlertLevel.RED_EVACUATE: 0,
        WarningAlertLevel.ORANGE_ALERT: 1,
        WarningAlertLevel.YELLOW_WATCH: 2,
        WarningAlertLevel.GREEN_NORMAL: 3,
    }
    outputs.sort(key=lambda o: (level_order.get(o.alert_level, 4), -o.evacuation_urgency_index))
    return outputs
