# Model M1: Extreme Rainfall & Nowcasting Engine

**FLOODY SHIELD — Predict • Protect • Preserve (SIH Problem Statement 26192)**  
*Domain: Hydrometeorology & Convective Cloudburst Prediction*

---

## 1. Architectural Overview

Model M1 forecasts near-term rainfall intensity and cloudburst probability over the Upper Beas Basin across six operational lead times:
$$\Delta t \in \{15\text{ min}, 30\text{ min}, 1\text{ hour}, 3\text{ hours}, 6\text{ hours}, 24\text{ hours}\}$$

```
IMD AWS / GPM IMERG Ingestion
           │
           ▼
M9 IoT Telemetry Sanitization (Rejects negative rates, ceiling breaches, stuck gauges)
           │
           ▼
Feature Engineering (Multi-window accumulations, intensity acceleration, orography)
           │
           ├──► Baseline 1: Pure Persistence (R(t+dt) = R(t))
           ├──► Baseline 2: Convective Exponential Decay
           │
           ▼
Multi-Horizon Gradient Boosted Quantile Regressors (LightGBM)
           │
           ▼
Standardized Output: {prediction, confidence, uncertainty, data_quality, horizon_forecasts}
```

---

## 2. Mathematical Formulation & Orographic Factor

Himalayan terrain strongly modulates convective storm cells. An orographic amplification multiplier $f_{\text{orog}}$ is computed from elevation and slope:
$$f_{\text{orog}} = 1.0 + 0.6 \cdot \left(\frac{Z - Z_{\min}}{Z_{\max} - Z_{\min}}\right) \cdot \sin(\theta_{\text{slope}})$$

Cloudburst risk is classified based on IMD disaster thresholds:
- **EXTREME**: Rain rate $\ge 60\text{ mm/hr}$
- **HIGH**: Rain rate $\ge 35\text{ mm/hr}$
- **MODERATE**: Rain rate $\ge 15\text{ mm/hr}$
- **LOW**: Rain rate $< 15\text{ mm/hr}$

---

## 3. Usage Example

```python
from ml.rainfall.m1_nowcast import predict

output = predict(
    features={
        "rainfall_rate_mmh": 45.0,
        "elevation_m": 1950.0,
        "slope_deg": 22.0,
    },
    rainfall_history=[10.0, 15.0, 25.0, 45.0],
)
print("1h Rain:", output["prediction"]["predicted_rainfall_mm"], "mm")
print("Risk Level:", output["prediction"]["risk_level"])
```
