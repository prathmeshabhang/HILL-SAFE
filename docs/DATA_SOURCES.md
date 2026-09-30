# DATA SOURCES & AUTHORITATIVE INVENTORY — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Ministry of Home Affairs | NDRF & Disaster Management Division*

---

## 1. Authoritative Geospatial & Remote Sensing Inventory

| Source | Provider | Variable | Resolution | Temporal Resolution | Coverage | Access | License | Reliability | Fallback |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Sentinel-2 MSI** | ESA / Copernicus | 12 Multispectral Bands (Visible, Red-Edge, NIR, SWIR), SCL Cloud Mask | $10\,\text{m} - 20\,\text{m}$ | 5 days (constellation) | Global / Indian Himalayas | Copernicus Data Space Ecosystem / CDSE STAC API | CC-BY-4.0 | Authoritative, High Radiometric Quality | Landsat 8/9 OLI ($30\,\text{m}$) |
| **Sentinel-1 SAR** | ESA / Copernicus | C-band Synthetic Aperture Radar (VV, VH, VV/VH Ratio, Coherence) | $10\,\text{m} \times 10\,\text{m}$ | 6–12 days | Global / Indian Himalayas | CDSE API / Planetary Computer STAC | CC-BY-4.0 | All-Weather / Cloud-Penetrating | NISAR / ALOS-2 PALSAR (where open) |
| **Copernicus GLO-30 DEM** | ESA / Airbus | Digital Elevation Model (Terrain surface ASL) | $30\,\text{m}$ | Static (Reference) | Global ($99.9\%$ coverage) | AWS Open Data / CDSE / OpenTopography | CC-BY-4.0 | High Vertical Accuracy ($<4\,\text{m}$) | SRTM GL1 ($30\,\text{m}$) / ALOS AW3D30 |
| **ESA WorldCover** | ESA / VITO | 11 Land Use / Land Cover classes (Tree cover, Shrub, Grass, Built-up, Bare, Water) | $10\,\text{m}$ | Annual (2020, 2021) | Global | ESA WorldCover Portal / AWS S3 | CC-BY-4.0 | High Thematic Accuracy ($>74\%$) | Dynamic World (Near Real-Time 10m) |
| **GPM IMERG Early Run** | NASA / JAXA | Half-hourly precipitation rate ($\text{mm/hr}$) | $0.1^\circ \times 0.1^\circ$ ($\approx 10\,\text{km}$) | 30 minutes (latency $<4\,\text{h}$) | Global ($60^\circ\text{N} - 60^\circ\text{S}$) | NASA Earthdata / CMR API / OPeNDAP | NASA Open Data | Satellite Calibrated Active & Passive Microwave | IMD Gridded Rainfall ($0.25^\circ$) |
| **Bhuvan Landslide Atlas** | ISRO / NRSC | Historical Landslide Inventory & Spatial Susceptibility | 1:50,000 / Sectoral | Periodic Updates | Pan-India Hilly States | ISRO Bhuvan Geo-Portal / WMS | Government of India Open Access | Official National Ground Truth | GSI National Landslide Susceptibility Mapping (NLSM) |
| **CWC Hydrometric Stages** | Central Water Commission (CWC) | River water level ($\text{m}$), Warning Mark, Danger Mark, High Flood Level (HFL) | Station point | Hourly / Bi-hourly (Monsoon) | Official Indian Gauges (Bhuntar, Mandi, Pandoh) | India-WRIS / CWC Flood Forecast Portal | Official GoI Data | Ground Telemetry Ground Truth | Local Ultrasonic IoT River Gauges |
| **OpenStreetMap Infrastructure** | OSM Foundation | Roads (National/State Highways, Village Links), Bridges, Buildings, Hospitals, Schools | Vector (Line, Point, Polygon) | Continuous crowd + official import | Global / Himachal Pradesh | Overpass API / Geofabrik Extracts | ODbL 1.0 | High Urban/Corridor Detail | Survey of India Topo Sheets (where open) |

---

## 2. Satellite Data Ingestion Standards & Preprocessing

### Spectral Bands Standard (Sentinel-2 L2A)
- **Band 2 (Blue)**: $490\,\text{nm}$ ($10\,\text{m}$) — Atmospheric scattering, water body differentiation.
- **Band 3 (Green)**: $560\,\text{nm}$ ($10\,\text{m}$) — Vegetation vigor, water reflectivity.
- **Band 4 (Red)**: $665\,\text{nm}$ ($10\,\text{m}$) — Chlorophyll absorption, soil vs built-up discrimination.
- **Band 8 (NIR)**: $842\,\text{nm}$ ($10\,\text{m}$) — High leaf reflectance, biomass quantification.
- **Band 11 (SWIR-1)**: $1610\,\text{nm}$ ($20\,\text{m}$) — Soil moisture, built-up surfaces, moisture absorption.
- **Band 12 (SWIR-2)**: $2190\,\text{nm}$ ($20\,\text{m}$) — Lithology, burnt area, moisture stress.
- **Scene Classification Layer (SCL)**: $20\,\text{m}$ — Class 3 (Cloud Shadows), Class 8 (Cloud Medium Prob), Class 9 (Cloud High Prob), Class 10 (Thin Cirrus).

### CRS & Spatial Alignment Mandate
All rasters must be geometrically rectified and reprojected to the official UTM projection of the study catchment:
- **Study Catchment**: Upper Beas Basin (Kullu–Manali, HP)
- **Target Coordinate Reference System**: `EPSG:32643` (WGS 84 / UTM Zone 43N)
- **Geographic WGS 84 Reference**: `EPSG:4326` (for GeoJSON / Leaflet outputs)

---

## 3. Data Operational Classification & Provenance Status

To maintain absolute scientific and engineering transparency, every data stream utilized by FLOODY SHIELD is explicitly categorized into one of five operational provenance states:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        DATA PROVENANCE TAXONOMY                            │
├───────────────────┬────────────────────────────────────────────────────────┤
│ STATUS            │ DESCRIPTION & REPOSITORY INSTANCES                     │
├───────────────────┼────────────────────────────────────────────────────────┤
│ REAL              │ Authentic physical observations & spatial geometries:   │
│                   │ • Copernicus GLO-30 DEM elevation rasters              │
│                   │ • OpenStreetMap road network and bridge locations      │
│                   │ • Upper Beas river thalweg and catchment boundaries    │
│                   │ • Physical infrastructure coordinates (Pandoh, Larji)   │
│                   │ • IMD / GPM gridded precipitation data                 │
├───────────────────┼────────────────────────────────────────────────────────┤
│ DERIVED           │ Deterministic physical & mathematical transformations: │
│                   │ • Horn's 3x3 slope, aspect, curvatures (terrain_engine)│
│                   │ • Topographic Wetness Index (TWI) & HAND elevation     │
│                   │ • Satellite indices: NDVI, NDWI, MNDWI, NDBI, NDMI     │
│                   │ • Lee speckle-filtered SAR intensity rasters           │
│                   │ • A* / Dijkstra evacuation route polylines             │
├───────────────────┼────────────────────────────────────────────────────────┤
│ SIMULATED         │ Physical-mathematical scenario generation:             │
│                   │ • Real-time IoT station streams during local dev       │
│                   │   (physically bounded diurnal rainfall + river stage)  │
│                   │ • Froehlich (2008) breach wave arrival timetables      │
│                   │ • Calibrated multi-band satellite scene granules       │
│                   │   (scene_data_generator.py for offline testing)        │
├───────────────────┼────────────────────────────────────────────────────────┤
│ EXPERIMENTAL      │ Benchmark model training labels & candidate detections:│
│                   │ • Historical Upper Beas July 2023 flood/slide labels   │
│                   │   generated via hydrological thresholds for prototype  │
│                   │ • Natural dam candidate scores requiring validation    │
├───────────────────┼────────────────────────────────────────────────────────┤
│ PENDING           │ Awaiting formal inter-agency integration:              │
│                   │ • Direct live API telemetry feeds from CWC telemetered │
│                   │   gauges (Bhuntar, Mandi, Thalout)                     │
│                   │ • Ground-truth field borehole geotechnical shear tests │
│                   │ • Official state cadastral land-ownership boundaries   │
└───────────────────┴────────────────────────────────────────────────────────┘
```

### UI Presentation Rules
In compliance with engineering authenticity, user interfaces (Leaflet map, EOC dashboard, and API payloads) must visibly display the data state badge:
- `[REAL OBSERVATION]` — Live or archive satellite/station observations.
- `[MODEL PREDICTION]` — Inferred hazard scores with attached confidence.
- `[SIMULATION]` — Dam breach scenario hydrographs and routing scenarios.
- `[DEMO DATA]` — Simulated IoT streams used during offline developer demonstration.

---

## 4. Geotechnical In-Situ Instrumentation & Pore-Water Pressure Audit

### Operational Telemetry Schema (`ml/landslide/pore_pressure/sensor.py`)
FLOODY SHIELD defines standardized IoT schemas for field borehole instrumentation:
- **`PiezometerReading`**: Ingests pore-water pressure ($u$ in $\text{kPa}$) from vibrating-wire or silicon-piezoresistive piezometers, complete with depth ($m$), node battery voltage ($V$), sensor temperature ($^\circ\text{C}$), and automated QA flags (`GOOD`, `SUSPECT_SPIKE`, `OUT_OF_RANGE`, `LOW_BATTERY`).
- **`TensiometerReading`**: Ingests unsaturated matric suction ($\psi = u_a - u_w$ in $\text{kPa}$) from ceramic-cup tensiometers.
- **Physical Bounds**: Valid range is strictly $-30.0\,\text{kPa}$ to $+250.0\,\text{kPa}$; maximum plausible hourly rate of change is $25.0\,\text{kPa/hr}$.

### Data Availability & Evidence Classification Table

| Parameter / Stream | Evidence Tier | Source & Measurement Specifics |
|:---|:---|:---|
| **Topography / Elevation** | `REAL` | Copernicus DEM 30m GLO-30 / AW3D30 |
| **Slope & Curvature** | `DERIVED` | 3D finite-difference gradient and second derivatives |
| **Topographic Wetness Index (TWI)** | `DERIVED` | $\ln(a / \tan \beta)$ lateral flow concentration |
| **Short-Term Rainfall (1h)** | `REAL` | IMD automated weather stations / GPM IMERG 0.1° |
| **Antecedent Rainfall (3d)** | `REAL` | 72-hour GPM IMERG precipitation accumulation |
| **Soil Moisture Content** | `PROXY` | Sentinel-2 NDMI / Copernicus SWIR band moisture proxy ($18\% - 90\%$) |
| **Pore-Water Pressure ($u$)** | `MODELLED` | 1D limit-equilibrium transient saturation mechanics ($\text{kPa}$) |
| **Dynamic Pressure Rise ($\Delta u$)** | `MODELLED` | Dynamic storm pressure increase above dry antecedent baseline ($\text{kPa}$) |
| **Matric Suction ($\psi$)** | `MODELLED` | Fredlund & Rahardjo unsaturated suction retention formulation ($\text{kPa}$) |
| **Effective Normal Stress ($\sigma'$)** | `MODELLED` | Terzaghi effective stress principle $\sigma' = \max(\sigma - u, 0.0)$ ($\text{kPa}$) |
| **Factor of Safety ($\text{FoS}$)** | `MODELLED` | 1D infinite slope limit equilibrium ratio (bounded $[0.05, 10.0]$) |
| **Slope Stability Indicator ($\text{SSI}$)** | `MODELLED` | Normalized relative stability index $\frac{\text{FoS}}{1 + \text{FoS}} \in [0.0, 1.0]$ |
| **Field Piezometer Continuous Records** | `UNAVAILABLE` | Continuous in-situ borehole sensor networks currently not installed in catchment |
| **Field Tensiometer Suction Records** | `UNAVAILABLE` | Continuous in-situ suction instrumentation currently not installed in catchment |
| **Laboratory Triaxial Shear Tests** | `UNAVAILABLE` | High-density per-pixel laboratory geotechnical shear strength data ($c', \phi'$) |

> **Statutory Notice**: Direct pore-water pressure validation data are currently unavailable for the Upper Beas catchment. Modelled pore-water pressures and slope stability indicators represent theoretical limit-equilibrium approximations derived from physical principles (Terzaghi, Fredlund) and surface hydrometeorological observations.

---

## 5. Independent External Disaster Validation Datasets

To ensure rigorous external validation without data fabrication, authentic post-disaster government inventories have been ingested and cryptographically fingerprinted:

| Inventory | Target Models | Records | Positive / Control | Spatial Coverage | Source Agencies & Documents | SHA-256 Fingerprint |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Upper Beas Landslide Inventory (2023)** | M6 (Susceptibility) & M7 (Dynamic Trigger) | 20 | 20 Failures / 11 Independent ($>500\,\text{m}$) | Lat $31.72^\circ - 32.36^\circ\text{N}$, Lon $77.12^\circ - 77.23^\circ\text{E}$ | Geological Survey of India (GSI Report M4EGG/C/NR/SU-PHP/2023/46620) & HPSDMA 42-point geoparametric datasheets | `e56c5ecd043eb796dd1a034bf038939b47d1af0ad09b7e61ede3768a294123df` |
| **Upper Beas Flood Inundation Inventory (2023)** | M2 (Flood Occurrence) & M4 (Multimodal U-Net) | 24 | 12 Flooded / 12 Unflooded Controls | Lat $31.637^\circ - 32.355^\circ\text{N}$, Lon $77.108^\circ - 77.398^\circ\text{E}$ | HPSDMA Post-Disaster Needs Assessment 2023, CWC Indus Basin Flood Situation Report, NRSC Flood Maps | `484c7677b5bc072cc944e9ae90670332cb1cba4ed470a0aed89051c44fa2b7cd` |
| **Full-Scene 2D Flood Mask (10m)** | M4 (Multimodal U-Net) | Raster | Pending authoritative release | Upper Beas Single Scene | Copernicus EMS / NRSC Disaster Watch (`PARTIALLY_VALIDATED` via point concordance) | Pending Open GIS Distribution |



