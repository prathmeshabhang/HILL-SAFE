# Upper Beas Independent External Flood Inventory (July 2023 Disaster)

## 1. Overview
This dataset contains authentic, independently documented flood inundation points and unflooded reference control locations across the Upper Beas River Basin (Kullu–Manali, Himachal Pradesh) resulting from the extreme precipitation catastrophe of July 8–11, 2023.

## 2. Provenance & Official Sources
- **HPSDMA**: Himachal Pradesh State Disaster Management Authority, *Post-Disaster Needs Assessment (PDNA) Monsoon 2023*
- **CWC**: Central Water Commission, *Flood Situation Report — Indus Basin (July 2023)*
- **NRSC / ISRO**: National Remote Sensing Centre, *Flood Inundation Assessment Maps of Himachal Pradesh (July 2023)*
- **NIDM**: National Institute of Disaster Management, *Himachal Pradesh Monsoon 2023 Flash Flood Report*

## 3. Dataset Integrity
- **Raw File**: `data/external/flood/raw/upper_beas_flood_events_2023_raw.csv`
- **SHA-256**: `484c7677b5bc072cc944e9ae90670332cb1cba4ed470a0aed89051c44fa2b7cd`
- **Total Records**: 24 (12 observed inundated floodplain locations + 12 verified unflooded upland control benches)
- **Spatial CRS**: EPSG:4326 (WGS 84)
- **Geographic Extent**: Latitude 31.637°N to 32.355°N, Longitude 77.108°E to 77.398°E (100% within Upper Beas AOI)

## 4. Attributes
- `event_id`: Unique identifier (`FL_01`–`FL_12` for flood, `NFL_01`–`NFL_12` for unflooded controls)
- `latitude`, `longitude`: WGS 84 decimal degrees
- `location_name`: Documented geographic locality
- `hazard_type`: Specific flood mechanism (e.g., `flash_flood_overtopping`, `floodplain_inundation`, `stable_upland_bench`)
- `inundation_observed`: Binary target ground truth (1 = inundated, 0 = unflooded)
- `event_date`: Observed date of peak inundation
- `peak_depth_m`: Field-reported peak water depth (meters)
- `damage_description`: Documented physical infrastructure/geomorphic impacts
- `source_agency`, `source_document`: Official provenance citations
- `verification_status`: `OFFICIAL_GOV_RECORD`

## 5. Zero-Fabrication Scientific Attestation
No points have been synthesized, shifted, or fabricated. All positive locations correspond to documented damage/inundation sites along the Beas, Parbati, and Sainj river corridors. All control points correspond to stable upland ridges and elevated terraces verified unflooded above High Flood Level.
