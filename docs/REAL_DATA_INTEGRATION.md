# FLOODY SHIELD — Real-Data Integration & Ingestion Architecture

**FLOODY SHIELD — Predict • Protect • Preserve**  
**AOI**: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**System Version**: 3.1.0 (Phase 2 Real-Data Integration)  
**Date**: 2026-09-21

---

## 1. Executive Summary

Phase 2 transitions the FLOODY SHIELD system from an isolated prototype to an integrated hydrometeorological, geotechnical, and hazard forecasting data architecture. 

In strict adherence to the project charter:
- **No new AI models were created.**
- **No models were retrained or tuned against held-out validation sets.**
- **Synthetic datasets are retained exclusively for deterministic regression tests.**
- **Three distinct evidence states are maintained:**
  1. `CONNECTOR_IMPLEMENTED`
  2. `DATA_ACQUIRED`
  3. `DATA_VALIDATED`

---

## 2. Ingestion Connectors & Adapter Modules

### 2.1 Rainfall Ingestion (`ml/data_ingestion/rainfall/`)
- **NASA GPM IMERG (`gpm_imerg.py`)**:
  - Ingests 30-minute satellite precipitation estimates (`3IMERGHHE_07B`).
  - Strict bounding box filter: $[31.40^\circ\text{N}, 32.45^\circ\text{N}]$ and $[76.80^\circ\text{E}, 77.45^\circ\text{E}]$.
  - Categorized as `DERIVED` (multi-satellite passive microwave and infrared algorithm).
- **IMD AWS In-Situ Network (`imd_aws.py`)**:
  - Connects to IMD station feeds for Kullu, Manali, Bhuntar, Kasol, Banjar, and Seobagh.
  - Tipping-bucket rain gauge telemetry recorded with hourly rainfall rate and physical bounds validation.
  - Categorized as `OBSERVATION`.

### 2.2 River Water-Level & Discharge (`ml/data_ingestion/river/`)
- **CWC River Gauge Adapter (`cwc_river.py`)**:
  - Telemetric water level ($m$) and discharge ($m^3/s$) for 5 Upper Beas stations: Manali, Patlikuhal, Kullu, Bhuntar, Thalout.
  - Dynamically calculates rate of rise ($\Delta H / \Delta t$) and evaluates statutory marks: `Warning Level`, `Danger Level`, and `Highest Flood Level (HFL)`.
  - Quality checks flag flash-flood surge exceedances ($> 4.0\text{ m/h}$).

### 2.3 Satellite Flood Inundation (`ml/data_ingestion/flood/`)
- **SAR & Ground Truth Parser (`satellite_flood.py`)**:
  - Strictly distinguishes `OBSERVED_FLOOD_MASK` (authoritative field-surveyed or NRSC-certified flood extent) from `PROXY_FLOOD_MASK` (heuristic satellite thresholding) and `MODELLED_FLOOD_MASK` (hydraulic simulations).
  - Records sensor metadata, orbit direction, CRS (`EPSG:32643`), resolution (10m), and total inundated area.

### 2.4 Landslides & Stable Controls (`ml/data_ingestion/landslide/`)
- **Landslide Inventory (`inventory_loader.py`)**:
  - Ingests GSI and HPSDMA landslide scarp points and debris flow paths.
  - Enforces spatial de-duplication within 10 meters and source document attribution.
- **M6 Non-Proxy Stable-Slope Framework (`stable_controls.py`)**:
  - **Rejects cultural/built proxies** (temples, buildings, roads, castles) as proof of slope stability.
  - Requires genuine slope geometry ($\text{slope angle} \ge 10^\circ$), lithology, multi-year observation window (2018–2023), and verified absence of failure (e.g. Sentinel-1 InSAR velocity $< 10\text{ mm/yr}$).
- **M7 Storm-Landslide Catalog (`storm_catalog.py`)**:
  - Enforces the **1-Storm = 1-Event** scientific rule.
  - Prevents intra-storm multi-point inflation from artificially biasing statistical power.
  - Requires $\ge 7$ days separation between independent storm events.

### 2.5 Slope Deformation & InSAR (`ml/data_ingestion/deformation/`)
- **InSAR & GNSS Profile Loader (`insar_gnss.py`)**:
  - Ingests multi-temporal line-of-sight (LOS) displacement.
  - Computes velocity ($mm/\text{day}$) and acceleration ($mm/\text{day}^2$) for Saito tertiary creep and pre-failure acceleration analysis in M8.

### 2.6 Exposure, Damage & Impact Timing (`ml/data_ingestion/exposure/`)
- **Infrastructure Assets (`infrastructure.py`)**: Lifeline categorization (bridges, hospitals, roads, substations, water supply). Disallows invented financial valuations (marks as `VALUE_UNAVAILABLE` unless sourced from official tenders).
- **Observed Damage (`damage.py`)**: Strictly separates field-audited disaster damage (`OBSERVED_DAMAGE`) from curve-based fragility estimates (`MODELLED_DAMAGE`).
- **Verified Impact Timestamps (`impact_timestamps.py`)**: Parses historical Himalayan events (e.g. Pareechu 2005, Chamoli 2021) and checks chronological ordering: $\text{Initiation} \le \text{Threshold Crossing} \le \text{Impact Arrival}$.

---

## 3. Real-Time Data Quality & Pre-Inference Input Gate

The shared model input gate enforces:
$$\text{Raw Data} \longrightarrow \text{Schema Validation} \longrightarrow \text{Provenance Check} \longrightarrow \text{Quality Check} \longrightarrow \text{Freshness Check} \longrightarrow \text{Model}$$

- **Freshness Classification**:
  - `FRESH`: Observation age $\le 30\text{ minutes}$.
  - `STALE`: Observation age between 30 and 90 minutes ($\to \text{DEGRADED}$ status, confidence scaled by $0.65\times$).
  - `EXPIRED`: Observation age $> 90\text{ minutes}$ ($\to \text{CRITICAL\_ERROR}$, inference **BLOCKED**).
- **Physical Boundary Checks**: Out-of-bounds coordinates ($< 31.40^\circ\text{N}$ or $> 32.45^\circ\text{N}$) or impossible physical values (e.g. water level $> 25\text{ m}$) trigger immediate blocking.

---

## 4. Distribution Drift Monitoring & Human Authorization Boundary

- **Drift Detection (`ml/monitoring/drift_detector.py`)**:
  - Computes Population Stability Index (PSI) and 2-sample Kolmogorov-Smirnov statistics against baseline training distributions.
  - When $\text{PSI} \ge 0.25$ or $p_{\text{KS}} < 0.001$, flags `DRIFT_DETECTED` and prompts human audit without autonomous model retraining.
- **Human Authorization Boundary (`ml/security/human_authorization.py`)**:
  - Model outputs generate **Decision Support Recommendations**, never autonomous public emergency broadcasts.
  - Release of Common Alerting Protocol (CAP v1.2) messages requires formal cryptographic authorization by certified Incident Commanders (DDMA Kullu, NDRF, HPSDMA).
