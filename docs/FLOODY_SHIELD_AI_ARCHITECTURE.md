# FLOODY SHIELD — AI System Architecture

**FLOODY SHIELD — Predict • Protect • Preserve**  
Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
SIH Problem Statement 26192  
Document Version: 2.0 | Date: 2026-09-21

---

> [!IMPORTANT]
> This document describes the architecture of a **Level 1 (Prototype)** system. Many ML models are trained on physics-calibrated simulation. No ML model independently issues governmental emergency orders. Human/Agency authorization is mandatory for all life-safety alerts.

---

## 1. Data Layer

The data layer ingests, stores, and serves all raw input data for the FLOODY SHIELD pipeline.

### 1.1 Real Observational Sources (Available / Partial)

| Source | Type | Temporal | Spatial | Used In |
|--------|------|---------|---------|---------|
| Copernicus 30m DEM | DERIVED (satellite) | Static | 30m | M6, M8, M11, M16 |
| ESA WorldCover 10m LULC | DERIVED (satellite) | Annual | 10m | M6 |
| Sentinel-1 SAR (July 2023) | OBSERVATION | Single event | 10m | M4 training proxy |
| Sentinel-2 Optical (July 2023) | OBSERVATION | Single event | 10m | M4 training proxy |
| Census 2011 Kullu VTD | OBSERVATION | Static | Settlement | M13 |
| HP Tourism statistics | DERIVED | Annual | District | M13 (seasonal) |
| CWC danger/warning levels | OBSERVATION (thresholds) | Static | Gauge point | M17 |
| NDMA/USACE fragility curves | DERIVED (global literature) | Static | Global | M14 |
| OSM road network | DERIVED | Periodic | Vector | M16 |
| GSI landslide scarp inventory | OBSERVATION | 2023 disaster | 20 point sites | M6/M7 external only |

### 1.2 Simulated/Modelled Sources (Training Data)

| Dataset | Model Used For | Nature |
|---------|--------------|--------|
| `upper_beas_monsoon_aws_timeseries` | M1 training | SYNTHETIC calibrated to IMD/GPM distributions |
| `upper_beas_flood_dataset.csv` | M2 training | MODELLED (HEC-RAS/HAND hydraulic simulation) |
| `upper_beas_july2023_scene` | M4 training | OBSERVATION scene + SAR-HAND PROXY masks |
| `upper_beas_landslide_dataset.csv` | M6, M7 training | SYNTHETIC (calibrated to GSI statistics + DEM) |
| `upper_beas_insar_gnss_creeping_slopes` | M8 training | SYNTHETIC (calibrated to InSAR/tiltmeter ranges) |
| `upper_beas_nominal_iot_telemetry` | M9 training | SYNTHETIC (physics-constrained nominal sensor readings) |
| `upper_beas_cwc_hydrographic_telemetry` | M10 training | MODELLED (seasonal Beas hydrographs) |
| `upper_beas_hecras_hand_floodplain_profiles` | M11 training | MODELLED (HEC-RAS multi-reach calibration) |
| `himalayan_storm_landslide_catalog.csv` | M7 external | SYNTHESISED (IMD/ERA5/HPSDMA distributions) |
| Froehlich/Costa global dam-breach database | M12 calibration | EMPIRICAL (111 published global cases) |

### 1.3 External Ground Observations

| Dataset | N | Use | Spatial Independence |
|---------|---|-----|---------------------|
| July 2023 ground survey points | 24 | M2, M4 external eval | 6 strictly independent (>500m) |
| July/Aug 2023 GSI landslide scarp inventory | 20 scarps + 12 controls | M6, M7 external eval | 6–8 strictly independent |
| Sun Kosi 2014 dam breach | 1 event | M12 benchmark | Independent |
| Pareechu 2000/2005 dam breach | 2 events | M12 benchmark | Independent |
| Chamoli 2021 GLOF | 1 event | M12 + M19 benchmark | Independent |

---

## 2. Data Quality Layer

Implemented in `ml/data_quality/`.

| Component | Function |
|-----------|---------|
| `schema.py` | Schema dataclasses for sensor readings, spatial features, timestamps |
| `rules.py` | Hard physical constraints (negative rainfall impossible, water level ≥ 0) |
| `validator.py` | Composite validation pipeline: schema → physics → statistics |
| `provenance.py` | Dataset provenance logging (source, type: OBS/DERIVED/SYNTHETIC) |

**Data classification mandate**: Every dataset entering any model must be labelled as one of:
`OBSERVATION | DERIVED | MODELLED | PREDICTION | SYNTHETIC`

---

## 3. Feature Engineering

Feature engineering occurs within each model's domain package. There is no shared global feature store at prototype level.

| Model | Key Features | Engineering Note |
|-------|-------------|-----------------|
| M1 | Rainfall rate, CAPE proxy, orographic index | Simulated from IMD distribution |
| M2 | HAND, discharge, slope, DEM features | HEC-RAS-derived terrain features |
| M4 | SAR VV/VH/Ratio, S2 bands, NDWI, HAND | 9-band stack, 10m resolution |
| M6 | Slope, aspect, TPI, TRI, drainage distance | Copernicus DEM-derived |
| M7 | M6 class + rainfall 1h + antecedent 3d + soil moisture | Dynamic storm features |
| M8 | InSAR LOS velocity, acceleration, crack width | Simulated from InSAR statistics |
| M9 | 5 telemetry channels | Physics hard limits applied first |
| M10 | Stage, rate of rise, multi-interval rainfall | Simulated hydrograph features |
| M11 | Source stage/discharge, HAND, distance | Simulated HEC-RAS features |
| M12 | Dam height, reservoir volume | Froehlich/Costa empirical inputs |
| M13 | Census demographics, tourist multiplier, egress | Real census + assumed tourism |
| M14 | Flood depth, velocity, asset category | NDMA/USACE curves |

---

## 4. Rainfall Models

### M1 — Extreme Rainfall Nowcasting

- **Location**: `ml/rainfall/m1_nowcast/`
- **Algorithm**: LightGBM multi-output quantile regressors (6 horizons: 15m, 30m, 1h, 3h, 6h, 24h) + semi-Lagrangian persistence + orographic updraft proxy
- **Artifact**: `ml/rainfall/m1_nowcast/m1_nowcast_lgbm.joblib`
- **Evidence status**: `PROTOTYPE_SIMULATED_DATA`
- **Inputs**: Current rainfall rate, CAPE proxy, wind speed, orographic index
- **Outputs**: P10/P50/P90 precipitation (mm) per horizon
- **Known limitation**: All training data is simulated from IMD distributions. No real continuous radar/AWS records used.

---

## 5. Flood Models

### M2 — Flood Risk Classification

- **Location**: `ml/flood/m2_upper_beas_flood_model.joblib` (frozen)
- **Algorithm**: Calibrated XGBoost + Platt scaling
- **Evidence status**: `PRELIMINARY_EXTERNAL_EVIDENCE` — N=6 strictly independent points
- **Artifact SHA-256**: `a3f349f6d10547ed...` ✅ FROZEN

### M4 — Flood Inundation Segmentation

- **Location**: `data/satellite_output/flood_multimodal_unet.pt` (frozen)
- **Algorithm**: 9-channel U-Net (ResNet-34 + SE attention)
- **Evidence status**: `PROXY_VALIDATED_PROTOTYPE` — Dice=0.973 against SAR-HAND proxy, NOT field ground truth; N=24 point concordance
- **CRITICAL**: Internal Dice must NEVER be cited as external accuracy
- **Artifact SHA-256**: `45aa1823c395e14f...` ✅ FROZEN

### M10 — River Water-Level Forecast

- **Location**: `ml/flood/m10_water_level/`
- **Algorithm**: Kinematic extrapolation + LightGBM GBDT (4 horizons: 30m, 1h, 3h, 6h)
- **Evidence status**: `PROTOTYPE_SIMULATED_DATA`
- **Outputs**: Predicted stage (m), exceedance vs CWC warning/danger/HFL marks

### M11 — Flood Propagation / Depth

- **Location**: `ml/flood/m11_flood_depth/`
- **Algorithm**: Muskingum-Cunge wave routing + HAND-Manning GBDT regression
- **Evidence status**: `PROTOTYPE_SIMULATED_DATA`
- **Outputs**: Inundation depth (m), severity class, wave arrival time (min)

---

## 6. Landslide Models

### M6 — Landslide Susceptibility (Static)

- **Location**: `ml/landslide/m6_beas_susceptibility_rf.joblib` (frozen)
- **Algorithm**: Random Forest (350 trees)
- **Evidence status**: `INSUFFICIENT_EXTERNAL_EVIDENCE` — Recall=16.67% on N=6 strictly independent scarps
- **Artifact SHA-256**: `e4f5f9336683...` ✅ FROZEN
- **CRITICAL**: Must NOT be used as a real-time warning trigger

### M7 — Landslide Trigger (Dynamic)

- **Location**: `ml/landslide/m7_beas_trigger_lgbm.joblib` (frozen)
- **Algorithm**: LightGBM GBDT (350 rounds)
- **Evidence status**: `PRELIMINARY_EXTERNAL_EVIDENCE` — N=7 storm episodes
- **Artifact SHA-256**: `f3b8e88d3701...` ✅ FROZEN
- **CRITICAL**: Must always be used with PWP/SSI safety layer

### M8 — Ground Movement / Deformation

- **Location**: `ml/landslide/m8_deformation/`
- **Algorithm**: Kinematic creep physics + Saito inverse-velocity estimator + LightGBM GBDT (3 horizons)
- **Evidence status**: `PROTOTYPE_SIMULATED_DATA` — 4,000 synthetic slope profiles; 0 real InSAR sites

---

## 7. Hydrological / Physics Models

### PWP / SSI — Pore Water Pressure & Slope Stability

- **Location**: `ml/landslide/` (physics routines)
- **Algorithm**: Richards' equation (infiltration) → Bishop effective stress → Infinite-slope FS
- **Evidence status**: `PHYSICS_VALIDATED_REGIONAL_PARAMETERS`
- **IMPORTANT**: Soil parameters (cohesion, friction, Ks) from regional GSI/MoEF literature — NOT Upper Beas borehole measurements

### M12 — Hazard Cascade / Landslide Dam Breach

- **Location**: `ml/flood/m12_cascade/`
- **Algorithm**: Froehlich (2008) + Costa (1985) empirical formulas + wave routing
- **Evidence status**: `EMPIRICALLY_BENCHMARKED` — 111 global cases (MEETS 100-event minimum)
- **Domain transfer caveat**: 111 cases are global; only 3 confirmed Himalayan events. Upper Beas applicability is analogous but NOT proven.
- **Himalayan benchmark**: Sun Kosi 2014, Pareechu 2000/2005, Chamoli 2021 — all within predicted Q ranges

---

## 8. Hazard Fusion

No dedicated fusion model exists at the ML level. Fusion occurs at the M17 decision layer through:

1. **Deterministic life-safety overrides**: Statutory CWC/NDMA thresholds applied first
2. **Multi-hazard risk aggregation**: Combined probabilities from M2 + M7 + M10 + M11 + M12
3. **M18 calibration**: Post-prediction probability calibration (prototype-only; synthetic pipeline)

**The fused flood risk score (M2 × 0.4 + M4 × 0.6) is a heuristic ensemble weight, NOT a calibrated probability.** This is explicitly documented in `docs/SCIENTIFIC_VALIDATION_REPORT.md`.

---

## 9. Exposure / Vulnerability

### M13 — Population & Vulnerability

- **Location**: `ml/decision/m13_vulnerability/`
- **Evidence status**: `CENSUS_GROUNDED_MODELLED_SCENARIOS`
- **Real data**: Census 2011 Kullu District; HP Tourism Development Corporation statistics
- **Modelled**: Seasonal tourist multipliers (1.8× peak; ASSUMED/MODELLED — not directly observed)
- **Coverage**: 12 core Upper Beas corridor settlements

### M14 — Infrastructure Damage & Loss

- **Location**: `ml/decision/m14_infrastructure_loss/`
- **Evidence status**: `PROTOTYPE_CURVE_BASED`
- **Real data**: Real asset register (HP PWD, HPSEB, hospital locations)
- **Modelled**: NDMA/USACE depth-damage curves — NOT calibrated against Upper Beas observed damage records
- **Output**: Damage ratio, direct loss (INR Lakhs), outage hours per asset

---

## 10. Warning Decision Support

### M17 — Early Warning Gating

- **Location**: `ml/decision/m17_warning_gating/`
- **Architecture**: Hybrid — deterministic life-safety overrides FIRST, then ML fusion
- **Evidence status**: `DETERMINISTIC_OVERRIDES_VALIDATED; ML_PROTOTYPE_ONLY`
- **Deterministic rules** (valid, sourced from CWC/NDMA SOPs):
  - Stage ≥ CWC danger level → RED_EVACUATE (mandatory)
  - Dam outburst Qp ≥ 1,000 m³/s → RED_EVACUATE (mandatory)
  - Inundation depth ≥ 1.5m → RED_EVACUATE (mandatory)
  - Stage ≥ CWC warning level → ORANGE_ALERT (floor)
- **ML classifier**: 100% accuracy on SYNTHETIC scenarios derived from the SAME deterministic rules → CIRCULAR VALIDATION; ML_PROTOTYPE_ONLY
- **Output format**: CAP v1.2 compliant alert payloads

---

## 11. Calibration

### M18 — Risk Calibration

- **Location**: `ml/calibration/m18_calibration/`
- **Algorithm**: Platt scaling / Isotonic regression (auto-selected via Brier score)
- **Evidence status**: `PROTOTYPE_SYNTHETIC_PIPELINE_ONLY`
- **Critical limitation**: 0 real prediction-outcome pairs; pipeline demonstrated on synthetic beta-distributed pairs ONLY
- **Returns**: `INSUFFICIENT_EVIDENCE` if < 50 samples or < 5 positives

---

## 12. Time-to-Impact

### M19 — Time-to-Impact Prediction

- **Location**: `ml/impact/m19_time_to_impact/`
- **Algorithm**: Kinematic physics (Manning wave speed + Hungr 1995) + ML quantile regression (INSUFFICIENT_EVIDENCE declared)
- **Evidence status**: `PHYSICS_PROOF_OF_CONCEPT; ML_INSUFFICIENT_EVIDENCE`
- **Benchmark**: 3/3 Himalayan analogues within P10–P90 range
- **CRITICAL**: 0 Upper Beas–specific timestamped events; 3 benchmark events far below 50-event minimum

---

## 13. Safe Zone

### M15 — Safe Zone Selection

- **Location**: `ml/decision/m15_safe_zones/`
- **Algorithm**: Constraint-based GIS optimization (not ML)
- **Evidence status**: `RULE_VALIDATED`
- **Data**: Real DEM + OSM + HPSDMA shelter register
- **Output**: Ranked safe zone list with capacity, distance, hazard score

---

## 14. Evacuation Routing

### M16 — Evacuation Routing

- **Location**: `ml/decision/m16_evacuation_routing/`
- **Algorithm**: NetworkX A\*/Dijkstra on hazard-weighted road graph
- **Evidence status**: `RULE_VALIDATED`
- **Data**: Real OSM road network + NH-3/NH-305 corridors
- **Dynamic**: Edge weights updated from M11 (flood depth) and M12 (surge) hazard maps

---

## 15. Post-Event Assessment

### M20 — Post-Event Damage Assessment

- **Location**: `ml/assessment/m20_damage_assessment/`
- **Algorithm**: Multi-indicator change detection (NDVI + NDWI + SAR coherence + physics proxy)
- **Evidence status**: `CHANGE_DETECTION_ONLY`
- **Critical limitation**: 0 labelled damage samples; EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE
- **Output**: `CHANGE_DETECTED` or `NO_CHANGE` — NOT a supervised damage classification
- **CRITICAL**: CHANGE_DETECTED ≠ DAMAGE_CONFIRMED

---

## 16. Physics Layer

| Physics Module | Equations | Location |
|---------------|-----------|---------|
| PWP Infiltration | Richards' unsaturated flow | `ml/landslide/` |
| Slope stability | Bishop effective stress, infinite-slope FS | `ml/landslide/` |
| Kinematic wave | Manning open-channel | M10, M19 |
| Dam breach | Froehlich (2008), Costa (1985) | M12 |
| Flood depth | HAND hydrostatic mapping | M11 |
| Debris runout | Hungr (1995) empirical | M19 |

---

## 17. Uncertainty Layer

Every model output carries uncertainty information:

| Model | Uncertainty Method |
|-------|------------------|
| M1 | P10/P50/P90 quantile regression |
| M2 | Clopper-Pearson CIs on validation metrics (documented) |
| M6 | Clopper-Pearson CIs; ROC-AUC NOT_ESTIMABLE on N<15 |
| M7 | Clopper-Pearson CIs per event class |
| M10 | MAE per horizon; CI on simulated holdout |
| M11 | R² per holdout; single scenario verified |
| M12 | ±24.5% RMSE envelope on Froehlich predictions |
| M18 | ECE, Brier score, calibration slope/intercept |
| M19 | P10/P50/P90 parametric uncertainty (±30%) |
| M20 | Composite probability [0,1]; no labelled confidence interval |

---

## 18. Human / Agency Authorization Layer

This layer is MANDATORY for any public emergency alert. The architecture enforces:

```
ML Prediction Output
        ↓
Data Quality Gate (M9 validation)
        ↓
Uncertainty Quantification
        ↓
Physics / Rule Override (M17 deterministic)
        ↓
Impact Assessment (M13/M14)
        ↓
Decision Support Recommendation
        ↓
AUTHORIZED HUMAN / AGENCY REVIEW
        ↓
DDMA / NDRF / SDRF Incident Commander
        ↓
CAP v1.2 Public Alert
```

**ML MUST NOT independently issue governmental emergency evacuation orders.**  
**Deterministic CWC threshold exceedances generate internal alerts; human authorization is required for public broadcast.**

---

## 19. Audit Logging

| Component | Location | Contents |
|-----------|----------|---------|
| Model registry | `reports/model_registry.json` | All model IDs, artifacts, SHA-256, metrics, limitations |
| Provenance log | `ml/data_quality/provenance.py` | Dataset source, type, license |
| Benchmark audit | `reports/DATASET_BENCHMARK_AUDIT.md` | Per-model data sufficiency |
| Validation summaries | `reports/validation_audit/` | Machine-readable audit JSONs |
| Test suite | `tests/` (393 tests) | Automated regression |
| External validation | `ml/validation/external/` | Evaluate scripts (M2/M4/M6/M7) |

---

## 20. Model Registry

Located at: `reports/model_registry.json`

All models must have:
- `model_id`, `version`, `artifact_path`, `sha256`
- `training_dataset_id`, `training_period`
- `validation_period`, `metrics`
- `limitations` (non-empty array)
- `status` (FROZEN / DEVELOPMENT / PROTOTYPE)
- `registered_at` (ISO 8601)

**Evidence status** (the scientific validation tier) is maintained separately in model cards (`docs/MODEL_CARD_*.md`) and the validation summary (`reports/remaining_models/FINAL_MODEL_VALIDATION_SUMMARY.md`).

---

## System-Level Scientific Readiness Assessment

| Tier | Definition | FLOODY SHIELD Status |
|------|-----------|---------------------|
| **Level 1 — Prototype** | Real physics + simulated training + small real validation datasets | ✅ **CURRENT LEVEL** |
| **Level 2 — Research-grade** | 100+ real events, 5–10 yr records, independent scene datasets | ❌ Requires CWC/IMD/GSI data agreements |
| **Level 3 — Operational** | Live sensors, real-time monitoring, independent large-scale validation, government authorization | ❌ Requires deployment infrastructure |

**What the system CAN claim:**
- A complete, architecturally sound 20-model pipeline for Upper Beas
- Physics-based foundations grounded in published hydrology/geotechnical science
- Honest, Clopper-Pearson CIs on all external evaluation metrics
- M12 meets the 100-event empirical benchmark (global dam-breach database)
- Safety architecture enforces human authorization before public alerts

**What the system CANNOT claim:**
- External validation for any ML model at research-grade level
- Precise probability estimates from models trained on simulation
- That synthetic training data performance will generalize to real-world observations
- Operational readiness without real data, government integration, and field testing

---

*FLOODY SHIELD v3.0 | SIH-26192 | Architecture Document v2.0 | 2026-09-21*
