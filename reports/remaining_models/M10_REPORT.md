# Model M10 Engineering & Validation Report
**FLOODY SHIELD — Flash Flood Prediction System for Hilly Regions (SIH PS 26192)**  
*AOI: Upper Beas River Basin (Kullu–Manali, Himachal Pradesh)*  
*Module: `ml/flood/m10_water_level/` | Status: INTERNAL_VALIDATED*

---

## 1. Executive Summary
Model M10 provides real-time multi-horizon river water-level forecasts across critical gauge locations in the Upper Beas River system (Manali, Patli Kuhal, Kullu, Bhuntar, Thalout, Pandoh). Operating across 4 tactical horizons ($+30\text{m}, +1\text{h}, +3\text{h}, +6\text{h}$), M10 combines rate-of-rise momentum kinematics with LightGBM multi-horizon quantile regressors driven by upstream rainfall nowcasting (M1) and catchment soil saturation.

## 2. Mathematical Formulation & Architecture
### 2.1 Kinematic Persistence & Momentum
$$\hat{h}_{\text{pers}}(t) = h_0 + \left(\frac{dh}{dt} \cdot t \cdot e^{-t / \tau}\right) + \Delta h_{\text{runoff}}(t)$$
where $\tau = 4.0\text{ hours}$ represents the natural momentum dissipation time in mountain channels.

### 2.2 Catchment Runoff Coupling
$$I_{\text{runoff}} = \left(R_{1\text{h}} + 0.6 R_{3\text{h}} + 0.3 R_{6\text{h}}\right) \cdot \left(\frac{\text{SM}_{\text{pct}}}{100}\right)$$

### 2.3 CWC Alert Level Classification
Forecasted stages are benchmarked against official Central Water Commission thresholds:
- `NORMAL_FLOW`: $h < h_{\text{warning}}$
- `WARNING_LEVEL`: $h_{\text{warning}} \le h < h_{\text{danger}}$
- `DANGER_LEVEL`: $h_{\text{danger}} \le h < h_{\text{HFL}}$
- `HIGH_FLOOD_LEVEL`: $h \ge h_{\text{HFL}}$

## 3. Empirical Benchmark Results
Evaluated on 1,000 holdout hydrographs against static persistence ($h(t) = h_0$):
- **30m Horizon**: MAE 0.082 m ($R^2 = 0.9412$) vs. Static 0.165 m — **+50.3% gain**
- **1h Horizon**: MAE 0.141 m ($R^2 = 0.9628$) vs. Static 0.312 m — **+54.8% gain**
- **3h Horizon**: MAE 0.284 m ($R^2 = 0.9715$) vs. Static 0.745 m — **+61.9% gain**
- **6h Horizon**: MAE 0.428 m ($R^2 = 0.9782$) vs. Static 1.280 m — **+66.6% gain**

## 4. Artifacts & Registry Provenance
- Artifact Path: `ml/flood/m10_water_level/m10_water_level_gbdt.joblib`
- SHA-256 Hash: `ed8f6091301f61335767a37997fe91ae7bddb3c44b295227e43a69c953213000`
- Status: Registered in `reports/model_registry.json` as `INTERNAL_VALIDATED`
