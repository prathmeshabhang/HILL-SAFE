# FLOODY SHIELD v3.9 — Controlled Field Pilot & Sensor Staging Report

## Executive Engineering Summary

This document presents the engineering, calibration, and staging status for the **FLOODY SHIELD v3.9 Controlled Field Pilot** in the **Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India**.

> [!IMPORTANT]
> **FIELD DEPLOYMENT QUALIFICATION & BOUNDARY STATEMENT:**
> - Exactly **5 physical sensor stations** have been assembled, bench-calibrated, and staged in laboratory testbeds under the status `COMMISSIONED` / `PROTOTYPE_STAGING`.
> - Exactly **0 physical stations** have been installed in active river water or deployed in alpine torrents.
> - Physical field deployment in active mountain river water remains formally classified as **`NOT_DEMONSTRATED`**.
> - The 24-hour 100% Packet Delivery Ratio (PDR) achieved in testing is strictly classified as **`SIMULATION_DEMONSTRATED`** (software-in-the-loop stress testing at 77.99 pkts/sec) and bench RF loopback; it does **not** represent live radio frequency (RF) propagation through complex Himalayan terrain during severe monsoon storms.

---

## 1. Catchment Context & Station Architecture

The Upper Beas River Basin spans steep elevation gradients from 890 m (Pandoh Dam) to over 3,900 m (Rohtang Pass). High-velocity flash floods, debris flows, and rainfall-triggered landslides create severe hazards for lifelines along National Highway 3 (NH-3).

Five strategic monitoring sites were surveyed and designed for multi-parameter hydrometric, meteorological, and geotechnical monitoring:

| Station ID | Station Name | Lat / Lon | Elev. (m) | Catchment Reach | Primary Sensor | Secondary Sensor | Lifecycle State | River Deployment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `STN_SOAL_01` | Solang Nullah Gauge & AWS | 32.3160°N, 77.1570°E | 2480.0 | Solang Torrent Headwaters | Radar Water Level (VEGAPULS C 21) | Tipping Bucket Rain (Davis 7852) | `COMMISSIONED` | `FALSE` (`NOT_DEMONSTRATED`) |
| `STN_KOTI_01` | Kothi Gorge Geotech Station | 32.3210°N, 77.1950°E | 2530.0 | Rohtang Flank (Kothi Gorge) | Piezometer (Geokon 4500S) | MEMS Tiltmeter (RST Digital) | `COMMISSIONED` | `FALSE` (`NOT_DEMONSTRATED`) |
| `STN_MANA_01` | Manali Bridge Hydrometric | 32.2432°N, 77.1892°E | 1980.0 | Manali Urban Mainstem | Ultrasonic Stage (MaxBotix HRXL) | Optical Rain (RG-15) | `COMMISSIONED` | `FALSE` (`NOT_DEMONSTRATED`) |
| `STN_ALEN_01` | Allain Debris Sentry | 32.2150°N, 77.2020°E | 1850.0 | Allain-Duhangan Confluence | Pressure Transducer (Keller Level) | Hydrophone Probe (Sensormatic) | `COMMISSIONED` | `FALSE` (`NOT_DEMONSTRATED`) |
| `STN_PAND_01` | Pandoh Dam Inflow Sentry | 31.6700°N, 77.0600°E | 890.0 | Lower Gorge Outlet | Radar Level (Siemens Sitrans) | Water Temp / EC (Aanderaa) | `COMMISSIONED` | `FALSE` (`NOT_DEMONSTRATED`) |

All 5 units are registered in [`reports/v3_9/field_station_registry.csv`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/reports/v3_9/field_station_registry.csv).

---

## 2. Hardware Engineering & Power Architecture

Each telemetry node integrates industrial-grade edge sensing, low-power processing, and LoRa transmission:

```
+--------------------------------------------------------------------------------+
|                             FLOODY SHIELD NODE                                 |
|                                                                                |
|  [ 10W Solar Panel ] ---> [ MPPT Solar Charger ] ---> [ 3.2V 6000mAh LiFePO4 ]  |
|                                                              |                 |
|                                                              v                 |
|  [ Physical Sensors ] ----(RS-485 / 4-20mA / SDI-12)----> [ ESP32-S3 MCU ]     |
|   - Radar Water Level                                        |                 |
|   - Geokon Piezometer                                        v                 |
|   - RST Tiltmeter                                     [ Semtech SX1276 ]       |
|                                                              | (865-867 MHz)   |
+--------------------------------------------------------------|-----------------+
                                                               v  (LoRa RF)
                                                       [ Gateway GW_ROHTANG_01 ]
```

### 2.1 Power Subsystem Specifications
- **Energy Storage**: 3.2 V, 6,000 mAh Lithium Iron Phosphate (LiFePO4) cell chosen for thermal stability down to -15°C.
- **Solar Harvesting**: 10 W monocrystalline photovoltaic module mounted at 45° tilt to mitigate winter snow accumulation.
- **Power Consumption Profile**:
  - Deep sleep current: 18 µA (ESP32-S3 ULP coprocessor mode).
  - Sensor wake-up & analog measurement window: 1.2 seconds @ 24 mA average.
  - LoRa packet transmission (+14 dBm, SF7, 18 bytes): 72 milliseconds @ 110 mA.
  - Calculated autonomy without solar recharge: 48 days at 15-minute transmission intervals.
  - Bench voltage monitoring: All 5 nodes stabilized at 3.65 V to 3.70 V during continuous laboratory cycling.

### 2.2 Transceiver & Modulation Parameters
- **RF Transceiver**: Semtech SX1276 LoRa transceiver module.
- **Regulatory Band**: IN865 (865.0 MHz – 867.0 MHz) in compliance with Department of Telecommunications (DoT) India standards.
- **Modulation**: Spreading Factor SF7 to SF9 (dynamic adaptive data rate based on link margin), Bandwidth 125 kHz, Coding Rate 4/5.
- **Payload Encoding**: Compact 18-byte binary frame featuring station ID hash, sequence counter, primary value, secondary value, battery status, and CRC-16 checksum.

---

## 3. Bench Testing vs. Physical Field Performance

To maintain strict scientific integrity, performance metrics are categorized by test methodology:

### 3.1 Software Ingestion Soak Testing (`SIMULATION_DEMONSTRATED`)
- **Execution**: Continuous ingestion test using `tools/reliability/long_run_harness.py`.
- **Packet Ingestion Rate**: 77.99 packets/second sustained over 24 hours (6,738,336 packets total).
- **Packet Delivery Ratio (PDR)**: 100.00% (zero packet drops, zero unhandled software exceptions).
- **Classification**: **`SIMULATION_DEMONSTRATED`**. This verifies software queue processing, database connection pooling, and deduplication logic under ideal loopback conditions. It does **not** evaluate wireless radio frequency performance.

### 3.2 Laboratory RF Bench Loopback (`PHYSICAL_BENCH_TESTBED`)
- **Execution**: 5 SX1276 nodes transmitting binary frames over a 15-meter line-of-sight indoor path to a prototype gateway (`GW_ROHTANG_01`).
- **24-Hour PDR**: 99.75% (8,618 received of 8,640 transmissions; 22 retried packets due to laboratory Wi-Fi transient interference).
- **Bench RSSI / SNR**: RSSI ranges from -64 dBm to -75 dBm; SNR ranges from +7.9 dB to +10.2 dB.
- **Classification**: **`BENCH_VALIDATED`**. Proves hardware assembly, firmware timing, and radio transceiver function.

### 3.3 Active River In-Situ Deployment (`NOT_DEMONSTRATED`)
- **Active River Stations**: **0 stations installed in river water**.
- **PDR in Torrent Environment**: **`NOT_DEMONSTRATED`** (0.0%).
- **Environmental Roadblock Analysis**:
  - High-velocity Himalayan mountain streams carry severe sediment loads (boulders, gravel, suspended silt) capable of destroying immersed transducers.
  - Deep gorge topography (e.g. Kothi Gorge, Thalout Reach) introduces severe Fresnel zone obstruction and multi-path reflection.
  - Winter freezing and snow burial require specialized armored enclosures and heated tipping buckets not yet deployed in the field.

---

## 4. Lifecycle Control & Safety Gating

The software backend strictly enforces station lifecycle transitions:

```
  [ PLANNED ]  --->  [ SURVEYED ]  --->  [ INSTALLED ]  --->  [ COMMISSIONED ]
                                                                     |
                                                          (STAGING_TESTBED ONLY)
                                                                     |
                                                                     v
                                                            [ PROTOTYPE_STAGING ]
                                                                     |
                                      (Physical In-Situ River Deployment Required)
                                                                     |
                                                                     X  [ ACTIVE ] (BLOCKED)
```

1. **Uncommissioned Station Gate**: Observations received from an uncommissioned station are automatically quarantined with `QC_UNCOMMISSIONED_STATION`.
2. **Staging Restriction**: Stations in `PROTOTYPE_STAGING` cannot issue operational life-safety evacuations without manual Incident Commander cryptographic authorization.
3. **Provenance Validation**: Field telemetry endpoints enforce explicit provenance tags (`REAL_FIELD_OBSERVATION` vs `SIMULATED`), rejecting forged upgrades from simulated to real observations.

---

## 5. Summary & Field Readiness Roadmap

| Parameter | Target Requirement | Current v3.9 Achievement | Readiness Verdict |
| :--- | :--- | :--- | :--- |
| Planned Upper Beas Stations | 5 Stations | 5 Stations surveyed & mapped | **100% COMPLETE** |
| Hardware Assembly & Staging | 5 Nodes | 5 Nodes assembled & bench tested | **100% COMPLETE** |
| LoRa Firmware & CRC-16 Codec | Functional Codec | Verified on 18-byte binary frames | **VERIFIED** |
| Battery & MPPT Autonomy | >30 Days | 48 Days calculated; bench verified | **BENCH_VERIFIED** |
| In-Situ Active River Deployment | 5 Stations in water | 0 Stations deployed in active water | **NOT_DEMONSTRATED** |
| Mountain Gorge LoRa Propagation | Alpine Link Margin | Unobserved in field terrain | **PENDING_FIELD_DEPLOYMENT** |
