# Model Card: M9 Multi-Stage IoT Sensor Anomaly & Fault Detection Engine
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-hybrid-isolation-forest | Framework: scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M9 |
| **Model Full Name** | Multi-Stage IoT Sensor Anomaly, Fault & Hardware Drift Detector |
| **Algorithm** | Hybrid Tri-Stage: Deterministic Physics + Rolling MAD/Z-Scores + Multivariate Isolation Forest |
| **Artifact Path** | `ml/anomaly/m9_sensor/m9_isolation_forest.joblib` |
| **Artifact SHA-256** | `3eafd43d5c5f5d347758ccfcd37c899a4ccb9d479e19aecd1d1f2606c99bdff4` |
| **Training Pipeline** | [`ml/anomaly/m9_sensor/train.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/anomaly/m9_sensor/train.py) |
| **Inference Interface** | [`ml/anomaly/m9_sensor/infer.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/anomaly/m9_sensor/infer.py) |
| **Validation Script** | [`ml/anomaly/m9_sensor/validation.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/anomaly/m9_sensor/validation.py) |
| **Validation Status** | **`PROTOTYPE_SIMULATED_DATA`** |
| **Benchmark Gap** | Minimum benchmark: 10,000+ real nominal readings + labelled anomalies. Current: 5,000 simulated nominal records (below minimum) + 6 injected synthetic fault archetypes. Deterministic Stage 1 physics rules are robust independently of data scale. Isolation Forest layer requires real sensor deployment logs for research-grade validation. |

---

## 2. Model Purpose & Architectural Design

Model M9 guarantees telemetry data integrity across rugged Himalayan sensor deployments (AWS rain gauges, ultrasonic river gauges, TDR soil probes, MEMS tiltmeters, vibrating-wire piezometers).

The architecture uses a three-tier defense:
1. **Stage 1 (Deterministic Physics)**: Immediate hard rejection of negative values, unphysical extremes ($R > 300\text{ mm/h}$, $W > 25\text{ m}$), frozen/stuck constant readings, and impossible 15-minute rate jumps.
2. **Stage 2 (Statistical & Cross-Sensor Physics)**: Identifies cross-sensor contradictions (e.g., river level surging $+2.5\text{m}$ while antecedent rain is zero).
   - **Crucial Safeguard**: Authentic disaster cloudbursts (extreme rainfall accompanied by surging river level and saturated soil) are verified and preserved as valid events rather than discarded as hardware faults!
3. **Stage 3 (Multivariate Isolation Forest)**: Unsupervised density isolation detecting subtle multi-dimensional drift and sensor recalibration requirements.

---

## 3. Training & Validation Datasets

| Field | Value |
|:------|:------|
| **Dataset ID** | `upper_beas_nominal_iot_telemetry` |
| **Sample Size** | 5,000 nominal catchment telemetry records across 5 core channels. |
| **Contamination Parameter** | 5% ($\nu = 0.05$). |
| **Validation Suite** | 11 multi-hazard scenarios encompassing 5 nominal regimes and 6 injected fault archetypes (negative drift, ceiling breach, frozen float, sudden unphysical surge, cross-sensor anomaly, dry tilt jerk). |

---

## 4. Input Features (5 Telemetry Channels)

1. `rainfall_rate_mmh`: Rain gauge precipitation intensity (mm/h)
2. `water_level_m`: Stream gauge stage height (meters)
3. `soil_moisture_pct`: Volumetric soil water content (%)
4. `tilt_deg`: Slope inclinometer deviation (degrees)
5. `pore_pressure_kpa`: Groundwater piezometric pressure (kPa)

---

## 5. Benchmark Performance

Evaluated on the canonical 11-case benchmark suite:

| Metric | Benchmark Score |
|:-------|:----------------|
| **Accuracy** | **100.0%** (11/11 cases correctly identified) |
| **Precision** | **1.000** |
| **Recall** | **1.000** |
| **F1 Score** | **1.000** |
| **Authentic Storm Spike Preserved** | **YES** (Zero false positives on severe multi-hazard storms) |

---

## 6. Sensor Anomaly Taxonomy

- `NONE`: Verified healthy observation.
- `PHYSICAL_RANGE_VIOLATION`: Value below zero or exceeding basin ceiling.
- `STUCK_SENSOR`: Identical non-zero reading across $\ge 4$ consecutive measurement cycles.
- `UNPHYSICAL_RATE_OF_CHANGE`: Instantaneous delta exceeding hydraulic/meteorological limits.
- `CROSS_SENSOR_INCONSISTENCY`: Unphysical discrepancy between coupled physical processes.
- `MULTIVARIATE_DRIFT`: Uncorrelated drift in joint phase space.

---

## 7. Known Limitations

1. **Cellular Packet Loss**: Burst packet drops can mimic intermittent sensor failure without history caching.
2. **Backwater Hydraulic Surges**: Dam releases or tributary debris blockages downstream can elevate water level without local precipitation; cross-sensor logic requires downstream gate telemetry assimilation for full multi-reach coverage.
