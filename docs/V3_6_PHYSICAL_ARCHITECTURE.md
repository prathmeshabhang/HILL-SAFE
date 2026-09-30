# FLOODY SHIELD v3.6 — Physical Sensor & Hardware Architecture

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** Physical Station Topology, Topographic Routing, Power Autonomy, Environmental Enclosures, and Radio Network Design.

---

## 1. Topographic & Environmental Context

The Upper Beas River Basin presents acute challenges for physical telemetry:
- **Steep Relief & Narrow Gorges**: Elevations range from 700 m (Pandoh/Larji Gorge) to over 6,000 m (Pir Panjal and Greater Himalayan crests). Narrow, V-shaped valleys block direct line-of-sight (LOS) communications.
- **Monsoon Climate Extremes**: High-intensity localized orographic rainfall ("cloudbursts") exceeding 100 mm/h, accompanied by sudden flash floods and debris flows.
- **Sub-Zero Winter Freezing**: Freezing temperatures down to -20°C at high passes (Rohtang Pass, Solang Nullah), causing battery discharge degradation and sensor freezing.
- **Vulnerable Terrestrial Infrastructure**: Road washouts and fiber optic cuts along National Highway 3 (NH-3) regularly isolate the valley, mandating autonomous solar/battery power and wireless LPWAN telemetry.

---

## 2. Physical Station Network Layout

Five primary pilot stations are planned and configured along the critical hydrological corridor:

```
[ Solang / Rohtang Ridge Gateway (GW_ROHTANG_01) - 3,978m ]
                      |   (LoRa IN865 Uplink)
                      v
      +-------------------------------+
      | ST_MANALI_01 (Manali Catchment)|  2,050m MSL: Optical Rain + Radar Stage + FDR Soil
      +-------------------------------+
                      |
                      v (Beas River Flow ~38 km)
      +-------------------------------+
      | ST_KULLU_01 (Kullu HQ Gauge)  |  1,220m MSL: Radar Stage + Rain + Pressure Sensor
      +-------------------------------+
                      |
                      v (Beas River Flow ~10 km)
      +-------------------------------+
      | ST_BHUNTAR_01 (Airport Reach) |  1,090m MSL: Parbati Confluence Radar + Silt Monitor
      +-------------------------------+
                      |
                      v (Beas River Flow ~18 km)
      +-------------------------------+
      | ST_AUT_01 (Aut Gorge / NH-3)  |    960m MSL: Vibrating Wire PWP + Inclinometer Tilt
      +-------------------------------+
                      |
                      v (Beas River Flow ~6 km)
      +-------------------------------+
      | ST_LARJI_01 (Larji Dam Inflow)|    950m MSL: Hydropower Reservoir Inflow Gauge
      +-------------------------------+
                      |
[ Bijli Mahadev Peak Gateway (GW_BIJLI_01) - 2,460m ] (Dual Backhaul: 4G + Satellite)
```

---

## 3. Physical Hardware Enclosure & Subsystems

Each field telemetry station comprises four decoupled physical subsystems:

### 3.1 Sensor Suite
- **Precipitation**: Optical/Tipping Bucket Rain Sensor (TB4 / Hydrological Services), resolution 0.2 mm/tip, heated rim for sub-zero operation.
- **River Stage (Water Level)**: Non-contact 80 GHz FMCW Radar Level Transmitter (measurement range 0–15 m, accuracy ±2 mm, beam angle 8°), mounted on cantilever steel arm over river centerline.
- **Soil Moisture**: Volumetric Water Content FDR Probe (Campbell Scientific CS655 / Decagon 5TE), 0–100% VWC, integrated soil temperature.
- **Pore Water Pressure (PWP)**: Vibrating Wire Piezometer (Geokon 4500 series), range 0–500 kPa, installed in drilled slope boreholes in landslide scarps.
- **Biaxial Inclinometer / Tilt**: MEMS dual-axis digital inclinometer, range ±30°, resolution 0.01°, measuring slope creep along highway cut-slopes.

### 3.2 Processing Core & Telemetry Node
- **Microcontroller**: ESP32-S3 / ESP32-WROOM-32 (Xtensa 32-bit dual-core, 240 MHz).
- **LPWAN Transceiver**: Semtech SX1262 sub-GHz LoRa RF engine operating at 865–867 MHz (IN865 band).
- **External Flash & RTC**: 8 MB SPI Flash for local non-volatile packet buffering; external DS3231 temperature-compensated real-time clock.
- **Hardware Watchdog**: External TPS3823 hardware supervisory timer to force clean hardware reboot upon CPU latch-up.

### 3.3 Power Supply & Solar Harvesting
- **Solar PV Panel**: 50W Monocrystalline PV module, mounted at 45° tilt facing true South.
- **Battery Chemistry**: Lithium Iron Phosphate ($LiFePO_4$), 12.8V 24Ah (307 Wh capacity).
- **Operating Temperature Range**: -20°C to +60°C with integrated low-temperature charge cutoff.
- **Autonomy**: 14 consecutive days of zero solar irradiation (total monsoon overcast).

### 3.4 Mechanical & Environmental Enclosure
- **Enclosure Rating**: IP67 / NEMA 4X cast-aluminum enclosure with UV-stabilized powder coating.
- **Surge Protection**: Gas discharge tube (GDT) and transient voltage suppressor (TVS) diodes on all external sensor cables (RS-485, 4-20mA, pulse).
- **Lightning Protection**: 2.5 m copper-clad air terminal (lightning rod) grounded via exothermic weld to 16 mm copper ground rod (ground resistance < 5 ohms).
