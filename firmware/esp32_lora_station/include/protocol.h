/**
 * firmware/esp32_lora_station/include/protocol.h
 * ==============================================
 * Compact Binary Packet Definitions and CRC-16 for FLOODY SHIELD LoRa Nodes.
 * Bit-for-bit compatible with tools/lora/packet_codec.py.
 */

#pragma once

#include <stdint.h>
#include <stddef.h>

#define PROTOCOL_SYNC_BYTE      0xF5
#define PROTOCOL_VERSION        0x01

#define MSG_TYPE_TELEMETRY      0x01
#define MSG_TYPE_HEARTBEAT      0x02
#define MSG_TYPE_ALARM          0x03
#define MSG_TYPE_DIAGNOSTIC     0x04

#define SENSOR_TYPE_RAIN_GAUGE        1
#define SENSOR_TYPE_WATER_LEVEL       2
#define SENSOR_TYPE_SOIL_MOISTURE     3
#define SENSOR_TYPE_PORE_PRESSURE     4
#define SENSOR_TYPE_TILT              5
#define SENSOR_TYPE_VIBRATION         6
#define SENSOR_TYPE_TEMPERATURE       7
#define SENSOR_TYPE_HUMIDITY          8
#define SENSOR_TYPE_BATTERY           9

#pragma pack(push, 1)

// Sensor Channel (6 bytes)
typedef struct {
    uint8_t  sensor_type_id;
    uint8_t  status_flags;
    float    value;              // IEEE 754 float
} SensorChannelPayload;

// Packet Header (6 bytes)
typedef struct {
    uint8_t  sync_byte;          // 0xF5
    uint8_t  version;            // 0x01
    uint16_t station_code;       // Big-endian uint16
    uint8_t  msg_type;           // 0x01 = TELEMETRY
    uint8_t  sensor_count;       // Number of channels
} LoRaHeader;

// Radio & Power Metadata (10 bytes)
typedef struct {
    uint16_t sequence_number;    // Big-endian uint16
    uint32_t timestamp_epoch;    // Big-endian uint32
    uint16_t battery_mv;         // Battery voltage in millivolts
    int8_t   rssi_dbm;           // Signed int8
    int8_t   snr_db;             // Signed int8
} LoRaMetadata;

#pragma pack(pop)

/**
 * Computes standard CRC-16-CCITT checksum across payload buffer.
 * Polynomial: 0x1021, Initial value: 0xFFFF.
 */
static inline uint16_t compute_crc16(const uint8_t *data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF;
            } else {
                crc = (crc << 1) & 0xFFFF;
            }
        }
    }
    return crc;
}
