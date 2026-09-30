# FLOODY SHIELD — Final Data Gaps Report

**Project**: FLOODY SHIELD — Predict • Protect • Preserve  
**AOI**: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh  
**Date**: 2026-09-21  
**Purpose**: Document the specific real-world data required to upgrade each model from prototype to research-grade validation.

---

> [!IMPORTANT]
> This document describes data that does NOT yet exist in the project. All items listed are genuine gaps — not deficiencies in methodology, but missing real observational data needed to progress from Level 1 (Prototype) to Level 2 (Research-grade).

---

## Priority Classification

| Level | Meaning |
|-------|---------|
| 🔴 HIGH | Critical for safety-relevant validation; most impactful upgrade |
| 🟠 MEDIUM | Important for model reliability; upgrade within 12–18 months |
| 🟡 LOWER | Useful but less urgent; upgrade within 24+ months |

---

## 🔴 HIGH PRIORITY GAPS

---

### GAP-01: M6 — Independent Stable Control Dataset

```
Model:                    M6 — Landslide Susceptibility
Current evidence:         N=6 strictly independent external points (8 total after 500m exclusion)
                          20 GSI failure scarps + 12 provisional controls
                          Only 2 controls are strictly spatially independent

Gap:
  Control quality problem: Buildings, temples, and castle sites were used as
  stable-slope controls. These demonstrate that specific point locations were
  not flooded/landslid during the 2023 event, but they do NOT demonstrate
  overall slope stability across the full susceptibility zone.
  
  A heritage temple on a rock spur proves that rock spur was stable — it does
  NOT prove that the adjacent cut-slope 200m away is stable.

Missing data:
  500+ verified stable slope points with:
    - GPS coordinates at or near actual slope faces (not structures)
    - Documented slope gradient, geology, aspect
    - Observation period specified (e.g. 2018–2023 monsoon seasons)
    - Confirmed absence of failure or creep by field inspection or InSAR

Minimum useful dataset:   500 failures + 500 matched controls
Preferred dataset:        2,000+ failures + 2,000+ controls
Potential source:         GSI Landslide Atlas, HPSDMA disaster reports,
                          Sentinel-1 InSAR coherence for stable slopes
Label requirement:        Field-confirmed stability, NOT proxy (building = stable)
Independence:             >500m from any training point; temporally separate
Priority:                 🔴 HIGH — controls directly affect specificity claims
```

---

### GAP-02: M7 — Independent Storm Events

```
Model:                    M7 — Landslide Trigger
Current evidence:         N=7 storm episodes (5 trigger + 2 non-trigger)
                          N=22 spatial points within ONE storm (July 2023)

Gap:
  22 spatial points from a single storm are NOT 22 independent events.
  Under a single storm, all measurement points share the same atmospheric
  forcing. The 22 points measure within-storm spatial variation, not
  storm-level independence.
  
  Event-level ROC-AUC from 7 storms requires at least 15–20 storms for
  reliable estimation (Hanley & McNeil 1982). N=7 provides a directional
  signal only.

Missing data:
  100+ historically documented storm episodes with:
    - Independently sourced IMD AWS/GPM rainfall records
    - Documented triggered/non-triggered outcome per storm
    - At least 30-minute temporal resolution
    - 3-day antecedent rainfall records
    - Georeferenced landslide activation or confirmed absence

Minimum useful dataset:   100 independent storm episodes
Preferred dataset:        300+ storm episodes over 10+ years
Potential source:         IMD Hydrometeorological Division, ERA5-Land,
                          HPSDMA post-monsoon disaster reports (2005–2023)
Label requirement:        Documented storm trigger/non-trigger per episode
Temporal independence:    Each storm episode separated by ≥ 7 days
Priority:                 🔴 HIGH — directly affects false-alarm characterization
```

---

### GAP-03: M10 — Real CWC Continuous River Gauge Data

```
Model:                    M10 — River Water-Level Forecast
Current evidence:         ALL training data is simulated seasonal hydrographs.
                          Zero real CWC continuous gauge telemetry used.

Gap:
  R²=0.978 at 6h horizon is against simulated holdout data — not real river
  behavior. Real Beas stage records include dam release effects (Larji,
  Pandoh, Manali barrage), tributary confluences, flash-flood nonlinearities,
  and glacier melt that simulated hydrographs cannot capture.

Missing data:
  2–5 years of continuous river stage records at:
    - Manali (upper Beas headwater gauge)
    - Patli Kuhal (mid-basin)
    - Kullu (main commercial zone)
    - Bhuntar (confluence zone)
    - Thalout / Pandoh (lower basin)
  15-minute or sub-hourly resolution preferred.
  Must include pre-event baseflows, storm events, and recession limbs.

Minimum useful dataset:   2 years continuous (2 monsoon seasons)
Preferred dataset:        10+ years with dam release metadata
Potential source:         CWC India Water Resources Information System (WRIS),
                          HP Water Resources Dept (Jal Shakti Vibhag)
Label requirement:        Raw stage records; dam gate state if available
Priority:                 🔴 HIGH — foundational for all downstream flood models
```

---

### GAP-04: M11 — Observed Flood Extents

```
Model:                    M11 — Flood Propagation / Depth
Current evidence:         Simulated HEC-RAS/HAND profiles. Single July 2023
                          disaster scenario cross-check.

Gap:
  HEC-RAS emulation R²=0.999 is against HEC-RAS itself — the model learns
  to replicate a hydraulic model, not real river behavior. No satellite
  flood extent validation exists.

Missing data:
  50+ pre-event / post-event SAR or optical image pairs with:
    - Clear flood inundation boundary delineation
    - Corresponding upstream gauge records for hydraulic forcing
    - At least 10 distinct flood events (recurrence-independent)
    - Depth markers from field surveys or high-water marks
    - Temporal coverage: within 72h of peak flood stage

Minimum useful dataset:   50 flood events with gauge + satellite extent
Preferred dataset:        100–300 events spanning multiple seasons/years
Potential source:         Copernicus Emergency Management Service (EMS),
                          NRSC Disaster Management Support Programme,
                          Sentinel-1 SAR flood archives (ESA Open Access)
Label requirement:        Authoritative inundation polygons, NOT proxy
Independence:             Events separated by ≥ 30 days
Priority:                 🔴 HIGH — M11 outputs propagate to M12/M13/M17
```

---

### GAP-05: M19 — Timestamped Hazard Arrival Events

```
Model:                    M19 — Time-to-Impact Prediction
Current evidence:         3 published Himalayan analogue events
                          0 Upper Beas-specific timestamped events

Gap:
  Time-to-impact requires actual timestamps: when did hazard initiate,
  when did it reach the reference location, what was the measured arrival
  time? Published literature gives ranges; real records give actual times.

Missing data:
  50+ documented hazard arrival events with:
    - Confirmed initiation time (e.g., CCTV, satellite, gauge trigger)
    - Confirmed impact time at reference point (gauge exceedance, road breach)
    - Distance from source to impact point
    - Hazard type (flash flood, debris flow, landslide dam breach)
    - Hydrometeorology at time of event

Minimum useful dataset:   50 timestamped events
Preferred dataset:        200+ events across multiple Himalayan basins
Potential source:         CWC flood forecasting logs, district control room
                          records, HPSDMA incident reports, NDRF response logs
Label requirement:        Actual timestamps (not estimates); <30 min precision
Priority:                 🔴 HIGH — timing errors have direct life-safety impact
```

---

## 🟠 MEDIUM PRIORITY GAPS

---

### GAP-06: M4 — Authoritative Flood Extent Rasters

```
Model:                    M4 — Flood Inundation Segmentation
Current evidence:         Internal proxy Dice=0.973 (SAR-HAND masks ≠ field GT)
                          N=24 ground survey points (point concordance only)

Gap:
  Scene-level segmentation accuracy CANNOT be computed without pixel-level
  authoritative ground truth. N=24 points sample <0.1% of the 10m flood
  extent raster area.

Missing data:
  500+ Sentinel-1/2 flood scene pairs with authoritative masks:
    - Copernicus EMS activation maps (GeoTIFF at ≥30m)
    - NRSC flood inundation assessment products
    - Validated field survey GPS transects covering flood boundary
    - At least 50 distinct flood events across Upper Beas

Minimum useful dataset:   50 scenes with authoritative masks (min)
Preferred dataset:        500–2,000 scenes for deep learning training
Potential source:         Copernicus EMS archive, NRSC DMSP historical products,
                          UNOSAT flood archives
Priority:                 🟠 MEDIUM — prerequisite for IOU/Dice external claims
```

---

### GAP-07: M14 — Observed Infrastructure Damage Records

```
Model:                    M14 — Infrastructure Damage & Loss
Current evidence:         Real asset register; NDMA/USACE fragility curves
                          1,680 synthetic scenarios (NO observed damage records)

Gap:
  Fragility curves derived from literature are NOT calibrated to Upper Beas
  assets. Himalayan mountain road pavement, suspension footbridges, and
  apple orchard drainage characteristics differ from USACE Central US data.

Missing data:
  100+ real post-event damage records:
    - Asset type, damage state, flood depth/velocity at time of damage
    - Economic loss estimate from official sources
    - Road closure duration
    - Post-event survey photographs with GPS tags

Minimum useful dataset:   100 asset-event damage records
Preferred dataset:        500+ records across multiple events
Potential source:         HP PWD post-monsoon road damage reports,
                          HPSEB power outage logs, HPSDMA PDNA 2023,
                          Insurance loss records (PM Fasal Bima Yojana)
Priority:                 🟠 MEDIUM — currently curves not calibrated to region
```

---

### GAP-08: M20 — Post-Event Damage Labels

```
Model:                    M20 — Post-Event Damage Assessment
Current evidence:         0 labelled damage samples
                          Output: CHANGE_DETECTED only (not classified damage)

Gap:
  Without supervised labels, the model cannot distinguish:
    - Debris deposition vs building collapse
    - Vegetation flattening vs road scour
    - Temporary inundation vs permanent damage

Missing data:
  500+ labelled pre/post image pairs:
    - Pre-event Sentinel-1/2 baseline
    - Post-event Sentinel-1/2 within 7 days of peak flood
    - Field-verified damage classification per pixel or polygon
    - Damage grade: 0=intact, 1=partial, 2=moderate, 3=severe, 4=destroyed

Minimum useful dataset:   500 labelled samples across ≥10 events
Preferred dataset:        2,000–10,000 labelled samples
Potential source:         NRSC DMSP post-event products, Copernicus EMS,
                          HPSDMA field survey GPS points,
                          Very High Resolution commercial imagery (Maxar/Planet)
Priority:                 🟠 MEDIUM — enables transition from CHANGE_DETECTED
                          to DAMAGE_CLASSIFIED
```

---

### GAP-09: M8 — Real InSAR Deformation Records

```
Model:                    M8 — Ground Movement / Deformation
Current evidence:         4,000 synthetic-calibrated slope profiles
                          0 real monitored sites

Missing data:
  50+ real slope monitoring sites with:
    - Sentinel-1 InSAR LOS velocity time series (2018–present)
    - 12+ months continuous per site
    - Corresponding rainfall records for hydro-mechanical correlation
    - Optional: GNSS, extensometer, or crackmeter validation
    - At least 5 sites showing confirmed pre-failure acceleration

Minimum useful dataset:   50 sites, multi-year
Preferred dataset:        200 sites, 5+ year InSAR stack
Potential source:         ESA Sentinel-1 SLC archive (Open Access),
                          ISRO Cartosat-1/2 InSAR, NRSC National SAR,
                          CSRE IIT Bombay landslide InSAR studies
Priority:                 🟠 MEDIUM — Saito failure detection needs real data
```

---

## 🟡 LOWER PRIORITY GAPS

---

### GAP-10: M13 — Direct Seasonal Population Evidence

```
Model:                    M13 — Population Vulnerability
Current evidence:         Census 2011 (real); HP Tourism statistics (real)
                          Tourist multiplier (e.g. 1.8×) — ASSUMED/MODELLED

Missing data:
  Annual tourist flow counts at key Beas corridor checkpoints:
    - Daily tourist entries at Manali: Rohtang Pass checkpoint
    - Seasonal hotel occupancy rates per zone
    - Post-event population displacement records

Minimum useful dataset:   5 years of seasonal tourist flow statistics
Preferred dataset:        Annual + sub-seasonal breakdown by locality
Potential source:         HPTDC seasonal reports, Manali municipal records,
                          Himachal Pradesh Tourism Board, 
                          Census 2021 (when released)
Priority:                 🟡 LOWER — Census 2011 basis is real; tourist
                          multiplier is directionally reasonable
```

---

### GAP-11: M9 — Real IoT Sensor Anomaly Dataset

```
Model:                    M9 — Sensor Anomaly Detection
Current evidence:         5,000 simulated nominal readings + 6 synthetic faults
                          Stage 1 deterministic rules are robust regardless

Missing data:
  10,000+ real operational sensor readings:
    - From deployed AWS, river gauges, tiltmeters, piezometers in upper Beas
    - Including confirmed normal periods AND confirmed hardware fault episodes
    - Metadata: sensor ID, installation date, maintenance log

Minimum useful dataset:   10,000 nominal + 100+ labelled fault events
Preferred dataset:        100,000+ nominal readings; continuous 2+ year logs
Potential source:         IMD AWS network data, CWC HP gauge telemetry,
                          HP Forest Dept tiltmeters (if deployed)
Priority:                 🟡 LOWER — Stage 1 physics rules cover most
                          real-world failure modes; Isolation Forest is
                          supplementary
```

---

### GAP-12: M18 — Real Prediction-Outcome Pairs

```
Model:                    M18 — Risk Calibration
Current evidence:         1,000 synthetic beta-distributed prediction-outcome pairs
                          0 real prediction-outcome pairs

Missing data:
  100+ real prediction-outcome pairs:
    - Each pair: model_id, raw_probability, observed_binary_outcome,
      event_id, timestamp
    - Must be genuinely independent from training and internal validation sets
    - Cover both positive (flood/landslide occurred) and negative outcomes

Minimum useful dataset:   100 independent prediction-outcome pairs
Preferred dataset:        500+ across ≥2 monsoon seasons
Potential source:         Operational deployment outputs matched to
                          HPSDMA post-event situation reports
Note:                     This gap resolves automatically once the system
                          is deployed operationally for ≥2 monsoon seasons
Priority:                 🟡 LOWER — only useful after operational deployment
```

---

## Data Collection Roadmap Summary

| Priority | Gap | Model | Minimum Target | Primary Source |
|----------|-----|-------|---------------|----------------|
| 🔴 1 | Independent stable slope controls | M6 | 500 points | GSI, InSAR, HPSDMA |
| 🔴 2 | Independent storm-landslide episodes | M7 | 100 storms | IMD/HPSDMA 2005–2023 |
| 🔴 3 | CWC continuous river gauge records | M10 | 2+ years | CWC WRIS, Jal Shakti |
| 🔴 4 | Observed flood extents (satellite) | M11/M4 | 50 events | Copernicus EMS, NRSC |
| 🔴 5 | Timestamped hazard arrival events | M19 | 50 events | CWC, HPSDMA, NDRF logs |
| 🟠 6 | Authoritative flood rasters (scenes) | M4 | 50 scenes | Copernicus EMS, NRSC |
| 🟠 7 | Post-event damage records (assets) | M14 | 100 records | HP PWD, HPSEB, HPSDMA |
| 🟠 8 | Labelled pre/post damage imagery | M20 | 500 samples | NRSC, Copernicus, field |
| 🟠 9 | InSAR deformation time series | M8 | 50 sites | Sentinel-1 SLC archive |
| 🟡 10 | Seasonal tourist flow counts | M13 | 5 yr annual | HPTDC, municipal records |
| 🟡 11 | Real IoT sensor readings + faults | M9 | 10,000+ | Deployed sensors |
| 🟡 12 | Real prediction-outcome pairs | M18 | 100 pairs | Operational deployment |

---

## Institutional Data Access Requirements

To close the HIGH priority gaps, the following institutional data agreements are needed:

| Institution | Data Type | Gap Addressed |
|------------|-----------|--------------|
| **Central Water Commission (CWC)** | River gauge telemetry | M10, M11, M19 |
| **India Meteorological Dept (IMD)** | AWS sub-hourly rainfall | M1, M7 |
| **Geological Survey of India (GSI)** | Landslide inventory | M6, M7 |
| **HP State Disaster Mgmt Authority (HPSDMA)** | Post-event reports | M7, M14, M20 |
| **European Space Agency (ESA/Copernicus)** | Sentinel-1/2 SLC archive | M4, M8, M11 |
| **NRSC / ISRO** | Disaster monitoring products | M4, M11, M20 |
| **HP Tourism Development Corp (HPTDC)** | Seasonal visitor statistics | M13 |
| **HP PWD / HPSEB** | Asset damage records | M14 |

---

*FLOODY SHIELD v3.0 | SIH-26192 | Final Data Gaps Report | 2026-09-21*
