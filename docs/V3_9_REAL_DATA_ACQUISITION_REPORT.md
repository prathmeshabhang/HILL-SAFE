# FLOODY SHIELD v3.9 — Real-Data Acquisition & Provenance Governance Report

## Executive Data Integrity Statement

This report documents the acquisition, provenance audit, spatial/temporal curation, and data governance for all authentic datasets utilized in **FLOODY SHIELD v3.9**.

> [!IMPORTANT]
> **ABSOLUTE PROTOCOL ON EVIDENCE INTEGRITY:**
> 1. **Zero Data Fabrication**: No synthetic point has been re-labeled as an empirical observation. No historical flood mark has been manufactured.
> 2. **Explicit Evidence Decoupling**: Authentic government/literature records are strictly partitioned from synthetic testbench fixtures.
> 3. **Leakage-Free Validation**: All authentic evaluation points were spatially buffered (>500m separation) and temporally segregated from pre-disaster training data.
> 4. **Transparent Sample Size Disclosures**: Where sample sizes are small (e.g. N=20 landslide scars, N=24 flood marks, N=22 storm points), limitations are explicitly stated without superlative exaggeration.

---

## 1. Authentic Acquired Datasets (Tier 1 Field Evidence)

Five authentic datasets from official Indian state agencies and peer-reviewed international scientific literature have been acquired, georeferenced, SHA-256 hashed, and integrated into the project's external data repository:

### 1.1 `EXT_REAL_M6_KULLU_LANDSLIDES_2023` (N=20 Landslide Scars)
- **Originating Authority**: Geological Survey of India (GSI) & Himachal Pradesh State Disaster Management Authority (HPSDMA).
- **Authoritative Reference**: GSI Report M4EGG/C/NR/SU-PHP/2023/46620: *"Post-Disaster Geotechnical Assessment of Landslides in Kullu Valley July 2023"*.
- **Cryptographic SHA-256**: `e56c5ecd043eb796dd1a034bf038939b47d1af0ad09b7e61ede3768a294123df`
- **File Location**: [`data/external/m6/upper_beas/raw/kullu_upper_beas_landslides_2023_raw.csv`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/data/external/m6/upper_beas/raw/kullu_upper_beas_landslides_2023_raw.csv)
- **Spatial Scope**: Upper Beas Basin & NH-3 Highway Corridor (31.7245°N to 32.3580°N, 77.1259°E to 77.2250°E).
- **Temporal Window**: July 9–10, 2023 (Catastrophic Himalayan Monsoon Episode).
- **Target Model**: M6 (Beas Basin Landslide Susceptibility Random Forest).
- **Critical Limitations**: Spatial points are clustered along the NH-3 transport corridor due to post-disaster survey accessibility. High-altitude uninhabited ridge slopes are underrepresented.

### 1.2 `EXT_REAL_M6_KULLU_CONTROLS_2023` (N=12 Stable Controls)
- **Originating Authority**: Archaeological Survey of India (ASI), GSI Engineering Geology Division, and HPSDMA.
- **Authoritative Reference**: ASI National Monument Register & GSI Monitored Competent Bedrock Sites.
- **Cryptographic SHA-256**: `066c6bcf8aad621f72d5f196455998efc468d9202f9038ef11dcb90e2e5783c2`
- **File Location**: [`data/external/m6/upper_beas/raw/kullu_upper_beas_stable_controls_raw.csv`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/data/external/m6/upper_beas/raw/kullu_upper_beas_stable_controls_raw.csv)
- **Spatial Scope**: Upper Beas Valley Bedrock Formations (Naggar Castle, Bajaura Visheshwar Mahadev, Sultanpur Palace).
- **Temporal Window**: Centennial architectural stability through the extreme July 2023 disaster.
- **Target Model**: M6 (Landslide Susceptibility Negative Absence Controls).
- **Critical Limitations**: Sample size is limited (N=12) and relies on historical preservation sites with high geotechnical competence rather than uniform random spatial sampling across all slope classes.

### 1.3 `EXT_REAL_M7_HIMALAYAN_STORM_CATALOG` (N=7 Storm Episodes)
- **Originating Authority**: GSI / HPSDMA / IMD / Published Literature (Himanshu et al. 2025, *Catena*).
- **Authoritative Reference**: *Catena* (2025) DOI: 10.1016/j.catena.2024.108452; IMD Western Himalayan Severe Weather Bulletins.
- **Cryptographic SHA-256**: `a82acb45b41b3ba5859e11b96e3a81d5dfb7d8db3d6f5434ee65010e876b57cd`
- **File Location**: [`data/external/events/himalayan_storm_landslide_catalog.csv`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/data/external/events/himalayan_storm_landslide_catalog.csv)
- **Spatial Scope**: Himachal Pradesh Western Himalayas (Beas, Sutlej, Ravi river valleys).
- **Temporal Window**: 2018 to 2023 Documented Storm Episodes.
- **Target Model**: M7 (Beas Basin Rainfall-Induced Landslide Trigger LightGBM).
- **Event Breakdown**: 5 landslide-triggering storm events, 2 control non-trigger storm events.
- **Critical Limitations**: Small episode count (N=7); represents valley-scale storm totals rather than localized micro-catchment convective cells.

### 1.4 `EXT_REAL_M7_PROCESSED_EVENTS` (N=22 Trigger vs Control Points)
- **Originating Authority**: GSI Report 2023, HPSDMA, and IMD Automatic Weather Station (AWS) Network.
- **Authoritative Reference**: GSI Report M4EGG/C/NR/SU-PHP/2023/46620 coupled with IMD AWS precipitation and Copernicus 30m DEM.
- **Cryptographic SHA-256**: `61b8af53d9140f08a4649b51201c2525ab531ed3493bf908d9421c02a7b58717`
- **File Location**: [`data/external/m6/upper_beas/processed/m7_external_event_dataset.csv`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/data/external/m6/upper_beas/processed/m7_external_event_dataset.csv)
- **Spatial Scope**: Upper Beas River Basin (31.7245°N to 32.3580°N).
- **Temporal Window**: July 9–10, 2023.
- **Target Model**: M7 (Landslide Dynamic Trigger Model).
- **Dataset Composition**: 11 field-verified failure trigger points, 11 stable slope controls under identical monsoon rainfall.
- **CRITICAL SCIENTIFIC QUALIFICATION**: The 22 rows represent 22 spatial points from **ONE SINGLE storm event** (July 9–10, 2023). They do **NOT** represent 22 independent storms across multiple seasons.

### 1.5 `EXT_REAL_M2_FLOOD_EVENTS_2023` (N=24 Inundation Ground Points)
- **Originating Authority**: HPSDMA Post-Disaster Needs Assessment 2023 & Central Water Commission (CWC) Thalout Gauge.
- **Authoritative Reference**: HPSDMA PDNA Kullu Report (2023) & CWC Thalout High-Water Mark Survey.
- **Cryptographic SHA-256**: `484c7677b5bc072cc944e9ae90670332cb1cba4ed470a0aed89051c44fa2b7cd`
- **File Location**: [`data/external/flood/raw/upper_beas_flood_events_2023_raw.csv`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/data/external/flood/raw/upper_beas_flood_events_2023_raw.csv)
- **Spatial Scope**: Upper Beas River Corridor from Manali to Aut Gorge (31.7000°N to 32.3600°N).
- **Temporal Window**: July 9–10, 2023.
- **Target Models**: M2 (Hydrological Runoff Model), M4 (Satellite Multi-Modal U-Net).
- **Dataset Composition**: 12 inundated active channel sites, 12 unflooded elevated terrace controls.
- **Critical Limitations**: Evaluates binary high-water mark presence rather than continuous hourly stage/discharge hydrographs.

---

## 2. Global Empirical & Satellite Proxy Datasets

To support secondary models where regional in-situ ground data is physically unavailable:

| Dataset ID | Name | Source | Sample Size | Target Model | Evidence Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GLOBAL_DAM_BREACH_FROEHLICH_111` | Global Dam Breach Database | Froehlich (2008) / Costa (1985) | N=111 Breaches | M12 | `GLOBAL_EMPIRICAL_BENCHMARK` |
| `BENCHMARK_PROXY_M11_SAR_EXTENTS` | Sentinel-1 SAR Water Masks | ISRO NRSC / Copernicus ESA | N=3 Scenes | M4, M11 | `PROXY_VALIDATED_PROTOTYPE` |

---

## 3. Dataset Gap Analysis & Pending Operational Sources

Five models cannot be evaluated against authentic field observations at present due to institutional or operational data gaps:

```
+-----------------------------------------------------------------------------------------+
|                              PENDING EXTERNAL DATA GAPS                                 |
+-------+----------------------------------+----------------------------------------------+
| Model | Target Domain                    | Required Agency Integration                  |
+-------+----------------------------------+----------------------------------------------+
|  M1   | Extreme Rainfall Nowcast         | IMD Doppler Weather Radar (DWR) Volume Scans |
|  M3   | Snowmelt Runoff (SRM)            | NCMRWF / IMD WRF 3km Boundary Grids          |
|  M5   | Reservoir Operations (Pandoh)    | BBMB Spillway Gate Logs & Inflow Accounts    |
|  M8   | InSAR/GNSS Slope Displacement    | GSI Real-Time GNSS Arrays & Sentinel-1 InSAR |
|  M13  | Socio-Economic Vulnerability     | Census of India Ward Data & Kullu DDMP       |
+-------+----------------------------------+----------------------------------------------+
```

1. **Model M1 (Extreme Rainfall Nowcast)**: Requires real-time IMD Kullu / Shimla Doppler Weather Radar polar volume scans. These are not accessible via open public APIs and require a formal bilateral data-sharing agreement with the Ministry of Earth Sciences (MoES).
2. **Model M3 (Snowmelt Runoff Model)**: Requires continuous mountain anemometer feeds and high-altitude temperature lapse data from ridgeline Automatic Weather Stations above 3,500 m.
3. **Model M5 (Reservoir & Dam Operations)**: Pandoh Dam is a critical national infrastructure asset managed by the Bhakra Beas Management Board (BBMB). Operational gate opening logs and reservoir level records during high-flow episodes are classified.
4. **Model M8 (InSAR & GNSS Geotechnical Displacement)**: Requires sub-centimeter GNSS station feeds and processed PS-InSAR velocity maps from GSI/ISRO.
5. **Model M13 (Multi-Dimensional Socio-Economic Vulnerability)**: Requires ward-level micro-census data and post-disaster household compensation logs from the Kullu District Administration.

---

## 4. Synthetic Fixture Disclaimers & Demarcation

The repository maintains 5 synthetic test fixtures used strictly for software testing and pipeline regression:
- `BENCHMARK_SYNTH_M6_SLOPES` (N=520 synthetic points)
- `BENCHMARK_SYNTH_M7_STORMS` (N=115 synthetic storm episodes)
- `BENCHMARK_SYNTH_M10_CWC_STAGE` (N=850 synthetic stage hydrograph rows)
- `BENCHMARK_SYNTH_M19_PROPAGATION` (N=55 synthetic wave travel times)
- `BENCHMARK_SYNTH_M20_DAMAGE` (N=510 synthetic structural inspection points)

**MANDATORY AUDIT RULE**: These fixtures are classified as **`SYNTHETIC_BENCHMARK_NOT_GROUND_TRUTH`**. They are never conflated with field observations and are completely quarantined from claims of empirical validity.
