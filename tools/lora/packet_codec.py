"""
tools/lora/packet_codec.py
==========================
Compact Binary LoRa LPWAN Packet Codec for FLOODY SHIELD v3.6.
Designed for sub-GHz LPWAN bandwidth constraints (51-222 byte maximum payload).
Encodes and decodes binary telemetry frames with CRC-16-CCITT integrity verification.
"""

import struct
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

SYNC_BYTE = 0xF5
PROTOCOL_VERSION = 0x01

MSG_TYPE_TELEMETRY = 0x01
MSG_TYPE_HEARTBEAT = 0x02
MSG_TYPE_ALARM = 0x03
MSG_TYPE_DIAGNOSTIC = 0x04

MSG_TYPE_NAMES = {
    MSG_TYPE_TELEMETRY: "TELEMETRY",
    MSG_TYPE_HEARTBEAT: "HEARTBEAT",
    MSG_TYPE_ALARM: "ALARM",
    MSG_TYPE_DIAGNOSTIC: "DIAGNOSTIC",
}

SENSOR_TYPE_TO_ID = {
    "RAIN_GAUGE": 1,
    "WATER_LEVEL": 2,
    "SOIL_MOISTURE": 3,
    "PORE_WATER_PRESSURE": 4,
    "TILT": 5,
    "VIBRATION": 6,
    "TEMPERATURE": 7,
    "HUMIDITY": 8,
    "BATTERY": 9,
}

ID_TO_SENSOR_TYPE = {v: k for k, v in SENSOR_TYPE_TO_ID.items()}

# Unit mapping
SENSOR_UNITS = {
    "RAIN_GAUGE": "mm/h",
    "WATER_LEVEL": "m",
    "SOIL_MOISTURE": "%",
    "PORE_WATER_PRESSURE": "kPa",
    "TILT": "deg",
    "VIBRATION": "mm/s2",
    "TEMPERATURE": "C",
    "HUMIDITY": "%",
    "BATTERY": "V",
}


def crc16_ccitt(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    """Computes CRC-16-CCITT checksum across bytes."""
    crc = init
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


@dataclass
class DecodedSensorChannel:
    sensor_type: str
    status_flags: int
    value: float
    unit: str


@dataclass
class DecodedLoRaPacket:
    version: int
    station_code: int
    msg_type: str
    sequence_number: int
    timestamp_epoch: int
    battery_mv: int
    battery_voltage: float
    rssi_dbm: int
    snr_db: int
    sensors: List[DecodedSensorChannel]
    crc_valid: bool
    raw_payload_bytes: int


class LoRaPacketCodec:
    """
    Compact Binary LoRa Packet Codec.
    
    Packet Structure:
    [Header: 6 bytes]
      - 0x00: Sync Byte (0xF5)
      - 0x01: Version (0x01)
      - 0x02..0x03: Station / Node ID (uint16 big-endian)
      - 0x04: Message Type (uint8: 0x01=TELEMETRY, 0x02=HEARTBEAT, etc.)
      - 0x05: Sensor Count N (uint8: 0..16)
    [Radio & Power Metadata: 10 bytes]
      - 0x06..0x07: Sequence Number (uint16 big-endian, 0..65535)
      - 0x08..0x0B: Unix Timestamp Epoch (uint32 big-endian seconds)
      - 0x0C..0x0D: Battery Voltage (uint16 big-endian mV, e.g. 3750 = 3.75V)
      - 0x0E: RSSI (int8 signed dBm, e.g. -85)
      - 0x0F: SNR (int8 signed dB, e.g. 8)
    [Sensor Array: N * 6 bytes]
      Each channel:
      - 0x00: Sensor Type ID (uint8: 1..9)
      - 0x01: Status Flags (uint8 bitmask)
      - 0x02..0x05: Float32 Value (float big-endian IEEE 754)
    [Checksum: 2 bytes]
      - Last 2 bytes: CRC-16-CCITT (uint16 big-endian)
    """

    def encode(
        self,
        station_code: int,
        sequence_number: int,
        timestamp_epoch: int,
        sensor_readings: List[Dict[str, Any]],
        battery_mv: int = 12600,
        rssi_dbm: int = -85,
        snr_db: int = 8,
        msg_type: int = MSG_TYPE_TELEMETRY,
    ) -> bytes:
        """Encodes structured telemetry into compact binary LoRa payload with CRC-16."""
        sensor_count = len(sensor_readings)
        if sensor_count > 16:
            raise ValueError("Maximum 16 sensor channels allowed in single LoRa frame.")

        # 1. Pack Header (6 bytes)
        header = struct.pack(
            "!BBHBB",
            SYNC_BYTE,
            PROTOCOL_VERSION,
            station_code & 0xFFFF,
            msg_type & 0xFF,
            sensor_count & 0xFF,
        )

        # 2. Pack Metadata (10 bytes)
        meta = struct.pack(
            "!HIHbb",
            sequence_number & 0xFFFF,
            timestamp_epoch & 0xFFFFFFFF,
            battery_mv & 0xFFFF,
            int(rssi_dbm),
            int(snr_db),
        )

        # 3. Pack Channels (N * 6 bytes)
        channels = bytearray()
        for s in sensor_readings:
            stype_name = s.get("sensor_type", "RAIN_GAUGE").upper()
            stype_id = SENSOR_TYPE_TO_ID.get(stype_name, 1)
            flags = int(s.get("status_flags", 0)) & 0xFF
            val = float(s.get("value", 0.0))
            channels.extend(struct.pack("!BBf", stype_id, flags, val))

        payload_without_crc = header + meta + bytes(channels)

        # 4. Compute CRC-16-CCITT across payload
        crc = crc16_ccitt(payload_without_crc)
        crc_bytes = struct.pack("!H", crc)

        return payload_without_crc + crc_bytes

    def decode(self, data: bytes) -> DecodedLoRaPacket:
        """Decodes binary LoRa payload, verifying sync byte and CRC-16."""
        if len(data) < 18:  # 6 header + 10 meta + 2 crc = 18 bytes minimum (0 channels)
            raise ValueError(f"Packet too short: {len(data)} bytes (minimum 18 bytes required).")

        sync, version, station_code, msg_type, sensor_count = struct.unpack("!BBHBB", data[:6])
        if sync != SYNC_BYTE:
            raise ValueError(f"Invalid sync byte 0x{sync:02X} (expected 0x{SYNC_BYTE:02X}).")

        expected_length = 6 + 10 + (sensor_count * 6) + 2
        if len(data) != expected_length:
            raise ValueError(
                f"Packet length mismatch: got {len(data)} bytes, expected {expected_length} for {sensor_count} channels."
            )

        # Verify CRC
        payload_data = data[:-2]
        received_crc = struct.unpack("!H", data[-2:])[0]
        calculated_crc = crc16_ccitt(payload_data)

        if received_crc != calculated_crc:
            raise ValueError(
                f"CRC integrity violation: received 0x{received_crc:04X}, calculated 0x{calculated_crc:04X}."
            )

        # Unpack metadata
        seq, epoch, batt_mv, rssi, snr = struct.unpack("!HIHbb", data[6:16])

        # Unpack sensor channels
        sensors: List[DecodedSensorChannel] = []
        offset = 16
        for _ in range(sensor_count):
            stype_id, flags, val = struct.unpack("!BBf", data[offset : offset + 6])
            stype_name = ID_TO_SENSOR_TYPE.get(stype_id, f"UNKNOWN_{stype_id}")
            unit = SENSOR_UNITS.get(stype_name, "")
            sensors.append(
                DecodedSensorChannel(
                    sensor_type=stype_name,
                    status_flags=flags,
                    value=round(val, 4),
                    unit=unit,
                )
            )
            offset += 6

        return DecodedLoRaPacket(
            version=version,
            station_code=station_code,
            msg_type=MSG_TYPE_NAMES.get(msg_type, f"TYPE_{msg_type}"),
            sequence_number=seq,
            timestamp_epoch=epoch,
            battery_mv=batt_mv,
            battery_voltage=round(batt_mv / 1000.0, 3),
            rssi_dbm=rssi,
            snr_db=snr,
            sensors=sensors,
            crc_valid=True,
            raw_payload_bytes=len(data),
        )


lora_codec = LoRaPacketCodec()
