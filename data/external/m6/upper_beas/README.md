# Upper Beas Historical Landslide External Validation Inventory
**FLOODY SHIELD — SIH Problem Statement 26192**  
*Predict • Protect • Preserve*

---

## 1. Directory Structure

```text
data/external/m6/upper_beas/
├── raw/
│   └── kullu_upper_beas_landslides_2023_raw.csv (Immutable source observations)
├── processed/
│   ├── kullu_upper_beas_external_events.csv
│   └── kullu_upper_beas_external_events.geojson
├── provenance/
│   └── provenance_record.json (Authoritative metadata, hashes, license, and provenance audit)
└── README.md (This document)
```

---

## 2. Authoritative Data Sources & Provenance

This dataset compiles verified real-world historical landslide locations from the extreme monsoon cloudburst disasters of July 7–11, 2023 in the Upper Beas Basin (Kullu–Manali corridor):
1. **Geological Survey of India (GSI) Northern Region**:
   - Report Title: *A Preliminary Report on Landslide Studies in Kullu, Banjar, Manali and Anni Sub-Division, Kullu District, Himachal Pradesh*
   - Official Report ID: `M4EGG/C/NR/SU-PHP/2023/46620` (2023)
2. **Himachal Pradesh State Disaster Management Authority (HPSDMA)**:
   - Framework: *42-Point Geoparametric Datasheet for Landslide of Kullu District*
   - Disaster Event: Post Disaster Needs Assessment (PDNA) & DDMA Kullu July 2023 Disaster Reports

---

## 3. Geographic Extent & AOI Verification

- **Catchment Target AOI**: Latitude `31.60°N` to `32.40°N`, Longitude `76.80°E` to `77.45°E`.
- **Observed Inventory Bounds**: Latitude `31.7245°N` to `32.3580°N`, Longitude `77.1259°E` to `77.2250°E`.
- **AOI Overlap**: **20 out of 20 points (100.0%) strictly fall inside the Upper Beas Catchment**.
- **Field Validation**: All records are ground-verified failure locations along the NH-3 Beas River corridor, Parbati-Beas confluence, and Rohtang highway flank.

---

## 4. Immutable File Fingerprint
- **Raw File**: `data/external/m6/upper_beas/raw/kullu_upper_beas_landslides_2023_raw.csv`
- **SHA-256**: `e56c5ecd043eb796dd1a034bf038939b47d1af0ad09b7e61ede3768a294123df`
- **Integrity Rule**: Never modify or overwrite raw source files.
