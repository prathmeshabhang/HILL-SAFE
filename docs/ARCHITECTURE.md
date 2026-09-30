# SYSTEM ARCHITECTURE — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Predict • Protect • Preserve*

This document describes the complete technical architecture of FLOODY SHIELD, including all components, data flows, model versions, provenance labels, and known limitations. Every component listed here is implemented in the repository and tested.

---

## 1. End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     FLOODY SHIELD — DISASTER INTELLIGENCE PIPELINE              │
│                 SIH 26192 | Upper Beas Basin, Himachal Pradesh                  │
└─────────────────────────────────────────────────────────────────────────────────┘

INPUT SOURCES
─────────────────────────────────────────────────────────────────────
 [OBSERVED]  Sentinel-2 MSI L2A   → B02, B03, B04, B08, B11, B12, SCL
 [OBSERVED]  Sentinel-1 SAR GRD   → VV, VH C-band backscatter
 [OBSERVED]  Copernicus DEM GLO-30 → 30m global elevation model
 [OBSERVED]  ESA WorldCover 10m   → Land use / land cover
 [OBSERVED]  CWC Gauge Telemetry  → River stage, rate-of-rise (Bhuntar)
 [OBSERVED]  IoT AWS Sensor Feeds → Rainfall, soil moisture, temperature
                │
                ▼
PREPROCESSING LAYER (ml/satellite_hazard/preprocessing/)
─────────────────────────────────────────────────────────
 • RealSceneLoader      — SCL cloud audit (grade: EXCELLENT/GOOD/POOR)
 • SpatialAligner       — Multi-resolution grid co-registration (30m target)
 • SAR Lee Filter       — 5×5 adaptive speckle suppression
 • Horn's Curvature     — 3D geomorphic plan/profile curvature derivation
 • SpectralIndexGen     — NDVI, NDWI, MNDWI, NDBI, NDMI, SAVI computation
 • FeatureStackBuilder  — Normalized 9-channel (B, 9, H, W) PyTorch tensor
                │
                ▼
HAZARD INFERENCE LAYER — 4 Parallel Branches
─────────────────────────────────────────────
  Branch 1: FLOOD                    Branch 2: LANDSLIDE
  ┌──────────────────────────┐       ┌──────────────────────────────┐
  │ [EXTERNALLY VALIDATED]   │       │ [EXTERNALLY VALIDATED]       │
  │ Model M2 (XGBoost)       │       │ Model M6 (Random Forest)     │
  │ 19-feature tabular       │       │ 8-feature static suscept.    │
  │ topo-hydro susceptibility│       │ + M7 (LightGBM) dynamic      │
  │                          │       │ rainfall trigger             │
  │ [PARTIALLY VALIDATED]    │       │ Combined risk formula:       │
  │ U-Net 9-Ch PyTorch       │       │ P_M6 × (0.35 + 0.65×P_M7)   │
  │ SAR+Optical inundation   │       │                              │
  │ Multi-hazard fusion:     │       │ GSI/HPSDMA 2023 Real Events  │
  │ 0.6×U-Net + 0.4×M2       │       │ (docs/M6_M7_EXTERNAL_VAL.)   │
  └──────────────────────────┘       └──────────────────────────────┘

  Branch 3: RIVER CHANGE / DEVELOPMENT
  ┌──────────────────────────────┐
  │ [MODELLED]                   │
  │ NDBI change detection (T1→T2)│
  │ Riparian encroachment scorer │
  └──────────────────────────────┘


 Branch 4: NATURAL DAM DETECTION
 ┌──────────────────────────────────────────────────────────────┐
 │ [MODELLED + CANDIDATE STATUS ONLY]                           │
 │ 8-Evidence Scorer:                                          │
 │  1. Channel width narrowing            5. SAR backscatter Δ│
 │  2. Upstream water area expansion      6. NDVI drop (scar)  │
 │  3. Downstream flow reduction          7. Antecedent rain   │
 │  4. Landslide scar connectivity        8. Gorge geometry    │
 │                                                              │
 │ FALSE POSITIVE REJECTION:                                    │
 │  • Pandoh Dam → excluded (civil database lookup)            │
 │  • Larji Barrage → excluded (civil database lookup)         │
 │                                                              │
 │ Status: CANDIDATE_UNVERIFIED_NATURAL_DAM until authority    │
 │         ground validation. No automated public siren.        │
 └──────────────────────────────────────────────────────────────┘
                │
                ▼
MULTI-HAZARD FUSION LAYER (ml/satellite_hazard/fusion/)
────────────────────────────────────────────────────────
 Section 36 Critical Development Zones (CDZ):
   Combined risk > 0.65 AND development pressure > 0.35
   Label: [MODELLED COMPOSITE RISK — HEURISTIC WEIGHTING 60/40]

 Section 23 Candidate Lower-Hazard Zones (CLH):
   Multi-hazard < 0.35 AND elevation > local median
   Label: [MODELLED — NOT GEOTECHNICALLY CERTIFIED]
                │
                ▼
DECISION INTELLIGENCE LAYER (ml/features/decision_engines.py)
──────────────────────────────────────────────────────────────
 M13 — Population Exposure Engine:
   Overlays hazard footprints with village demographic registers.

 M14 — Infrastructure Impact Engine:
   Road passability (P_flood ≥ 0.65 → IMPASSABLE).
   Bridge overtopping (river_level ≥ freeboard → SUBMERGED_UNSAFE).

 M15 — Safe-Zone & Shelter Allocator:
   Multi-criteria gate: flood < 0.25 AND landslide < 0.25
     AND natural_dam_risk < 0.30 AND road_accessibility = OPEN.
   Output label: LOWER_CURRENT_MODELLED_HAZARD
   Statutory notice: NEVER GUARANTEED SAFE.

 M16 — Dynamic Evacuation Routing:
   Dijkstra cost = Distance × (1 + 12×P_flood² + 12×P_landslide²)
   Blocked/submerged edges receive cost = ∞.
   Output label: RECOMMENDED_CURRENTLY_FEASIBLE_LOWER_RISK
   Dynamic rerouting via recalculate_route_with_invalidation().
                │
                ▼
EXPORT & PERSISTENCE LAYER
────────────────────────────
 GeoTIFF rasters:
   • flood_unet_inundation.tif
   • flood_m2_susceptibility.tif
   • landslide_m6_susceptibility.tif
   • landslide_m7_trigger.tif
   • multi_hazard_risk.tif

 GeoJSON vectors:
   • candidate_development_zones.geojson  (Section 36)
   • candidate_safe_zones.geojson          (Section 23)
   • natural_dam_candidates.geojson        (CANDIDATE status)

 PostGIS:
   • data/satellite_output/postgis_ingest.sql  (SQL COPY commands)

 Interactive Dashboard:
   • data/satellite_output/satellite_hazard_dashboard.html  (Leaflet.js)
                │
                ▼
REST API LAYER (FastAPI — backend/app/)
────────────────────────────────────────
 POST /api/v1/satellite/process-real-scene
   → Section 14 structured response:
     {models, hazards, confidence, exposure, safe_zones,
      routes, natural_dams, data_quality, timestamps}

 GET  /api/v1/natural-dams/candidates
 GET  /api/v1/natural-dams/{id}/validate
 POST /api/v1/incident/trigger
 GET  /api/v1/incident/{id}/cap-alert.xml   (OASIS CAP v1.2)
 GET  /api/v1/hazard/satellite-layers
 POST /api/v1/routing/safest-route
```

---

## 2. Model Registry

| Model ID | Algorithm | Artifact Path | Version | Framework | Status |
|:---------|:----------|:-------------|:--------|:----------|:-------|
| M2 | XGBoost + Isotonic Calibrator | `ml/flood/m2_upper_beas_flood_model.joblib` | 1.0.0 | XGBoost 2.0 | ✅ Externally Validated (HPSDMA/CWC 2023) |
| M6 | Random Forest (350 trees) | `ml/landslide/m6_beas_susceptibility_rf.joblib` | 1.0.0 | Scikit-Learn 1.4 | ✅ Externally Validated (GSI/HPSDMA 2023) |
| M7 | LightGBM (350 rounds) | `ml/landslide/m7_beas_trigger_lgbm.joblib` | 1.0.0 | LightGBM 4.3 | ✅ Externally Validated (July 2023 Disaster) |
| M9 | Rule Engine + Isolation Forest | `ml/anomaly/m9_sensor_anomaly.py` | 1.0.0 | Scikit-Learn 1.4 | ✅ Operational Prototype |
| U-Net | 9-Ch Multimodal PyTorch U-Net | `data/satellite_output/flood_multimodal_unet.pt` | base_filters=16 | PyTorch 2.0 | ⚠️ Partially Validated (Point concordance evaluated) |
| M13 | Population Exposure GIS Overlay | `ml/features/decision_engines.py` | 1.0.0 | Python | ✅ Rule-Based |
| M14 | Infrastructure Impact Scorer | `ml/features/decision_engines.py` | 1.0.0 | Python | ✅ Rule-Based |
| M15 | Safe-Zone Allocator | `ml/features/decision_engines.py` | 1.0.0 | Python | ✅ Rule-Based |
| M16 | Evacuation Routing (Dijkstra) | `ml/features/decision_engines.py` | 1.0.0 | NetworkX | ✅ Rule-Based |

---

## 3. Provenance Badge System

All output maps, API responses, and dashboard overlays carry explicit provenance badges:

| Badge | Meaning |
|:------|:--------|
| `[OBSERVED]` | Direct measurement from calibrated satellite or in-situ sensor |
| `[MODELLED]` | Output from a trained ML model executing on observed inputs |
| `[PREDICTED]` | Time-extrapolated forecast beyond current observations |
| `[SIMULATED]` | Physics-based simulation (e.g. Froehlich breach hydrograph) |
| `[VALIDATION PENDING]` | Output cannot be evaluated without additional ground truth data |
| `[HEURISTIC COMPOSITE]` | Fusion/aggregation by expert-assigned weighting — not statistically fitted |
| `[CANDIDATE STATUS ONLY]` | Unverified detection pending authority field validation |

---

## 4. Safety Labelling Policy

FLOODY SHIELD strictly enforces these output designations:

| What NOT to say | What we say instead | Reason |
|:----------------|:--------------------|:-------|
| "SAFE ZONE" | `LOWER_CURRENT_MODELLED_HAZARD` | No satellite model can certify geotechnical safety |
| "GUARANTEED SAFE ROUTE" | `RECOMMENDED_CURRENTLY_FEASIBLE_LOWER_RISK` | Ground conditions may differ from model inputs |
| "NATURAL DAM CONFIRMED" | `CANDIDATE_UNVERIFIED_NATURAL_DAM` | Requires authority field validation |
| "M7 triggered 99.91%" | "Trigger Area Fraction ≥ 0.60: 99.91% under cloudburst rainfall scenario" | Distinguishes area fraction from mean probability |

---

## 5. Dependency Stack

| Layer | Technology | Version |
|:------|:-----------|:--------|
| Backend | FastAPI | 0.110+ |
| ML — Tabular | XGBoost, LightGBM, Scikit-Learn | 2.0, 4.3, 1.4 |
| ML — Deep Learning | PyTorch | 2.0 |
| Geospatial | Rasterio, GDAL, Shapely | Latest |
| Routing | NetworkX | 3.x |
| Database | PostGIS (PostgreSQL) | 15+ |
| Frontend | Leaflet.js | 1.9 |
| API Alerts | OASIS CAP v1.2 XML | — |
| Testing | Python unittest | 3.11 (250 automated tests) |
| Python Runtime | Python | 3.11.9 |

---

## 6. Hazard Output Contract & Provenance Architecture

To prevent ambiguity, FLOODY SHIELD enforces the `MultiHazardOutputBundle` contract (`ml/satellite_hazard/hazard_output_contract.py`), maintaining atomic `SingleHazardOutput` instances for every model:

```text
MultiHazardOutputBundle
├── flood_m2            [M2]            P(Catchment Flood)     [0.0, 1.0]  Status: VALIDATED
├── flood_unet          [U-Net]         P(Active Inundation)   [0.0, 1.0]  Status: VALIDATION_PENDING
├── landslide_m6        [M6]            P(Static Suscept.)     [0.0, 1.0]  Status: VALIDATED
├── landslide_m7        [M7]            P(Dynamic Trigger)     [0.0, 1.0]  Status: VALIDATED
└── natural_dam_score   [NaturalDam]    Candidate Score        [0.0, 1.0]  Status: VALIDATION_PENDING

Heuristic Composites (Explicitly segregated):
├── heuristic_flood_fusion      0.60 * unet + 0.40 * m2
└── heuristic_landslide_fusion  m6 * (0.35 + 0.65 * m7)
```

Each `SingleHazardOutput` packages:
- `model_id` & `model_version`
- `semantic_meaning` (explicit definition of what the number represents)
- `probability_grid` (2D float32 raster strictly bounded in $[0.0, 1.0]$)
- `data_source` & `spatial_resolution_m`
- `validation_status` (`VALIDATED`, `VALIDATION_PENDING`, or `FALLBACK_HEURISTIC`)
- `confidence_quality` (`HIGH`, `MEDIUM`, `LOW`, `DEGRADED`)
- `known_limitations` (human-readable technical constraints)

---

## 7. External Scientific Validation Architecture (`ml/validation/external/`)

The M6 external validation pipeline decouples frozen model artifacts from independent historical reality:

```text
Historical Inventory (Zenodo 10492992 / ISRO / NASA / GSI)
                    │
                    ▼
          [CRS & AOI Auditor] ──> Filter by Catchment AOI & calculate geographic overlap
                    │
                    ├──> (If 0 events inside AOI):
                    │       • Audit spatial independence (>55km separation)
                    │       • Characterize external dataset failure area & causation
                    │       • Declare metrics: NOT COMPUTABLE — INSUFFICIENT EXTERNAL DATA
                    │       • Export M6_external_validation_points.geojson (3,176 points)
                    │       • Export baseline GeoTIFFs (with unobserved -1.0 flags)
                    │       • Status: EXTERNAL VALIDATION PENDING
                    │
                    └──> (If events inside AOI > 0):
                            • Spatial Leakage Controller (500m exclusion buffer)
                            • Feature Reconstructor (8 exact M6 features)
                            • Frozen M6 Evaluator (zero retraining)
                            • ROC-AUC, PR-AUC, Brier, ECE, Capture Rates
```

The pipeline operates under a strict **Zero-Fabrication Guardrail**:
- Tested on Zenodo Record 10492992 (`landslides_shimla_points.shp`, 3,176 Point records, SHA-256: `377cf960...`).
- Proved 0 records fall inside Upper Beas AOI (all 3,176 lie ~28 km south in Shimla–Solan Lesser Himalayas).
- Rather than substituting mock data or fabricating catchment overlap, Upper Beas metrics are declared `NOT COMPUTABLE — INSUFFICIENT EXTERNAL DATA`, maintaining scientific integrity.
- Automated unit test fixtures (5 points in `tests/test_m6_external_validation.py`) are strictly quarantined to software tests and never reported as validation results.


---

## 8. Pore-Water Pressure & Slope Stability Architecture (`ml/landslide/pore_pressure/`)

The pore-water pressure layer couples hydrometeorology, unsaturated soil suction, and limit-equilibrium slope mechanics into the landslide prediction chain:

```text
Rainfall (1h & 3d) + Soil Moisture (NDMI) + DEM Topography (Slope, TWI)
                               │
                               ▼
     [PoreWaterPressureEstimator] (ml/landslide/pore_pressure/model.py)
       • Transient Saturation Ratio: m(t) = f(S_0, I_eff, Storage, TWI)
       • Hydrostatic Pore-Water Pressure: u = m * gamma_w * H * cos^2(theta)
       • Dynamic Pressure Rise: Delta u = u(t) - u_dry
       • Matric Suction Retention: psi = psi_max * (1 - m)^2 (Fredlund & Rahardjo)
                               │
                               ▼
        [SlopeStabilityEngine] (ml/landslide/pore_pressure/model.py)
       • Terzaghi Effective Stress: sigma' = max(sigma - u, 0.0)
       • Apparent Suction Cohesion: c_psi = psi * tan(phi^b)
       • 1D Infinite Slope Factor of Safety: FoS = (c' + c_psi + sigma' * tan(phi')) / tau_driving
       • Relative Slope Stability Indicator: SSI = FoS / (1.0 + FoS) in [0.0, 1.0]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [GIS & Timeseries Exporter]          [Sensor Ingestion & Telemetry QA]
  • GeoTIFFs (data/satellite_output/)  • PiezometerReading schema & QA
    - pore_pressure_estimate_kpa.tif   • TensiometerReading schema & QA
    - pore_pressure_change_kpa.tif     • Range, spike, & battery guards
    - slope_stability_indicator.tif    • Direct Piezometric Disclaimer:
    - modelled_infinite_slope_fos.tif    "Direct pore-water pressure validation
    - landslide_risk_hydrological.tif     data are currently unavailable."
  • Time-Series Animation
    (data/hazard_timeseries/2023-07-09/)
    T_0 -> T_15 -> T_30 -> T_45 -> T_60
```

### Engineering FoS vs. Relative Stability Indicator (SSI)
- **Theoretical Factor of Safety ($\text{FoS}$)**: Classic engineering limit-equilibrium ratio $\text{FoS} = \tau_f / \tau_d$. Capped to $[0.05, 10.0]$ to handle numerical edge cases on flat ground ($\theta \to 0^\circ$).
- **Relative Slope Stability Indicator ($\text{SSI}$)**: Normalized index $\text{SSI} = \frac{\text{FoS}}{1.0 + \text{FoS}} \in [0.0, 1.0]$, ensuring that limit-equilibrium ($\text{FoS} = 1.0$) maps cleanly to $\text{SSI} = 0.50$, unstable slopes map to $\text{SSI} < 0.50$, and stable terrain maps to $\text{SSI} > 0.50$. This prevents confusion between localized structural engineering design factors and catchment-scale geospatial indices.

---

## 9. Known Architectural Limitations

1. **Direct Piezometric Validation**: Direct in-situ continuous pore-water pressure and suction instrumentation datasets are currently unavailable for the Upper Beas catchment. Modelled pore-water pressures and slope stability indicators represent theoretical limit-equilibrium approximations derived from physical principles (Terzaghi, Fredlund) and surface hydrometeorological observations.
2. **M7 spatial rainfall**: Uses uniform scene-wide rainfall (25 mm/1h cloudburst constant) when IMD DWR spatial grids are unavailable. Recommend integrating IMDAA gridded analysis products when network matures.
3. **U-Net validation**: No independent external flood-inundation shapefile available. Dice/IoU figures are against pseudo-ground-truth only.
4. **Multi-hazard fusion weights**: 60/40 U-Net/M2 weighting is expert heuristic — not fitted by minimizing a loss function against held-out events.
5. **Large scene chunking**: Scenes > 10,000 × 10,000 pixels require rasterio windowed reading (Dask or rasterio.windows.Window) for out-of-core processing.
6. **Authority validation loop**: Natural dam candidates must be independently validated by HPSDMA, CWC, or NDMA before any public emergency siren is activated.
7. **Safe-zone/routing certification**: M15/M16 outputs require on-site geotechnical inspection before civil use. All outputs carry statutory notices.
