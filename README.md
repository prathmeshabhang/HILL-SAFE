# FLOODY SHIELD — Predict • Protect • Preserve
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Ministry of Home Affairs | National Disaster Response Force (NDRF) & Disaster Management Division*

---

## Project Overview

FLOODY SHIELD is an end-to-end geospatial disaster intelligence platform engineered specifically for flash flood, landslide, and natural dam hazard assessment in steep, complex Himalayan catchments (Study Area: **Upper Beas Basin, Himachal Pradesh**).

The project is built on the core engineering philosophy:
$$\text{"We don't stop at predicting the disaster. We convert prediction into action."}$$

The system transitions across the complete operational continuum:
$$\text{Detect} \longrightarrow \text{Predict} \longrightarrow \text{Locate} \longrightarrow \text{Prioritize} \longrightarrow \text{Route} \longrightarrow \text{Alert} \longrightarrow \text{Evacuate} \longrightarrow \text{Rescue} \longrightarrow \text{Recover}$$

---

## Engineering Authenticity & Transparency

In compliance with rigorous academic and engineering standards, this repository maintains full provenance tracking without fabricated results, synthetic claims of unperformed experiments, or hidden AI abstractions:
* **All reported metrics are code-generated** and verified by automated test suites.
* **All data sources are explicitly tagged** as `REAL`, `DERIVED`, `SIMULATED`, `EXPERIMENTAL`, or `PENDING`.
* **Natural dam detection is formulated as Candidate Detection**, requiring mandatory authority verification rather than claiming unverified automated truth.
* **Section 23 safe zones carry statutory planning notices** under Section 36 of the Indian Disaster Management Act (2005) noting that geotechnical borehole surveys remain legally required prior to construction.

---

## Internal Implementation Map

| Module Category | Status | Components & Description |
| :--- | :---: | :--- |
| **Real Scene Pipeline** | `IMPLEMENTED` | Multi-sensor GeoTIFF ingestion (`B02-B12`, `SCL`, `VV/VH`, `Copernicus DEM`), SCL cloud auditing, Horn's 3D geomorphic derivations, 9-channel PyTorch tensor constructor, parallel 4-branch hazard models, GeoTIFF/GeoJSON export, PostGIS synchronization, and Leaflet map generation. |
| **Natural Dam Detection** | `IMPLEMENTED` | 8-evidence candidate scoring engine, channel narrowing detection, upstream water impoundment volume calculation, Froehlich (2008) breach peak outflow ($Q_p$), downstream risk indicator, and explicit false-positive rejection for Pandoh Dam and Larji Barrage. |
| **Incident Orchestration** | `IMPLEMENTED` | Autonomous incident manager linking breach hydrographs, downstream wave arrival timetables, population exposure calculation, A* mountain bypass evacuation routing around severed NH-3, and ITU-T X.1303 / OASIS bilingual CAP v1.2 XML alerting for NDMA Sachet. |
| **Damage Assessment** | `IMPLEMENTED` | Copernicus EMS European Macro-seismic Scale building damage grading, SAR interferometric coherence loss, lifeline severance calculation, and Rescue Priority Index (RPI) ranking. |
| **Flood & Landslide ML** | `IMPLEMENTED` | Model M2 (Upper Beas Flood XGBoost with isotonic calibration), Model M6 (Static Landslide Susceptibility Random Forest), Model M7 (Dynamic Trigger LightGBM), Model M9 (Dual-Stage Anomaly Gatekeeper). |
| **FastAPI Microservice** | `IMPLEMENTED` | Production API endpoints across `satellite.py`, `natural_dams.py`, `orchestrator.py`, `damage.py`, `nowcast.py`, `telemetry.py`, `alerts.py`, `cascade.py`, `decision.py`. |
| **EOC & GIS Frontends** | `IMPLEMENTED` | Dark-mode interactive EOC Command Center (`backend/app/static/eoc/command_center.html`) and Leaflet multi-layer hazard dashboard (`data/satellite_output/satellite_hazard_dashboard.html`). |
| **PostGIS Spatial Database** | `IMPLEMENTED` | Spatial DDL schema (`schema.sql`) and automated DML generator (`data/satellite_output/postgis_ingest.sql`) with dual-mode live connection support. |
| **Live CWC Telemetry** | `MOCK/SIMULATED` | Simulated physically-bounded telemetry feeds (water stage, rainfall, soil moisture) matching diurnal Himachal monsoon patterns during offline development. |
| **2D Hydrodynamic Breach** | `PLANNED` | Full 2D Saint-Venant hydraulic grid modeling (currently using empirical Froehlich breach physics + 1D kinematic wave travel time for real-time latency). |
| **External Open-Source** | `EXTERNAL` | PyTorch, Scikit-Learn, LightGBM, XGBoost, FastAPI, Shapely, Leaflet.js, Tifffile (all audited with permissive MIT/BSD/Apache-2.0 licenses). |

---

## Architectural Documentation Index

Detailed engineering documentation is maintained in the `docs/` directory:

1. [`docs/DEVELOPMENT_LOG.md`](docs/DEVELOPMENT_LOG.md) — Chronological engineering log recording problems, code changes, reasons, tests, results, known limitations, and next steps.
2. [`docs/DECISIONS.md`](docs/DECISIONS.md) — Architectural Decision Records (ADRs) detailing why methods were chosen, alternatives considered, assumptions, and failure modes.
3. [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) — Exact machine learning configurations, feature sets, train/test splits, evaluation scripts, and code-measured metrics.
4. [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) — Authoritative inventory and operational provenance classification (`REAL`, `DERIVED`, `SIMULATED`, `EXPERIMENTAL`, `PENDING`).
5. [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — Realistic accounting of satellite revisit latencies, cloud masking gaps, DEM resolution bounds, sensor failure modes, and graceful degradation strategies.
6. [`docs/VALIDATION.md`](docs/VALIDATION.md) — Validation methodology, control site evaluation (Pandoh vs Sainj), and comprehensive 94-test regression inventory.

---

## Quickstart & Verification

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/<your-org>/floody-shield.git
cd floody-shield

# Activate Python 3.11 virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Regression Test Suite
Verify that all 94 unit and integration tests pass with zero errors:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### 3. Execute Real-Scene Satellite Hazard Pipeline
Runs the end-to-end mission architecture on calibrated multi-sensor GeoTIFF granules from disk:
```bash
python -m ml.satellite_hazard.real_scene_pipeline
```
Outputs:
* GeoTIFF rasters in `data/satellite_output/`
* Section 36 & Section 23 GeoJSONs in `data/satellite_output/`
* PostGIS ingestion SQL script: `data/satellite_output/postgis_ingest.sql`
* Interactive Leaflet Dashboard: `data/satellite_output/satellite_hazard_dashboard.html`

### 4. Start the FastAPI Production Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Interfaces:
* **Interactive API Docs (Swagger)**: http://localhost:8000/docs
* **EOC Command Center UI**: http://localhost:8000/eoc
* **Health Check**: http://localhost:8000/health

---

## Team Viva & Technical Presentation Defense Points

When explaining FLOODY SHIELD to evaluators, judges, or technical reviewers, emphasize these authentic engineering design points:

1. **Why Decoupled Models instead of a Single Black-Box Neural Network?**
   * Hilly disasters combine independent physical phenomena (atmospheric rainfall nowcasts, catchment hydrology, slope geotechnical failure, and road network accessibility). Decoupling allows updating the landslide model without retraining the atmospheric model, enables partial operation when a sensor fails, and provides explainability through TreeSHAP.
2. **How is Cloud Contamination Handled during the Monsoon?**
   * Sentinel-2 optical imagery is audited using the 20m Scene Classification Layer (SCL classes 3, 8, 9, 10). If clouds exceed 15%, the system automatically fuses all-weather Sentinel-1 C-Band SAR radar, using a Lee adaptive speckle filter on linear power intensity ($I = 10^{\sigma^\circ/10}$) to detect specular delta backscatter water surfaces.
3. **How are False Alarms Avoided in Natural Dam Detection?**
   * The 8-evidence scoring engine cross-examines channel narrowing, upstream lake expansion, downstream reduction, and landslide scar connectivity, while maintaining an explicit database of known permanent civil hydraulic structures (Pandoh Dam, Larji Barrage) to prevent false alerts.
4. **Why Froehlich Breach Equations?**
   * Real-time emergency evacuation planning requires instantaneous peak discharge and travel time estimates ($< 2\,\text{seconds}$). Empirical Froehlich (2008) physics provides mathematically calibrated estimates from 111 historical breach cases, enabling rapid wave arrival timetables before running computationally intensive 2D hydrodynamic solvers.
5. **What is the Legal Significance of Section 36 & Section 23?**
   * Under the Indian Disaster Management Act (2005), Section 36 mandates restricting development in hazard zones, while Section 23 guides safe shelter siting. FLOODY SHIELD partitions multi-hazard risk into Critical Development Zones and Candidate Safe Zones, accompanied by mandatory statutory planning notices.
