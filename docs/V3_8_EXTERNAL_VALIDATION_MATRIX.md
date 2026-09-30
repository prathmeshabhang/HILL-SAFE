# FLOODY SHIELD v3.8 / v3.8.1 — Evidence & Validation Matrix (All 20 Models)

**System:** FLOODY SHIELD — Flash Flood Prediction System for Hilly Regions  
**Target Basin:** Upper Beas River Basin, Himachal Pradesh, India  
**Maturity Tier:** Level 1 — Prototype / Research Decision-Support System  
**Version:** v3.8.1 Audited Baseline  

---

| Model ID | Model Name | Evidence Status | Dataset ID / Reference | Sample Size ($N$) | Primary Metric | Primary Score | Scientific Notes |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **M1** | Extreme Rainfall Nowcast | `PENDING_EXTERNAL_DATA` | None | 0 | - | - | Pending IMD Doppler X-band radar volume scans. |
| **M2** | Catchment Runoff / Flood Model (Frozen) | `PRELIMINARY_EXTERNAL_EVIDENCE` | `EXT_REAL_M2_FLOOD_EVENTS_2023` | 24 | F1_Score | **0.6667** | Evaluated on 24 authentic HPSDMA/CWC July 2023 disaster flood inundation locations. Preliminary external evidence. |
| **M3** | Snowmelt Runoff Model (SRM) | `PENDING_EXTERNAL_DATA` | None | 0 | - | - | Awaiting cloud-free Sentinel-3 SCA time series. |
| **M4** | Satellite U-Net Inundation (Frozen) | `PROXY_VALIDATED_PROTOTYPE` | `BENCHMARK_PROXY_M11_SAR_EXTENTS` | 3 | IoU | **0.8320** | Benchmarked against Sentinel-1A SAR July 2023 flood extent polygons. Proxy remote sensing validation. |
| **M5** | Reservoir Operations Model | `PENDING_EXTERNAL_DATA` | None | 0 | - | - | Awaiting official BBMB Pandoh spillway gate logs. |
| **M6** | Landslide Susceptibility RF (Frozen)| `PRELIMINARY_EXTERNAL_EVIDENCE` | `EXT_REAL_M7_PROCESSED_EVENTS` | 22 | AUROC | **0.1653** | Evaluated on 22 field points (GSI Report M4EGG/C/NR/SU-PHP/2023/46620 & HPSDMA). Preliminary external evidence. |
| **M7** | Landslide Trigger LightGBM (Frozen)| `PRELIMINARY_EXTERNAL_EVIDENCE` | `EXT_REAL_M7_PROCESSED_EVENTS` | 22 | F1_Score | **0.6667** | Verified on 22 spatially independent storm-landslide field points (July 2023 disaster). Preliminary external evidence. |
| **M8** | InSAR / GNSS Slope Displacement | `PENDING_EXTERNAL_DATA` | None | 0 | - | - | Requires continuous dual-frequency GNSS rover network. |
| **M9** | Sensor Anomaly Isolation Forest | `EMPIRICALLY_BENCHMARKED` | `INTERNAL_INJECTED_BENCHMARK` | 250 | F1_Score | **0.9420** | Tested against multi-sensor synthetic anomalies in test bench. |
| **M10**| River Stage & Discharge Model | `EMPIRICALLY_BENCHMARKED` | `BENCHMARK_SYNTH_M10_CWC_STAGE` | 850 | NSE | **0.9946** | Evaluated against synthetic stage hydrograph simulation. Real-time CWC stream gauge API pending field integration. |
| **M11**| High-Res Flood Depth Model | `PROXY_VALIDATED_PROTOTYPE` | `BENCHMARK_PROXY_M11_SAR_EXTENTS` | 3 | RMSE | **0.42 m** | Delineation tested against high-water marks and Sentinel-1 SAR flood extents proxy. |
| **M12**| Landslide-Dam Breach Cascade | `PENDING_EXTERNAL_DATA` | None | 0 | - | - | Pending post-event physical survey of breach episodes. |
| **M13**| Socio-Economic Vulnerability | `PENDING_EXTERNAL_DATA` | None | 0 | - | - | DDMP socioeconomic ward-level survey pending. |
| **M14**| Critical Infrastructure Loss | `EMPIRICALLY_BENCHMARKED` | `BENCHMARK_SYNTH_M20_DAMAGE` | 510 | R² | **0.9707** | Tested against simulated structural loss benchmark fixture (N=510). Pipeline regression benchmark. |
| **M15**| Evacuation Routing Optimizer | `EMPIRICALLY_BENCHMARKED` | `OSM_KULLU_ROAD_NETWORK` | 120 | Optimality | **98.2%** | Evaluated on OpenStreetMap Kullu road network graph. |
| **M16**| Multi-Hazard Risk Aggregator | `EMPIRICALLY_BENCHMARKED` | `SIMULATED_MONSOON_SCENARIOS` | 150 | Rank Corr | **0.9120** | Risk fusion consistency across simulated coupled hazard scenarios. |
| **M17**| Warning Gating & False Alarm Suppr.| `EMPIRICALLY_BENCHMARKED` | `HISTORICAL_WARNING_LOGS` | 85 | FA Reduct. | **78.5%** | Evaluated on multi-source confirmation logic in software test harness. |
| **M18**| Dynamic Sensor Calibration | `EMPIRICALLY_BENCHMARKED` | `FIELD_CALIBRATION_LOGS` | 60 | Bias Reduct.| **86.4%** | Verified on pressure transducer and ultrasonic stage sensor test bench. |
| **M19**| Time-to-Impact Forecaster | `EMPIRICALLY_BENCHMARKED` | `BENCHMARK_SYNTH_M19_PROPAGATION` | 55 | MAPE | **5.51%** | Tested against synthesized mountain channel wave celerity simulation events (N=55). |
| **M20**| Structural Damage Assessment | `EMPIRICALLY_BENCHMARKED` | `BENCHMARK_SYNTH_M20_DAMAGE` | 510 | Macro F1 | **0.7900** | Tested against simulated civil engineering structural damage fixture (N=510). |

---

### Audited Evidence Summary (v3.8.1)
- **Total Models in Catalog:** Exactly 20 models (M1–M20; zero M21+)
- **Preliminary External Evidence:** 3 models (M2, M6, M7: evaluated on genuine GSI/HPSDMA July 2023 disaster field records)
- **Proxy Validated Prototype:** 2 models (M4, M11: benchmarked against satellite SAR microwave flood delineations)
- **Empirically Benchmarked:** 9 models (M9, M10, M14, M15, M16, M17, M18, M19, M20: evaluated on simulated test benches & regression fixtures)
- **Pending External Data:** 6 models (M1, M3, M5, M8, M12, M13: awaiting official agency telemetry)
- **Frozen Models Immutability:** 4/4 bit-identical (M2, M4, M6, M7)
