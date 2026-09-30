"""
ml/decision/m14_infrastructure_loss/validation.py
=================================================
Validation and physical invariant checks for Model M14.
"""

from __future__ import annotations

from typing import Any, Dict, List
from ml.decision.m14_infrastructure_loss.assets import get_asset_or_default
from ml.decision.m14_infrastructure_loss.schema import DamageState, M14PredictionOutput


def validate_m14_prediction(output: M14PredictionOutput) -> Dict[str, Any]:
    """
    Validates physical invariants on Model M14 output:
      1. structural_damage_ratio in [0.0, 1.0]
      2. estimated_direct_loss_lakhs_inr >= 0.0
      3. estimated_direct_loss <= asset replacement value
      4. outage_hours >= 0.0
      5. uncertainty lower <= upper bounds
      6. damage state matches damage ratio thresholds
    """
    issues: List[str] = []
    asset = get_asset_or_default(output.asset_id)

    if not (0.0 <= output.structural_damage_ratio <= 1.0):
        issues.append(f"Damage ratio out of [0, 1]: {output.structural_damage_ratio}")

    if output.estimated_direct_loss_lakhs_inr < 0.0:
        issues.append(f"Loss is negative: {output.estimated_direct_loss_lakhs_inr}")

    max_val = asset.replacement_value_lakhs_inr * 1.02  # Allow 2% rounding margin
    if output.estimated_direct_loss_lakhs_inr > max_val:
        issues.append(f"Direct loss ({output.estimated_direct_loss_lakhs_inr}) exceeds replacement value ({asset.replacement_value_lakhs_inr})")

    if output.service_outage_hours < 0.0:
        issues.append(f"Outage hours negative: {output.service_outage_hours}")

    ci_loss = output.uncertainty.get("loss_lakhs_80ci", [0, 0])
    if ci_loss[0] > ci_loss[1]:
        issues.append(f"Loss CI inverted: {ci_loss}")

    ci_d = output.uncertainty.get("damage_ratio_80ci", [0, 0])
    if ci_d[0] > ci_d[1]:
        issues.append(f"Damage ratio CI inverted: {ci_d}")

    # Consistency check
    if output.damage_state == DamageState.COLLAPSED_DESTROYED and output.structural_damage_ratio < 0.70:
        issues.append("COLLAPSED_DESTROYED state requires damage ratio >= 0.70")

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "asset_id": output.asset_id,
        "damage_state": output.damage_state.value,
        "loss_lakhs": output.estimated_direct_loss_lakhs_inr,
    }
