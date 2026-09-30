# Model M11 Engineering & Validation Report
**FLOODY SHIELD — Flash Flood Prediction System for Hilly Regions (SIH PS 26192)**  
*AOI: Upper Beas River Basin (Kullu–Manali, Himachal Pradesh)*  
*Module: `ml/flood/m11_flood_depth/` | Status: INTERNAL_VALIDATED*

---

## 1. Executive Summary
Model M11 simulates downstream flood wave propagation along the Upper Beas River and forecasts localized inundation depths on floodplain communities. Operating along 6 distinct river reaches (Palchan to Pandoh Dam), M11 computes wave celerity, arrival times, peak attenuation, and 1D-HAND inundation depths ($d_{\text{flood}}$ in meters).

## 2. Mathematical Formulation & Architecture
### 2.1 Muskingum-Cunge Wave Celerity
$$c = 1.5 \cdot v = 1.5 \cdot \left(\frac{1}{n} R^{2/3} S^{1/2}\right)$$
yielding downstream wave front travel times:
$$t_{\text{travel}} = \sum_{i=1}^k \frac{L_i}{c_i}$$

### 2.2 Localized Inundation Depth via Copernicus DEM HAND
$$d_{\text{flood}}(x, y) = \max\left(0.0, h_{\text{reach}} - \text{HAND}(x, y) - \Delta h_{\text{friction}}\right)$$

### 2.3 Reach Corridor Taxonomy
1. `REACH_01_PALCHAN_MANALI` ($11.0\text{ km}$, slope $0.024$)
2. `REACH_02_MANALI_PATLIKUHAL` ($14.0\text{ km}$, slope $0.015$)
3. `REACH_03_PATLIKUHAL_KULLU` ($18.0\text{ km}$, slope $0.010$)
4. `REACH_04_KULLU_BHUNTAR` ($10.0\text{ km}$, slope $0.008$)
5. `REACH_05_BHUNTAR_AUT` ($22.0\text{ km}$, slope $0.006$)
6. `REACH_06_AUT_PANDOH` ($15.0\text{ km}$, slope $0.004$)

## 3. Empirical Benchmark Results
Evaluated across 1,000 holdout floodplain locations:
- **MAE**: 0.061 m vs. Linear Baseline 0.128 m (**+52.3% improvement**)
- **$R^2$ Score**: 0.9989
- **Disaster Surge Verification**: Submergence of $7.29\text{m}$ correctly predicted for $8.5\text{m}$ crest at Patli Kuhal/Akhara Bazar.

## 4. Artifacts & Registry Provenance
- Artifact Path: `ml/flood/m11_flood_depth/m11_depth_gbdt.joblib`
- SHA-256 Hash: `b93259c1fa7a9fbf450b9e4a129a62f1c78df68ff251f5c2b19ae7e1e3d138df`
- Status: Registered in `reports/model_registry.json` as `INTERNAL_VALIDATED`
