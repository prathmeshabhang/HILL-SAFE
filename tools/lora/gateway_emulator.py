"""
tools/lora/gateway_emulator.py
==============================
Outdoor LoRa Gateway Hardware Emulator for Upper Beas River Basin.
Simulates field reception of LPWAN radio frames, backhaul link disconnects,
flash buffer preservation, and automatic chronological replay upon reconnect.
"""

from __future__ import annotations

import argparse
import datetime
import time
from typing import Any, Dict, List, Optional
import requests

from tools.lora.packet_codec import lora_codec, DecodedLoRaPacket


class LoRaGatewayEmulator:
    """Emulates a ruggedized outdoor LoRa gateway (e.g. Multitech Conduit / Dragino DLOS8)."""

    def __init__(
        self,
        gateway_id: str = "GW_ROHTANG_01",
        backend_url: str = "http://localhost:8000/api/v1/telemetry",
        offline_capacity: int = 10000,
    ):
        self.gateway_id = gateway_id
        self.backend_url = backend_url
        self.offline_capacity = offline_capacity
        self.buffer: List[DecodedLoRaPacket] = []
        self.is_connected = True

    def set_backhaul_connection(self, connected: bool) -> None:
        self.is_connected = connected
        state = "ONLINE" if connected else "OFFLINE"
        print(f"[{self.gateway_id}] Backhaul connection switched to {state}")

    def receive_radio_frame(self, raw_bytes: bytes) -> Dict[str, Any]:
        """Receives a physical sub-GHz radio frame."""
        decoded = lora_codec.decode(raw_bytes)

        if not self.is_connected:
            if len(self.buffer) < self.offline_capacity:
                self.buffer.append(decoded)
            print(f"[{self.gateway_id}] BACKHAUL DOWN — Buffered frame seq={decoded.sequence_number} (Buffer size: {len(self.buffer)})")
            return {"status": "BUFFERED_OFFLINE", "buffer_size": len(self.buffer)}

        return self._forward_to_backend(decoded)

    def _forward_to_backend(self, packet: DecodedLoRaPacket) -> Dict[str, Any]:
        """Translates packet and posts to backend API."""
        obs_iso = datetime.datetime.fromtimestamp(packet.timestamp_epoch, tz=datetime.timezone.utc).isoformat()
        recv_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        station_id = f"ST_NODE_{packet.station_code}"
        device_id = f"DEV_NODE_{packet.station_code}"

        results = []
        for s in packet.sensors:
            payload = {
                "source_id": "LORA_GATEWAY_EMULATOR",
                "station_id": station_id,
                "device_id": device_id,
                "sensor_id": f"{device_id}_{s.sensor_type}",
                "observed_at": obs_iso,
                "received_at": recv_iso,
                "measurement_type": s.sensor_type,
                "value": s.value,
                "unit": s.unit,
                "sequence_number": packet.sequence_number,
                "firmware_version": f"v{packet.version}.0-lora",
            }
            try:
                resp = requests.post(self.backend_url, json=payload, timeout=5)
                results.append({"status_code": resp.status_code, "data": resp.json()})
            except Exception as e:
                results.append({"error": str(e)})

        return {"status": "FORWARDED", "station_id": station_id, "results": results}

    def reconnect_and_flush(self) -> Dict[str, Any]:
        """Re-establishes connection and replays buffer in chronological order."""
        self.set_backhaul_connection(True)
        if not self.buffer:
            return {"status": "NO_BUFFERED_DATA", "flushed_count": 0}

        print(f"[{self.gateway_id}] Replaying {len(self.buffer)} buffered packets in chronological order...")
        self.buffer.sort(key=lambda p: p.timestamp_epoch)
        replayed = 0
        for pkt in self.buffer:
            self._forward_to_backend(pkt)
            replayed += 1

        total_flushed = len(self.buffer)
        self.buffer.clear()
        return {"status": "BUFFER_FLUSHED", "flushed_count": total_flushed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoRa Gateway Hardware Emulator")
    parser.add_argument("--gateway-id", default="GW_ROHTANG_01", help="Gateway identifier")
    parser.add_argument("--url", default="http://localhost:8000/api/v1/telemetry", help="Backend ingestion URL")
    args = parser.parse_args()

    gw = LoRaGatewayEmulator(gateway_id=args.gateway_id, backend_url=args.url)
    print(f"LoRa Gateway {args.gateway_id} initialized listening on virtual radio interface.")
