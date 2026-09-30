# SYSTEM LIMITATIONS & FAILURE MODES — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Predict • Protect • Preserve*

This document provides a realistic, unvarnished accounting of the technical constraints, spatial/temporal resolution limits, environmental failure modes, and graceful degradation strategies within FLOODY SHIELD.

---

## 1. Remote Sensing & Satellite Limitations

### A. Satellite Constellation Revisit Latency
- **Sentinel-2 Optical**: 5-day revisit period under standard constellation orbit ($10\,\text{m}\text{–}20\,\text{m}$ resolution).
- **Sentinel-1 SAR**: 6-to-12-day revisit period ($10\,\text{m} \times 10\,\text{m}$ resolution).
- **Operational Reality**: Flash floods and debris flows in Himalayan catchments frequently initiate, crest, and recede within 2 to 6 hours. Satellite remote sensing is therefore primarily an **antecedent hazard screening, post-event damage mapping, and medium-term impoundment monitoring system**, not a zero-latency real-time flash flood alert trigger. Real-time alerting relies on ground radar, IMD nowcasting, and automated IoT river gauges.

### B. Persistent Cloud Cover & Optical Shadowing
- **Limitation**: During active Southwest Monsoon events (July–August), optical satellite imagery suffers from $> 80\%$ cloud and shadow contamination.
- **Mitigation & Degradation**:
  - The pipeline automatically applies the Sentinel-2 Scene Classification Layer (SCL classes 3, 8, 9, 10) to mask clouds.
  - When cloud cover exceeds 15%, the system degrades confidence and relies on Sentinel-1 C-Band SAR radar, which penetrates clouds and operates in darkness.
  - If SAR data is older than 48 hours, the system issues a `STALE OBSERVATION` advisory and relies primarily on IoT hydrometric telemetry.

### C. Mountain Radar Layover & Shadowing
- **Limitation**: In deep, V-shaped gorges (such as the Larji and Aut gorges on the Beas), side-looking SAR radar suffers from geometric layover on foreslopes and radar shadowing on backslopes.
- **Handling**: `MultiHazardFusionEngine` automatically identifies slopes $> 60^\circ$ and reduces confidence scores by $25\%$ to reflect radar geometry degradation.

### D. Digital Elevation Model (DEM) Resolution
- **Limitation**: The Copernicus GLO-30 DEM has a $30\,\text{m}$ grid cell size.
- **Operational Impact**: Micro-topography features—such as roadside culverts, drainage ditches, concrete flood retaining walls, and river channels $< 25\,\text{m}$ wide—cannot be resolved. Water depth approximations in narrow gullies carry an estimated $\pm 1.5\,\text{m}$ vertical uncertainty.

---

## 2. Machine Learning Model Limitations

### A. Non-Extrapolation of Gradient Boosting Beyond Training Extrema
- **Limitation**: Tree-based models (LightGBM and XGBoost in Models M2 and M7) perform orthogonal axis splits and cannot extrapolate linear trends beyond the maximum rainfall rates observed in the training distribution.
- **Mitigation**: An extreme cloudburst rule override triggers if 1-hour rainfall exceeds $100\,\text{mm/hr}$ (the IMD cloudburst definition), automatically elevating risk to `EXTREME` regardless of model tree prediction.

### B. Synthetic Benchmark Training Labels
- **Limitation**: Historical ground-truth flood inundation masks in remote Himalayan valleys are scarce. Training datasets in the current prototype are calibrated using historical hydrological event reconstructions (Upper Beas July 2023 disaster profile) combined with physical thresholds.
- **Status**: Formally designated as `EXPERIMENTAL BENCHMARK`. Official verification against future automated CWC stage recorders remains ongoing.

### C. Natural Dam Candidate False Alarm vs Miss Trade-off
- **Limitation**: 8-indicator candidate scoring uses empirical weights calibrated against historical blockage events. Natural blockages with minimal impounded water (e.g., dry rubble fills with high subsurface seepage) may produce lower optical/SAR water signatures, leading to potential under-detection until backwater develops.

---

## 3. IoT Sensor & Telemetry Limitations

### A. Harsh Mountain River Environment
- **Limitation**: Ultrasonic and radar river level sensors in Himalayan torrents face physical destruction during boulder-laden flash floods, lightning strikes, severe siltation, and power battery depletion.
- **Mitigation**: Model M9 dual-stage anomaly detection catches sensor failures:
  - Stuck sensor flatline detection.
  - Impossible rate-of-rise threshold ($> 6\,\text{m/hr}$ rejected unless neighboring gauges confirm).
  - Multi-station spatial cross-validation.

### B. Cellular & Satellite Telemetry Blackouts
- **Limitation**: Landslides frequently sever roadside optical fiber lines and topple cellular base stations during cloudburst emergencies.
- **Degradation**: IoT gateway nodes must maintain local offline flash memory logging and fall back to low-power sub-GHz LoRa mesh networks for peer-to-peer relay.

---

## 4. Statutory & Geotechnical Limitations

### A. Section 36 & Section 23 Planning Notice
- **Non-Negotiable Reality**: Satellite multi-hazard mapping provides spatial vulnerability screening across square kilometers. It **does NOT and CANNOT** replace in-situ geotechnical drilling, borehole standard penetration tests (SPT), or structural engineering foundation design complying with Bureau of Indian Standards (IS 1893, IS 14458).
- **Mandatory Policy**: All candidate safe development zones are explicitly tagged with the statutory planning disclaimer in all APIs, GeoJSONs, and dashboard visual interfaces.
