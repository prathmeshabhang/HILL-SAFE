# Model M14: Infrastructure Damage & Loss Estimation — Technical Report

## Executive Summary
Model M14 evaluates the physical vulnerability, direct monetary losses (in INR Lakhs), and operational disruption across vital infrastructure assets along the Upper Beas River corridor. By fusing empirical NDMA flash flood guidelines and USACE stage-damage tables with machine learning hydrodynamic regression, M14 delivers actionable loss and passability intelligence to road authorities, power boards, and emergency response teams.

## Asset Typologies & Hydrodynamic Curves
M14 models specific damage mechanics tailored to steep Himalayan mountain valleys:
1. **Mountain Roads (NH-3 Corridor)**: Evaluates asphalt peeling, shoulder erosion, and sub-base failure as flow velocity and flood depth breach critical shear thresholds.
2. **Suspension & Bailey Bridges**: Evaluates deck clearance (freeboard), hydrodynamic buoyancy forces, and impact loads from flood-borne debris (boulders, uprooted pine trunks).
3. **Power Generating & Distribution Substations**: High-voltage transformers (e.g., Larji 126MW) sustain severe catastrophic damage when water submerges plinths ($>1.2\text{m}$).
4. **Hospitals & Lifeline Centers**: Evaluates functional downtime and isolation of emergency trauma centers (Kullu Regional Hospital).
5. **Commercial Apple Orchards**: High-value alluvial river terraces (Patli Kuhal) subject to sediment burial and root suffocation.

## Training & Model Performance
- **Model**: Scikit-Learn GradientBoostingRegressor (120 trees, learning_rate=0.07, max_depth=4).
- **Validation Dataset**: 1,680 asset inundation and velocity combinations across the Upper Beas reach network.
- **Metrics**:
  - $R^2$: $0.9886$
  - MAE: $0.0223$
  - Loss Bound Integrity: 100% compliant (no negative losses, no loss exceeding replacement cost).

## Universal Contract Compliance
Every prediction returns:
1. `prediction`: Asset ID, name, category, damage state (`NEGLIGIBLE_INTACT` to `COLLAPSED_DESTROYED`), damage ratio, direct loss (INR Lakhs), outage hours, lifeline status (`OPERATIONAL`, `PARTIALLY_DEGRADED`, `IMPASSABLE_CUT_OFF`, `STRUCTURALLY_FAILED`), criticality score, and rationale.
2. `confidence`: $0.88$
3. `uncertainty`: 80% CI on monetary loss and damage ratio.
4. `data_quality`: $0.93\text{--}0.95$.
5. `model_version`: `1.0.0`
6. `applicability`: `UPPER_BEAS_KULLU_MANALI_CORRIDOR`
7. `provenance`: `NDMA_FLASH_FLOOD_GUIDELINES + USACE_DEPTH_DAMAGE_TABLES + BEAS_INFRA_INVENTORY`
