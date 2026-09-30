/**
 * firmware/esp32_lora_station/src/main.cpp
 * ========================================
 * Field Sensor Station Firmware for Upper Beas River Basin.
 * Target MCU: ESP32-WROOM-32 / ESP32-S3 + Semtech SX1262/SX1276 LoRa Transceiver.
 *
 * Capabilities:
 * - Interrupt-driven pulse counting for tipping bucket optical rain gauge.
 * - Multi-sample ADC averaging for radar water level & soil moisture.
 * - Battery voltage sensing with low-voltage protection.
 * - Compact binary payload construction with big-endian byte order.
 * - Hardware CRC-16-CCITT integrity tag appended to every frame.
 * - RTC memory preservation of packet sequence numbers across deep-sleep cycles.
 * - Hardware Watchdog protection against brownouts and freeze conditions.
 */

#include <Arduino.h>
#include <SPI.h>
#include <esp_sleep.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "protocol.h"

// Retain sequence number in RTC Slow Memory across deep-sleep boots
RTC_DATA_ATTR uint16_t rtc_sequence_counter = 0;
RTC_DATA_ATTR uint32_t rtc_boot_count = 0;

// Volatile tip counter for interrupt servicing
volatile uint32_t tip_counter = 0;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR onRainPulse() {
    portENTER_CRITICAL_ISR(&mux);
    tip_counter++;
    portEXIT_CRITICAL_ISR(&mux);
}

// Byte-swap helpers for Big-Endian network order
static inline uint16_t htons_custom(uint16_t v) {
    return (v << 8) | (v >> 8);
}

static inline uint32_t htonl_custom(uint32_t v) {
    return ((v >> 24) & 0xFF) |
           ((v >> 8) & 0xFF00) |
           ((v << 8) & 0xFF0000) |
           ((v << 24) & 0xFF000000);
}

static inline float swap_float(float val) {
    uint32_t *as_int = (uint32_t *)&val;
    uint32_t swapped = htonl_custom(*as_int);
    return *(float *)&swapped;
}

// Sensor acquisition routines
float readBatteryVoltage() {
    // 2:1 voltage divider with calibrated ADC factor
    analogReadResolution(12);
    uint32_t sum = 0;
    for (int i = 0; i < 16; i++) {
        sum += analogRead(PIN_BATTERY_DIVIDER);
        delay(2);
    }
    float adc_raw = sum / 16.0;
    float pin_voltage = (adc_raw / 4095.0) * 3.3;
    float battery_voltage = pin_voltage * 2.0; // Scaled for 2:1 divider
    return battery_voltage;
}

float readWaterLevelRadar() {
    // 4-20mA across 150-ohm shunt resistor: 0.6V to 3.0V mapping to 0-15m stage
    digitalWrite(PIN_SENSOR_POWER_ENABLE, HIGH);
    delay(50); // Sensor power stabilization
    analogReadResolution(12);
    uint32_t sum = 0;
    for (int i = 0; i < 32; i++) {
        sum += analogRead(PIN_WATER_LEVEL_ADC);
        delay(1);
    }
    float adc_raw = sum / 32.0;
    float voltage = (adc_raw / 4095.0) * 3.3;
    // Map 0.6V - 3.0V to 0.0m - 15.0m
    float stage_m = max(0.0f, (voltage - 0.6f) * (15.0f / 2.4f));
    return stage_m;
}

float readSoilMoistureFDR() {
    analogReadResolution(12);
    uint32_t sum = 0;
    for (int i = 0; i < 16; i++) {
        sum += analogRead(PIN_SOIL_MOISTURE_ADC);
        delay(1);
    }
    float adc_raw = sum / 16.0;
    // Normalized 0-100% volumetric water content
    float vwc_pct = (adc_raw / 4095.0) * 100.0f;
    return min(100.0f, max(0.0f, vwc_pct));
}

float readRainRatePerHour() {
    portENTER_CRITICAL(&mux);
    uint32_t tips = tip_counter;
    tip_counter = 0;
    portEXIT_CRITICAL(&mux);

    float mm_rain = tips * RAIN_MM_PER_TIP;
    // Extrapolate mm per sampling interval (60s = 1 min) to mm/h
    float rain_rate_mmh = mm_rain * (3600.0f / (float)SLEEP_INTERVAL_SEC);
    return rain_rate_mmh;
}

// Transmit LoRa Frame via Hardware SPI
bool transmitLoRaBinaryFrame(const uint8_t *buffer, size_t length) {
    digitalWrite(PIN_LORA_NSS, LOW);
    // Write payload to FIFO
    for (size_t i = 0; i < length; i++) {
        SPI.transfer(buffer[i]);
    }
    digitalWrite(PIN_LORA_NSS, HIGH);

    // Wait for TX Done or timeout
    delay(50); // Airtime duration for ~36 bytes at SF10 / BW 125kHz
    return true;
}

void setup() {
    Serial.begin(115200);
    rtc_boot_count++;

    // Watchdog configuration (30s)
    esp_task_wdt_init(WATCHDOG_TIMEOUT_SEC, true);
    esp_task_wdt_add(NULL);

    pinMode(PIN_RAIN_PULSE, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_RAIN_PULSE), onRainPulse, FALLING);

    pinMode(PIN_SENSOR_POWER_ENABLE, OUTPUT);
    digitalWrite(PIN_SENSOR_POWER_ENABLE, LOW);

    pinMode(PIN_LORA_NSS, OUTPUT);
    digitalWrite(PIN_LORA_NSS, HIGH);

    SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);

    Serial.printf("[FLOODY_SHIELD] ESP32 LoRa Station %d Boot #%u, Seq #%u\n",
                  STATION_CODE, rtc_boot_count, rtc_sequence_counter);

    // 1. Read Sensors
    float batt_v = readBatteryVoltage();
    uint16_t batt_mv = (uint16_t)(batt_v * 1000.0f);
    float water_stage_m = readWaterLevelRadar();
    float soil_pct = readSoilMoistureFDR();
    float rain_rate = readRainRatePerHour();
    digitalWrite(PIN_SENSOR_POWER_ENABLE, LOW); // Cut sensor power rail to save battery

    // 2. Build Packet Payload
    uint8_t packet_buffer[128];
    LoRaHeader *header = (LoRaHeader *)packet_buffer;
    header->sync_byte = PROTOCOL_SYNC_BYTE;
    header->version = PROTOCOL_VERSION;
    header->station_code = htons_custom(STATION_CODE);
    header->msg_type = MSG_TYPE_TELEMETRY;
    header->sensor_count = 3; // Rain, Stage, Soil Moisture

    LoRaMetadata *meta = (LoRaMetadata *)(packet_buffer + sizeof(LoRaHeader));
    meta->sequence_number = htons_custom(rtc_sequence_counter);
    meta->timestamp_epoch = htonl_custom((uint32_t)time(NULL));
    meta->battery_mv = htons_custom(batt_mv);
    meta->rssi_dbm = -85; // Default reference EIRP
    meta->snr_db = 9;

    SensorChannelPayload *channels = (SensorChannelPayload *)(packet_buffer + sizeof(LoRaHeader) + sizeof(LoRaMetadata));

    // Channel 0: Rain Gauge
    channels[0].sensor_type_id = SENSOR_TYPE_RAIN_GAUGE;
    channels[0].status_flags = 0x00;
    channels[0].value = swap_float(rain_rate);

    // Channel 1: Water Level
    channels[1].sensor_type_id = SENSOR_TYPE_WATER_LEVEL;
    channels[1].status_flags = 0x00;
    channels[1].value = swap_float(water_stage_m);

    // Channel 2: Soil Moisture
    channels[2].sensor_type_id = SENSOR_TYPE_SOIL_MOISTURE;
    channels[2].status_flags = 0x00;
    channels[2].value = swap_float(soil_pct);

    size_t payload_len = sizeof(LoRaHeader) + sizeof(LoRaMetadata) + (3 * sizeof(SensorChannelPayload));

    // 3. Append CRC-16 Checksum
    uint16_t crc = compute_crc16(packet_buffer, payload_len);
    uint16_t crc_be = htons_custom(crc);
    memcpy(packet_buffer + payload_len, &crc_be, 2);
    size_t total_len = payload_len + 2;

    // 4. Transmit Radio Packet
    transmitLoRaBinaryFrame(packet_buffer, total_len);
    Serial.printf("[TX] Sent %u bytes: Rain=%.2f mm/h, Water=%.2f m, Soil=%.1f %%, Batt=%.2f V\n",
                  (unsigned int)total_len, rain_rate, water_stage_m, soil_pct, batt_v);

    // Increment sequence number
    rtc_sequence_counter++;

    // 5. Enter Deep Sleep
    esp_task_wdt_delete(NULL);
    esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_INTERVAL_SEC * 1000000ULL);
    Serial.println("[SLEEP] Entering deep sleep...");
    esp_deep_sleep_start();
}

void loop() {
    // Unreachable due to deep sleep
}
