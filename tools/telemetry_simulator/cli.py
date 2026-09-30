"""
tools/telemetry_simulator/cli.py
================================
Command-Line Interface for FLOODY SHIELD Telemetry Simulator & Replay Engine.

Usage Examples:
    # Run 50 cloudburst spike packets against local server
    python -m tools.telemetry_simulator.cli --scenario CLOUDBURST_SPIKE --count 50

    # Dry-run historical July 2023 replay
    python -m tools.telemetry_simulator.cli --replay-july-2023 --dry-run

    # Replay July 2023 to live backend endpoint
    python -m tools.telemetry_simulator.cli --replay-july-2023 --target-url http://localhost:8000/api/v1/telemetry/batch
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List
import urllib.error
import urllib.request

from tools.telemetry_simulator.generator import (
    SimulationScenario,
    TelemetrySimulator,
    generate_scenario_packets,
)
from tools.telemetry_simulator.replay import HistoricalDisasterReplay


def send_batch_http(target_url: str, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Posts batch of packets via HTTP without requiring third-party requests library."""
    payload = json.dumps({"packets": packets}).encode("utf-8")
    req = urllib.request.Request(
        target_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "FloodyShield-Simulator/v3.5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_data = resp.read().decode("utf-8")
            return json.loads(resp_data)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"error": f"HTTP {e.code}: {e.reason}", "details": err_body}
    except Exception as e:
        return {"error": str(e)}


def main() -> int:
    parser = argparse.ArgumentParser(description="FLOODY SHIELD Synthetic Telemetry Simulator CLI")
    parser.add_argument(
        "--scenario",
        choices=[s.value for s in SimulationScenario],
        default=SimulationScenario.NORMAL_MONSOON.value,
        help="Simulation scenario type",
    )
    parser.add_argument("--count", type=int, default=20, help="Number of packets to generate")
    parser.add_argument("--replay-july-2023", action="store_true", help="Replay historical July 2023 catastrophe")
    parser.add_argument("--target-url", type=str, default="http://localhost:8000/api/v1/telemetry/batch", help="Target API endpoint")
    parser.add_argument("--dry-run", action="store_true", help="Print generated packets to stdout without sending")

    args = parser.parse_args()

    print("[*] FLOODY SHIELD v3.5 Telemetry Simulator")
    print(f"[*] Provenance: SIMULATED | Environment: TEST")

    if args.replay_july_2023:
        print("[+] Replaying Historical July 2023 Upper Beas Disaster Sequence...")
        replay = HistoricalDisasterReplay(time_offset_hours=0.5)
        packets = replay.generate_all_packets()
    else:
        scenario = SimulationScenario(args.scenario)
        print(f"[+] Generating {args.count} packets for scenario: {scenario.value}")
        packets = generate_scenario_packets(scenario=scenario, count=args.count)

    print(f"[+] Generated {len(packets)} packets.")

    if args.dry_run:
        print("[+] DRY-RUN MODE: Sample packet:")
        print(json.dumps(packets[0] if packets else {}, indent=2))
        return 0

    print(f"[+] Dispatching to {args.target_url}...")
    res = send_batch_http(args.target_url, packets)
    print(f"[+] Response: {json.dumps(res, indent=2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
