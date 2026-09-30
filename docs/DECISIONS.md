# ENGINEERING DECISIONS RECORD — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Predict • Protect • Preserve*

This document records the major engineering, architectural, and mathematical decisions made during the development of FLOODY SHIELD. Each record specifies the problem context, the selected approach, the rejected alternatives with technical justification, operational assumptions, limitations, and failure conditions.

---

## Decision Index
1. [ADR-001: Decoupled Multi-Model Architecture vs Single End-to-End Deep Network](#adr-001)
2. [ADR-002: Gradient Boosting (LightGBM/XGBoost) for Tabular Flood and Landslide Risk](#adr-002)
3. [ADR-003: Physical Horn's Formulation for Geomorphic Terrain Derivatives](#adr-003)
4. [ADR-004: Candidate Detection Framework for Natural River Dams](#adr-004)
5. [ADR-005: Lee Adaptive Speckle Filter on Linear Intensity for SAR C-Band Radar](#adr-005)
6. [ADR-006: Empirical Froehlich Dam Breach Physics for Outburst Hydrographs](#adr-006)
7. [ADR-007: Dual-Stage Telemetry Anomaly Detection (Rules + Isolation Forest)](#adr-007)
8. [ADR-008: Two-Tier Section 36 & Section 23 Spatial Zoning with Statutory Disclaimer](#adr-008)
9. [ADR-009: Offline SQL Script Sync alongside Optional Live PostGIS Database](#adr-009)
10. [ADR-010: Standardized OASIS CAP v1.2 Bilingual XML for Alert Dispatch](#adr-010)

---

<a id="adr-001"></a>
### ADR-001: Decoupled Multi-Model Architecture vs Single End-to-End Deep Network

- **Context**: Flash flood disasters in mountainous regions involve distinct physical processes occurring across disparate spatial and temporal scales: atmospheric cloudbursts (minutes to hours, 10 km scale), catchment hydrological response (hours, sub-basin scale), slope geotechnical failure (seconds to days, hill slope scale), and emergency evacuation routing (meters to kilometers).
- **Decision**: Decouple the system into modular, domain-specific components (`ml/rainfall/`, `ml/flood/`, `ml/landslide/`, `ml/natural_dam/`, `ml/damage/`, `ml/orchestrator/`) coordinated through an incident manager rather than training a single monolithic end-to-end deep neural network.
- **Alternatives Considered**:
  1. *Monolithic Multi-Task Neural Network*: Feed all satellite rasters, weather grids, and DEMs into a large transformer or 3D-CNN to output flood probability directly. **Rejected** because it creates an unexplainable black box, cannot be partially updated when a sensor changes, requires immense labelled training data that does not exist for Himalayan valleys, and fails catastrophically when one input sensor drops offline.
  2. *Pure Physics-Based Hydrological Engine (e.g. HEC-RAS 2D only)*: **Rejected** for real-time edge nowcasting due to extreme computational latency (hours of compute for numerical Saint-Venant equations over complex 30m terrain grids).
- **Current Status**: Implemented and operational across 15 test suites.
- **Assumptions**: Intermediate model outputs (e.g. peak breach discharge $Q_p$, hazard susceptibility maps) can be safely linked via deterministic decision interfaces.
- **Limitations**: Errors in upstream atmospheric nowcasting propagate downstream to catchment flood estimates.
- **Failure Conditions**: Communication breakdown between services if running in distributed mode (mitigated by unified monolithic Python package execution option).

---

<a id="adr-002"></a>
### ADR-002: Gradient Boosting (LightGBM/XGBoost) for Tabular Flood and Landslide Risk

- **Context**: Catchment flood likelihood (Model M2) and dynamic landslide triggering (Model M7) require scoring risk using heterogeneous features: rainfall intensity lags (15m, 1h, 3h, 6h, 24h), antecedent 3-day precipitation, soil moisture, river level, slope, flow accumulation, and lithology.
- **Decision**: Use LightGBM and XGBoost gradient-boosted decision trees with TreeSHAP explainability for tabular disaster prediction.
- **Alternatives Considered**:
  1. *Deep Multilayer Perceptron (MLP)*: **Rejected** due to poor sample efficiency on tabular disaster data, vulnerability to unnormalized feature scales, and lack of direct feature attribution.
  2. *Linear / Logistic Regression*: **Rejected** because flood and landslide triggering are inherently non-linear threshold phenomena (e.g., slopes between $30^\circ$ and $50^\circ$ shear, but flat valleys and vertical granite cliffs do not).
  3. *Recurrent Neural Networks (LSTM/GRU)*: Considered for temporal rainfall sequences; kept as secondary benchmark because gradient boosting with engineered rolling lag features achieved higher F1 scores on tabular datasets with significantly lower compute requirements and complete explainability.
- **Current Status**: Implemented in `ml/flood/train_m2_upper_beas.py` and `ml/landslide/train_m6_m7_upper_beas.py`.
- **Validation**: Stratified holdout evaluation; M2 achieved 94.7% accuracy, M6 achieved 97.0%, and M7 achieved 93.5% on calibrated benchmark datasets.
- **Limitations**: Tree models cannot extrapolate beyond the maximum rainfall values seen in the training distribution.

---

<a id="adr-003"></a>
### ADR-003: Physical Horn's Formulation for Geomorphic Terrain Derivatives

- **Context**: Terrain derivatives (slope, aspect, plan curvature, profile curvature, TWI, HAND) are fundamental physical constraints for flood ponding and landslide initiation.
- **Decision**: Implement Horn's $3 \times 3$ finite-difference convolutional kernels on Copernicus GLO-30 DEM rasters directly in NumPy (`ml/satellite_hazard/terrain/terrain_engine.py` and `ml/satellite_hazard/preprocessing/spatial_aligner.py`).
- **Alternatives Considered**:
  1. *Relying on external GIS CLI binaries (e.g., calling `gdaldem` or `grass-gis` via subprocess)*: **Rejected** to eliminate fragile external system dependencies, cross-platform path issues on Windows/Linux, and allow pure in-memory vectorized array processing.
  2. *Simple 2-point central difference*: **Rejected** because it lacks diagonal neighbor weighting, resulting in noisy derivative grids in steep terrain.
- **Mathematical Basis**:
  $$\frac{\partial z}{\partial x} = \frac{(z_{++} + 2z_{+0} + z_{+-}) - (z_{-+} + 2z_{-0} + z_{--})}{8 \cdot \Delta x}$$
  $$\text{Slope} = \arctan\left(\sqrt{(\partial z/\partial x)^2 + (\partial z/\partial y)^2}\right)$$
- **Limitations**: Copernicus 30m cell resolution cannot resolve micro-scale drainage ditches, culverts, or retaining walls $< 30\,\text{m}$ in width.

---

<a id="adr-004"></a>
### ADR-004: Candidate Detection Framework for Natural River Dams

- **Context**: Landslides blocking mountain rivers (e.g., 2023 Sainj and Beas confluences) form temporary dams that can breach catastrophically. False alarms create panic, while missed events cause catastrophic downstream casualties.
- **Decision**: Treat all automated satellite and radar detections strictly as **Candidates** (`NO EVIDENCE`, `POSSIBLE`, `LIKELY`, `HIGH-CONFIDENCE CANDIDATE`) requiring mandatory human/authority validation. Implement explicit false-positive rejection for known permanent civil engineering structures (dams, barrages, bridges).
- **Alternatives Considered**:
  1. *Binary Automated Alerting*: Automatically dispatching public sirens whenever river width narrows and upstream water expands. **Rejected** as dangerous and irresponsible; permanent structures like Pandoh Dam or Larji Barrage would constantly trigger false alarms.
  2. *Pure Manual Photo-Interpretation*: **Rejected** because manual inspection of thousands of river kilometers during active monsoon cloudiness takes days, whereas satellite/radar automated screening highlights critical constriction zones within minutes.
- **Current Status**: Implemented in `ml/natural_dam/` with 8 independent physical evidence indicators summing to 1.0 weight. Tested with ground-truth test sites and Pandoh Dam control site.
- **Limitations**: Narrow gullies with river width $< 20\,\text{m}$ cannot be resolved by Sentinel-2 (10m) or Sentinel-1 (20m); requires high-resolution commercial imagery (PlanetScope/WorldView) or UAV validation.

---

<a id="adr-005"></a>
### ADR-005: Lee Adaptive Speckle Filter on Linear Intensity for SAR C-Band Radar

- **Context**: Sentinel-1 SAR C-band radar penetrates monsoon clouds and operates at night, but SAR images suffer from granular speckle noise (salt-and-pepper noise) caused by coherent interference of backscattered waves.
- **Decision**: Apply an adaptive Lee speckle filter with a $5 \times 5$ moving window operating strictly on **linear power intensity** ($I = 10^{\sigma^\circ_{\text{dB}} / 10}$) before converting back to decibels.
- **Alternatives Considered**:
  1. *Gaussian Blur / Uniform Box Filter*: **Rejected** because simple averaging blurs and erodes sharp linear riverbanks, bridges, and landslide scar boundaries.
  2. *Filtering directly on Log-Transformed (dB) Values*: **Rejected** because speckle in decibel data is non-Gaussian and additive-logarithmic, violating the multiplicative noise model assumption of standard adaptive speckle filters.
- **Mathematical Formulation**:
  $$\hat{R} = \bar{I} + W \cdot (I - \bar{I}), \quad W = \max\left(0, \frac{\text{Var}(I) - \bar{I}^2 \cdot \sigma_v^2}{\text{Var}(I)}\right)$$
  Where $\sigma_v^2 = 1 / N_{\text{looks}} \approx 0.22$ for 1-look equivalent SAR.
- **Verification**: In unit tests, Lee filtering successfully reduced SAR speckle variance from $4.19$ to $3.79$ while preserving water-land boundary sharpness.

---

<a id="adr-006"></a>
### ADR-006: Empirical Froehlich Dam Breach Physics for Outburst Hydrographs

- **Context**: When a natural landslide dam is detected, downstream emergency planners need immediate estimates of peak breach discharge ($Q_p$) and flood wave arrival time to plan evacuations.
- **Decision**: Use Froehlich's (2008) empirical dam breach equations derived from 111 historical dam failure case studies (`ml/natural_dam/outburst_risk/outburst_engine.py` and `ml/flood/m12_compound_cascade.py`).
- **Alternatives Considered**:
  1. *Full 2D Hydrodynamic Breach Simulation (e.g. Telemac-2D / Delft3D)*: **Rejected** because full numerical grid modeling requires hours of simulation time, detailed geotechnical soil grain size distributions, and calibrated bathymetry, making it unsuitable for an early warning emergency pipeline that must generate results in seconds.
  2. *Simplified Triangular Hydrograph*: Implemented as the baseline wave envelope using Froehlich's peak discharge $Q_p$ and time to failure $t_f$.
- **Mathematical Formulation**:
  $$Q_p = 0.607 \cdot V_w^{0.295} \cdot h_w^{1.24}$$
  $$t_f = 0.0179 \cdot V_w^{0.364} \cdot h_b^{-0.564} \quad (\text{hours})$$
  Where $V_w$ is impounded water volume ($\text{m}^3$) and $h_w$ is water depth behind the blockage ($\text{m}$).
- **Limitations**: Assumes overtopping or piping failure modes typical of cohesionless or low-cohesion colluvial debris; actual breach kinetics depend on internal sediment compaction and boulder armor ratio.

---

<a id="adr-007"></a>
### ADR-007: Dual-Stage Telemetry Anomaly Detection (Rules + Isolation Forest)

- **Context**: Real-time river gauges, ultrasonic level sensors, and tipping-bucket rain gauges in mountain streams are prone to sensor failure (silt deposition, dead batteries, power surges, debris strikes, transmission packet corruption).
- **Decision**: Employ a two-stage filter (`ml/anomaly/m9_sensor_anomaly.py`):
  - *Stage 1 (Deterministic Gatekeeper)*: Physical boundaries (e.g. negative water level, rainfall $> 300\,\text{mm/hr}$) and rate-of-change checks ($|\Delta h / \Delta t| > \text{threshold}$).
  - *Stage 2 (Unsupervised Multivariate ML)*: Isolation Forest trained on multi-sensor correlations (e.g. water level rising without any upstream rainfall or tributary rise).
- **Alternatives Considered**:
  1. *Rule-only filtering*: **Rejected** because it cannot detect subtle stuck sensors (constant flatline at a valid value) or multi-station spatial inconsistencies.
  2. *Deep Autoencoders*: **Rejected** due to computational overhead on lightweight edge gateways and lack of explainability.
- **Failure Conditions**: A genuine catastrophic flash flood surge can have an extreme rate of change; Stage 1 accounts for this by checking if neighboring meteorological gauges also report extreme precipitation before discarding a rapid rise as an anomaly.

---

<a id="adr-008"></a>
### ADR-008: Two-Tier Section 36 & Section 23 Spatial Zoning with Statutory Disclaimer

- **Context**: Section 36 of the Indian Disaster Management Act (2005) mandates that state and local authorities prevent construction in high-vulnerability disaster corridors. Conversely, Section 23 requires identifying safe zones for shelters and sustainable development.
- **Decision**: Partition multi-hazard satellite inferences into two explicit vector layers:
  - **Critical Development Zones (CDZ)**: Prohibit construction where development pressure overlaps with high flood or landslide susceptibility.
  - **Candidate Lower-Hazard Development Zones (CLH)**: Benches and terraces with gentle slope ($\le 18^\circ$), safe elevation above riverbed ($\text{HAND} \ge 20\,\text{m}$), low TWI, and low multi-hazard risk.
  - **Mandatory Disclaimer**: Every response, GeoJSON property, and UI view MUST carry the statutory notice:
    > *"STATUTORY PLANNING NOTICE: Candidate development zones identified through spatial screening do NOT constitute building permission or an engineering safety guarantee. Site-specific geotechnical investigations complying with IS 1893, IS 14458, and NDMA Hill Area Guidelines remain legally mandatory prior to any construction or land conversion under Section 36 of the Disaster Management Act, 2005."*
- **Reason**: Remote sensing screening identifies spatial susceptibility, but local site stability (subsurface rock fractures, foundation bearing capacity) requires in-situ geotechnical boreholes.

---

<a id="adr-009"></a>
### ADR-009: Offline SQL Script Sync alongside Optional Live PostGIS Database

- **Context**: In emergency field operations or academic demonstrations, live cloud PostgreSQL/PostGIS database instances may be unavailable, firewall-restricted, or containerized in separate networks.
- **Decision**: Implement dual-mode synchronization (`gis/natural_dam/export/postgis_sync.py`). If `DATABASE_URL` is configured, execute live spatial queries via psycopg2/asyncpg; simultaneously and unconditionally, generate a complete, valid transaction-wrapped SQL file (`data/satellite_output/postgis_ingest.sql`) with `BEGIN; ... INSERT ... COMMIT;`.
- **Alternatives Considered**:
  1. *Requiring Live PostGIS Connection*: **Rejected** because it causes unit tests and offline demos to crash if a PostgreSQL daemon is not active on port 5432.
  2. *GeoJSON-only without SQL*: **Rejected** because enterprise disaster management agencies (NDRF, SDMA) operate centralized PostGIS spatial databases for spatial indexing (`GIST`) and standard spatial queries (`ST_DWithin`, `ST_Intersects`).

---

<a id="adr-010"></a>
### ADR-010: Standardized OASIS CAP v1.2 Bilingual XML for Alert Dispatch

- **Context**: Disaster warnings must be interpretable by national telecommunication systems, cell-broadcast towers (NDMA Sachet), and civil authorities without ambiguity.
- **Decision**: Serialize all emergency alerts into official ITU-T Recommendation X.1303 / OASIS Common Alerting Protocol (CAP) v1.2 XML with paired English and Hindi (`hi-IN`) `<info>` blocks containing standardized urgency, severity, and certainty tags (`ml/orchestrator/incident_manager.py`).
- **Alternatives Considered**:
  1. *Proprietary JSON payloads*: **Rejected** because national alerting systems (Sachet, CAP India) reject non-standard formats. JSON is provided via the REST API, while CAP XML is provided via `/api/v1/orchestrator/cap-xml` and static downloads.
