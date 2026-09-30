# Model M8 Engineering & Validation Report
**FLOODY SHIELD — Flash Flood Prediction System for Hilly Regions (SIH PS 26192)**  
*AOI: Upper Beas River Basin (Kullu–Manali, Himachal Pradesh)*  
*Module: `ml/landslide/m8_deformation/` | Status: INTERNAL_VALIDATED*

---

## 1. Executive Summary
Model M8 provides ground movement forecasting and slope deformation analysis across the steep vulnerable slopes of the Upper Beas Basin. Combining multi-temporal InSAR line-of-sight velocity telemetry, in-situ tiltmeter/crackmeter observations, antecedent rainfall, and the classical Saito inverse-velocity failure criterion, M8 delivers multi-horizon displacement projections ($+24\text{h}, +72\text{h}, +7\text{d}$) and slope regime classifications (`STABLE`, `LINEAR_CREEP`, `ACCELERATING`, `CRITICAL_FAILURE_IMMINENT`).

## 2. Theoretical Foundations
### 2.1 Kinematic Creep Physics
Displacement increments are modeled through combined primary/secondary creep with sub-linear damping:
$$d(t) = v_0 t + \frac{1}{2} \left(a_0 + F_{\text{hydro}} \cdot 0.005\right) t^{1.8} e^{-0.08 t}$$
where the hydro-mechanical driving force is:
$$F_{\text{hydro}} = R_{72h} \sin(\theta)$$

### 2.2 Saito Inverse Velocity Failure Forecast
When creeping slopes enter tertiary acceleration ($v > 5\text{ mm/day}$ and $a > 0.5\text{ mm/day}^2$), the asymptotic failure law applies:
$$\frac{d}{dt}\left(\frac{1}{v}\right) = -\frac{a}{v^2}$$
Yielding predicted time to failure in hours:
$$t_f = \frac{v}{a} \times 24.0$$

## 3. Empirical Benchmark Results
Evaluated on 1,000 holdout creeping slopes against linear persistence ($d = v_0 \cdot t$):
- **24h Horizon**: MAE 1.139 mm ($R^2 = 0.9634$) vs. Linear 1.405 mm ($R^2 = 0.9427$) — **+18.9% gain**
- **72h Horizon**: MAE 2.054 mm ($R^2 = 0.9859$) vs. Linear 5.378 mm ($R^2 = 0.8988$) — **+61.8% gain**
- **7d Horizon**: MAE 4.673 mm ($R^2 = 0.9904$) vs. Linear 16.924 mm ($R^2 = 0.8653$) — **+72.4% gain**

### Saito Validation Test
Under simulated paroxysmal conditions ($v = 25\text{ mm/day}, a = 3.5\text{ mm/day}^2$):
- Estimated time-to-failure: $171.4\text{ hours}$
- Correctly classified as `CRITICAL_FAILURE_IMMINENT`.

## 4. Artifacts & Registry Provenance
- Artifact Path: `ml/landslide/m8_deformation/m8_deformation_gbdt.joblib`
- SHA-256 Hash: `f82b0c8cc2c30e743e9dceeb0238de92020161ae2192db0e28ebb26bf966ddf6`
- Status: Registered in `reports/model_registry.json` as `INTERNAL_VALIDATED`
