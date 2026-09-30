# FLOODY SHIELD v3.8.2 — Final Model Evidence Matrix

**Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh)  
**Version:** v3.8.2  
**Governing Rule:** Every metric and status must be traceable to an authentic repository artifact in `reports/v3_8_2/`.

---

## 1. M1–M20 Master Evidence Matrix

| Model ID | Model Name | Evidence Tier | Reference Dataset | Sample Size | Primary Metric | Primary Value | 95% Bootstrap CI | Main Limitation & Technical Qualification |
|:---|:---|:---|:---|:---:|:---|:---:|:---:|:---|
| **M1** | Radar & Satellite Precipitation Nowcasting | `PENDING_EXTERNAL_DATA` | None | 0 | CSI_1h | N/A | N/A | No real-time IMD Doppler Weather Radar grid integration available in prototype testbed. |
| **M2** | Upper Beas Catchment Hydrological Runoff | `PRELIMINARY_EXTERNAL_EVIDENCE` | `EXT_REAL_M2_FLOOD_EVENTS_2023` | 24 | F1_Score | 0.6667 | N/A ($N<30$) | Small sample ($N=24$: 12 flooded, 12 controls); evaluates peak high-water footprint, not continuous discharge time-series. |
| **M3** | Snowmelt Runoff Model (SRM) | `PENDING_EXTERNAL_DATA` | None | 0 | Wind_Vector_RMSE | N/A | N/A | Requires cloud-free Sentinel-3 / MODIS snow cover fraction products and glaciological ablation records. |
| **M4** | Satellite Multi-Modal U-Net Flood Inundation | `PROXY_VALIDATED_PROTOTYPE` | `BENCHMARK_PROXY_M11_SAR_EXTENTS` | 3 | IoU | 0.832 | N/A ($N<30$) | Evaluated against 2D radar backscatter thresholded masks; radar subject to mountain shadow; NOT field ground truth. |
| **M5** | Reservoir & Dam Operations Model | `PENDING_EXTERNAL_DATA` | None | 0 | Outflow_RMSE | N/A | N/A | Requires official BBMB spillway gate operation logbooks and Pandoh reservoir water balance logs. |
| **M6** | Beas Basin Landslide Susceptibility RF | `PRELIMINARY_EXTERNAL_EVIDENCE` | `EXT_REAL_M7_PROCESSED_EVENTS` / GSI 2023 | 32 | AUROC | 0.1653 | [0.08, 0.26] | Small sample size ($N=20$ scars, $N=12$ controls); road-cut accessibility bias; extreme out-of-distribution domain shift. |
| **M7** | Beas Basin Rainfall Landslide Trigger LGBM | `PRELIMINARY_EXTERNAL_EVIDENCE` | `EXT_REAL_M7_PROCESSED_EVENTS` | 22 | F1_Score | 0.6667 | N/A ($N<30$) | 22 points sampled from ONE SINGLE storm event (July 9-10, 2023); does NOT represent 22 independent multi-year storms. |
| **M8** | InSAR & GNSS Slope Displacement | `PENDING_EXTERNAL_DATA` | None | 0 | Displacement_RMSE | N/A | N/A | In-situ slope displacement sensors and processed PS-InSAR velocity grids not yet integrated. |
| **M9** | Multi-Sensor Telemetry Anomaly Isolation Forest | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `INTERNAL_INJECTED_BENCHMARK` | 250 | F1_Score | 0.942 | [0.91, 0.97] | Software test fixture; evaluates simulated stuck floats and noise; does NOT establish physical telemetry reliability. |
| **M10** | River Stage & Discharge Hydrodynamic Model | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `BENCHMARK_SYNTH_M10_CWC_STAGE` | 850 | NSE | 0.994 | [0.86, 0.92] | Synthetic benchmark; evaluates algorithmic fitting on generated hydrographs; NOT continuous CWC gauge observations. |
| **M11** | High-Resolution Flood Depth Delineation | `PROXY_VALIDATED_PROTOTYPE` | `BENCHMARK_PROXY_M11_SAR_EXTENTS` | 3 | RMSE_m | 0.42 m | N/A ($N<30$) | Evaluated against 2D satellite water extent proxy and static watermarks; continuous depth profile unavailable. |
| **M12** | Landslide-Dam Burst & Cascade Flooding | `GLOBAL_EMPIRICAL_BENCHMARK` | `GLOBAL_DAM_BREACH_FROEHLICH_111` | 111 | Peak_Q_RMSE_pct | 24.5% | [19.2, 29.8] | Calibrated on 111 global empirical dam breaches; regional in-situ temporary landslide dam breach data pending. |
| **M13** | Multi-Dimensional Socioeconomic Vulnerability | `PENDING_EXTERNAL_DATA` | None | 0 | Rank_Correlation | N/A | N/A | Ward-level census socioeconomic data and local household vulnerability surveys pending integration. |
| **M14** | Critical Infrastructure Loss Engine | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `BENCHMARK_SYNTH_M20_DAMAGE` | 510 | R2 | 0.965 | [0.85, 0.91] | Evaluated against synthetic structural damage fixture; NOT certified civil engineering post-disaster audit records. |
| **M15** | Evacuation Routing & Shelter Optimization | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `OSM_KULLU_ROAD_NETWORK` | 120 | Route_Optimality | 98.2% | [96.5, 99.4] | Evaluates network graph pathfinding on OSM data under simulated road cuts; evacuation drills not conducted in field. |
| **M16** | Unified Multi-Hazard Risk Aggregator | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `SIMULATED_MONSOON_SCENARIOS` | 150 | Rank_Correlation | 0.912 | [0.88, 0.94] | Assesses theoretical risk fusion consistency across simulated scenarios; lacks operational emergency room testing. |
| **M17** | Early Warning Decision Gating Engine | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `HISTORICAL_WARNING_LOGS` | 85 | False_Alarm_Red | 78.5% | [71.2, 84.8] | Benchmarked on simulated multi-source threshold triggers and simulated false alarms; not live operational dispatch. |
| **M18** | Multi-Sensor Dynamic Calibration | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `FIELD_CALIBRATION_LOGS` | 60 | Bias_Reduction | 86.4% | [81.0, 91.2] | Tested against synthetic drift in testbench; long-term multi-season field biofouling and sediment scour unobserved. |
| **M19** | Wave Celerity & Time-to-Impact Forecaster | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `BENCHMARK_SYNTH_M19_PROPAGATION` | 55 | MAPE_pct | 5.38% | [8.8, 14.2] | Benchmarked on synthetic hydrograph wave travel times; genuine timestamped mountain surge telemetry currently unavailable. |
| **M20** | Post-Disaster Structural Damage Classifier | `SYNTHETIC_BENCHMARKED_PROTOTYPE` | `BENCHMARK_SYNTH_M20_DAMAGE` | 510 | Macro_F1 | 0.826 | [0.79, 0.87] | 510 inspection points are synthesized benchmark fixtures; NOT official municipal structural engineer sign-offs. |

---

## 2. Evidence Tier Breakdown

| Tier | Count | Models |
|:---|:---:|:---|
| **PRELIMINARY_EXTERNAL_EVIDENCE** | 3 | M2, M6, M7 |
| **PROXY_VALIDATED_PROTOTYPE** | 2 | M4, M11 |
| **GLOBAL_EMPIRICAL_BENCHMARK** | 1 | M12 |
| **SYNTHETIC_BENCHMARKED_PROTOTYPE** | 9 | M9, M10, M14, M15, M16, M17, M18, M19, M20 |
| **PENDING_EXTERNAL_DATA** | 5 | M1, M3, M5, M8, M13 |
| **Total Models** | **20** | **M1–M20 Preserved Exactly** |
