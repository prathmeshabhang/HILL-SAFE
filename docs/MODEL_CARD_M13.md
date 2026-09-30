# Model Card: Model M13 — Vulnerability & Population Exposure Assessment Engine

## 1. Model Details
- **Model Identifier**: `M13`
- **Model Name**: Vulnerability & Population Exposure Assessment Engine
- **Version**: `1.0.0`
- **Release Date**: September 2026
- **Task**: Spatially explicit demographic exposure overlay, seasonal tourist inflation estimation, and multidimensional Social Vulnerability Index (SoVI) synthesis for Upper Beas settlements.
- **Framework**: Scikit-Learn `GradientBoostingRegressor` (100 estimators, learning_rate=0.08, max_depth=4) with calibrated analytical fallback.
- **Repository Location**: `ml/decision/m13_vulnerability/`
- **Artifact**: `ml/decision/m13_vulnerability/m13_vulnerability_gbdt.joblib`

## 2. Intended Use & Domain Scope
- **Primary Domain**: Upper Beas River Catchment, Kullu–Manali corridor, Himachal Pradesh, India.
- **Coverage**: 12 core settlements (Manali Municipal Area, Old Manali, Bahang, Vashisht, Patli Kuhal, Naggar, Kullu Town, Bhuntar, Larji, Aut, Sainj, Banjar).
- **Target Users**: District Disaster Management Authority (DDMA Kullu), NDRF/SDRF evacuation commanders, Emergency Operations Center (EOC).

## 3. Mathematical Formulations
- **Dynamic Seasonal Population**:
  $$P_{\text{total}}(t) = P_{\text{permanent}} \times \left(1 + \kappa_{\text{tourist}} \cdot M(t)\right)$$
- **Social Vulnerability Index (SoVI)**:
  $$V_{\text{social}} = 0.30 \cdot I_{\text{age\_dep}} + 0.25 \cdot I_{\text{kutcha}} + 0.25 \cdot I_{\text{egress}} + 0.20 \cdot \frac{d_{\text{hospital}}}{25\text{ km}}$$
- **Physical Hazard Exposure**:
  $$E_{\text{hazard}} = \min\left(1.0, \max(P_{\text{flood}}, P_{\text{slide}}) + 0.35 \cdot \min(P_{\text{flood}}, P_{\text{slide}}) \cdot \min\left(1.0, \frac{d_{\text{flood}}}{2.5}\right)\right)$$
- **Disaster Risk Formulation**:
  $$V_{\text{composite}} = E_{\text{hazard}} \times \left(\text{scale}_{\text{base}} + 0.24 \cdot V_{\text{social}} + 0.15 \cdot \frac{\log_{10}(P_{\text{total}})}{4.5}\right)$$

## 4. Performance & Validation Metrics
- **$R^2$ Score**: $0.9956$
- **Mean Absolute Error (MAE)**: $0.0086$
- **Demographic Invariant Compliance**: 100% (Exposed population $\le$ Total population; CIs valid).
- **Life Safety Priority Gating**: Zero false negatives on critical high-hazard compound scenarios.

## 5. Provenance & Scientific Integrity
- **Demographic Data**: Census 2011 Kullu District Village & Town Directory.
- **Tourist Dynamics**: Himachal Pradesh Tourism Development Corporation seasonal occupancy statistics.
- **Zero Fabrication**: All settlement demographics are derived from published Census and DDMP datasets.
- **Validation Status**: `CENSUS_GROUNDED_MODELLED_SCENARIOS`
- **Benchmark Gap**: Population census data (Census 2011) meets the real-data requirement. Seasonal tourist multipliers (e.g. 1.8× peak season) are derived from HP Tourism statistics — the conversion from occupancy to population is **MODELLED/ASSUMED**, not directly observed. Training scenarios (3,600 synthetic settlement-month combinations) are model-generated, not real event observations. Upgrade path: annual tourist flow counts at Manali/Kullu + direct post-disaster population surveys.
