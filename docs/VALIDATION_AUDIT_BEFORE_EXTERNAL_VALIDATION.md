# VALIDATION AUDIT BEFORE EXTERNAL VALIDATION — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Predict • Protect • Preserve*  
*Audit Date: 2026-09-20*

---

## 1. Executive Summary & Objective

This pre-execution audit evaluates the current scientific state of the disaster intelligence models (**M6, M7, M2, M4**), the recently integrated **Pore-Water Pressure (PWP) / Slope Stability Layer**, and the status of **external ground-truth validation datasets**.

The objective is to establish an uncompromised scientific baseline:
1. Audit and correct the PWP implementation to enforce physical monotonicity, dimensional consistency, explicit parameter provenance, and non-engineering-grade disclaimers.
2. Freeze PWP v1 with a comprehensive Model Card.
3. Conduct authentic, zero-fabrication external validation for landslide models (M6, M7) using genuine independent datasets.
4. Conduct authentic external validation for flood models (M2, M4) using independent event records and flood masks.

---

## 2. Model & Layer Status Audit

| Model / Layer | Task | Algorithm / Framework | Training Data & Feature Contract | Current Status | Scientific Validation State |
|:---|:---|:---|:---|:---|:---|
| **Model M6** | Static Landslide Susceptibility | Random Forest (350 trees), Scikit-Learn | `upper_beas_landslide_dataset.csv` (8 features: `elevation_m`, `slope_deg`, `aspect_deg`, `profile_curvature`, `lithology_code`, `dist_to_road_m`, `dist_to_river_m`, `lulc_code`) | Frozen (`m6_beas_susceptibility_rf.joblib`) | **Partially Validated (Catchment Benchmark)**; External validation pending in-AOI independent observations. |
| **Model M7** | Dynamic Landslide Trigger | LightGBM (350 rounds) | `upper_beas_landslide_dataset.csv` (5 features: `susceptibility_class`, `slope_deg`, `rainfall_1h`, `antecedent_rain_3d`, `soil_moisture_pct`) | Frozen (`m7_beas_trigger_lgbm.joblib`) | **Catchment Benchmark Verified**; Event-based external dynamic validation pending. |
| **PWP v1** | Pore Pressure & Slope Stability | 1D Infinite Slope Mechanics + Terzaghi Effective Stress | Physical simulation from `slope_deg`, `rainfall_1h`, `antecedent_rain_3d`, `surface_moisture_proxy_pct`, `twi` | Operational Prototype (`ml/landslide/pore_pressure/`) | **Not Field-Validated**; Direct in-situ piezometer/tensiometer validation data currently unavailable. |
| **Model M2** | Catchment Flood Occurrence | XGBoost + Isotonic Calibrator | `upper_beas_flood_dataset.csv` (19 topo-hydro-meteorological features) | Frozen (`m2_upper_beas_xgboost.joblib`) | **Catchment Benchmark Verified**; Independent external flood-event validation pending. |
| **Model M4 (U-Net)** | Multimodal Flood Extent Segmentation | 9-Channel PyTorch U-Net | Real & simulated Sentinel-1 SAR + Sentinel-2 optical + DEM stacks | Operational Prototype (`flood_multimodal_unet.pt`) | **Pseudo-GT Benchmark Verified**; Independent satellite flood mask validation pending. |

---

## 3. Spatial Source of Truth

- **Study Area AOI**: Upper Beas Catchment (Kullu–Manali, Himachal Pradesh)
- **Authoritative Geographic Bounds** (`ml/satellite_hazard/config.py`):
  - Longitude: `76.80°E` to `77.45°E`
  - Latitude: `31.60°N` to `32.40°N` (extended regional basin bounds up to `31.40°N` to `32.45°N` in dataset loader)
- **Target Projected CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N) — all distance, buffer, and slope derivatives must be computed in true metric units.
- **Display / Interchange CRS**: `EPSG:4326` (WGS 84 geographic).
- **Spatial Resolution**: $30\,\text{m} \times 30\,\text{m}$ grid (aligned with Copernicus GLO-30 DEM). Standard scene dimensions: $500 \times 400$ pixels ($15\,\text{km} \times 12\,\text{km}$).

---

## 4. Known Scientific Risks & Required Corrections

### Risk 1: Factor-of-Safety Terminology
- **Risk**: Describing the 1D infinite slope output simply as an "engineering Factor of Safety" implies certified geotechnical design suitability.
- **Correction**: Re-label and document as **"modelled infinite-slope FoS under representative assumptions"**. Clarify that it is a geospatial decision-support indicator, NOT a substitute for site-specific borehole geotechnical investigation.

### Risk 2: Assumed Geotechnical Parameters
- **Risk**: Parameters such as effective cohesion $c' = 10\,\text{kPa}$, friction angle $\phi' = 32^\circ$, soil depth $H = 2.0\,\text{m}$, bulk unit weight $\gamma_{\text{bulk}} = 18\,\text{kN/m}^3$, saturated unit weight $\gamma_{\text{sat}} = 20\,\text{kN/m}^3$, and hydraulic conductivity $K_{\text{sat}} = 15\,\text{mm/h}$ could be misinterpreted as measured field values.
- **Correction**: Explicitly tag these as **`ASSUMED_REPRESENTATIVE`** based on published literature for Himalayan colluvium / residual soils (e.g. Martha et al., 2010; Catena literature).

### Risk 3: NDMI Semantic Conflation
- **Risk**: Using `soil_moisture_pct` can lead users to believe Sentinel-2 NDMI is a direct measurement of volumetric soil water content ($\text{m}^3/\text{m}^3$) or in-situ pore pressure.
- **Correction**: Explicitly document and alias this variable as **`surface_moisture_proxy_pct`** (derived from Sentinel-2 NIR/SWIR normalized difference moisture index, scaled $18\% - 90\%$).

### Risk 4: Rainfall Provenance
- **Risk**: Describing precipitation inputs as "gauge telemetry" when using gridded products.
- **Correction**: Explicitly distinguish satellite precipitation estimations (GPM IMERG Early Run, 0.1° resolution) and regional gridded products (IMD 0.25°) from direct in-situ automated weather station (AWS) tipping-bucket telemetry.

### Risk 5: Overstating M7 Controlled Experiment Benefit
- **Risk**: Claiming that adding physical features "proved" or "significantly improved" Model M7.
- **Correction**: Rephrase objectively: *On the tested 80/20 stratified split, adding the 5 physically derived features produced a minor metric change ($\Delta \text{ROC-AUC} = +0.0002$, $\Delta \text{Brier} = -0.0003$). While features accounted for 41.09% of tree split decisions, this single split does not establish independent generalization or causal superiority. Independent event-based validation is required.* Production M7 model artifact remains frozen.

### Risk 6: Zenodo 10492992 External Landslide Data Dislocation
- **Risk**: Claiming the Shimla–Solan dataset (Zenodo 10492992, 3,176 points) validates M6 in the Upper Beas.
- **Correction**: Maintain strict honesty: **0 points fall within Upper Beas AOI**. This dataset serves as a geographic transferability audit, NOT local catchment validation.

---

## 5. Data Gaps

1. **In-Situ Piezometer & Tensiometer Networks**: Currently unavailable in the Upper Beas catchment.
2. **In-Catchment Historical Landslide Inventory**: Need to audit and compile genuine Upper Beas / Kullu district landslide records (e.g., HPSDMA Kullu geoparametric reports, GSI post-monsoon reports, HIMCOSTE inventories) with verified spatial coordinates.
3. **Independent Satellite Flood Inundation Masks**: Need authoritative independent flood extents (e.g., NRSC July 2023 Beas flood maps, HiFlo-DAT event records) to evaluate M2 and M4.

---

## 6. Exact Next Execution Actions

1. **Phase 1**: Complete PWP scientific corrections in `ml/landslide/pore_pressure/` (parameter provenance audit, terminology updates, proxy documentation, physical monotonicity & edge case unit tests).
2. **Phase 2**: Freeze PWP v1 with `docs/PWP_V1_MODEL_CARD.md`.
3. **Phase 3**: Acquire and provenance-audit genuine Upper Beas / Kullu landslide inventory records into `data/external/m6/upper_beas/`.
4. **Phase 4**: Execute frozen M6 external validation pipeline with spatial and temporal leakage controls.
5. **Phase 5**: Build event-based M7 validation framework and comparative evaluation.
6. **Phase 6**: Conduct external validation for flood models M2 and M4.
