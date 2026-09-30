# FLOODY SHIELD v3.6 — Gateway Operations & Replay Architecture

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Document Version:** 1.0  
**Scope:** LoRa Gateway Field Deployment, Mountain Ridge Topography, Backhaul Resilience, Offline Ring Buffering, and Chronological Replay.

---

## 1. Gateway Site Selection & Strategic Mountain Geometry

Due to severe mountain diffraction and terrain blockage in the Upper Beas Valley, LoRa gateways are positioned atop high commanding ridge peaks providing wide-angle line-of-sight (LOS) down the valley axis:

| Gateway ID | Geographical Location | Elevation (m MSL) | Valley Line-of-Sight Coverage Reach |
|:---|:---|:---:|:---|
| **GW_ROHTANG_01** | Rohtang Ridge / Marhi Spur | 3,350 m | Solang Valley, Palchan, Upper Manali Reach |
| **GW_BIJLI_01** | Bijli Mahadev Peak | 2,460 m | Kullu Town, Bhuntar Airport, Parbati Confluence |
| **GW_LARJI_01** | Aut / Larji Dam Ridge | 1,420 m | Aut Gorge, Pandoh Reservoir, Larji Hydropower |

---

## 2. Gateway Hardware Specification

- **Gateway Engine**: Multitech Conduit IP67 Outdoor / Dragino DLOS8 Industrial LoRaWAN Gateway.
- **RF Engine**: Semtech SX1302 / SX1303 multi-channel concentrator with 8 concurrent uplink demodulation channels.
- **Backhaul Connectivity**:
  - Primary: Industrial 4G/LTE Cat-M1/NB-IoT modem with dual-SIM auto-failover (Airtel + Jio).
  - Secondary: High-reliability low-earth-orbit (LEO) satellite data link or 5.8 GHz directional microwave link back to Kullu Emergency Operations Center (EOC).
- **Power**: 100W solar panel + 12V 50Ah LiFePO4 battery bank with 21-day autonomy.

---

## 3. Backhaul Loss & Chronological Replay Architecture

During cloudburst events, debris flows frequently take down terrestrial cellular base transceiver stations (BTS) along NH-3.

```
[ Field Sensor Nodes ] --- (LoRa Radio IN865) ---> [ Mountain Gateway ]
                                                           |
                                               Is 4G Cellular Backhaul Up?
                                                /                      \
                                              YES                       NO
                                              /                          \
                                [ Direct Forward to ]           [ Write to Local Flash ]
                                [ Backend REST API  ]           [ Ring Buffer (5,000 pkts)]
                                                                         |
                                                               (Cellular Reconnects)
                                                                         |
                                                                [ Chronological Drain ]
                                                                [  Sorted by Obs Time ]
                                                                         |
                                                                         v
                                                                [ Ingest into Backend ]
                                                                [ Deduplication Safe  ]
```

### 3.1 Ring Buffer Specifications
- Capacity: 5,000 LoRa frames (sufficient for >3.5 days of continuous multi-sensor buffering per gateway).
- Storage: Non-volatile industrial SLC NAND flash with power-fail safe journaling.

### 3.2 Chronological Replay Execution
When cellular or satellite connectivity is restored:
1. The gateway suspends real-time streaming for a brief synchronization window.
2. The buffer is sorted by `timestamp_epoch` (observation time).
3. Packets are streamed chronologically with original `observed_at` metadata and current `received_at` metadata.
4. The backend Quality Gate evaluates `temporal_state`: observations older than 1 hour are flagged `LATE` or `STALE` but correctly ingested into the historical database without corrupting real-time models.
5. Idempotency hashes ensure zero double-counting.
