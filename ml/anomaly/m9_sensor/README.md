# Model M9: IoT Sensor Anomaly Detection

**FLOODY SHIELD — Predict • Protect • Preserve (SIH Problem Statement 26192)**  
*Domain: Sensing & Telemetry Quality Assurance*

---

## 1. Architectural Overview

Model M9 is a hybrid multi-stage anomaly detection engine engineered to safeguard FLOODY SHIELD's downstream hydro-mechanical pipelines (M1, M8, M10, M11) from degraded, drifted, or malicious telemetry.

```
Incoming Stream
      │
      ▼
Stage 1: Deterministic Physics & Range Bounds
      │ (Ceiling breaches, negative values, stuck sensors, rate-of-change spikes)
      ▼
Stage 2: Cross-Sensor Physical Consistency
      │ (Cross-validates rainfall spikes vs. river water level rises)
      ▼
Stage 3: Unsupervised Multivariate Isolation Forest
      │ (Detects multi-variable subspace drift on nominal inliers)
      ▼
Standardized Output: {prediction, confidence, uncertainty, data_quality, status}
```

---

## 2. Key Safeguard: Event vs. Hardware Fault Differentiation

A common failure in naive anomaly detectors is flagging authentic disaster cloudbursts as "outliers":
- **Authentic Severe Storm**: High rainfall rate ($>60\text{ mm/hr}$) + rising river level + saturated soil $\implies$ **VALID EVENT** (data quality preserved).
- **Hardware Glitch**: River water level suddenly jumps $+3\text{m}$ in 15 minutes with zero upstream rainfall $\implies$ **CROSS_SENSOR_INCONSISTENCY** (flagged as anomalous).

---

## 3. Public API

```python
from ml.anomaly.m9_sensor import predict

result = predict(
    features={
        "rainfall_rate_mmh": 12.0,
        "water_level_m": 2.4,
        "soil_moisture_pct": 45.0,
        "tilt_deg": 0.1,
        "pore_pressure_kpa": 3.5,
    },
    recent_history=[...],
)
# Returns typed dictionary matching universal FLOODY SHIELD contract
```
