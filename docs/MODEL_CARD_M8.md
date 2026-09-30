# Model Card: M8 Ground Movement & Slope Deformation Forecast Engine
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-deformation-gbdt | Framework: LightGBM 4.0+ & scikit-learn 1.4 | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M8 |
| **Model Full Name** | Ground Movement & Slope Deformation Forecast Engine |
| **Algorithm** | Kinematic Creep Physics, Saito Inverse Velocity Failure Estimator & Multi-Horizon LightGBM Regressors |
| **Artifact Path** | `ml/landslide/m8_deformation/m8_deformation_gbdt.joblib` |
| **Artifact SHA-256** | `f82b0c8cc2c30e743e9dceeb0238de92020161ae2192db0e28ebb26bf966ddf6` |
| **Training Pipeline** | [`ml/landslide/m8_deformation/train.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/landslide/m8_deformation/train.py) |
| **Inference Interface** | [`ml/landslide/m8_deformation/infer.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/landslide/m8_deformation/infer.py) |
| **Validation Script** | [`ml/landslide/m8_deformation/validation.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/landslide/m8_deformation/validation.py) |
| **Validation Status** | **`PROTOTYPE_SIMULATED_DATA`** |
| **Benchmark Gap** | Minimum benchmark: 50+ real monitored landslide sites with multi-year InSAR/GNSS. Current: 4,000 synthetic-calibrated slope profiles (0 real Sentinel-1 InSAR sites). R² metrics are on simulated holdout. Real Sentinel-1 InSAR stacks + GNSS/extensometer data required for research-grade validation. |

---

## 2. Model Purpose & Semantic Definition

Model M8 forecasts continuous slope displacement increments across 3 planning horizons:
$$\{+24\text{h}, +72\text{h}, +7\text{d}\}$$
and categorizes slope kinematic regimes into:
- `STABLE` ($v < 1.0\text{ mm/day}, a \le 0.1\text{ mm/day}^2$)
- `LINEAR_CREEP` ($1.0 \le v \le 5.0\text{ mm/day}$)
- `ACCELERATING` ($v > 5.0\text{ mm/day}, a > 0.5\text{ mm/day}^2$)
- `CRITICAL_FAILURE_IMMINENT` ($v > 15.0\text{ mm/day}, a > 1.5\text{ mm/day}^2$, or Saito estimated failure $\le 72\text{h}$)

---

## 3. Training & Validation Datasets

| Field | Value |
|:------|:------|
| **Dataset ID** | `upper_beas_insar_gnss_creeping_slopes` |
| **Data Nature** | Multi-year creeping slope simulation calibrated against Sentinel-1 C-band InSAR LOS velocities and in-situ borehole tiltmeter / crackmeter responses in Kullu–Manali. |
| **Sample Size** | 4,000 synthetic-calibrated slope profiles (train) and 1,000 holdout profiles (validation). |

---

## 4. Input Features (10 Kinematic & Hydro-Mechanical Predictors)

1. `velocity_mm_day`: Instantaneous surface displacement velocity ($\text{mm}/\text{day}$)
2. `acceleration_mm_day2`: Second-order kinematic acceleration ($d^2d/dt^2$, $\text{mm}/\text{day}^2$)
3. `inverse_velocity_day_mm`: Saito failure proxy ($1/v$, $\text{day}/\text{mm}$)
4. `cumulative_displacement_mm`: Total recorded displacement from baseline (mm)
5. `rainfall_72h_mm`: Antecedent 72-hour precipitation volume (mm)
6. `slope_deg`: Local terrain gradient (degrees)
7. `hydro_driving_index`: Hydro-mechanical destabilization parameter ($R_{72h} \cdot \sin(\theta)$)
8. `insar_coherence`: Satellite radar phase coherence metric ($\gamma \in [0, 1]$)
9. `tilt_rate_deg_day`: In-situ borehole tilt angle change rate ($\text{deg}/\text{day}$)
10. `crack_width_rate_mm_day`: Surface extensional fissure expansion rate ($\text{mm}/\text{day}$)

---

## 5. Benchmark Performance vs. Linear Baseline

Evaluated across 1,000 holdout creeping slopes against standard linear persistence ($d = v_0 \cdot t$):

| Horizon | M8 MAE (mm) | M8 $R^2$ | Linear Baseline MAE (mm) | Linear Baseline $R^2$ | MAE Gain over Baseline |
|:--------|:------------|:---------|:-------------------------|:----------------------|:-----------------------|
| **24h** | 1.139 mm | 0.9634 | 1.405 mm | 0.9427 | **+18.9%** |
| **72h** | 2.054 mm | 0.9859 | 5.378 mm | 0.8988 | **+61.8%** |
| **7d** | 4.673 mm | 0.9904 | 16.924 mm | 0.8653 | **+72.4%** |

### Saito Asymptotic Failure Detection Test
On synthetic tertiary creep acceleration ($v = 25\text{ mm/day}, a = 3.5\text{ mm/day}^2$):
- **Estimated Time-to-Failure**: $171.4\text{ hours}$
- **Identified Regime**: `CRITICAL_FAILURE_IMMINENT`
- **Result**: Successfully triggers critical life-safety early warning.

---

## 6. Known Limitations

1. **InSAR Decorrelation**: In dense forest canopy (e.g. dense pine/deodar zones) or steep north-facing shadows, C-band coherence drops below 0.35, widening uncertainty margins.
2. **Failure Mechanism Scope**: Saito asymptotic inverse velocity applies predominantly to progressive brittle shearing and rotational slides; rapid liquefaction or planar block detachment may fail without extended tertiary warning.
