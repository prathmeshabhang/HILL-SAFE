"""
backend/app/services/ingestion/lora_gateway.py
==============================================
LoRa Gateway Translation, Sequence Tracking, Offline Buffering, and Ingestion Engine.
Normalizes compact binary LPWAN packets into canonical Floody Shield telemetry,
tracks sequence number continuity, and handles cellular backhaul disconnection/replay.
"""

from __future__ import annotations

import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from tools.lora.packet_codec import (
    LoRaPacketCodec,
    DecodedLoRaPacket,
    lora_codec,
)
from backend.app.services.ingestion.ingestion_service import ingestion_service
from backend.app.services.devices.registry_service import device_registry_service
from backend.app.core.logging import get_logger

logger = get_logger("floody.ingestion.lora_gateway")

# Mapping numeric station codes to canonical Station IDs and Device IDs
STATION_CODE_MAP: Dict[int, Dict[str, str]] = {
    101: {"station_id": "ST_MANALI_01", "device_id": "DEV_MANALI_01"},
    102: {"station_id": "ST_KULLU_01", "device_id": "DEV_KULLU_01"},
    103: {"station_id": "ST_BHUNTAR_01", "device_id": "DEV_BHUNTAR_01"},
    104: {"station_id": "ST_AUT_01", "device_id": "DEV_AUT_01"},
    105: {"station_id": "ST_LARJI_01", "device_id": "DEV_LARJI_01"},
}


class SequenceState:
    IN_ORDER = "IN_ORDER"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    GAP_DETECTED = "GAP_DETECTED"


@dataclass
class SequenceTracker:
    last_seq: Optional[int] = None
    total_received: int = 0
    total_duplicates: int = 0
    total_gaps: int = 0
    total_dropped: int = 0

    def update(self, seq: int) -> Tuple[str, int]:
        """
        Analyzes sequence number. Handles 16-bit unsigned integer rollover (0..65535).
        Returns: (state, dropped_packet_count)
        """
        self.total_received += 1
        if self.last_seq is None:
            self.last_seq = seq
            return SequenceState.IN_ORDER, 0

        # Handle 16-bit rollover
        diff = (seq - self.last_seq) & 0xFFFF

        if diff == 0:
            self.total_duplicates += 1
            return SequenceState.DUPLICATE, 0
        elif diff == 1:
            self.last_seq = seq
            return SequenceState.IN_ORDER, 0
        elif diff > 32768:
            # Out of order or old delayed packet
            return SequenceState.OUT_OF_ORDER, 0
        else:
            # Gap detected
            dropped = diff - 1
            self.total_gaps += 1
            self.total_dropped += dropped
            self.last_seq = seq
            return SequenceState.GAP_DETECTED, dropped

    @property
    def packet_loss_pct(self) -> float:
        expected = self.total_received + self.total_dropped
        if expected <= 0:
            return 0.0
        return round((self.total_dropped / expected) * 100.0, 2)


class GatewayOfflineBuffer:
    """
    Simulates local gateway flash storage / ring buffer.
    Buffers packets when cellular backhaul connection is down.
    Flushes packets chronologically when backhaul connection is restored.
    """

    def __init__(self, max_capacity: int = 5000):
        self._buffer: deque[DecodedLoRaPacket] = deque(maxlen=max_capacity)

    def append(self, packet: DecodedLoRaPacket) -> None:
        self._buffer.append(packet)

    def size(self) -> int:
        return len(self._buffer)

    def is_empty(self) -> bool:
        return len(self._buffer) == 0

    def drain_chronological(self) -> List[DecodedLoRaPacket]:
        """Drains and sorts buffered packets by timestamp_epoch."""
        packets = list(self._buffer)
        self._buffer.clear()
        packets.sort(key=lambda p: p.timestamp_epoch)
        return packets


class LoRaGatewayService:
    """Orchestrates LoRa packet reception, sequence continuity, and backend normalization."""

    def __init__(self):
        self.codec = lora_codec
        self.trackers: Dict[str, SequenceTracker] = {}
        self.offline_buffers: Dict[str, GatewayOfflineBuffer] = {}
        self.is_backhaul_online: bool = True

    def set_backhaul_status(self, online: bool) -> None:
        self.is_backhaul_online = online

    def get_tracker(self, device_id: str) -> SequenceTracker:
        if device_id not in self.trackers:
            self.trackers[device_id] = SequenceTracker()
        return self.trackers[device_id]

    def get_buffer(self, gateway_id: str = "GW_ROHTANG_01") -> GatewayOfflineBuffer:
        if gateway_id not in self.offline_buffers:
            self.offline_buffers[gateway_id] = GatewayOfflineBuffer()
        return self.offline_buffers[gateway_id]

    def process_raw_frame(
        self,
        db: Session,
        raw_bytes: bytes,
        gateway_id: str = "GW_ROHTANG_01",
    ) -> Dict[str, Any]:
        """
        1. Decode LoRa binary payload and verify CRC-16.
        2. Resolve station and device identity.
        3. Check sequence continuity.
        4. If backhaul offline, buffer packet.
        5. If backhaul online, translate and persist via ingestion_service.
        """
        decoded = self.codec.decode(raw_bytes)
        mapping = STATION_CODE_MAP.get(
            decoded.station_code,
            {
                "station_id": f"ST_UNKNOWN_{decoded.station_code}",
                "device_id": f"DEV_UNKNOWN_{decoded.station_code}",
            },
        )
        station_id = mapping["station_id"]
        device_id = mapping["device_id"]

        tracker = self.get_tracker(device_id)
        seq_state, dropped = tracker.update(decoded.sequence_number)

        obs_dt = datetime.datetime.fromtimestamp(decoded.timestamp_epoch, tz=datetime.timezone.utc)
        recv_dt = datetime.datetime.now(datetime.timezone.utc)

        # Record heartbeat telemetry into device registry
        try:
            device_registry_service.record_heartbeat(
                db=db,
                device_id=device_id,
                battery_voltage=decoded.battery_voltage,
                battery_percentage=max(0.0, min(100.0, (decoded.battery_voltage - 11.0) / (12.8 - 11.0) * 100.0)),
                rssi_dbm=float(decoded.rssi_dbm),
                snr_db=float(decoded.snr_db),
                error_flags=0,
            )
        except Exception as e:
            logger.warning(f"Could not record heartbeat for device {device_id}: {e}")

        # Check backhaul state
        if not self.is_backhaul_online:
            buf = self.get_buffer(gateway_id)
            buf.append(decoded)
            return {
                "status": "BUFFERED_OFFLINE",
                "gateway_id": gateway_id,
                "buffered_packets": buf.size(),
                "sequence_state": seq_state,
                "dropped_count": dropped,
                "packet_loss_pct": tracker.packet_loss_pct,
            }

        # Normalize and ingest channels
        ingested_packets = []
        for ch in decoded.sensors:
            packet_dict = {
                "source_id": "UPPER_BEAS_LORA_LPWAN",
                "station_id": station_id,
                "device_id": device_id,
                "sensor_id": f"{device_id}_{ch.sensor_type}",
                "observed_at": obs_dt.isoformat(),
                "received_at": recv_dt.isoformat(),
                "measurement_type": ch.sensor_type,
                "value": ch.value,
                "unit": ch.unit,
                "sequence_number": decoded.sequence_number,
                "firmware_version": f"v{decoded.version}.0-lora",
            }
            res = ingestion_service.ingest_telemetry_packet(db, packet_dict)
            ingested_packets.append(res)

        return {
            "status": "INGESTED",
            "station_id": station_id,
            "device_id": device_id,
            "sequence_number": decoded.sequence_number,
            "sequence_state": seq_state,
            "dropped_packets": dropped,
            "packet_loss_pct": tracker.packet_loss_pct,
            "battery_voltage": decoded.battery_voltage,
            "channels_ingested": len(ingested_packets),
            "results": ingested_packets,
        }

    def flush_offline_buffer(
        self,
        db: Session,
        gateway_id: str = "GW_ROHTANG_01",
    ) -> Dict[str, Any]:
        """
        Replays buffered packets chronologically when backhaul reconnects.
        """
        buf = self.get_buffer(gateway_id)
        if buf.is_empty():
            return {"status": "EMPTY", "replayed_count": 0}

        buffered_packets = buf.drain_chronological()
        replayed = 0
        duplicates = 0
        errors = 0

        for pkt in buffered_packets:
            mapping = STATION_CODE_MAP.get(
                pkt.station_code,
                {
                    "station_id": f"ST_UNKNOWN_{pkt.station_code}",
                    "device_id": f"DEV_UNKNOWN_{pkt.station_code}",
                },
            )
            station_id = mapping["station_id"]
            device_id = mapping["device_id"]
            obs_dt = datetime.datetime.fromtimestamp(pkt.timestamp_epoch, tz=datetime.timezone.utc)
            recv_dt = datetime.datetime.now(datetime.timezone.utc)

            for ch in pkt.sensors:
                packet_dict = {
                    "source_id": "UPPER_BEAS_LORA_LPWAN_BUFFERED",
                    "station_id": station_id,
                    "device_id": device_id,
                    "sensor_id": f"{device_id}_{ch.sensor_type}",
                    "observed_at": obs_dt.isoformat(),
                    "received_at": recv_dt.isoformat(),
                    "measurement_type": ch.sensor_type,
                    "value": ch.value,
                    "unit": ch.unit,
                    "sequence_number": pkt.sequence_number,
                    "firmware_version": f"v{pkt.version}.0-lora",
                }
                try:
                    res = ingestion_service.ingest_telemetry_packet(db, packet_dict)
                    if res.get("is_duplicate"):
                        duplicates += 1
                    else:
                        replayed += 1
                except Exception as e:
                    errors += 1
                    logger.error(f"Error replaying buffered packet: {e}")

        return {
            "status": "REPLAY_COMPLETED",
            "gateway_id": gateway_id,
            "total_packets_flushed": len(buffered_packets),
            "channels_replayed": replayed,
            "duplicates": duplicates,
            "errors": errors,
        }


lora_gateway_service = LoRaGatewayService()
