# MACHINE LEARNING SPECIFICATION — FLOODY SHIELD

---

## 1. Machine Learning Ecosystem Map
FLOODY SHIELD employs specialized, decoupled models rather than a single black-box network:

```
                         FLOODY SHIELD AI
                               │
        ┌──────────────────────┼───────────────────────┐
        │                      │                       │
        ▼                      ▼                       ▼
  ATMOSPHERIC AI          HAZARD AI              VISION AI
        │                      │                       │
        ├─ M1 Rain forecast    ├─ M2 Flood risk        ├─ M4 Flood segmentation (U-Net)
        ├─ M1 Extreme rain     ├─ M6 Susceptibility    ├─ M5 Multi-source mapping
        └─ M9 Sensor anomaly   ├─ M7 Trigger risk      └─ M20 Damage change detection
                               └─ M12 Cascade risk
        │
        └──────────────────────────────────────────────┐
                                                       ▼
                                             DECISION INTELLIGENCE
                                                       │
                                  ┌────────────────────┼─────────────────┐
                                  ▼                    ▼                 ▼
                             M13 Population       M15 Safe-zones    M16 Routing
                             M14 Infrastructure
```

---

## 2. Priority 0 (P0) Model Specifications

### Model M2: Flood Occurrence & Risk
- **Type**: Tabular Supervised Classifier
- **Algorithm**: XGBoost / LightGBM
- **Features (15)**:
  - Atmospheric: `rainfall_15m`, `rainfall_1h`, `rainfall_3h`, `rainfall_6h`, `rainfall_12h`, `rainfall_24h`, `antecedent_rainfall_3d`
  - Soil & Hydrology: `soil_moisture`, `river_level`, `river_level_change`
  - Terrain: `elevation`, `slope`, `flow_accumulation`, `distance_to_stream`, `land_cover_code`
- **Output**: `probability_of_flood` [0, 1], `risk_class` (LOW, MODERATE, HIGH, EXTREME), `shap_feature_importance`
- **Validation**: Stratified temporal/spatial holdout, Brier score calibration $< 0.15$, ROC-AUC $\ge 0.85$.

### Model M6: Landslide Susceptibility Baseline
- **Type**: Spatial Multi-class / Binary Classifier
- **Algorithm**: Random Forest
- **Features**: `slope`, `aspect`, `plan_curvature`, `profile_curvature`, `elevation`, `distance_to_fault`, `distance_to_stream`, `soil_type`, `lithology_code`
- **Output**: Static Susceptibility Index (LOW, MEDIUM, HIGH, VERY_HIGH).

### Model M7: Dynamic Landslide Trigger Model
- **Type**: Temporal Risk Model
- **Algorithm**: LightGBM / XGBoost
- **Features**: Static Susceptibility Score (from M6), `short_term_intensity_1h`, `antecedent_rainfall_3d`, `soil_moisture_saturation_pct`, `temperature`, `tilt_rate_deg_hr`
- **Output**: `trigger_probability`, `current_landslide_risk_level`.

### Model M9: Sensor Anomaly & Quality Detection
- **Type**: Hybrid (Rule-based Gatekeeper + Unsupervised ML)
- **Algorithm**: Isolation Forest + Rolling Z-score
- **Targets**: Stuck sensors, drift, impossible spikes, telemetry dropouts.
