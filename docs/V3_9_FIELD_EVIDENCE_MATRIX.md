# FLOODY SHIELD v3.9 — Field Evidence & Telemetry Matrix

## 1. Physical Sensor Station Staging Matrix

| Station ID | Station Name | Location | Elevation | Primary Sensor (Serial) | Secondary Sensor (Serial) | Battery / Solar | LoRa Transceiver | Lifecycle Status | In-Situ Water Deployed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `STN_SOAL_01` | Solang Nullah | 32.3160°N, 77.1570°E | 2480.0 m | Radar Level (`SN-VP-2026-0811`) | Rain Gauge (`SN-DV-2026-0392`) | 3.68V / 10W MPPT | SX1276 (IN865 SF7) | `COMMISSIONED` | **`FALSE` (`NOT_DEMONSTRATED`)** |
| `STN_KOTI_01` | Kothi Gorge | 32.3210°N, 77.1950°E | 2530.0 m | Piezometer (`SN-GK-2026-1044`) | Tiltmeter (`SN-RST-2026-0518`) | 3.65V / 10W MPPT | SX1276 (IN865 SF8) | `COMMISSIONED` | **`FALSE` (`NOT_DEMONSTRATED`)** |
| `STN_MANA_01` | Manali Bridge | 32.2432°N, 77.1892°E | 1980.0 m | Ultrasonic Stage (`SN-MB-2026-4401`) | Optical Rain (`SN-RG-2026-0922`) | 3.70V / 10W MPPT | SX1276 (IN865 SF7) | `COMMISSIONED` | **`FALSE` (`NOT_DEMONSTRATED`)** |
| `STN_ALEN_01` | Allain Barrage | 32.2150°N, 77.2020°E | 1850.0 m | Pressure Transducer (`SN-KL-2026-7819`) | Hydrophone (`SN-SH-2026-1105`) | 3.66V / 10W MPPT | SX1276 (IN865 SF9) | `COMMISSIONED` | **`FALSE` (`NOT_DEMONSTRATED`)** |
| `STN_PAND_01` | Pandoh Dam | 31.6700°N, 77.0600°E | 890.0 m | Radar Level (`SN-SM-2026-5532`) | EC / Temp (`SN-AA-2026-0412`) | 3.69V / 10W MPPT | SX1276 (IN865 SF7) | `COMMISSIONED` | **`FALSE` (`NOT_DEMONSTRATED`)** |

> [!NOTE]
> **FIELD DEPLOYMENT VERDICT**: All 5 stations are staged in laboratory testbeds. **0 stations are deployed in active river water**. In-situ mountain river deployment is classified as **`NOT_DEMONSTRATED`**.

---

## 2. Telemetry Performance Matrix: Simulation vs. Physical Bench vs. Field

| Time Window | Ingestion Tier | Packets Attempted | Packets Received | PDR (%) | Latency | CRC Error | Provenance Classification | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **24 Hours** | Software Soak Ingestion | 6,738,336 | 6,738,336 | **100.00%** | 12.8 ms | 0.00% | `SIMULATION_DEMONSTRATED` | Software Stress Verified |
| **24 Hours** | Bench Physical RF Loopback | 8,640 | 8,618 | **99.75%** | 84.2 ms | 0.12% | `PHYSICAL_BENCH_TESTBED` | Bench Hardware Validated |
| **24 Hours** | In-Situ River Water Deployment | 0 | 0 | **0.00%** | N/A | N/A | `NOT_DEMONSTRATED` | **NOT_DEMONSTRATED** |
| **72 Hours** | Software Soak Ingestion | 20,215,008 | 20,215,008 | **100.00%** | 13.1 ms | 0.00% | `SIMULATION_DEMONSTRATED` | Software Stress Verified |
| **72 Hours** | Bench Physical RF Loopback | 25,920 | 25,832 | **99.66%** | 86.5 ms | 0.19% | `PHYSICAL_BENCH_TESTBED` | Bench Hardware Validated |
| **72 Hours** | In-Situ River Water Deployment | 0 | 0 | **0.00%** | N/A | N/A | `NOT_DEMONSTRATED` | **NOT_DEMONSTRATED** |
| **7 Days** | Software Soak Ingestion | 47,168,352 | 47,168,352 | **100.00%** | 13.4 ms | 0.00% | `SIMULATION_DEMONSTRATED` | Software Stress Verified |
| **7 Days** | Bench Physical RF Loopback | 60,480 | 60,128 | **99.42%** | 88.9 ms | 0.31% | `PHYSICAL_BENCH_TESTBED` | Bench Hardware Validated |
| **7 Days** | In-Situ River Water Deployment | 0 | 0 | **0.00%** | N/A | N/A | `NOT_DEMONSTRATED` | **NOT_DEMONSTRATED** |
| **30 Days** | Software Soak Ingestion | 202,150,080 | 202,150,080 | **100.00%** | 13.5 ms | 0.00% | `SIMULATION_DEMONSTRATED` | Software Stress Verified |
| **30 Days** | Bench Physical RF Loopback | 259,200 | 257,385 | **99.30%** | 91.2 ms | 0.38% | `PHYSICAL_BENCH_TESTBED` | Bench Hardware Validated |
| **30 Days** | In-Situ River Water Deployment | 0 | 0 | **0.00%** | N/A | N/A | `NOT_DEMONSTRATED` | **NOT_DEMONSTRATED** |

---

## 3. Pre-Track B Evidence Tier Classification (M1–M20)

| Evidence Tier | Models Assigned | Model Count | Ground Truth Character |
| :--- | :--- | :--- | :--- |
| **Preliminary External Evidence** | **M2, M6, M7** | **3** | Official GSI/HPSDMA GPS survey points, CWC high-water marks |
| **Proxy Validated Prototype** | **M4, M11** | **2** | ISRO/Copernicus Sentinel-1 microwave SAR water extent masks |
| **Global Empirical Benchmark** | **M12** | **1** | Peer-reviewed Froehlich (2008) / Costa (1985) global dam breaches |
| **Synthetic Benchmarked Prototype** | **M9, M10, M14, M15, M16, M17, M18, M19, M20** | **9** | Internal statistical fixtures and graph routing stress fixtures |
| **Pending External Data** | **M1, M3, M5, M8, M13** | **5** | Operational agency archives (IMD DWR, NCMRWF, BBMB, Census) |
| **TOTAL** | **M1–M20** | **20** | **100% Accounted For (Zero Retraining, Zero Modifications)** |
