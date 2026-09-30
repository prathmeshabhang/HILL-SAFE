# Model M8: Ground Movement & Slope Deformation Forecast Engine

## 1. Overview
Model M8 delivers multi-horizon continuous displacement forecasts and kinematic regime classifications for creeping and unstable slopes in the Upper Beas Basin (Kullu–Manali, Himachal Pradesh). It combines satellite InSAR line-of-sight (LOS) telemetry, in-situ tiltmeter/crackmeter observations, and antecedent rainfall with physics-informed tertiary creep failure prediction.

## 2. Theoretical Foundations
1. **Kinematic Creep Formulation**:
   $$d(t) = v_0 t + \frac{1}{2} a t^2$$
   Modulated by geotechnical damping and rainfall driving force:
   $$F_{\text{hydro}} = R_{72h} \sin(\theta)$$
2. **Saito (1969) / Fukuzono (1985) Inverse Velocity Law**:
   $$\frac{d}{dt}\left(\frac{1}{v}\right) = -\frac{a}{v^2}$$
   As catastrophic tertiary creep approaches failure:
   $$t_f \approx \frac{v}{a}$$
3. **Machine Learning Layer**:
   LightGBM gradient boosted regressors predicting non-linear displacement increments across three operational horizons:
   - $+24\text{ hours}$ (Rapid tactical response)
   - $+72\text{ hours}$ (Evacuation and roadway management)
   - $+7\text{ days}$ (Strategic monitoring)

## 3. Movement Regimes
- `STABLE`: Velocity $< 1.0\text{ mm/day}$, acceleration $\le 0.1\text{ mm/day}^2$.
- `LINEAR_CREEP`: Velocity $1.0\text{--}5.0\text{ mm/day}$, steady secondary creep.
- `ACCELERATING`: Velocity $> 5.0\text{ mm/day}$ or acceleration $> 0.5\text{ mm/day}^2$.
- `CRITICAL_FAILURE_IMMINENT`: Velocity $> 15.0\text{ mm/day}$, acceleration $> 1.5\text{ mm/day}^2$, or Saito estimated failure within $72\text{ hours}$.

## 4. Usage
```python
from ml.landslide.m8_deformation.infer import predict

features = {
    "sensor_or_pixel_id": "PX_SOLANG_03",
    "latitude": 32.31,
    "longitude": 77.15,
    "elevation_m": 2400.0,
    "slope_deg": 38.0,
    "velocity_mm_day": 8.5,
    "acceleration_mm_day2": 1.2,
    "rainfall_72h_mm": 65.0,
    "insar_coherence": 0.88,
}

result = predict(features)
print(result["prediction"]["movement_regime"])
print(result["prediction"]["horizon_forecasts"])
```
