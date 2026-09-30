# SYSTEM SPECIFICATION — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Ministry of Home Affairs | NDRF, DM Division*

---

## 1. System Mission & Operational Mandate
FLOODY SHIELD is a multi-source disaster intelligence platform operating along the full operational pipeline:
$$\text{Detect} \longrightarrow \text{Predict} \longrightarrow \text{Locate} \longrightarrow \text{Prioritize} \longrightarrow \text{Route} \longrightarrow \text{Alert} \longrightarrow \text{Evacuate} \longrightarrow \text{Rescue} \longrightarrow \text{Recover}$$

Core Axiom: **"We don't stop at predicting the disaster. We convert prediction into action."**

---

## 2. Core Functional Requirements
1. **Multi-Source Ingestion**: Ingest satellite rainfall (GPM IMERG), terrain (SRTM/Copernicus DEM), river hydrometry, soil moisture, and IoT ground sensors.
2. **Data Quality & Gating**: Audit sensor latency, missing values, stuck sensors, and drift. Disallow invalid data from reaching inference engines.
3. **Decoupled Model Ecosystem**:
   - **M1**: Extreme Rainfall Nowcasting (pySTEPS optical flow + ensemble).
   - **M2**: Flood Occurrence / Risk (XGBoost/LightGBM with SHAP explainability).
   - **M6**: Landslide Spatial Susceptibility (Random Forest baseline).
   - **M7**: Dynamic Landslide Trigger (LightGBM on antecedent moisture + intensity).
   - **M9**: Dual-Stage Telemetry Anomaly Detection.
4. **Decision Intelligence**:
   - **M13**: Population Exposure calculation (GIS vector overlay).
   - **M14**: Infrastructure Impact mapping (road blockages, compromised bridges).
   - **M15**: Safe-Zone & Shelter multi-criteria allocation.
   - **M16**: Risk-weighted dynamic evacuation routing (A* / Dijkstra).
5. **Safety Guardrails**: Never directly issue sirens or emergency alerts from raw unvalidated ML predictions. Maintain separation between **Risk** and **Confidence**.

---

## 3. Study Area Strategy (Prototype Scope)
- **Country**: India
- **State**: Himachal Pradesh (Beas / Sutlej River Basin)
- **District**: Kangra / Mandi
- **Sub-Catchment Bounding Box**: $76.5^\circ\text{E} - 78.5^\circ\text{E},\; 30.5^\circ\text{N} - 32.0^\circ\text{N}$
- **Coverage**: 5–10 representative hilly villages, 3–5 simulated/physical IoT nodes.
