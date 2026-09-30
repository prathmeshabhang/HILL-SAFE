# AUDIT RECORD — OPEN-SOURCE ML & GIS ADAPTATION

---

## 1. Candidate Repository Audit Summary

### A. FloodML & Tabular Flood Likelihood (`vgadodia/FloodML`, `yashgamit20/edge-flood-early-warning-system`)
- **License**: MIT / Permissive.
- **Architectural Strength**: Demonstrates effective multi-horizon precipitation lags (`1h, 3h, 6h, 12h, 24h`) mapped against river-level thresholds using gradient boosting.
- **Identified Limitations**:
  1. Often hardcoded to foreign or single plain-basin gauges (not hilly Himalayan terrain).
  2. Frequently omits steep slope dynamics (elevation gradients, flow accumulation).
  3. Lacks Brier score probability calibration.
- **FLOODY SHIELD Adaptation (Model M2)**:
  - Add explicit topographic controls: slope, flow accumulation, distance to stream.
  - Implement isotonic calibration so probabilities map to real event frequencies.
  - Implement SHAP tree explainability to return the primary 3 meteorological/terrain drivers.

### B. Landslide Susceptibility & Trigger Models (`ANUMITHAR/Landslide-warning-system`, `Nethinkarakkat/IoT-ML`)
- **License**: MIT.
- **Architectural Strength**: Uses terrain raster parameters (slope, aspect, curvature, lithology) with Random Forest for spatial susceptibility.
- **Identified Limitations**:
  1. Combines static susceptibility and dynamic rainfall into a single monolithic model, making it impossible to distinguish between a steep dry mountain and an active mudflow.
- **FLOODY SHIELD Adaptation (Models M6 & M7)**:
  - **Decoupled Architecture**:
    - **M6**: Static Susceptibility Index (Terrain + Geology).
    - **M7**: Dynamic Trigger Risk (3-day antecedent rainfall + short-term intensity + soil saturation).
    - Combine: $\text{Current Landslide Risk} = f(\text{Susceptibility}_{\text{M6}}, \text{Trigger}_{\text{M7}})$.

### C. Sensor Telemetry & Quality Anomaly Detection (`M9`)
- **FLOODY SHIELD Bespoke Design**:
  - Dual-stage: Stage 1 = Physical & rate-of-change range filters. Stage 2 = Multi-variate Isolation Forest.
