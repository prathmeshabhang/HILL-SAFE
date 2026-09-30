# MODEL CARD: PORE-WATER PRESSURE & SLOPE STABILITY (PWP v1)
**FLOODY SHIELD — Predict • Protect • Preserve**  
*SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data*  
*Model Version*: `1.0.0` (Frozen Release)  
*Status*: **PWP v1 — IMPLEMENTED, UNIT-TESTED, NOT FIELD-VALIDATED**

---

## 1. Purpose & Overview

The **Pore-Water Pressure & Slope Stability Layer (PWP v1)** is a physically grounded simulation module that bridges hydrometeorological forcing (short-term rainfall, antecedent moisture buildup) with geotechnical hillslope stability mechanics.

Rather than predicting landslide occurrence solely via statistical correlations, PWP v1 models the physical chain of hillslope failure:
$$\text{Rainfall Infiltration} \longrightarrow \text{Water Table Rise } (m) \longrightarrow \text{Pore-Water Pressure } (u) \longrightarrow \text{Effective Stress Reduction } (\sigma' = \sigma - u) \longrightarrow \text{Slope Stability Reduction } (\text{FoS} \downarrow) \longrightarrow \text{Landslide Trigger Likelihood}$$

---

## 2. Core Physical Equations & Mechanics

### 2.1 Transient Saturation Ratio ($m$)
$$m(t) = \text{clip}\left( 0.4 \cdot S_{\text{base}} + 0.6 \cdot \frac{I_{\text{eff}} \cdot f_{\text{TWI}}}{n \cdot (1 - S_{\text{base}}) \cdot H}, 0.0, 1.0 \right)$$
- $S_{\text{base}}$: Base surface wetness proxy from Sentinel-2 NDMI ($18\% - 90\%$).
- $I_{\text{eff}} = \min(R_{1h}, K_{\text{sat}}) + 0.25 \cdot R_{3d}$ (net effective water input in mm).
- $f_{\text{TWI}} = \text{clip}(1.0 + 0.08 \cdot (\text{TWI} - 8.0), 0.5, 2.0)$ (lateral flow convergence).
- $n = 0.40$ (porosity), $H = 2.0\,\text{m}$ (mantle depth), $K_{\text{sat}} = 15.0\,\text{mm/h}$.

### 2.2 Hydrostatic Pore-Water Pressure on Slope ($u$)
$$u = m \cdot \gamma_w \cdot H \cdot \cos^2 \theta \quad [\text{kPa}]$$
- $\gamma_w = 9.81\,\text{kN/m}^3$, $\theta$ is slope angle in degrees.
- Dimensional units: $[\text{kN/m}^3] \times [\text{m}] \times [\text{dimensionless}] = [\text{kN/m}^2] = [\text{kPa}]$.

### 2.3 Unsaturated Matric Suction & Apparent Cohesion (*Fredlund & Rahardjo, 1993*)
$$\psi = \psi_{\max} \cdot (1 - m)^2 \quad [\text{kPa}]$$
$$c_{\psi} = \psi \cdot \tan \phi^b \quad [\text{kPa}]$$
- $\psi_{\max} = 50.0\,\text{kPa}$, $\phi^b = 15.0^\circ$. As $m \to 1.0$, $\psi \to 0$ and apparent suction cohesion vanishes.

### 2.4 Terzaghi Effective Normal Stress Principle
$$\sigma' = \max(\sigma - u, 0.0) \quad [\text{kPa}]$$
$$\sigma = \gamma_{\text{total}} \cdot H \cdot \cos^2 \theta \quad [\text{kPa}]$$

### 2.5 Modelled Infinite-Slope Factor of Safety ($\text{FoS}$)
$$\text{FoS} = \frac{c' + c_{\psi} + \sigma' \tan \phi'}{\gamma_{\text{total}} \cdot H \cdot \sin \theta \cdot \cos \theta}$$
- Capped to $[0.05, 10.0]$ to prevent numerical infinities on flat plains ($\theta \to 0^\circ$).

### 2.6 Relative Slope Stability Indicator ($\text{SSI}$)
$$\text{SSI} = \frac{\text{FoS}}{1.0 + \text{FoS}} \in [0.0, 1.0]$$
- $\text{FoS} = 1.0$ (Limit Equilibrium) $\implies \text{SSI} = 0.50$
- $\text{FoS} < 1.0$ (Unstable) $\implies \text{SSI} < 0.50$
- $\text{FoS} > 1.0$ (Stable) $\implies \text{SSI} > 0.50$

---

## 3. Parameter Provenance & Technical Assumptions

| Parameter | Symbol | Nominal Value | Units | Provenance Tier | Selection Rationale & Sensitivity |
|:---|:---:|:---:|:---:|:---:|:---|
| **Effective Cohesion** | $c'$ | $10.0$ | $\text{kPa}$ | `ASSUMED_REPRESENTATIVE` | Weathered Himalayan schist/phyllite colluvium (Martha et al., 2010). High sensitivity. |
| **Effective Friction Angle** | $\phi'$ | $32.0$ | degrees | `ASSUMED_REPRESENTATIVE` | Angular gravelly-sandy slope debris. High sensitivity. |
| **Soil Mantle Depth** | $H$ | $2.0$ | meters | `ASSUMED_REPRESENTATIVE` | Typical regolith depth across Upper Beas valley flanks. Moderate sensitivity. |
| **Bulk Soil Unit Weight** | $\gamma_{\text{bulk}}$ | $18.0$ | $\text{kN/m}^3$ | `ASSUMED_REPRESENTATIVE` | Typical unsaturated colluvium density. Low sensitivity. |
| **Saturated Unit Weight** | $\gamma_{\text{sat}}$ | $20.0$ | $\text{kN/m}^3$ | `ASSUMED_REPRESENTATIVE` | Saturated colluvium density. Low sensitivity. |
| **Water Unit Weight** | $\gamma_w$ | $9.81$ | $\text{kN/m}^3$ | `DERIVED` | Fundamental physical constant at mountain temperatures. |
| **Soil Porosity** | $n$ | $0.40$ | - | `ASSUMED_REPRESENTATIVE` | Loosely consolidated regolith void fraction. Governs infiltration storage. |
| **Hydraulic Conductivity** | $K_{\text{sat}}$ | $15.0$ | $\text{mm/h}$ | `ASSUMED_REPRESENTATIVE` | Silty-sandy loam hydraulic capacity. Caps hourly rainfall infiltration. |
| **Suction Friction Angle** | $\phi^b$ | $15.0$ | degrees | `ASSUMED_REPRESENTATIVE` | Unsaturated shear strength angle (Fredlund & Rahardjo, 1993). |
| **Maximum Matric Suction** | $\psi_{\max}$ | $50.0$ | $\text{kPa}$ | `ASSUMED_REPRESENTATIVE` | Capillary retention suction under residual dry conditions. |

---

## 4. Input Data & Proxies

1. **Terrain Gradient ($\theta$) & TWI**:
   - Source: Copernicus DEM 30m (GLO-30) / JAXA AW3D30.
   - Classification: `DERIVED` via Horn's $3 \times 3$ finite-difference gradient.
2. **Precipitation Forcing ($R_{1h}, R_{3d}$)**:
   - Source: IMD gridded telemetry & GPM IMERG 0.1° satellite estimates.
   - Classification: `REAL` (satellite/gridded precipitation estimation, not in-situ AWS unless local gauge feeds exist).
3. **Surface Wetness ($S_{\text{base}}$)**:
   - Variable: `surface_moisture_proxy_pct` (aliased with `soil_moisture_pct` for backward compatibility).
   - Source: Sentinel-2 NDMI (SWIR band 11 & NIR band 8).
   - Classification: `PROXY` (optical/SWIR surface moisture index, NOT in-situ volumetric soil moisture).

---

## 5. Non-Engineering-Grade Statutory Disclaimer

> **STATUTORY NOTICE**:  
> The Factor of Safety ($\text{FoS}$) and Relative Slope Stability Indicator ($\text{SSI}$) generated by PWP v1 are **modelled geospatial approximations under representative literature assumptions**.  
> They are intended strictly for macro-scale catchment hazard prioritization and early warning decision-support.  
> **THEY DO NOT CONSTITUTE ENGINEERING-GRADE DESIGN FACTORS OF SAFETY AND CANNOT REPLACE ON-SITE BOREHOLE GEOTECHNICAL INVESTIGATIONS.**

---

## 6. Known Unavailable Observations & Data Gaps

- **Direct In-Situ Piezometer Telemetry**: Continuous field vibrating-wire piezometers are currently **UNAVAILABLE** in the Upper Beas catchment.
- **Direct In-Situ Tensiometer Telemetry**: Continuous soil matric suction instrumentation is currently **UNAVAILABLE**.
- **Site-Specific Borehole Triaxial Shear Data**: Direct shear laboratory tests ($c', \phi'$) per spatial pixel are **UNAVAILABLE**.

---

## 7. Validation Status & Machine Learning Impact

- **Unit Test Status**: 30 automated unit tests passing (`tests/test_pore_pressure_stability.py`) verifying Terzaghi effective stress non-negativity, matric suction monotonicity, rainfall response, parameter immutability, sensor QA, and numerical safety (zero NaN/Inf).
- **M7 Experimental Benchmark** (`docs/m7_hydrological_experiment_metrics.json`):
  - On an 80/20 stratified holdout split (10,000 samples, 2,000 test), adding physical features resulted in:
    - ROC-AUC: $0.8697 \to 0.8699$ ($\Delta = +0.0002$)
    - Brier Score: $0.1365 \to 0.1363$ ($\Delta = -0.0003$, improved calibration)
    - F1 Score: $0.8548 \to 0.8570$ ($\Delta = +0.0022$)
    - Physical features captured **4,314 tree splits (41.09%)**, replacing unconstrained geometric interactions with physical stress mechanics.
  - **Scientific Finding**: On the tested controlled split, adding physical features produced a small change in reported metrics. This experiment demonstrates an explainable feature representation, but **does not establish independent generalization or causal superiority. Independent event-based validation is required.**
- **Production Lock**: The production frozen M7 model artifact (`m7_beas_trigger_lgbm.joblib`) remains locked to ensure zero regression in operational workflows.

---

## 8. Reproducibility Information

```pwsh
# Run targeted unit tests:
python -m unittest tests/test_pore_pressure_stability.py

# Run M7 integration experiment:
python -c "from ml.landslide.pore_pressure import run_m7_integration_experiment; res = run_m7_integration_experiment('data/processed/upper_beas/upper_beas_landslide_dataset.csv'); print(res['scientific_finding'])"

# Generate GIS GeoTIFFs:
python -c "from ml.landslide.pore_pressure import generate_spatial_geotiffs; generate_spatial_geotiffs()"
```
