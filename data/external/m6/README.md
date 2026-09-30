# External Landslide Datasets for Model M6 Independent Validation
**FLOODY SHIELD — SIH Problem Statement 26192**  
*Predict • Protect • Preserve*

This directory is the dedicated intake location for **independent, real-world historical landslide inventory datasets** used to externally validate the frozen **Model M6 Random Forest Landslide Susceptibility Model**.

---

## 1. Scientific Principles & Strict Guardrails

1. **Frozen Model Guarantee**: Model M6 (`ml/landslide/m6_beas_susceptibility_rf.joblib`) is NEVER retrained, tuned, or calibrated on external data.
2. **Zero Fabrication**: No synthetic points or pseudo-labels are accepted as external validation. If real observations are absent, the pipeline strictly reports:
   ```text
   VALIDATION NOT POSSIBLE WITH CURRENT EXTERNAL DATA
   ```
3. **Training Independence**: The Upper Beas M6 model was trained on catchment geomorphic characteristics. External validation requires real, independently cataloged historical landslide events.

---

## 2. Supported Authoritative Data Sources

The intake pipeline automatically recognizes and parses datasets from the following four authoritative government and scientific inventories:

### A. Zenodo Himalayan 2023 Inventory (Recommended for July 2023 Event)
- **Title**: *V1: Landslide Inventory - Anthropogenic Activities and the Two-Fold Surge in Landslides During the 2023 July-August Extreme Rainfall in the Lesser Himalayas*
- **Authors**: Himanshu et al. (published in *Catena*, 2025)
- **DOI**: [10.5281/zenodo.10492992](https://doi.org/10.5281/zenodo.10492992)
- **Coverage**: Himachal Pradesh Lesser Himalayas (including Solan, Mandi, Kullu corridors)
- **Format**: `landslides.zip` containing ESRI Shapefile (`.shp`, `.shx`, `.dbf`, `.prj`) or exported GeoJSON
- **Placement**: Extract files into `data/external/m6/zenodo_2023/` or place `zenodo_himachal_2023.geojson` in this directory.

### B. ISRO / NRSC Landslide Atlas of India
- **Publisher**: National Remote Sensing Centre (NRSC), Indian Space Research Organisation (ISRO)
- **Portal**: [ISRO Bhuvan Disaster Services](https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=landslide)
- **Scope**: ~80,000 pan-India mapped landslides (1998–2022) with seasonal, event-based, and route-wise layers.
- **Access**: Download WFS/Shapefile extract for Himachal Pradesh / Kullu Sector.
- **Placement**: Place `.shp` or `.geojson` file as `data/external/m6/isro_nrsc_landslides.geojson`.

### C. NASA Global Landslide Catalog (GLC) / COOLR
- **Publisher**: NASA Goddard Space Flight Center (D. Kirschbaum et al.)
- **Portal**: [NASA Open Data Catalog](https://catalog.data.gov/dataset/global-landslide-catalog-export) / [NASA COOLR](https://gpm.nasa.gov/landslides/data.html)
- **Citation**: Kirschbaum et al. (2010, 2015)
- **Format**: CSV export (`Global_Landslide_Catalog_Export.csv`) or GeoJSON
- **Placement**: Place in `data/external/m6/nasa_glc_himachal.csv` or `data/external/m6/nasa_glc.geojson`.

### D. Geological Survey of India (GSI) NLSM Inventory
- **Publisher**: Geological Survey of India (GSI), Ministry of Mines
- **Portal**: [GSI Bhukosh Geo-Portal](https://bhukosh.gsi.gov.in/)
- **Scope**: National Landslide Susceptibility Mapping (NLSM) 1:50,000 spatial polygons and field records.
- **Placement**: Place in `data/external/m6/gsi_nlsm_landslides.shp` or `.geojson`.

---

## 3. Accepted File Formats & Schemas

The intake loader ([`ml/validation/external/dataset_loader.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/validation/external/dataset_loader.py)) accepts:

1. **GeoJSON (`.geojson` / `.json`)**:
   - Must contain Point, MultiPoint, Polygon, or MultiPolygon features.
   - Recommended CRS: `EPSG:4326` (WGS84 lon/lat).
2. **ESRI Shapefile (`.shp`)**:
   - Must include companion `.shx`, `.dbf`, and `.prj` files.
3. **CSV (`.csv`)**:
   - Must contain latitude and longitude columns (e.g. `latitude`/`longitude`, `lat`/`lon`, `y`/`x`).
   - Optional fields: `event_date`, `source`, `confidence`, `landslide_type`.

---

## 4. Area of Interest (AOI) Bounds

External observations will be evaluated for spatial intersection with the Upper Beas study domain:
- **Latitude**: $31.40^\circ\text{N} - 32.45^\circ\text{N}$ (core catchment: $31.60^\circ\text{N} - 32.40^\circ\text{N}$)
- **Longitude**: $76.80^\circ\text{E} - 77.45^\circ\text{E}$ (core catchment: $76.80^\circ\text{E} - 77.45^\circ\text{E}$)
- **Target Projected Metric CRS**: `EPSG:32643` (UTM Zone 43N)

---

## 5. How to Run External Validation

Once an external file is placed in this directory:
```bash
# Execute external validation pipeline
python -m ml.validation.external.evaluate_m6
```

If no external file is present, the pipeline safely outputs:
```text
STATUS: VALIDATION NOT POSSIBLE WITH CURRENT EXTERNAL DATA
MISSING: Real external landslide inventory in data/external/m6/
```
