# Model M10: River Water-Level & Stage Forecast Engine

## 1. Overview
Model M10 provides multi-horizon river water-level forecasts across the Upper Beas River system (Kullu–Manali, Himachal Pradesh). Operating at key hydrological monitoring reaches (Manali, Patli Kuhal, Kullu, Bhuntar Confluence, Thalout, Pandoh), M10 forecasts stage increments $\Delta h$ across four tactical horizons:
$$\{+30\text{m}, +1\text{h}, +3\text{h}, +6\text{h}\}$$
and categorizes stages against Central Water Commission (CWC) alert levels (`NORMAL_FLOW`, `WARNING_LEVEL`, `DANGER_LEVEL`, `HIGH_FLOOD_LEVEL`).

## 2. Mathematical Formulation
1. **Kinematic Persistence & Momentum**:
   $$\hat{h}_{\text{pers}}(t) = h_0 + \left(\frac{dh}{dt} \cdot t \cdot e^{-t / \tau}\right) + \Delta h_{\text{runoff}}$$
2. **Effective Catchment Runoff Coupling**:
   $$I_{\text{runoff}} = \left(R_{1\text{h}} + 0.6 R_{3\text{h}} + 0.3 R_{6\text{h}}\right) \cdot \left(\frac{\text{SM}_{\text{pct}}}{100}\right)$$
3. **Machine Learning Layer**:
   LightGBM gradient boosted regressors predict the non-linear stage increment conditioned on current stage, rate of rise, antecedent rainfall, soil moisture, and catchment runoff parameters.

## 3. Usage
```python
from ml.flood.m10_water_level.infer import predict

features = {
    "station_id": "CWC_BHUNTAR_01",
    "station_name": "Bhuntar Confluence",
    "latitude": 31.88,
    "longitude": 77.15,
    "elevation_m": 1090.0,
    "current_stage_m": 5.4,
    "rate_of_rise_m_hr": 0.45,
    "rainfall_1h_mm": 28.0,
    "rainfall_3h_mm": 65.0,
    "soil_moisture_pct": 78.0,
    "warning_level_m": 5.0,
    "danger_level_m": 7.0,
    "hfl_m": 9.5,
}

result = predict(features)
print(result["prediction"]["forecasted_stage_m"])
print(result["prediction"]["alert_level"])
```
