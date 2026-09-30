"""
ml/decision/m17_warning_gating/gating_rules.py
===============================================
Authoritative disaster safety rules and lead-time mechanics for Model M17.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple
from ml.decision.m17_warning_gating.schema import (
    EvacuationStrategy,
    EvacuationUrgencyTier,
    M17WarningInput,
    WarningAlertLevel,
)


def evaluate_evacuation_lead_time(
    population: int,
    road_blocked: bool,
    bridge_down: bool,
    lead_time_min: float,
) -> Tuple[float, float, EvacuationStrategy, EvacuationUrgencyTier]:
    """
    Computes required evacuation clearance time (RET in minutes) and Evacuation Urgency Index (EUI).
    If EUI > 1.0 (water will arrive before full community can clear via road),
    forces VERTICAL_SHELTER_IN_PLACE to prevent citizens getting trapped on roads.
    """
    # Base clearance rate: ~60 persons per minute per evacuation lane/footpath
    # In hilly terrain, egress lanes are constrained
    lanes = 1 if (road_blocked or bridge_down) else 2
    egress_rate_per_min = 45.0 * lanes

    # Overhead time for community mobilization and notification dissemination: 20 min
    mobilization_min = 20.0
    transit_min = float(population) / egress_rate_per_min
    required_time_min = round(mobilization_min + transit_min, 1)

    effective_lead_time = max(5.0, lead_time_min)
    eui = round(required_time_min / effective_lead_time, 2)

    # Strategy selection
    if (road_blocked or bridge_down) and eui > 1.0:
        strategy = EvacuationStrategy.VERTICAL_SHELTER_IN_PLACE
    elif eui > 1.5:
        strategy = EvacuationStrategy.VERTICAL_SHELTER_IN_PLACE
    elif population > 3000 and eui > 0.8:
        strategy = EvacuationStrategy.COMBINED_PRIORITY_EVACUATION
    else:
        strategy = EvacuationStrategy.HORIZONTAL_ROAD_EVACUATION

    # Urgency tier
    if eui >= 1.0 or effective_lead_time <= 30.0:
        urgency = EvacuationUrgencyTier.IMMEDIATE_ACTION
    elif eui >= 0.50 or effective_lead_time <= 90.0:
        urgency = EvacuationUrgencyTier.STANDBY_STAGING
    elif eui >= 0.25 or effective_lead_time <= 240.0:
        urgency = EvacuationUrgencyTier.HEIGHTENED_ADVISORY
    else:
        urgency = EvacuationUrgencyTier.ROUTINE_MONITORING

    return required_time_min, eui, strategy, urgency


def check_deterministic_safety_override(inp: M17WarningInput) -> Tuple[bool, WarningAlertLevel, str]:
    """
    Life-safety determinism: Certain catastrophic threshold crossings
    MUST trigger mandatory RED_EVACUATE or ORANGE_ALERT regardless of ML model outputs.
    """
    # 1. River Stage >= Danger Level or High Flood Level
    if inp.river_water_level_m >= inp.danger_level_m:
        return True, WarningAlertLevel.RED_EVACUATE, (
            f"MANDATORY RED ALERT: River water level ({inp.river_water_level_m:.1f}m) has breached "
            f"CWC Danger Level ({inp.danger_level_m:.1f}m)."
        )

    # 2. Catastrophic Natural Dam Outburst Wave
    if inp.natural_dam_outburst_discharge_m3s >= 1000.0:
        return True, WarningAlertLevel.RED_EVACUATE, (
            f"MANDATORY RED ALERT: Active upstream natural dam outburst flood wave detected "
            f"(Peak Q={inp.natural_dam_outburst_discharge_m3s:.0f} m3/s)."
        )

    # 3. Severe Inundation Depth on Ground
    if inp.flood_depth_m >= 1.50:
        return True, WarningAlertLevel.RED_EVACUATE, (
            f"MANDATORY RED ALERT: Active floodplain inundation depth ({inp.flood_depth_m:.2f}m) exceeds 1.5m life-safety threshold."
        )

    # 4. Severe Landslide Trigger with Saturated Slope
    if inp.landslide_probability >= 0.80 and inp.pore_water_pressure_ratio >= 0.75:
        return True, WarningAlertLevel.RED_EVACUATE, (
            f"MANDATORY RED ALERT: Imminent slope failure trigger (P={inp.landslide_probability:.2f}) "
            f"with critical pore pressure saturation ({inp.pore_water_pressure_ratio:.2f})."
        )

    # 5. Warning Level Exceedance
    if inp.river_water_level_m >= inp.warning_level_m:
        return True, WarningAlertLevel.ORANGE_ALERT, (
            f"ORANGE ALERT OVERRIDE: River stage ({inp.river_water_level_m:.1f}m) has crossed CWC Warning Level ({inp.warning_level_m:.1f}m)."
        )

    return False, WarningAlertLevel.GREEN_NORMAL, "No deterministic safety override triggered."


def build_cap_payload(
    reach_id: str,
    alert_level: WarningAlertLevel,
    urgency_tier: EvacuationUrgencyTier,
    strategy: EvacuationStrategy,
    lead_time_min: float,
    eui: float,
    actions: List[str],
) -> Dict[str, Any]:
    """Generates NDMA Common Alerting Protocol (CAP) compliant message structure."""
    severity_map = {
        WarningAlertLevel.GREEN_NORMAL: "Minor",
        WarningAlertLevel.YELLOW_WATCH: "Moderate",
        WarningAlertLevel.ORANGE_ALERT: "Severe",
        WarningAlertLevel.RED_EVACUATE: "Extreme",
    }
    urgency_map = {
        EvacuationUrgencyTier.IMMEDIATE_ACTION: "Immediate",
        EvacuationUrgencyTier.STANDBY_STAGING: "Expected",
        EvacuationUrgencyTier.HEIGHTENED_ADVISORY: "Future",
        EvacuationUrgencyTier.ROUTINE_MONITORING: "Past",
    }

    return {
        "identifier": f"FLOODY_SHIELD_CAP_{reach_id}_{alert_level.value}",
        "sender": "DDMA_KULLU_EOC_AUTOMATED_SYSTEM",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "info": {
            "category": "Met",
            "event": "Flash Flood & Landslide Multi-Hazard Warning",
            "urgency": urgency_map.get(urgency_tier, "Expected"),
            "severity": severity_map.get(alert_level, "Moderate"),
            "certainty": "Observed" if alert_level == WarningAlertLevel.RED_EVACUATE else "Likely",
            "areaDesc": f"Upper Beas River Basin — Reach/Settlement: {reach_id}",
            "headline": f"{alert_level.value}: {strategy.value}",
            "lead_time_minutes": lead_time_min,
            "evacuation_urgency_index": eui,
            "instruction": " ".join(actions),
        },
    }
