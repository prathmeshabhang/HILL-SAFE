# Model M12: Hazard Cascade & Landslide Dam Breach Engine

## 1. Overview
Model M12 simulates multi-hazard cascading disasters in steep Himalayan terrain:
$$\text{Cloudburst} \longrightarrow \text{Landslide} \longrightarrow \text{River Damming} \longrightarrow \text{Lake Impoundment} \longrightarrow \text{Overtopping Breach} \longrightarrow \text{Outburst Flood Wave}$$

## 2. Mathematical Formulations
1. **Froehlich (2008) Peak Outflow**:
   $$Q_p = 0.607 \cdot V_w^{0.295} \cdot H_d^{1.24}$$
2. **Froehlich Breach Formation Time**:
   $$t_f = 0.0177 \cdot \sqrt{\frac{V_w}{g H_d^2}} \quad (\text{hours})$$
3. **Costa (1985) Potential Energy Outflow Envelope**:
   $$Q_p = 0.00013 \cdot (\gamma_w V_w H_d)^{0.60}$$
4. **Downstream Reach Attenuation**:
   $$Q(x) = Q_{\text{base}} + Q_p \cdot e^{-0.024 x}$$
   $$h_{\text{surge}}(x) = \left(\frac{Q(x) \cdot n}{W \cdot \sqrt{S}}\right)^{0.60}$$

## 3. Usage
```python
from ml.flood.m12_cascade.infer import predict

features = {
    "dam_location": "Larji_Sainj_Confluence",
    "dam_height_m": 35.0,
    "impounded_volume_m3": 8_500_000.0,
    "normal_river_discharge_m3s": 450.0,
}

result = predict(features)
print(result["prediction"]["peak_outflow_discharge_m3s"])
print(result["prediction"]["cascade_severity"])
print(result["prediction"]["shortest_evacuation_lead_time_min"])
```
