"""
tools/telemetry_simulator/__init__.py
=====================================
FLOODY SHIELD Synthetic Telemetry Simulator & Historical Replay Engine.
Designed for stress testing, failure injection, and field-pilot verification.

All generated and replayed telemetry packets explicitly carry:
    provenance = "SIMULATED"
    environment = "TEST"
"""

from tools.telemetry_simulator.generator import (
    TelemetrySimulator,
    SimulationScenario,
    generate_scenario_packets,
)
from tools.telemetry_simulator.replay import (
    HistoricalDisasterReplay,
    get_july_2023_event_timeline,
)

__all__ = [
    "TelemetrySimulator",
    "SimulationScenario",
    "generate_scenario_packets",
    "HistoricalDisasterReplay",
    "get_july_2023_event_timeline",
]
