# Model Card: Model M14 — Infrastructure Damage & Loss Estimation Engine

## 1. Model Details
- **Model Identifier**: `M14`
- **Model Name**: Infrastructure Damage & Loss Estimation Engine
- **Version**: `1.0.0`
- **Release Date**: September 2026
- **Task**: Multi-asset stage-damage vulnerability assessment, hydrodynamic drag and debris impact quantification, direct economic loss modeling (INR Lakhs), and service outage estimation.
- **Framework**: Scikit-Learn `GradientBoostingRegressor` (120 estimators, learning_rate=0.07, max_depth=4) fused with deterministic NDMA/USACE hydrodynamic curves.
- **Repository Location**: `ml/decision/m14_infrastructure_loss/`
- **Artifact**: `ml/decision/m14_infrastructure_loss/m14_infrastructure_gbdt.joblib`

## 2. Intended Use & Domain Scope
- **Primary Domain**: Upper Beas River Basin (Kullu–Manali corridor, Himachal Pradesh).
- **Asset Scope**: Critical lifelines across transportation (NH-3, bridges), energy (hydro substations), healthcare (trauma hospitals), water supply, and commercial horticulture (apple orchards).
- **Target Users**: Himachal Pradesh PWD, HP State Electricity Board (HPSEB), Jal Shakti Vibhag (JSV), DDMA Kullu.

## 3. Vulnerability Functions
- **Mountain Highway (NH-3)**: Pavement scouring ($d \ge 0.2\text{m}$), shoulder erosion, and full sub-base wash-out ($d \ge 0.8\text{m}$, $v > 2.0\text{ m/s}$).
- **Bridges**: Freeboard overtopping, hydrodynamic uplift drag, and boulder/tree battering when water breaches deck level.
- **Substations & Hospitals**: Plinth breach thresholds ($1.2\text{--}1.5\text{m}$) triggering electrical short circuits and emergency isolation.
- **Apple Orchards**: Root submersion and siltation deposition loss curves.

## 4. Performance & Validation Metrics
- **$R^2$ Score**: $0.9886$
- **Mean Absolute Error (MAE)**: $0.0223$
- **Physical Loss Constraints**: 100% compliance (direct loss bounded by $[0, \text{replacement\_value}]$).
- **Damage State Alignment**: Monotonic mapping between damage ratio and Copernicus EMS damage grades.

## 5. Provenance & Scientific Integrity
- **Methodology**: NDMA Guidelines on Management of Flash Floods, USACE Depth-Damage Functions.
- **Asset Register**: HP PWD Road Master Plan, HPSEB generation registers, Kullu District Disaster Management Plan.
- **Zero Fabrication**: All asset locations and valuations correspond to real Beas corridor infrastructure.
- **Validation Status**: `PROTOTYPE_CURVE_BASED`
- **Benchmark Gap**: Minimum benchmark: 100+ real asset-event damage observations. Current: real asset register (14 assets, real valuations) + NDMA/USACE fragility curves; damage ratios are literature-derived, not field-measured from real events. 1,680 training records are synthetic scenario combinations, not observed post-disaster damage records. Upgrade path: HP PWD/HPSEB post-event damage registers post July 2023, ideally 100+ asset-event damage observation records.
