"""
ml/decision/m17_warning_gating/validation.py
============================================
Validation and safety override invariant checks for Model M17.
"""

from __future__ import annotations

from typing import Any, Dict, List
from ml.decision.m17_warning_gating.schema import (
    EvacuationStrategy,
    M17WarningInput,
    M17WarningOutput,
    WarningAlertLevel,
)


def validate_m17_prediction(output: M17WarningOutput, inp: M17WarningInput) -> Dict[str, Any]:
    """
    Validates physical and life-safety invariants:
      1. If water level >= danger level, alert level MUST be RED_EVACUATE (Zero false negative rule).
      2. If natural dam outburst Q >= 1000 m3/s, alert level MUST be RED_EVACUATE.
      3. EUI >= 0.0 and lead_time >= 0.0.
      4. If road is blocked and EUI > 1.0, strategy MUST be VERTICAL_SHELTER_IN_PLACE.
      5. CAP compliant payload has required OASIS CAP v1.2 structure.
    """
    issues: List[str] = []

    # Zero False Negative Checks on Dangerous Thresholds
    if inp.river_water_level_m >= inp.danger_level_m and output.alert_level != WarningAlertLevel.RED_EVACUATE:
        issues.append(f"SAFETY VIOLATION: Water level ({inp.river_water_level_m}m) breached Danger Level ({inp.danger_level_m}m) but alert is not RED_EVACUATE.")

    if inp.natural_dam_outburst_discharge_m3s >= 1000.0 and output.alert_level != WarningAlertLevel.RED_EVACUATE:
        issues.append(f"SAFETY VIOLATION: Dam outburst ({inp.natural_dam_outburst_discharge_m3s} m3/s) active but alert is not RED_EVACUATE.")

    if output.evacuation_urgency_index < 0.0:
        issues.append(f"EUI is negative: {output.evacuation_urgency_index}")

    if output.lead_time_minutes < 0.0:
        issues.append(f"Lead time is negative: {output.lead_time_minutes}")

    if inp.arterial_road_blocked and output.evacuation_urgency_index > 1.0:
        if output.evacuation_strategy != EvacuationStrategy.VERTICAL_SHELTER_IN_PLACE:
            issues.append("SAFETY VIOLATION: Road blocked and EUI > 1.0 requires VERTICAL_SHELTER_IN_PLACE.")

    # CAP payload validation
    cap = output.cap_compliant_payload
    for cap_key in ["identifier", "sender", "status", "msgType", "scope", "info"]:
        if cap_key not in cap:
            issues.append(f"CAP payload missing required key: {cap_key}")

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "reach_or_settlement_id": output.reach_or_settlement_id,
        "alert_level": output.alert_level.value,
        "strategy": output.evacuation_strategy.value,
    }
