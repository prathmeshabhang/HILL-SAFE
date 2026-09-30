# FLOODY SHIELD v3.6 — Device Provisioning Procedure

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** Factory Key Generation, Hardware Flashing, Provisioning Checklist, and Database Registry Onboarding.

---

## 1. Device Provisioning Lifecycle Overview

Each hardware sensor node undergoes a formal 5-step factory and bench provisioning procedure before field deployment:

```
[ Step 1: Serial Generation & UID Tagging ]
                    |
                    v
[ Step 2: Firmware Compilation & Flashing ]
                    |
                    v
[ Step 3: Bench Calibration & Zeroing ]
                    |
                    v
[ Step 4: Secure Key Burning (eFuse / NVS) ]
                    |
                    v
[ Step 5: Registry Onboarding via REST API ]
```

---

## 2. Step-by-Step Provisioning Guide

### Step 1: Serial Number Generation
Every node receives an indelible serial number adhering to the standard naming convention:
`FS-HW-[LOC]-[YEAR]-[SEQUENCE]`
- Example: `FS-HW-MNL-2026-001` (Floody Shield Hardware, Manali, Year 2026, Node #1).
- Assigned Station Code: 16-bit numeric identifier (e.g., `101`).

### Step 2: Firmware Flashing
Using PlatformIO or `esptool.py`, flash the verified v3.6 reference firmware:
```bash
cd firmware/esp32_lora_station
pio run --target upload --environment esp32dev
```

### Step 3: Bench Sensor Calibration
Before packing, sensors are wired to bench reference instruments:
- Optical rain gauge: verified against calibrated 500 mL water drip column.
- Radar river stage: verified at 1.000 m, 5.000 m, and 10.000 m acoustic targets.
- Voltage divider: calibrated against Fluke 87V multimeter reference.

### Step 4: Device Registry Onboarding
An authorized system administrator or technician onboards the new station and device via the REST API:

```bash
# 1. Register Station (Status: PLANNED or SURVEYED)
curl -X POST http://localhost:8000/api/v1/stations \
  -H "Authorization: Bearer $ANALYST_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "station_id": "ST_MANALI_01",
    "name": "Manali Catchment & Upper Precipitation Station",
    "station_type": "METEOROLOGICAL_HYDROLOGICAL",
    "latitude": 32.255,
    "longitude": 77.185,
    "elevation_m": 2050.0,
    "river_basin": "Upper Beas Basin",
    "status": "PLANNED"
  }'

# 2. Register Physical Device Node
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer $ANALYST_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEV_MANALI_01",
    "station_id": "ST_MANALI_01",
    "serial_number": "FS-HW-MNL-2026-001",
    "device_type": "LORA_NODE",
    "manufacturer": "FloodyShield-Hardware",
    "firmware_version": "v3.6.0-lora",
    "protocol": "LORAWAN",
    "status": "PLANNED",
    "latitude": 32.255,
    "longitude": 77.185,
    "elevation": 2050.0
  }'

# 3. Register Attached Sensors
curl -X POST http://localhost:8000/api/v1/sensors \
  -H "Authorization: Bearer $ANALYST_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "DEV_MANALI_01_RAIN_GAUGE",
    "device_id": "DEV_MANALI_01",
    "sensor_type": "RAIN_GAUGE",
    "unit": "mm/h",
    "measurement_range_min": 0.0,
    "measurement_range_max": 500.0,
    "sampling_interval_sec": 60
  }'
```

---

## 3. Pre-Deployment Acceptance Criteria

Before shipment to the Upper Beas field station, the device must satisfy:
- [x] Zero bit-errors over 1,000 consecutive LoRa bench packets transmitted to test gateway.
- [x] Battery charging verified via 12V solar bench simulator.
- [x] Sleep current consumption verified $\le 25\ \mu\text{A}$ during deep-sleep cycle.
- [x] IP67 gasket vacuum seal pressure decay test passed.
