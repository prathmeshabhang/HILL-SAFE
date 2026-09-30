# Model M13: Vulnerability & Population Exposure Assessment — Technical Report

## Executive Summary
Model M13 is the human vulnerability and demographic exposure intelligence engine of FLOODY SHIELD. It translates physical hazard outputs from hydrological and geotechnical models (M1, M2, M4, M6, M7, M8, M10, M11, M12) into life-safety priority rankings and at-risk population figures for disaster response managers.

## Demographic Baseline & Tourist Influx Dynamics
The Upper Beas valley experiences extreme population surges during tourist seasons. Using Census 2011 baseline data paired with Himachal Pradesh Tourism statistics, M13 accounts for:
- 12 major registered settlements from Palchan/Manali down to Aut/Pandoh.
- Seasonal tourist multipliers ranging from 0.40x (August monsoon lull) to 1.80x (May/June summer peak) and 1.40x (October Kullu Dussehra).
- Social vulnerability factors: age dependency (children & elderly), kutcha/timber-mud construction ratio, steep egress impedance, and distance to emergency healthcare.

## Training & Model Performance
- **Algorithm**: Scikit-Learn GradientBoostingRegressor (100 trees, learning_rate=0.08, max_depth=4).
- **Validation Dataset**: 3,600 multi-hazard combinations across all 12 settlements and 12 calendar months.
- **Validation Metrics**:
  - $R^2$: $0.9956$
  - MAE: $0.0086$
  - Invariant Verification: 100% compliant across zero-hazard baseline and catastrophic compound flood/landslide tests.

## Model Contract Compliance
Every prediction returns:
1. `prediction`: Settlement breakdown, permanent/tourist populations, SoVI, physical exposure, composite score, tier (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), life-safety priority (Priority 1 to Priority 4), and rationale.
2. `confidence`: $0.89$
3. `uncertainty`: 80% CI on exposed population ($\pm 15\%$) and composite score ($\pm 0.06$).
4. `data_quality`: $0.92\text{--}0.96$ based on demographic register completeness.
5. `model_version`: `1.0.0`
6. `applicability`: `UPPER_BEAS_KULLU_MANALI_CORRIDOR`
7. `provenance`: `CENSUS_2011_KULLU + HP_TOURISM_REGISTRY + WORLDPOP_GRID`
