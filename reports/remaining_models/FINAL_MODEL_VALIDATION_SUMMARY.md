# FLOODY SHIELD — Final Model Validation Summary (M1–M20)

**FLOODY SHIELD — Predict • Protect • Preserve**
AOI: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India
SIH Problem Statement 26192

Generated: 2026-09-21 (Revised after Dataset Benchmark Audit)

---

> [!IMPORTANT]
> **Data integrity pledge**: No observations have been fabricated, no external landslide/flood points have been moved into the Upper Beas AOI, no model metrics have been artificially inflated, and no synthetic data is presented as external validation evidence.

> [!NOTE]
> Validation statuses were revised on 2026-09-21 following a systematic dataset benchmark audit against published minimum training-data requirements. See [`reports/DATASET_BENCHMARK_AUDIT.md`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/reports/DATASET_BENCHMARK_AUDIT.md) for the full audit.

---

## All-Model Validation Summary Table (Revised)

| ID | Model Name | Domain | Method | Training Data Nature | Benchmark Min | Current Scale | Benchmark Met? | Honest Validation Status | Key Limitations |
|----|-----------|--------|--------|---------------------|--------------|--------------|---------------|--------------------------|----------------|
| M1 | Extreme Rainfall Nowcasting | Rainfall | LightGBM (6 horizons) | Simulated AWS calibrated to IMD | 2–3 yr real hourly | Simulated 5-yr, n=600 eval | ❌ Below | `PROTOTYPE_SIMULATED_DATA` | No raw IMD/GPM records; degrades >+3h |
| M2 | Flood Risk Classification | Flood | XGBoost + Platt | Calibrated HEC-RAS simulation | 100+ real events | 10k sim points; N=6 ext. valid | ❌ Below | `PRELIMINARY_EXTERNAL_EVIDENCE` | N=6 ext. valid points; wide CIs |
| M4 | Flood Inundation Segmentation | Flood | 9-Channel U-Net | 1 event + SAR-HAND proxy masks | 500+ labelled scenes | 1 event, proxy GT | ❌ Below | `PROXY_VALIDATED_PROTOTYPE` | No scene-level GT; Dice vs proxy masks |
| M6 | Landslide Susceptibility | Landslide | Random Forest (350 trees) | Synthetic DEM/GSI simulation | 500+ failures + controls | 10k sim; N=6 ext. valid | ❌ Below | `INSUFFICIENT_EXTERNAL_EVIDENCE` | Recall 16.67% on 6 ext. points |
| M7 | Landslide Trigger | Landslide | LightGBM (350 rounds) | Synthetic IMD/ERA5 storm catalog | 100+ real storms | 10k sim; N=7 storms | ❌ Below | `PRELIMINARY_EXTERNAL_EVIDENCE` | N=7 storms; spec. = 0%; spatial AUC 0.198 |
| PWP | Pore Water Pressure / SSI | Physics | Analytical (Bishop + Richards) | N/A — physics | Site-specific params | Regional literature params | ⚠️ Partial | `PHYSICS_VALIDATED_REGIONAL_PARAMETERS` | Regional params; no site boreholes |
| M8 | Ground Movement / Deformation | Landslide | GBDT (3 horizons) | Simulated InSAR/tiltmeter profiles | 50+ real monitored sites | 4k synthetic profiles | ❌ Below | `PROTOTYPE_SIMULATED_DATA` | 0 real InSAR sites; synthetic only |
| M9 | IoT Sensor Anomaly Detection | Anomaly | Isolation Forest + rules | Simulated IoT telemetry | 10k+ real + labelled | 5k simulated + 6 faults | ❌ Below | `PROTOTYPE_SIMULATED_DATA` | 5k < 10k minimum; Stage 1 rules robust |
| M10 | River Water-Level Forecast | Flood | GBDT (4 horizons) | Simulated Beas hydrographs | 2–5 yr real gauge | Simulated; n=4,500 | ❌ Below | `PROTOTYPE_SIMULATED_DATA` | No real CWC gauge records |
| M11 | Flood Propagation / Depth | Flood | GBDT (regression) | Simulated HEC-RAS/HAND | 50+ real flood events | Simulated; n=4,000 | ❌ Below | `PROTOTYPE_SIMULATED_DATA` | No real flood extent scenes |
| M12 | Hazard Cascade / Dam Breach | Flood | Empirical (Froehlich + wave) | 111 global dam breach cases | 100+ multi-hazard events | 111 global cases ✅ | ✅ **MEETS** | `EMPIRICALLY_BENCHMARKED_MEETS_MINIMUM` | Himalayan: 3/3 events within obs. range |
| M13 | Vulnerability / Pop. Exposure | Decision | GBDT (UNDRR composite) | Census 2011 + HP Tourism stats | Census + seasonal pop | Real Census; modelled tourism | ✅ Partial | `CENSUS_GROUNDED_MODELLED_SCENARIOS` | Tourist multipliers MODELLED/ASSUMED |
| M14 | Infrastructure Damage & Loss | Decision | GBDT + fragility curves | NDMA/USACE curves + synthetic scenarios | 100+ asset-event records | Real assets; synthetic damage | ❌ Below | `PROTOTYPE_CURVE_BASED` | Damage ratios not from field observations |
| M15 | Safe Zone Selection | Decision | Rule-based constraint opt. | Real GIS (DEM + OSM + HPSDMA) | GIS + hazard maps | Complete GIS coverage | ✅ **MEETS** | `RULE_VALIDATED` | Static shelter capacity |
| M16 | Evacuation Routing | Decision | NetworkX A\* / Dijkstra | Real OSM road graph | GIS network | Real OSM graph | ✅ **MEETS** | `RULE_VALIDATED` | No real-time blockage feed |
| M17 | Warning Gating & Evacuation | Decision | GBDT + deterministic override | CWC/NDMA thresholds + 1,600 synthetic scenarios | 100+ real events | 1,600 synthetic (circular) | ❌ Below | `DETERMINISTIC_OVERRIDES_VALIDATED; ML_PROTOTYPE_ONLY` | 100% accuracy on synthetic scenarios only |
| M18 | Risk Calibration | Calibration | Platt + Isotonic | SYNTHETIC beta pairs only | 100+ real pred-outcome pairs | 1k synthetic pairs | ❌ Below | `PROTOTYPE_SYNTHETIC_PIPELINE_ONLY` | 0 real event outcomes |
| M19 | Time-to-Impact Prediction | Impact | Kinematic baseline | N/A (physics) + 3 published events | 50+ timestamped events | 3 Himalayan benchmarks | ❌ Below | `PHYSICS_PROOF_OF_CONCEPT; ML_INSUFFICIENT_EVIDENCE` | 3 events vs 50 minimum; 0 Upper Beas |
| M20 | Post-Event Damage Assessment | Assessment | Change detection baseline | N/A (unsupervised) | 500+ labelled damage samples | 0 labelled samples | ❌ Below | `CHANGE_DETECTION_ONLY` | EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE |

---

## Models That Meet Their Benchmark Minimum

| Model | Why |
|-------|-----|
| **M12** | Froehlich (2008) + Costa (1985) calibrated on **111 global dam-breach cases** — exceeds 100-event minimum; 3/3 Himalayan benchmarks within observed range |
| **M15** | Rule-based GIS optimization; benchmark is routing completeness/correctness — satisfied with real DEM + OSM + HPSDMA data |
| **M16** | NetworkX routing on real OSM road graph; benchmark satisfied |
| **M13** | Census 2011 demographic foundation is real published data (tourist scenarios are modelled but the base data is authoritative) |

---

## Validation Status Definitions (Full Taxonomy)

| Status | Meaning |
|--------|---------|
| `EMPIRICALLY_BENCHMARKED_MEETS_MINIMUM` | Evaluated on ≥ benchmark minimum real observations; published equations independently calibrated |
| `RULE_VALIDATED` | Deterministic rule logic verified for constraint compliance; not an ML training-data benchmark |
| `CENSUS_GROUNDED_MODELLED_SCENARIOS` | Real Census/government data underpins demographics; scenario training is model-generated |
| `PHYSICS_VALIDATED_REGIONAL_PARAMETERS` | Physics equations correct; soil/geotechnical parameters from regional literature, not site boreholes |
| `PHYSICS_PROOF_OF_CONCEPT; ML_INSUFFICIENT_EVIDENCE` | Physics verified on analogue events; ML layer lacks minimum real data |
| `PRELIMINARY_EXTERNAL_EVIDENCE` | Some real external evidence exists but sample size far below minimum (N << 100) |
| `PROTOTYPE_SIMULATED_DATA` | All or nearly all training data is physics-calibrated simulation; no real event records |
| `PROXY_VALIDATED_PROTOTYPE` | Internal convergence against proxy masks verified; no authoritative external ground truth |
| `INSUFFICIENT_EXTERNAL_EVIDENCE` | External evidence attempted but sample insufficient for statistical claims |
| `PROTOTYPE_CURVE_BASED` | Real asset register; damage functions from literature curves, not field observations |
| `DETERMINISTIC_OVERRIDES_VALIDATED; ML_PROTOTYPE_ONLY` | Life-safety overrides implement statutory thresholds (valid); ML fusion layer validated only on synthetic scenarios |
| `PROTOTYPE_SYNTHETIC_PIPELINE_ONLY` | Infrastructure verified; no real training data |
| `CHANGE_DETECTION_ONLY` | Change indicators without supervised label classification; EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE |

---

## Priority Data Gaps for Upgrade to Research-Grade

| Priority | Model | Gap | Source |
|----------|-------|-----|--------|
| 🔴 1 | M10 | 2+ yr real CWC gauge records | CWC / HP Water Resources |
| 🔴 2 | M1 | 2+ yr real IMD/GPM sub-hourly | IMD AWS + GPM IMERG |
| 🔴 3 | M2/M11 | 50–100 real independent flood events | CWC, HPSDMA, Sentinel-1 |
| 🔴 4 | M6/M7 | 500+ GSI/HPSDMA landslide failures | GSI field survey, HPSDMA reports |
| 🟠 5 | M8 | 50+ real InSAR slope sites, multi-year | Sentinel-1, ISRO Cartosat |
| 🟠 6 | M4/M11 | 50–100 Sentinel-1/2 flood scene pairs | Copernicus EMS, NRSC DMSP |
| 🟠 7 | M14/M20 | 100+ post-event damage records | HP PWD / HPSDMA |
| 🟡 8 | M9 | 10,000+ real IoT sensor readings | Deployed AWS/tiltmeter logs |
| 🟡 9 | M19 | 50+ timestamped hazard-arrival events | CWC + district records |
| 🟡 10 | M18 | 100+ real prediction-outcome pairs | Operational model outputs |

---

## Test Suite Status (Unchanged)

| Batch | New Tests | Cumulative |
|-------|----------|-----------|
| Baseline (M2/M4/M6/M7/PWP) | — | 113 |
| Validation audit | — | 155 |
| Batch 1 (M1/M8/M9) | +50 | 205 |
| Batch 2 (M10/M11/M12) | +60 | 265 |
| Batch 3 (M13/M14/M17) | +22 | 348 |
| Final (M18/M19/M20) | +45 | **393** |

**Final test suite: 393 passed, 0 failed, 0 errors.**

---

## Project Level Declaration

This is an honest **Level 1 (Prototype)** system.

- **Level 1 (Prototype)**: Real public data + existing physics models + small authentic validation datasets + simulated scenarios for demonstration. ← **Current project status**
- **Level 2 (Research-grade)**: 100+ flood events, 100+ landslide storms, 5–10 yr real gauge/rainfall records, satellite scene datasets.
- **Level 3 (Operational-grade)**: Continuous live sensors, government data agreements, real-time monitoring, independent large-scale validation, field validation, cybersecurity, and human authorization workflows.

Correcting validation statuses to their honest level does not invalidate the system architecture, the physics, or the SIH prototype. It accurately characterises what data is needed to progress from Level 1 to Level 2.

---
*FLOODY SHIELD v3.0 | SIH-26192 | Revised: 2026-09-21 following Dataset Benchmark Audit*
