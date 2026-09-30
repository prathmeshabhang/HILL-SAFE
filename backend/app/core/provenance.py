"""
backend/app/core/provenance.py
==============================
Authoritative Data Provenance & Operational Safety Boundary for FLOODY SHIELD.
Defines unambiguous data modes, isolation rules, and notification safety states.

Core Invariants:
1. Only verified REAL data (field IoT, statutory agency feeds, certified satellite)
   may drive LIVE OPERATIONAL risk evaluation and operational alert drafts.
2. SYNTHETIC, SIMULATED, REPLAY, PROXY, and TEST inputs are strictly quarantined
   to non-operational simulation and exercise pipelines.
3. Mixed inputs are subject to conservative non-operational tainting: if any input
   is non-operational, the composite risk state is classified as NON_OPERATIONAL / MIXED.
4. In SANDBOX notification mode, all notification channels are in-memory stubs;
   zero external network calls are transmitted over SMTP, SMS, or hardware sirens.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


class DataMode(str, Enum):
    """Authoritative Data Modes for Telemetry, Risk States, and Alerts."""

    # --- Operational Modes ---
    REAL_FIELD_OBSERVATION = "REAL_FIELD_OBSERVATION"
    REAL_AGENCY_DATA = "REAL_AGENCY_DATA"
    REMOTE_SENSING_OBSERVATION = "REMOTE_SENSING_OBSERVATION"

    # --- Non-Operational Modes ---
    PROXY_DATA = "PROXY_DATA"
    REPLAY = "REPLAY"
    SIMULATED = "SIMULATED"
    SYNTHETIC = "SYNTHETIC"
    TEST = "TEST"

    # --- Synthesized Composite Classifications ---
    OPERATIONAL = "OPERATIONAL"
    SIMULATION = "SIMULATION"
    MIXED = "MIXED"
    NON_OPERATIONAL = "NON_OPERATIONAL"


# Standardized categorization sets
OPERATIONAL_MODES: Set[str] = {
    DataMode.OPERATIONAL.value,
    DataMode.REAL_FIELD_OBSERVATION.value,
    DataMode.REAL_AGENCY_DATA.value,
    DataMode.REMOTE_SENSING_OBSERVATION.value,
    "REAL",  # Legacy/shorthand support
    "FIELD",
}

NON_OPERATIONAL_MODES: Set[str] = {
    DataMode.PROXY_DATA.value,
    DataMode.REPLAY.value,
    DataMode.SIMULATED.value,
    DataMode.SYNTHETIC.value,
    DataMode.TEST.value,
    DataMode.SIMULATION.value,
    DataMode.MIXED.value,
    DataMode.NON_OPERATIONAL.value,
    "PROXY",
    "EXERCISE",
}


class NotificationMode(str, Enum):
    """Controls whether notification dispatcher transmits to live gateways or safe sandbox."""
    SANDBOX = "SANDBOX"
    LIVE = "LIVE"


class DeliveryStatus(str, Enum):
    """Delivery confirmation semantics for notification providers."""
    SIMULATED = "SIMULATED"
    QUEUED = "QUEUED"
    ATTEMPTED = "ATTEMPTED"
    DELIVERED_CONFIRMED = "DELIVERED_CONFIRMED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


def is_operational_provenance(provenance_str: Optional[str]) -> bool:
    """Returns True if and only if the provenance string represents genuine operational data."""
    if not provenance_str:
        return False
    return provenance_str.strip().upper() in OPERATIONAL_MODES


def normalize_provenance(raw_provenance: Optional[str]) -> str:
    """Normalizes raw input provenance string into canonical DataMode value."""
    if not raw_provenance:
        return DataMode.SIMULATED.value

    clean = raw_provenance.strip().upper()
    if clean in ("OPERATIONAL", DataMode.OPERATIONAL.value):
        return DataMode.OPERATIONAL.value
    if clean in ("REAL", "FIELD", DataMode.REAL_FIELD_OBSERVATION.value):
        return DataMode.REAL_FIELD_OBSERVATION.value
    if clean in ("AGENCY", "CWC", "IMD", DataMode.REAL_AGENCY_DATA.value):
        return DataMode.REAL_AGENCY_DATA.value
    if clean in ("SATELLITE", "SENTINEL", DataMode.REMOTE_SENSING_OBSERVATION.value):
        return DataMode.REMOTE_SENSING_OBSERVATION.value
    if clean in ("REPLAY", "HISTORICAL", DataMode.REPLAY.value):
        return DataMode.REPLAY.value
    if clean in ("SYNTHETIC", DataMode.SYNTHETIC.value):
        return DataMode.SYNTHETIC.value
    if clean in ("TEST", DataMode.TEST.value):
        return DataMode.TEST.value
    if clean in ("PROXY", DataMode.PROXY_DATA.value):
        return DataMode.PROXY_DATA.value
    if clean in ("MIXED", DataMode.MIXED.value):
        return DataMode.MIXED.value
    if clean in ("SIMULATION", DataMode.SIMULATION.value):
        return DataMode.SIMULATION.value

    return DataMode.SIMULATED.value


def classify_provenance_mode(modes: Iterable[str]) -> Tuple[str, bool]:
    """
    Evaluates a collection of input provenance strings and determines composite data mode.

    Rule: Conservative Non-Operational Tainting
    A composite state is OPERATIONAL if and only if:
      1. At least one input exists.
      2. 100% of inputs are verified OPERATIONAL modes.
    If ANY input is SYNTHETIC, SIMULATED, REPLAY, PROXY, or TEST:
      - If all are REPLAY -> REPLAY
      - If all are SIMULATED or SYNTHETIC -> SIMULATION
      - If all are PROXY -> PROXY
      - If a mix of operational and non-operational -> MIXED (non-operational)

    Returns:
      Tuple of (composite_data_mode, is_operational_bool)
    """
    mode_list = [m.strip().upper() for m in modes if m]
    if not mode_list:
        return DataMode.SIMULATION.value, False

    all_operational = all(m in OPERATIONAL_MODES for m in mode_list)
    if all_operational:
        return DataMode.OPERATIONAL.value, True

    # Check for homogenous non-operational categories
    has_operational = any(m in OPERATIONAL_MODES for m in mode_list)
    has_replay = any(m in ("REPLAY", "HISTORICAL") for m in mode_list)
    has_sim = any(m in ("SIMULATED", "SYNTHETIC", "TEST", "SIMULATION") for m in mode_list)
    has_proxy = any(m in ("PROXY", "PROXY_DATA") for m in mode_list)

    if has_operational and (has_replay or has_sim or has_proxy):
        return DataMode.MIXED.value, False

    if has_replay and not has_sim and not has_proxy:
        return DataMode.REPLAY.value, False

    if has_proxy and not has_sim and not has_replay:
        return DataMode.PROXY_DATA.value, False

    return DataMode.SIMULATION.value, False


def get_cap_status_for_mode(data_mode: str) -> str:
    """
    Returns the statutory OASIS CAP v1.2 <status> string for a given data mode.
    Guarantees non-operational scenarios never generate 'Actual' alerts.
    """
    norm = data_mode.strip().upper()
    if norm == DataMode.OPERATIONAL.value or norm in OPERATIONAL_MODES:
        return "Actual"
    if norm in (DataMode.REPLAY.value, "EXERCISE", "HISTORICAL"):
        return "Exercise"
    return "Test"
