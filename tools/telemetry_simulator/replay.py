"""
tools/telemetry_simulator/replay.py
===================================
Historical Event Replay Engine for Upper Beas River Basin (July 9–11, 2023).

Reconstructs the calibrated chronological progression of the catastrophic July 2023
flood, debris flow, and infrastructure destruction sequence across:
  - ST_MANALI_01 (Solang / Upper Beas Catchment)
  - ST_KULLU_01 (Sarvari Confluence / Kullu Town)
  - ST_BHUNTAR_01 (Parbati-Beas Confluence / Airport Reach)
  - ST_AUT_01 (Aut Gorge / NH-3 Corridor)
  - ST_LARJI_01 (Larji Hydropower Dam Reservoir)

Non-negotiable Invariant:
  All replayed data MUST be explicitly marked:
    provenance = "SIMULATED"
    environment = "TEST"
    historical_event_ref = "JULY_2023_UPPER_BEAS_FLOOD"
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Iterator, List, Optional


# Calibrated event steps representing the progression of July 9–11, 2023 catastrophe
# Timestamps normalized to ISO-8601 UTC
JULY_2023_EVENT_TIMELINE: List[Dict[str, Any]] = [
    {
        "step": 1,
        "event_time": "2023-07-08T18:00:00Z",
        "phase": "PRE_EVENT_MONSOON_INFLOW",
        "description": "Antecedent continuous rainfall across Beas catchment. River stage normal-high.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 12.5, "WATER_LEVEL": 1.8, "SOIL_MOISTURE": 68.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 15.0, "WATER_LEVEL": 2.1, "WATER_FLOW": 180.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 14.2, "WATER_LEVEL": 2.4, "WATER_FLOW": 260.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 11.0, "PORE_WATER_PRESSURE": 28.0, "TILT": 0.03, "WATER_LEVEL": 2.3},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 955.2, "WATER_FLOW": 290.0, "RAINFALL": 10.5},
        ],
    },
    {
        "step": 2,
        "event_time": "2023-07-09T02:00:00Z",
        "phase": "CONVECTIVE_INTENSIFICATION",
        "description": "High-intensity precipitation bands stall over Upper Beas and Solang Valley.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 48.0, "WATER_LEVEL": 3.2, "SOIL_MOISTURE": 82.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 38.5, "WATER_LEVEL": 3.5, "WATER_FLOW": 390.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 34.0, "WATER_LEVEL": 3.8, "WATER_FLOW": 510.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 30.0, "PORE_WATER_PRESSURE": 45.0, "TILT": 0.12, "WATER_LEVEL": 3.6},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 957.5, "WATER_FLOW": 580.0, "RAINFALL": 28.0},
        ],
    },
    {
        "step": 3,
        "event_time": "2023-07-09T08:00:00Z",
        "phase": "CLOUDBURST_AND_SURGE_PEAK",
        "description": "Extreme cloudburst event (>90 mm/hr in upper catchment). River stage breaches Danger Level.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 96.0, "WATER_LEVEL": 5.8, "SOIL_MOISTURE": 98.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 72.0, "WATER_LEVEL": 6.4, "WATER_FLOW": 920.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 65.0, "WATER_LEVEL": 7.1, "WATER_FLOW": 1350.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 58.0, "PORE_WATER_PRESSURE": 82.0, "TILT": 0.85, "WATER_LEVEL": 6.8},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 963.0, "WATER_FLOW": 1420.0, "RAINFALL": 54.0},
        ],
    },
    {
        "step": 4,
        "event_time": "2023-07-09T14:00:00Z",
        "phase": "CATASTROPHIC_DEBRIS_FLOW_AND_BREACH",
        "description": "Massive slope washouts, NH-3 roadway collapses, bridge scour at Bhuntar and Aut.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 64.0, "WATER_LEVEL": 6.2, "SOIL_MOISTURE": 100.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 58.0, "WATER_LEVEL": 7.5, "WATER_FLOW": 1450.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 52.0, "WATER_LEVEL": 8.4, "WATER_FLOW": 2100.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 62.0, "PORE_WATER_PRESSURE": 98.0, "TILT": 2.45, "WATER_LEVEL": 8.1},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 968.4, "WATER_FLOW": 2250.0, "RAINFALL": 50.0},
        ],
    },
    {
        "step": 5,
        "event_time": "2023-07-09T22:00:00Z",
        "phase": "PEAK_DISCHARGE_FLOOD_WAVE",
        "description": "Maximum hydrograph flood wave crest passing Aut and Larji dam spillways.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 32.0, "WATER_LEVEL": 5.4, "SOIL_MOISTURE": 95.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 30.0, "WATER_LEVEL": 6.9, "WATER_FLOW": 1280.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 28.0, "WATER_LEVEL": 7.9, "WATER_FLOW": 1850.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 35.0, "PORE_WATER_PRESSURE": 92.0, "TILT": 2.80, "WATER_LEVEL": 7.8},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 969.8, "WATER_FLOW": 2400.0, "RAINFALL": 32.0},
        ],
    },
    {
        "step": 6,
        "event_time": "2023-07-10T08:00:00Z",
        "phase": "SUSTAINED_HIGH_STAGE_AND_SECONDARY_SLIDES",
        "description": "Prolonged high groundwater saturation, progressive geotechnical failures along NH-3.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 18.0, "WATER_LEVEL": 4.2, "SOIL_MOISTURE": 90.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 20.0, "WATER_LEVEL": 5.2, "WATER_FLOW": 880.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 19.0, "WATER_LEVEL": 6.1, "WATER_FLOW": 1200.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 22.0, "PORE_WATER_PRESSURE": 78.0, "TILT": 3.10, "WATER_LEVEL": 5.9},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 964.5, "WATER_FLOW": 1350.0, "RAINFALL": 20.0},
        ],
    },
    {
        "step": 7,
        "event_time": "2023-07-10T20:00:00Z",
        "phase": "RECESSION_LIMB",
        "description": "Gradual cessation of storm; river begins slow recession while slopes remain unstable.",
        "readings": [
            {"station_id": "ST_MANALI_01", "RAINFALL": 4.5, "WATER_LEVEL": 3.1, "SOIL_MOISTURE": 82.0},
            {"station_id": "ST_KULLU_01", "RAINFALL": 5.2, "WATER_LEVEL": 3.8, "WATER_FLOW": 520.0},
            {"station_id": "ST_BHUNTAR_01", "RAINFALL": 4.8, "WATER_LEVEL": 4.3, "WATER_FLOW": 710.0},
            {"station_id": "ST_AUT_01", "RAINFALL": 6.0, "PORE_WATER_PRESSURE": 65.0, "TILT": 3.15, "WATER_LEVEL": 4.2},
            {"station_id": "ST_LARJI_01", "WATER_LEVEL": 960.0, "WATER_FLOW": 820.0, "RAINFALL": 5.0},
        ],
    },
]


def get_july_2023_event_timeline() -> List[Dict[str, Any]]:
    """Returns the calibrated July 2023 timeline data structure."""
    return list(JULY_2023_EVENT_TIMELINE)


class HistoricalDisasterReplay:
    """
    Chronological replay engine that converts the July 2023 disaster timeline
    into standard TelemetryPacketRequest dictionaries.
    """

    def __init__(self, time_offset_hours: Optional[float] = None):
        self.time_offset_hours = time_offset_hours
        self._seq = 5000

    def generate_step_packets(self, step_index: int) -> List[Dict[str, Any]]:
        """Generates all sensor packets for a specific disaster step."""
        if step_index < 0 or step_index >= len(JULY_2023_EVENT_TIMELINE):
            raise IndexError(f"Step index {step_index} out of range (0-{len(JULY_2023_EVENT_TIMELINE)-1})")

        step_data = JULY_2023_EVENT_TIMELINE[step_index]
        orig_dt = datetime.datetime.fromisoformat(step_data["event_time"].replace("Z", "+00:00"))

        if self.time_offset_hours is not None:
            now = datetime.datetime.now(datetime.timezone.utc)
            obs_dt = now - datetime.timedelta(hours=self.time_offset_hours)
        else:
            obs_dt = orig_dt

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        obs_str = obs_dt.isoformat()

        packets: List[Dict[str, Any]] = []
        for station_reading in step_data["readings"]:
            st_id = station_reading["station_id"]
            for mtype, val in station_reading.items():
                if mtype == "station_id":
                    continue
                self._seq += 1

                unit = "mm/h" if mtype == "RAINFALL" else "m"
                if mtype == "WATER_FLOW":
                    unit = "m3/s"
                elif mtype == "PORE_WATER_PRESSURE":
                    unit = "kPa"
                elif mtype == "TILT":
                    unit = "deg"
                elif mtype == "SOIL_MOISTURE":
                    unit = "%"

                pkt: Dict[str, Any] = {
                    "source_id": "REPLAY_HISTORICAL_JULY_2023",
                    "station_id": st_id,
                    "device_id": f"DEV_{st_id}",
                    "sensor_id": f"SNS_{st_id}_{mtype}",
                    "observed_at": obs_str,
                    "received_at": now_str,
                    "measurement_type": mtype,
                    "value": float(val),
                    "unit": unit,
                    "sequence_number": self._seq,
                    "firmware_version": "REPLAY-v3.5.0",
                    "quality_hint": "HISTORICAL_REPLAY",
                    "provenance": "SIMULATED",
                    "environment": "TEST",
                }
                packets.append(pkt)

        return packets

    def generate_all_packets(self) -> List[Dict[str, Any]]:
        """Generates all packets across all chronological phases."""
        all_pkts: List[Dict[str, Any]] = []
        for i in range(len(JULY_2023_EVENT_TIMELINE)):
            all_pkts.extend(self.generate_step_packets(i))
        return all_pkts
