"""
tools/telemetry_simulator/generator.py
======================================
Synthetic Field Telemetry Stream Generator for FLOODY SHIELD v3.5.

Supports generating realistic sensor observations across the Upper Beas River Basin
(Kullu, Manali, Bhuntar, Aut, Larji) under various operational and stress scenarios:
  1. NORMAL_MONSOON: Realistic diurnal monsoon rainfall and moderate river discharge.
  2. CLOUDBURST_SPIKE: Severe convective rainfall peak (>100 mm/h), rapid river stage rise.
  3. SENSOR_FAILURE: Missing data, out-of-bounds readings, NaN/Inf, dead battery voltage.
  4. PACKET_LOSS: Severe communication dropout simulating mountain terrain telemetry loss.
  5. REPLAY_TAMPERING: Replay attack generation with matching hash keys but tampered payload values.
  6. CLOCK_SKEW: Timestamps with historical lag, extreme staleness, or future clock drift.

Non-negotiable Invariant:
  All synthetic packets MUST include:
    provenance = "SIMULATED"
    environment = "TEST"
"""

from __future__ import annotations

import datetime
from enum import Enum
import math
import random
from typing import Any, Dict, List, Optional


class SimulationScenario(str, Enum):
    NORMAL_MONSOON = "NORMAL_MONSOON"
    CLOUDBURST_SPIKE = "CLOUDBURST_SPIKE"
    SENSOR_FAILURE = "SENSOR_FAILURE"
    PACKET_LOSS = "PACKET_LOSS"
    REPLAY_TAMPERING = "REPLAY_TAMPERING"
    CLOCK_SKEW = "CLOCK_SKEW"


UPPER_BEAS_STATIONS = {
    "ST_MANALI_01": {
        "name": "Manali Club House / Catchment Gauge",
        "lat": 32.255,
        "lon": 77.185,
        "elev": 2050.0,
        "device_id": "DEV_MANALI_01",
        "sensors": ["RAIN_GAUGE", "WATER_LEVEL", "SOIL_MOISTURE"],
    },
    "ST_KULLU_01": {
        "name": "Kullu Sarvari Confluence Gauge",
        "lat": 31.960,
        "lon": 77.112,
        "elev": 1220.0,
        "device_id": "DEV_KULLU_01",
        "sensors": ["RAIN_GAUGE", "WATER_LEVEL", "WATER_FLOW"],
    },
    "ST_BHUNTAR_01": {
        "name": "Bhuntar Parbati-Beas Confluence",
        "lat": 31.885,
        "lon": 77.160,
        "elev": 1090.0,
        "device_id": "DEV_BHUNTAR_01",
        "sensors": ["RAIN_GAUGE", "WATER_LEVEL", "WATER_FLOW"],
    },
    "ST_AUT_01": {
        "name": "Aut Gorge Slope & River Gauge",
        "lat": 31.745,
        "lon": 77.180,
        "elev": 960.0,
        "device_id": "DEV_AUT_01",
        "sensors": ["RAIN_GAUGE", "PORE_WATER_PRESSURE", "TILT", "WATER_LEVEL"],
    },
    "ST_LARJI_01": {
        "name": "Larji Dam Hydropower Inflow",
        "lat": 31.715,
        "lon": 77.220,
        "elev": 950.0,
        "device_id": "DEV_LARJI_01",
        "sensors": ["WATER_LEVEL", "WATER_FLOW", "RAIN_GAUGE"],
    },
}

SENSOR_UNITS = {
    "RAINFALL": "mm/h",
    "WATER_LEVEL": "m",
    "WATER_FLOW": "m3/s",
    "SOIL_MOISTURE": "%",
    "PORE_WATER_PRESSURE": "kPa",
    "TILT": "deg",
    "BATTERY": "V",
}


class TelemetrySimulator:
    def __init__(self, seed: Optional[int] = 42):
        if seed is not None:
            random.seed(seed)
        self.seq_counters: Dict[str, int] = {}

    def _next_seq(self, device_id: str) -> int:
        curr = self.seq_counters.get(device_id, 1000) + 1
        self.seq_counters[device_id] = curr
        return curr

    def generate_packet(
        self,
        station_id: str,
        measurement_type: str,
        scenario: SimulationScenario = SimulationScenario.NORMAL_MONSOON,
        timestamp: Optional[datetime.datetime] = None,
        base_value: Optional[float] = None,
        tamper: bool = False,
    ) -> Dict[str, Any]:
        """Generates a single simulated telemetry packet adhering to TelemetryPacketRequest."""
        now = datetime.datetime.now(datetime.timezone.utc)
        obs_time = timestamp or now
        station_info = UPPER_BEAS_STATIONS.get(station_id, {
            "device_id": f"DEV_{station_id}",
            "sensors": [measurement_type],
        })
        device_id = station_info.get("device_id", f"DEV_{station_id}")
        sensor_id = f"SNS_{station_id}_{measurement_type}"
        unit = SENSOR_UNITS.get(measurement_type, "unit")
        seq = self._next_seq(device_id)

        # Value calculation based on scenario
        val = 0.0
        if scenario == SimulationScenario.NORMAL_MONSOON:
            if measurement_type == "RAINFALL":
                val = round(max(0.0, random.gauss(8.0, 4.0)), 2)
            elif measurement_type == "WATER_LEVEL":
                val = round(max(0.5, random.gauss(2.2, 0.3)), 2)
            elif measurement_type == "WATER_FLOW":
                val = round(max(10.0, random.gauss(150.0, 25.0)), 1)
            elif measurement_type == "PORE_WATER_PRESSURE":
                val = round(max(5.0, random.gauss(25.0, 5.0)), 2)
            elif measurement_type == "TILT":
                val = round(random.gauss(0.02, 0.01), 3)
            elif measurement_type == "BATTERY":
                val = round(random.uniform(12.2, 12.8), 2)
            else:
                val = round(random.uniform(10.0, 50.0), 2)

        elif scenario == SimulationScenario.CLOUDBURST_SPIKE:
            if measurement_type == "RAINFALL":
                val = round(random.uniform(95.0, 145.0), 2)  # Extreme cloudburst intensity
            elif measurement_type == "WATER_LEVEL":
                val = round(random.uniform(6.5, 9.8), 2)  # Surging past danger level
            elif measurement_type == "WATER_FLOW":
                val = round(random.uniform(850.0, 1800.0), 1)  # Catastrophic surge
            elif measurement_type == "PORE_WATER_PRESSURE":
                val = round(random.uniform(75.0, 110.0), 2)  # Near liquefaction
            elif measurement_type == "TILT":
                val = round(random.uniform(1.8, 4.5), 3)  # Rapid slope displacement
            elif measurement_type == "BATTERY":
                val = round(random.uniform(11.5, 12.1), 2)
            else:
                val = round(random.uniform(80.0, 120.0), 2)

        elif scenario == SimulationScenario.SENSOR_FAILURE:
            failure_mode = random.choice(["NEGATIVE", "OUT_OF_BOUNDS", "DEAD_BATTERY"])
            if failure_mode == "NEGATIVE":
                val = -15.5  # Impossible physical value
            elif failure_mode == "OUT_OF_BOUNDS":
                val = 9999.0  # Absurd sensor runaway
            else:
                val = 0.0  # Zero reading / dead sensor

        elif scenario == SimulationScenario.CLOCK_SKEW:
            # Shift observation timestamp into past (stale) or future
            skew_type = random.choice(["STALE", "FUTURE_INVALID", "SLIGHT_LATE"])
            if skew_type == "STALE":
                obs_time = now - datetime.timedelta(hours=8)
            elif skew_type == "FUTURE_INVALID":
                obs_time = now + datetime.timedelta(hours=3)  # Exceeds 120m limit -> INVALID
            else:
                obs_time = now - datetime.timedelta(minutes=15)
            val = round(random.uniform(5.0, 20.0), 2)

        else:
            val = round(random.uniform(5.0, 25.0), 2)

        if base_value is not None:
            val = base_value

        packet: Dict[str, Any] = {
            "source_id": "SIMULATOR_UPPER_BEAS",
            "station_id": station_id,
            "device_id": device_id,
            "sensor_id": sensor_id,
            "observed_at": obs_time.isoformat(),
            "received_at": now.isoformat(),
            "measurement_type": measurement_type,
            "value": val,
            "unit": unit,
            "sequence_number": seq,
            "firmware_version": "SIM-v3.5.0",
            "quality_hint": "SIMULATED_TEST",
            "provenance": "SIMULATED",
            "environment": "TEST",
        }

        if tamper:
            # Tamper with the value while keeping other attributes to test replay tampering
            packet["value"] = val + 99.9

        return packet

    def generate_batch(
        self,
        count: int = 20,
        scenario: SimulationScenario = SimulationScenario.NORMAL_MONSOON,
        stations: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generates a batch of simulated packets."""
        active_stations = stations or list(UPPER_BEAS_STATIONS.keys())
        packets: List[Dict[str, Any]] = []

        for _ in range(count):
            if scenario == SimulationScenario.PACKET_LOSS and random.random() < 0.6:
                continue  # Simulate 60% packet transmission drop

            st = random.choice(active_stations)
            sensor = random.choice(["RAINFALL", "WATER_LEVEL", "PORE_WATER_PRESSURE", "TILT"])
            packet = self.generate_packet(
                station_id=st,
                measurement_type=sensor,
                scenario=scenario,
            )
            packets.append(packet)

        return packets


def generate_scenario_packets(
    scenario: SimulationScenario,
    count: int = 25,
    seed: Optional[int] = 42,
) -> List[Dict[str, Any]]:
    """Helper convenience function to quickly obtain scenario-specific packets."""
    sim = TelemetrySimulator(seed=seed)
    return sim.generate_batch(count=count, scenario=scenario)
