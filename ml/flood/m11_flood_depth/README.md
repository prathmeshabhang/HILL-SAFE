# Model M11: Flood Propagation & Inundation Depth Forecast Engine

## 1. Overview
Model M11 simulates downstream flood wave propagation and calculates point- and reach-scale inundation depths along the Upper Beas River corridor (Palchan $\to$ Manali $\to$ Patli Kuhal $\to$ Kullu $\to$ Bhuntar $\to$ Aut $\to$ Pandoh Dam).

## 2. Mathematical Formulations
1. **Muskingum-Cunge Wave Celerity**:
   $$v = \frac{1}{n} R^{2/3} S^{1/2}$$
   $$c = 1.5 \cdot v \quad (\text{kinematic wave speed})$$
   $$t_{\text{travel}} = \sum_{i=1}^k \frac{L_i}{c_i}$$
2. **HAND (Height Above Nearest Drainage) Inundation Depth**:
   $$d(x, y) = \max\left(0.0, h_{\text{reach}} - \text{HAND}(x, y) - \Delta h_{\text{friction}}\right)$$
3. **Inundation Severity Tiers**:
   - `NO_INUNDATION`: $d < 0.05\text{m}$
   - `SHALLOW_NUISANCE`: $0.05\text{m} \le d < 0.30\text{m}$
   - `MODERATE_FLOODING`: $0.30\text{m} \le d < 1.00\text{m}$
   - `SEVERE_DANGER`: $1.00\text{m} \le d < 2.50\text{m}$
   - `CATASTROPHIC_SUBMERGENCE`: $d \ge 2.50\text{m}$

## 3. Usage
```python
from ml.flood.m11_flood_depth.infer import predict

features = {
    "source_stage_m": 7.2,
    "source_discharge_m3s": 1800.0,
    "target_reach_id": "REACH_03_PATLIKUHAL_KULLU",
    "hand_m": 1.1,
    "distance_to_river_m": 50.0,
    "slope_deg": 5.0,
}

result = predict(features)
print(result["prediction"]["forecasted_depth_m"])
print(result["prediction"]["inundation_severity"])
print(result["prediction"]["flood_wave_arrival_time_min"])
```
