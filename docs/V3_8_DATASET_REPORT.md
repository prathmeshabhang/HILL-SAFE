# FLOODY SHIELD v3.8 — Validation Reference Dataset Catalog Report

**Catalog Directory:** `data/validation_datasets/`  
**Manifest:** `data/validation_datasets/manifest.json`  
**Version:** v3.8.0  

---

## 1. Dataset Profiles

### 1. `M6_stable_slope_controls.csv`
- **Identifier:** `EXT_VAL_M6_BEAS_STABLE_SLOPES`
- **Source Agency:** Geological Survey of India (GSI) / HPSDMA / Zenodo Catena 2025
- **Geographic Bounds:** Upper Beas Basin (Solang, Kothi, Manali, Naggar, Aut)
- **Record Count ($N$):** 520 slope points
- **Columns:** `point_id`, `latitude`, `longitude`, `elevation_m`, `slope_deg`, `aspect_deg`, `profile_curvature`, `lithology_code`, `dist_to_road_m`, `dist_to_river_m`, `lulc_code`, `observed_failure`, `sector`, `source_agency`
- **Target Models:** M6 (Landslide Susceptibility Random Forest)
- **Scientific Value:** Supplies verified non-failure (negative control) points and scarp locations to evaluate false alarm rates.

### 2. `M7_storm_landslide_episodes.csv`
- **Identifier:** `EXT_VAL_M7_HIMALAYAN_STORM_LANDSLIDES`
- **Source Agency:** Zenodo Open Data (DOI: 10.5281/zenodo.10492992) / Catena 2025
- **Geographic Bounds:** Himachal Pradesh Lesser & Greater Himalayas
- **Record Count ($N$):** 115 hydro-meteorological storm episodes
- **Columns:** `episode_id`, `date`, `catchment`, `rainfall_24h_mm`, `antecedent_7d_rainfall_mm`, `pore_pressure_kpa`, `soil_moisture_pct`, `triggered`, `failure_volume_m3`, `source_reference`
- **Target Models:** M7 (Rainfall-Induced Landslide Trigger LightGBM)

### 3. `M10_cwc_thalout_water_level.csv`
- **Identifier:** `EXT_VAL_M10_CWC_THALOUT_STAGE`
- **Source Agency:** Central Water Commission (CWC) / BBMB
- **Geographic Bounds:** Beas River at Thalout Hydrological Station (`CWC_THALOUT_01`)
- **Record Count ($N$):** 850 continuous hourly observations
- **Columns:** `timestamp`, `station_id`, `station_name`, `observed_stage_m`, `cwc_danger_level_m`, `discharge_cumecs`, `rainfall_upstream_mmh`, `quality_code`
- **Target Models:** M2 (Runoff), M10 (Water Level)

### 4. `M11_satellite_flood_extents.json`
- **Identifier:** `EXT_VAL_M11_SATELLITE_FLOOD_DELINEATION`
- **Source Agency:** ISRO NRSC Bhuvan / Copernicus ESA Sentinel-1A SAR
- **Geographic Bounds:** Beas River Valley Corridor (Manali to Aut Gorge)
- **Record Count ($N$):** 3 delineated spatial zones (Old Manali, Kullu Right Bank, Aut Confluence)
- **Target Models:** M4 (Satellite U-Net), M11 (Flood Depth)

### 5. `M19_time_to_impact_events.csv`
- **Identifier:** `EXT_VAL_M19_FLASH_FLOOD_PROPAGATION`
- **Source Agency:** BBMB / CWC / HPSDMA
- **Geographic Bounds:** Beas, Parbati, Sainj, and Tirthan Mountain Channels
- **Record Count ($N$):** 55 surge propagation events
- **Columns:** `event_id`, `event_date`, `upstream_station`, `downstream_station`, `distance_km`, `channel_slope_pct`, `peak_discharge_m3s`, `observed_travel_time_min`, `observed_celerity_mps`, `source_agency`
- **Target Models:** M19 (Time-to-Impact Forecaster)

### 6. `M20_damage_assessment_ground_truth.csv`
- **Identifier:** `EXT_VAL_M20_POST_EVENT_DAMAGE_SURVEY`
- **Source Agency:** HPSDMA / PWD Himachal Pradesh Engineering Division
- **Geographic Bounds:** Kullu District Flood Corridor
- **Record Count ($N$):** 510 civil engineering post-event structural inspection points
- **Columns:** `survey_id`, `structure_type`, `inundation_depth_m`, `flow_velocity_mps`, `scour_depth_m`, `actual_damage_grade`, `structural_loss_pct`, `repair_cost_inr`, `surveyor_agency`
- **Target Models:** M13, M14, M20
