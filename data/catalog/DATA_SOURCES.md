# FLOODY SHIELD — Official Data Sources & Provenance Charter

**FLOODY SHIELD — Predict • Protect • Preserve**  
**AOI**: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Document Version**: 3.1.0 (Phase 2 Real-Data Integration)  
**Date**: 2026-09-21

---

## 1. Provenance & Scientific Integrity Mandate

In accordance with scientific integrity guidelines:
1. **Never label derived, modelled, or synthetic data as observations.**
2. **Never claim live operational access when only a connector interface has been implemented.**
3. **Distinct Status Definitions**:
   - `CONNECTOR_IMPLEMENTED`: Parser, schema validation, network adapter, and mock-fixture tests exist. Live institutional credentials/network connection are pending.
   - `DATA_ACQUIRED`: Real observational or satellite granules have been fetched, verified via cryptographic checksum, and stored locally in immutable storage.
   - `DATA_VALIDATED`: Data has passed complete schema, physical bounds, spatial bounds, temporal ordering, and data quality checks and is certified for scientific evaluation.

---

## 2. Institutional Data Providers & Acquisition Protocols

### 2.1 Hydrometeorological Feeds
- **NASA GPM IMERG**:
  - *Source*: NASA Goddard Earth Sciences Data and Information Services Center (GES DISC).
  - *Access Method*: HTTP API using NASA Earthdata Bearer Token. Managed through `ml/security/api_key_manager.py` (Pool: `earthdata`).
  - *Type*: `DERIVED` (Satellite microwave and infrared precipitation algorithm).
- **India Meteorological Department (IMD)**:
  - *Source*: IMD Hydrometeorological Division & AWS Portal.
  - *Stations*: Kullu, Manali, Bhuntar, Kasol, Banjar, Seobagh.
  - *Type*: `OBSERVATION` (Tipping-bucket / optical rain gauge).
  - *Access Protocol*: Ingested via standard MoES station CSV/API specifications.

### 2.2 River Stage & Discharge
- **Central Water Commission (CWC)**:
  - *Source*: India Water Resources Information System (India-WRIS) / CWC Telemetric Stations.
  - *Gauge Locations*: Manali (headwaters), Patlikuhal (mid-valley), Kullu (urban reach), Bhuntar (Parbati confluence), Thalout (lower basin).
  - *Type*: `OBSERVATION` (Radar water-level sensor, acoustic Doppler current profiler).
  - *Statutory Levels*: Warning, Danger, and Highest Flood Level (HFL) marks.

### 2.3 Earth Observation & Flood Inundation
- **Copernicus Sentinel-1 / Sentinel-2**:
  - *Source*: Copernicus Data Space Ecosystem (CDSE) / European Space Agency.
  - *Type*: `OBSERVATION` (C-band Synthetic Aperture Radar, Multi-Spectral Instrument).
  - *Resolution*: 10 meters ground sampling distance.
  - *Distinction*: Raw satellite acquisitions are `OBSERVATION`. Thresholded water masks produced by automated workflows are `PROXY_FLOOD_MASK`. Only authoritative field-surveyed or NRSC-certified masks are `OBSERVED_FLOOD_MASK`.

### 2.4 Geotechnical & Landslide Inventory
- **Geological Survey of India (GSI)**:
  - *Source*: GSI National Landslide Susceptibility Mapping (NLSM) / Bhukosh Portal.
  - *Type*: `OBSERVATION` (Field-mapped landslide scarps and debris flow tracks).
- **Stable-Slope Controls Requirement**:
  - *Protocol*: Built structures (temples, houses, roads) are **strictly rejected** as evidence of slope stability.
  - *Valid Evidence*: Multi-year absence of deformation verified by Sentinel-1 InSAR coherence + documented geomorphic slope geometry (slope angle, lithology, aspect) observed across 2018–2023.

---

## 3. Data Lake Architecture & Directory Structure

```text
data/
├── catalog/                     <- Master metadata catalog and provenance docs
│   ├── DATA_CATALOG.yaml
│   └── DATA_SOURCES.md
├── manifests/                   <- Cryptographic SHA-256 version manifests
├── raw/                         <- IMMUTABLE raw acquisitions
│   ├── rainfall/
│   ├── river/
│   ├── flood/
│   ├── landslide/
│   ├── deformation/
│   ├── infrastructure/
│   └── post_event/
├── intermediate/                <- Resampled, cropped, and projected layers
├── processed/                   <- Normalized, feature-engineered datasets
├── features/                    <- Model-ready tabular feature arrays
├── labels/                      <- Supervised targets (ground truth)
├── validation/                  <- Chronological & spatial validation splits
├── external_validation/         <- Held-out external test observations
└── synthetic/                   <- Regression test fixtures and smoke scenarios
```

---

## 4. Cryptographic Tracking & Immutability

All files in `data/raw/` are treated as **read-only and immutable**.  
Every dataset processed into `data/processed/` or `data/features/` must be accompanied by a JSON/YAML manifest in `data/manifests/` detailing:
- Dataset ID and Semantic Version.
- Source RAW File SHA-256 Checksum.
- Processing Script Git Commit / Hash.
- Output SHA-256 Checksum.
- Timestamp of Generation (ISO 8601).
