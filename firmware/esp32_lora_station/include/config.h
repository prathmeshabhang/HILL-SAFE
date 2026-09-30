/**
 * firmware/esp32_lora_station/include/config.h
 * ============================================
 * Hardware & Radio Configuration for FLOODY SHIELD ESP32 Field Station.
 * Target Region: Upper Beas River Basin, Himachal Pradesh (IN865 Band).
 */

#pragma once

#include <Arduino.h>

// Station Hardware Identity
#define STATION_CODE            101               // Numeric Station Code (e.g. 101 = ST_MANALI_01)
#define FIRMWARE_VERSION_MAJOR  3
#define FIRMWARE_VERSION_MINOR  6
#define FIRMWARE_VERSION_PATCH  0

// LoRa LPWAN Radio Configuration (IN865 Band: 865 - 867 MHz)
#define LORA_FREQUENCY_MHZ      865.200           // Carrier Frequency (MHz)
#define LORA_BANDWIDTH_KHZ      125.0             // Bandwidth: 125 kHz
#define LORA_SPREADING_FACTOR   10                // SF10 for steep mountain valley coverage
#define LORA_CODING_RATE        5                 // 4/5 Coding Rate
#define LORA_SYNC_WORD          0x34              // LoRa public WAN sync word
#define LORA_TX_POWER_DBM       20                // +20 dBm (Max legal EIRP with power amplifier)
#define LORA_PREAMBLE_LEN       8                 // Preamble symbols

// ESP32 SPI Pin Assignments for Semtech SX1262 / SX1276
#define PIN_LORA_SCK            18
#define PIN_LORA_MISO           19
#define PIN_LORA_MOSI           23
#define PIN_LORA_NSS            5
#define PIN_LORA_RST            14
#define PIN_LORA_DIO0           26                // DIO0 (SX1276) or BUSY (SX1262)

// Physical Sensor GPIO & ADC Mapping
#define PIN_RAIN_PULSE          13                // Tipping bucket optical interrupt pin
#define PIN_WATER_LEVEL_ADC     34                // 4-20mA pressure/radar stage receiver (ADC1_CH6)
#define PIN_SOIL_MOISTURE_ADC   35                // FDR soil moisture analog signal (ADC1_CH7)
#define PIN_BATTERY_DIVIDER     36                // Resistor divider voltage monitor (ADC1_CH0)
#define PIN_SENSOR_POWER_ENABLE 12                // P-MOSFET gate for switching sensor rail power

// Power Management & Sampling Intervals
#define SLEEP_INTERVAL_SEC      60                // Active monsoon transmission interval (60 seconds)
#define DRY_SEASON_SLEEP_SEC    300               // Low-flow non-monsoon interval (5 minutes)
#define RAIN_MM_PER_TIP         0.2               // 0.2mm per bucket tip
#define WATCHDOG_TIMEOUT_SEC    30                // Hardware WDT timeout
