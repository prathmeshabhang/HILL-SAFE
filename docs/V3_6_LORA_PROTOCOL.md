# FLOODY SHIELD v3.6 — LoRa LPWAN Protocol Specification

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** LPWAN Physical Layer, IN865 Frequency Plan, Binary Frame Layout, Airtime Budget, and CRC-16 Integrity.

---

## 1. Regulatory & Radio Frequency Plan (IN865)

FLOODY SHIELD complies strictly with the Department of Telecommunications (DoT) / Wireless Planning and Coordination (WPC) Wing of India for license-exempt sub-GHz operation:

| Parameter | Specification | Standard / Regulatory Requirement |
|:---|:---|:---|
| **Frequency Band** | **865.000 – 867.000 MHz** | National Frequency Allocation Plan (NFAP-2018) |
| **Uplink Frequencies** | 865.0625, 865.4025, 865.9850 MHz | 3 Default Mandatory Channels |
| **Bandwidth (BW)** | **125 kHz** | Sub-band standard |
| **Spreading Factor (SF)** | **SF10** (Adaptive SF7–SF12) | High-link-margin mountain valley propagation |
| **Coding Rate (CR)** | **4/5** | Forward error correction |
| **Max Transmit Power** | **+20 dBm (100 mW) EIRP** | WPC maximum permissible license-exempt limit |
| **Duty Cycle Limit** | **1%** | Max 36 seconds per hour continuous transmission |

---

## 2. Binary Frame Structure

To minimize transmission airtime, conserve battery, and avoid network congestion, telemetry packets are encoded in compact binary format (Big-Endian network byte order).

### 2.1 Packet Layout Diagram

```
+---------------+---------------+--------------------+------------------+-------------------+
|  Sync (0xF5)  | Version (0x01)| Station ID (uint16)| Msg Type (uint8) | Sensor Count (N)  |
|    1 byte     |    1 byte     |      2 bytes       |      1 byte      |      1 byte       |
+---------------+---------------+--------------------+------------------+-------------------+
|                           HEADER (Total: 6 bytes)                                         |
+-------------------------------------------------------------------------------------------+

+--------------------+----------------------+--------------------+------------+------------+
| Sequence # (uint16)| Epoch Time (uint32)  | Battery mV (uint16)| RSSI (int8)| SNR (int8) |
|      2 bytes       |       4 bytes        |      2 bytes       |   1 byte   |   1 byte   |
+--------------------+----------------------+--------------------+------------+------------+
|                     RADIO & POWER METADATA (Total: 10 bytes)                              |
+-------------------------------------------------------------------------------------------+

+--------------------+----------------------+-----------------------------------------------+
| Sensor ID (uint8)  | Status Flags (uint8) | Float32 Value (4 bytes IEEE 754)              |
+--------------------+----------------------+-----------------------------------------------+
|                 SENSOR CHANNEL 1..N (Total: N * 6 bytes)                                  |
+-------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------+
| CRC-16-CCITT Checksum (uint16 big-endian, Polynomial 0x1021, Init 0xFFFF)                |
|                                       2 bytes                                             |
+-------------------------------------------------------------------------------------------+
```

### 2.2 Frame Byte Offsets

| Offset (Bytes) | Field Name | Data Type | Encoding / Units | Description |
|:---:|:---|:---|:---|:---|
| `0x00` | `sync_byte` | `uint8` | Constant `0xF5` | Frame synchronization tag |
| `0x01` | `protocol_version` | `uint8` | Constant `0x01` | FLOODY SHIELD LPWAN Version |
| `0x02..0x03` | `station_code` | `uint16` | Big-Endian unsigned integer | Node ID (e.g., 101 = Manali) |
| `0x04` | `msg_type` | `uint8` | 1=Telemetry, 2=Heartbeat, 3=Alarm | Message classification |
| `0x05` | `sensor_count` | `uint8` | 1 to 16 | Number of appended channels ($N$) |
| `0x06..0x07` | `sequence_number`| `uint16` | 0 to 65535 (Rollover aware) | Consecutive transmission index |
| `0x08..0x0B` | `timestamp_epoch`| `uint32` | Unix epoch seconds | Sensor measurement timestamp |
| `0x0C..0x0D` | `battery_mv` | `uint16` | Millivolts (e.g. 12600 = 12.60V) | Bus supply voltage |
| `0x0E` | `rssi_dbm` | `int8` | Signed dBm (-128 to 0) | Gateway reception power level |
| `0x0F` | `snr_db` | `int8` | Signed dB (-20 to +15) | Signal-to-noise ratio |
| `0x10..0x15` | `channel_0` | `6 bytes` | ID (1B), Flags (1B), Float (4B) | First sensor measurement |
| `...` | `channel_N-1` | `6 bytes` | ID (1B), Flags (1B), Float (4B) | N-th sensor measurement |
| `End - 2..End` | `crc16` | `uint16` | CRC-16-CCITT (poly 0x1021) | Hardware/software verification |

---

## 3. Airtime & Duty Cycle Calculations

For a typical 3-sensor station (Precipitation + Stage + Soil Moisture):
- Total payload size: $6 + 10 + (3 \times 6) + 2 = \mathbf{36\text{ bytes}}$.

At Spreading Factor 10 (SF10) with Bandwidth 125 kHz and 4/5 Coding Rate:
- Symbol duration: $T_s = \frac{2^{10}}{125,000} = 8.192\text{ ms}$.
- Preamble duration (8 symbols): $T_{preamble} = (8 + 4.25) \times 8.192 = 100.35\text{ ms}$.
- Payload symbols: $N_{payload} = 8 + \max\left(\lceil \frac{8 \times 36 - 4 \times 10 + 28 + 16}{4 \times 10} \rceil \times 5, 0\right) = 43\text{ symbols}$.
- Payload duration: $T_{payload} = 43 \times 8.192 = 352.26\text{ ms}$.
- **Total Time on Air (ToA)**: $T_{ToA} = 100.35 + 352.26 = \mathbf{452.6\text{ ms}}$.

### Duty Cycle Verification:
- Transmission frequency: Once per 60 seconds (1 minute interval).
- Hourly transmission count: 60 transmissions.
- Total hourly airtime: $60 \times 0.4526\text{ s} = 27.16\text{ seconds}$.
- Duty cycle percentage: $\frac{27.16}{3600} = \mathbf{0.75\%} < 1.0\%$.
- **Compliant with Indian WPC 1% duty cycle limit.**
