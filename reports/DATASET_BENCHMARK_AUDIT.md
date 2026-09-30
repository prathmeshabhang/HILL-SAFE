# FLOODY SHIELD — Dataset Benchmark Audit Report

**Purpose**: Audit every model against the minimum and preferred training-data benchmarks.
**Rule**: Document the honest gap between what exists and what is needed.
**Scope**: No system architecture or code changes — documentation and validation-status corrections only.

**Date**: 2026-09-21 | Version: 1.0

---

> [!CAUTION]
> This document intentionally exposes dataset shortfalls. It is not a sign of project failure — it is the scientifically honest characterisation of a prototype-stage system. Level 1 (Prototype) systems are not expected to meet Level 2 (Research-grade) benchmarks.

---

## Benchmark Legend

| Symbol | Meaning |
|--------|---------|
| ✅ MEETS | Current data meets or exceeds the stated minimum |
| ⚠️ PARTIAL | Partially meets minimum; important caveats apply |
| ❌ BELOW | Clearly below the stated minimum |
| 🔵 N/A | Benchmark concept does not apply (physics/rule-based) |

---

## Per-Model Audit

---

### M1 — Extreme Rainfall Nowcasting

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Training data type | Real IMD/GPM/AWS hourly | 5–10 years real | **Simulated multi-year AWS series calibrated to IMD profiles** | ⚠️ PARTIAL |
| Duration | 2–3 years hourly | 5–10 years | Simulated 2018–2023 (5 year range), n=600 evaluation time-steps | ⚠️ PARTIAL |
| Sources | IMD, GPM IMERG, AWS | Multiple | Simulated from IMD/GPM distributions (not raw records) | ❌ BELOW |
| External validation | Independent storms | Historical record | Chronological 20% holdout of same simulated series | ❌ BELOW |

**Current validation status in card**: `INTERNAL_VALIDATED`
**Honest gap**: Training data is simulated/synthetic calibrated to real distributions, not raw IMD/GPM records. No independently-sourced storm events for external validation.
**Corrected status**: `PROTOTYPE_SIMULATED_DATA` — meets prototype benchmark, below research-grade.
**Required for upgrade**: 2+ years of real IMD AWS sub-hourly records + GPM IMERG grid for Upper Beas.

---

### M2 — Flood Risk Classification

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Training events | 100+ flood events | 300–1,000 events | 10,000 spatial points from **calibrated hydro-physical simulation** | ⚠️ PARTIAL |
| Data nature | Real flood events | Real events | Simulated HEC-RAS/HAND outputs (not event-by-event observations) | ❌ BELOW |
| External validation N | 100+ independent | 300+ | **N=6 strictly independent points** (4 flood, 2 control) | ❌ BELOW |
| Sources | CWC, HPSDMA, NRSC, Sentinel | Multiple | July 2023 ground survey (N=24 total, 6 strictly independent) | ❌ BELOW |

**Current validation status in card**: `PARTIALLY_EXTERNAL_VALIDATED`
**Honest gap**: N=6 independent test points is far below 100+ event minimum. Wide Clopper-Pearson CIs (Recall 95% CI: 39.76%–100%). Training data is simulated.
**Corrected status**: `PRELIMINARY_EXTERNAL_EVIDENCE` — valid as prototype evidence, not as statistically rigorous external validation.
**Required for upgrade**: 100+ real independently-sourced flood events from CWC + HPSDMA + Sentinel-1 flood maps.

---

### M4 — Flood Inundation Segmentation

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Training scenes | 500+ labelled scenes | 2,000–10,000 scenes | **1 disaster period** (July 2023 single event); internal proxy masks only | ❌ BELOW |
| Ground truth masks | Pixel-level field maps | Full-scene raster GT | **SAR-HAND proxy** — not authoritative field maps | ❌ BELOW |
| External validation | Scene-level F1/IoU | Full-scene raster | **N=24 ground survey points** (point-level only, not scene-level) | ❌ BELOW |
| Sources | Sentinel-1/2, NRSC | Multiple | Single Sentinel-1/2 pass July 2023 | ❌ BELOW |

**Current validation status in card**: `PARTIALLY_EXTERNAL_VALIDATED`
**Honest gap**: Internal Dice=0.973 is against **proxy masks, not field ground truth** (card itself warns this). Point-level recall is 50% with wide CIs. 2D raster ground truth unavailable.
**Corrected status**: `PROXY_VALIDATED_PROTOTYPE` — internal convergence verified; no scene-level external validation.
**Required for upgrade**: 500+ Sentinel-1/2 flood scenes with authoritative pixel-level masks (Copernicus EMS, NRSC).

---

### M6 — Landslide Susceptibility

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Training failures | 500–1,000 verified | 2,000–10,000 points | **10,000 simulated** (calibrated synthetic; not verified field failures) | ❌ BELOW |
| Quality of controls | Verified stable areas | Independent checks | Synthetic controls from DEM/GSI maps | ❌ BELOW |
| External test failures | 100+ independent | 500+ | **N=6 strictly independent** (6 scarps, 2 controls, 500m exclusion) | ❌ BELOW |
| Sources | GSI, GLOF inventories, HPSDMA | Multiple | 20 documented scarps from July/Aug 2023 (used as external test only) | ⚠️ PARTIAL |

**Current validation status in card**: `INSUFFICIENT_EXTERNAL_EVIDENCE`
**Honest gap**: External recall = 16.67% (1/6), ROC-AUC=0.333 on independent subset. Card correctly declares INSUFFICIENT. Training data is synthetic.
**Corrected status**: `INSUFFICIENT_EXTERNAL_EVIDENCE` — **status already correct** in card. Confirmed.
**Required for upgrade**: 500+ GSI/HPSDMA verified failures + comparable stable controls with GPS coordinates.

---

### M7 — Landslide Trigger

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Training storms | 100+ independent storms | 300+ storms | **10,000 samples** from **simulated storm catalog** (not real storm records) | ❌ BELOW |
| Independent storm events | 100+ | 300+ | **N=7 storm episodes** (5 trigger + 2 control) | ❌ BELOW |
| Data nature | Real storm-landslide pairs | Multiple years | Synthesised from IMD/ERA5-Land/HPSDMA distributions | ❌ BELOW |
| External validation | Event-level holdout | 300+ events | 7 storms; 22 spatial points within one storm | ❌ BELOW |

**Current validation status in card**: `PARTIALLY_EXTERNAL_VALIDATED`
**Honest gap**: N=7 events is far below 100-event minimum. Event specificity = 0% (false alarms on moderate storms). Spatial ROC-AUC=0.198 within storm. Training is synthetic.
**Corrected status**: `PRELIMINARY_EXTERNAL_EVIDENCE` — 7 storms provide directional evidence only; not statistically sufficient for external validation claim.
**Required for upgrade**: 100+ real independently-sourced storm–landslide trigger pairs from IMD/GPM + HPSDMA.

---

### M8 — Ground Movement / Deformation

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Monitored sites | 50+ sites | 200+ sites | **4,000 synthetic profiles** (calibrated to InSAR/tiltmeter statistics) | ❌ BELOW |
| Real InSAR sites | 50+ | 200+ | **0 real Sentinel-1 InSAR sites** — all synthetic-calibrated | ❌ BELOW |
| Time series depth | Multi-year per site | Long series | Simulated creep sequences (not real multi-year InSAR stacks) | ❌ BELOW |
| Sources | Sentinel-1 InSAR, GNSS | Extensometers | Calibrated simulation grounded in InSAR velocity statistics | ⚠️ PARTIAL |

**Current validation status in card**: `INTERNAL_VALIDATED`
**Honest gap**: No real monitored sites. 4,000 training samples = 4,000 synthetic slope profiles, not independent sites. Benchmark requires 50+ real monitored sites.
**Corrected status**: `PROTOTYPE_SIMULATED_DATA` — physics calibration credible but no real site validation.
**Required for upgrade**: Sentinel-1 InSAR time-series for 50+ Upper Beas slope points; GNSS/extensometer data.

---

### M9 — IoT Sensor Anomaly Detection

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Normal readings | 10,000+ nominal | 100,000+ | **5,000 simulated nominal records** | ❌ BELOW |
| Anomaly labels | Labelled real faults | Controlled tests | **6 injected fault archetypes** (synthetic) | ⚠️ PARTIAL |
| Sensor channels | Multiple sensor types | Multi-station | 5 channels simulated | ⚠️ PARTIAL |
| Real sensor data | Operational sensor logs | Long-term | **None — all simulated** | ❌ BELOW |

**Current validation status in card**: `INTERNAL_VALIDATED`
**Honest gap**: 5,000 samples is below the 10,000 minimum. All data synthetic. 11-case validation suite is a controlled benchmark, not real-world sensor deployment.
**Corrected status**: `PROTOTYPE_SIMULATED_DATA` — deterministic Stage 1 rules are robust; Isolation Forest layer is prototype-only.
**Required for upgrade**: 10,000+ real IoT readings from deployed sensors in Upper Beas (AWS, river gauges, tiltmeters).

---

### PWP / SSI — Pore Water Pressure / Slope Stability

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Implementation type | Physics (not ML) | Site-specific field measurements | **Analytical physics** (Bishop + Richards equations) | ✅ MEETS |
| Soil parameters | Site-specific geotechnical | Many field samples | Regional published values (GSI, MoEF studies) — not site-specific | ⚠️ PARTIAL |
| Validation | Safety factor compliance | Field monitoring | SF > 1.0 compliance tests (physics-consistent) | ✅ MEETS |

**Current validation status**: `PHYSICS_VALIDATED`
**Honest gap**: Soil cohesion, friction angle, hydraulic conductivity are from regional literature, not site-specific Upper Beas borehole samples.
**Corrected status**: `PHYSICS_VALIDATED_REGIONAL_PARAMETERS` — model physics correct; soil parameters require site-specific calibration for full engineering validity.

---

### M10 — River Water-Level Forecast

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Training data | 2–5 years continuous gauge | 10+ years | **Simulated** from Beas seasonal hydrograph patterns (n=3,600 train) | ❌ BELOW |
| Real gauge data | CWC/HP gauges | 10+ years | **None — simulated** | ❌ BELOW |
| Validation | Continuous holdout | Multi-year | 20% holdout of same simulated series (n=1,000) | ❌ BELOW |
| Sources | CWC, state departments | Multiple | Simulated multi-year hydrographs | ❌ BELOW |

**Current validation status in card**: `INTERNAL_VALIDATED`
**Honest gap**: All training data is simulated from seasonal patterns. No real CWC continuous gauge records used. R²=0.978 is on simulated holdout.
**Corrected status**: `PROTOTYPE_SIMULATED_DATA` — hydraulic physics well-grounded; real gauge records required for credible operational validation.
**Required for upgrade**: 2+ years of CWC/HP continuous stage readings at Manali, Kullu, Bhuntar, Pandoh gauges.

---

### M11 — Flood Propagation / Depth

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Flood events | 50+ independent events | 100–300 | **Simulated multi-reach HEC-RAS calibrations** (n=3,200 train, 1,000 val) | ❌ BELOW |
| Ground truth | Observed flood extents | Scene-level | 1 disaster scenario cross-check (July 2023 single event) | ❌ BELOW |
| Real observations | Gauge + satellite extent | Multiple | DEM-HAND proxy, no satellite flood extent scenes | ❌ BELOW |

**Current validation status in card**: `INTERNAL_VALIDATED`
**Honest gap**: No real flood extent observations. R²=0.999 is on simulated HEC-RAS emulation. 50-event minimum not met.
**Corrected status**: `PROTOTYPE_SIMULATED_DATA` — HEC-RAS grounding gives physical credibility; external scene validation needed.
**Required for upgrade**: 50+ real Beas flood events with gauge + Sentinel-1 flood extent rasters.

---

### M12 — Hazard Cascade / Dam Breach

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Multi-hazard events | 100+ | 300+ | **111 global historical dam-breach case studies** (Froehlich/Costa database) | ✅ MEETS |
| Calibration basis | Published equations | Many events | Froehlich (2008) + Costa (1985) — globally calibrated on 111 events | ✅ MEETS |
| Himalayan benchmarks | Regional events | | 3 events: Sun Kosi 2014, Pareechu 2000/2005, Chamoli 2021 | ✅ MEETS |
| Sources | HPSDMA, CWC, GSI | Multiple | Global landslide dam database + Himalayan post-event surveys | ✅ MEETS |

**Current validation status in card**: `INTERNAL_VALIDATED`
**Honest gap**: 111 global cases meet the 100+ minimum. Himalayan benchmarks match observed ranges.
**Corrected status**: `EMPIRICALLY_BENCHMARKED_MEETS_MINIMUM` — **status upgrade from INTERNAL_VALIDATED**.
**Note**: Peak-Q RMSE 24.5% is consistent with published Froehlich benchmark scatter.

---

### M13 — Population Vulnerability

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Population data | Census + seasonal | Multiple years | **Census 2011** Kullu District VTD | ✅ MEETS |
| Seasonal population | Tourism estimates | Observed tourism data | HP Tourism Development Corp statistics + **ASSUMED multipliers** | ⚠️ PARTIAL |
| Settlement coverage | All at-risk settlements | Complete register | 12 core Beas corridor settlements | ⚠️ PARTIAL |
| Training scenarios | Scenario-based | Multiple years | 12 settlements × 12 months × 25 scenarios = 3,600 synthetic samples | ⚠️ PARTIAL |

**Current validation status in card**: Not stated explicitly
**Honest gap**: Tourist multipliers (e.g. 1.8×) are from HP Tourism statistics — provenance is real but occupancy-to-population conversion is ASSUMED/MODELLED, not directly observed. Training scenarios are synthetic.
**Corrected status**: `CENSUS_GROUNDED_MODELLED_SCENARIOS` — demographic basis is real; scenario training is modelled.
**Required for upgrade**: Annual tourist flow counts at Manali/Kullu with seasonal breakdown + direct population survey.

---

### M14 — Infrastructure Damage & Loss

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Asset-event records | 100+ labelled | 500–2,000 | **14 assets × 120 scenarios = 1,680 synthetic records** | ❌ BELOW |
| Damage labels | Observed real damage | 500+ asset observations | **NDMA/USACE fragility curves** (no real event-asset damage records) | ❌ BELOW |
| Real damage data | HP PWD, HPSEB records | Government reports | Asset register is real; damage ratio is curve-derived, not field-measured | ⚠️ PARTIAL |

**Current validation status in card**: Not stated explicitly; implied INTERNAL_VALIDATED
**Honest gap**: 1,680 training records are synthetic scenarios, not real event-asset damage observations. Fragility curves (NDMA/USACE) are real but not calibrated to Upper Beas assets specifically. 100-record minimum not met with real observations.
**Corrected status**: `PROTOTYPE_CURVE_BASED` — real asset register; damage functions are literature-based; no observed damage labels.
**Required for upgrade**: 100+ real post-event damage observations from HP PWD/HPSEB damage registers post July 2023.

---

### M15 — Safe Zone Selection

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Implementation type | GIS optimization, not ML | Scenario-based | **Rule-based constraint optimization** (GIS + hazard maps) | ✅ MEETS |
| GIS data | DEM, settlements, roads, hospitals | Complete | Beas corridor DEM + OSM + HPSDMA shelter register | ✅ MEETS |
| Validation | Constraint compliance | Scenario tests | Life-safety constraint enforcement tested | ✅ MEETS |

**Corrected status**: `RULE_VALIDATED` — **status already correct**. Rule-based; benchmark concept does not require ML training data.

---

### M16 — Evacuation Routing

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Implementation type | GIS graph routing | 100+ scenarios | **NetworkX A\*/Dijkstra** on real OSM road graph | ✅ MEETS |
| Road network | Complete road graph | Multiple hazard scenarios | OSM + HP PWD road network, Upper Beas corridor | ✅ MEETS |
| Hazard-aware routing | Dynamic edge weights | Real incident history | Dynamic weight updates from M11/M12 hazard maps | ✅ MEETS |

**Corrected status**: `RULE_VALIDATED` — **status already correct**. Not an ML model; benchmark applies to routing completeness, not training data.

---

### M17 — Warning Gating

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Historical events | 100+ threshold events | Several hundred | **1,600 synthetic scenarios** (400 per alert class) | ❌ BELOW |
| Real events | Real CWC/IMD records | 100+ | **Zero real historical events** — all synthetic scenarios | ❌ BELOW |
| Deterministic thresholds | CWC/NDMA statutory | Published SOPs | Directly from CWC and NDMA SOPs | ✅ MEETS |
| ML accuracy claim | 100% on real events | Independent history | **100% on synthetic benchmark** — not on real event history | ❌ BELOW |

**Current validation status in card**: 100% accuracy, macro-F1 = 1.000
**Honest gap**: 100% accuracy is on **synthetic scenarios designed from the same rules** — circular validation. No real independent historical events from CWC/IMD used. Deterministic safety overrides are valid regardless.
**Corrected status**: `DETERMINISTIC_OVERRIDES_VALIDATED; ML_LAYER_PROTOTYPE_ONLY` — safety rules are grounded in statutory thresholds; ML fusion layer has not been validated on real events.
**Required for upgrade**: 100+ real historical CWC danger-level events with corresponding on-ground emergency responses.

---

### M18 — Risk Calibration

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Calibration pairs | 100+ independent predictions + outcomes | 500+ | **SYNTHETIC dataset** (1,000 beta-distributed pairs) | ❌ BELOW |
| Real event outcomes | Required | 500+ | **None — all synthetic** | ❌ BELOW |
| Independence from training | Calibration set ≠ training | Separate external | Separate synthetic sets (no real data to split) | ⚠️ PARTIAL |

**Current validation status**: `INTERNAL_VALIDATED`
**Honest gap**: 0 real prediction-outcome pairs. Benchmark requires 100+ real independent outcomes. Brier improvement is on synthetic data only.
**Corrected status**: `PROTOTYPE_SYNTHETIC_PIPELINE_ONLY` — calibration infrastructure verified; no real outcomes to calibrate against.
**Required for upgrade**: Accumulate M2/M6/M7 predictions against real post-event outcomes (100+ events minimum).

---

### M19 — Time-to-Impact

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Timestamped events | 50+ | 200+ | **3 published Himalayan benchmark events** | ❌ BELOW |
| Upper Beas events | Required | 200+ | **0 Upper Beas–specific timestamped events** | ❌ BELOW |
| ML quantile regression | Requires real timestamps | 200+ events | Declared INSUFFICIENT_EVIDENCE | ✅ MEETS (honest declaration) |
| Physics benchmark | Regional calibration | Multiple | 3/3 Himalayan events within P10–P90 | ⚠️ PARTIAL |

**Current validation status**: `PHYSICS_BASELINE_VALIDATED`
**Honest gap**: 3 benchmark events is far below 50-event minimum. All from published literature (Pareechu, Sun Kosi, Chamoli) — none from Upper Beas.
**Corrected status**: `PHYSICS_PROOF_OF_CONCEPT; ML_INSUFFICIENT_EVIDENCE` — physics principles verified on 3 analogous events; not sufficient for validated operational prediction.
**Required for upgrade**: 50+ real timestamped hazard-arrival observations from Upper Beas (CWC gauge records + ground truth timing).

---

### M20 — Post-Event Damage Assessment

| Field | Benchmark Minimum | Preferred | Current | Status |
|-------|------------------|-----------|---------|--------|
| Labelled damage samples | 500+ | 2,000–10,000 | **0 labelled samples** — change detection baseline only | ❌ BELOW |
| Pre/post image pairs | 500+ labelled | 2,000–5,000 | No labelled image pairs (NDVI/NDWI indicators, no ground truth) | ❌ BELOW |
| Field survey labels | Required for classification | Government reports | Declared EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE | ✅ MEETS (honest declaration) |
| Sources | Sentinel, NRSC, gov reports | Multiple | None authoritative available | ❌ BELOW |

**Current validation status**: `CHANGE_DETECTION_ONLY`
**Honest gap**: 0 labelled damage samples vs 500 minimum. Card and code correctly declare EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE.
**Corrected status**: `CHANGE_DETECTION_ONLY` — **status already correct**. Confirmed.
**Required for upgrade**: 500+ labelled pre/post satellite scenes with field-verified damage grades from NRSC/HPSDMA.

---

## Summary Table: Benchmark vs. Current State

| Model | Benchmark Min | Current Training Scale | Benchmark Met? | Corrected Status |
|-------|--------------|----------------------|----------------|-----------------|
| M1 | 2–3 yr real hourly | Simulated 5-yr AWS | ⚠️ Simulated only | `PROTOTYPE_SIMULATED_DATA` |
| M2 | 100+ real flood events | 10k simulated points; N=6 ext. valid | ❌ Below | `PRELIMINARY_EXTERNAL_EVIDENCE` |
| M4 | 500+ labelled scenes | 1 event, proxy masks | ❌ Below | `PROXY_VALIDATED_PROTOTYPE` |
| M6 | 500+ failures + controls | 10k simulated; N=6 ext. valid | ❌ Below | `INSUFFICIENT_EXTERNAL_EVIDENCE` ✓already |
| M7 | 100+ real storms | 10k simulated; N=7 storms | ❌ Below | `PRELIMINARY_EXTERNAL_EVIDENCE` |
| M8 | 50+ real monitored sites | 4k simulated profiles | ❌ Below | `PROTOTYPE_SIMULATED_DATA` |
| M9 | 10k+ real + labelled anomalies | 5k simulated + 6 injected | ❌ Below | `PROTOTYPE_SIMULATED_DATA` |
| PWP/SSI | Physics + site params | Physics + regional params | ⚠️ Regional params | `PHYSICS_VALIDATED_REGIONAL_PARAMETERS` |
| M10 | 2–5 yr real gauge | Simulated hydrographs | ❌ Below | `PROTOTYPE_SIMULATED_DATA` |
| M11 | 50+ real flood events | Simulated HEC-RAS | ❌ Below | `PROTOTYPE_SIMULATED_DATA` |
| M12 | 100+ multi-hazard events | 111 global cases ✅ | ✅ MEETS | `EMPIRICALLY_BENCHMARKED_MEETS_MINIMUM` |
| M13 | Census + seasonal pop | Census 2011 + HP tourism | ✅ Data basis meets | `CENSUS_GROUNDED_MODELLED_SCENARIOS` |
| M14 | 100+ asset-event records | 1,680 synthetic scenarios | ❌ Below | `PROTOTYPE_CURVE_BASED` |
| M15 | GIS + hazard maps | Real GIS + OSM | ✅ MEETS | `RULE_VALIDATED` ✓already |
| M16 | GIS network + scenarios | Real OSM road graph | ✅ MEETS | `RULE_VALIDATED` ✓already |
| M17 | 100+ real events | 1,600 synthetic scenarios | ❌ Below | `DETERMINISTIC_OVERRIDES_VALIDATED; ML_PROTOTYPE_ONLY` |
| M18 | 100+ real pred-outcome pairs | 1k synthetic pairs | ❌ Below | `PROTOTYPE_SYNTHETIC_PIPELINE_ONLY` |
| M19 | 50+ timestamped events | 3 published events | ❌ Below | `PHYSICS_PROOF_OF_CONCEPT; ML_INSUFFICIENT_EVIDENCE` |
| M20 | 500+ labelled damage samples | 0 labelled | ❌ Below | `CHANGE_DETECTION_ONLY` ✓already |

---

## Models That Already Meet Their Benchmark

| Model | Why |
|-------|-----|
| **M12** | 111 global empirical dam-breach cases exceeds the 100-event minimum; Froehlich/Costa are the industry-standard formulations |
| **M15** | Rule-based GIS optimization; benchmark is on completeness/correctness, not training data volume |
| **M16** | NetworkX routing on real OSM network; benchmark applies to routing correctness |
| **M13** | Census 2011 demographic basis is real; tourist multipliers from HP Tourism statistics |

---

## Models With Status Already Correctly Set

| Model | Declared Status | Audit Verdict |
|-------|----------------|--------------|
| M6 | `INSUFFICIENT_EXTERNAL_EVIDENCE` | ✅ Confirmed correct |
| M15 | `RULE_VALIDATED` | ✅ Confirmed correct |
| M16 | `RULE_VALIDATED` | ✅ Confirmed correct |
| M20 | `CHANGE_DETECTION_ONLY` | ✅ Confirmed correct |
| M19 | `ML_INSUFFICIENT_EVIDENCE` declared | ✅ Confirmed correct |

---

## Data Collection Priority (For Future Upgrades)

| Priority | Gap | Target | Source |
|----------|-----|--------|--------|
| 🔴 1 | Real CWC gauge records (M10) | 2+ years hourly | CWC/HP Water Resources |
| 🔴 2 | Real IMD/GPM rainfall records (M1) | 2+ years sub-hourly | IMD AWS, GPM IMERG |
| 🔴 3 | Independently sourced flood events (M2/M11) | 50–100 events | CWC, HPSDMA, Sentinel-1 |
| 🔴 4 | GSI/HPSDMA landslide failure inventory (M6/M7) | 500+ scarps | GSI field survey, HPSDMA reports |
| 🟠 5 | Sentinel-1 InSAR deformation stacks (M8) | 50+ slopes, multi-year | ESA Sentinel-1, ISRO Cartosat |
| 🟠 6 | Real Sentinel-1/2 flood scene pairs (M4/M11) | 50–100 scenes | Copernicus EMS, NRSC DMSP |
| 🟠 7 | HP PWD post-event damage records (M14/M20) | 100+ asset records | HP PWD, HPSDMA |
| 🟡 8 | Real IoT sensor telemetry (M9) | 10,000+ readings | Deployed AWS/tiltmeter logs |
| 🟡 9 | Timestamped hazard arrival data (M19) | 50+ events | CWC, district records |
| 🟡 10 | Real prediction-outcome pairs (M18) | 100+ pairs | Operational model outputs |

---

## What This Does Not Mean

This audit does NOT mean the project is invalid or should be discarded. The Floody Shield prototype:

- Has a **complete, architecturally sound 20-model pipeline**
- Is built on **physically grounded simulation** (not random data)
- Has **correct physics** in M12, PWP, M15, M16, M19
- Has **real ground data** underpinning M2/M4/M6/M7/M13 (even if sample sizes are small)
- Has **honest uncertainty declarations** throughout

This is an honest **Level 1 (Prototype)** system. Meeting Level 2 (Research-grade) benchmarks requires real data agreements with CWC, IMD, GSI, HPSDMA, and NRSC — a multi-year institutional effort.

---

*FLOODY SHIELD v3.0 | SIH-26192 | Dataset Benchmark Audit | 2026-09-21*
