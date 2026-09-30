# Model M17: Early Warning Gating & Evacuation Urgency Recommendation Engine

## 1. Overview
Model M17 is the authoritative decision intelligence and early warning gating apex of the FLOODY SHIELD ecosystem. It integrates physical predictions across rainfall nowcasting (M1), flood risk (M2), landslide trigger (M7), slope movement (M8), water stage (M10), flood depth (M11), cascade outburst waves (M12), population exposure (M13), and lifeline damage (M14) into actionable NDMA/CAP warning levels.

## 2. Gating Architecture
- **Deterministic Life-Safety Overrides**: If river stage $\ge$ Danger Level, or natural dam outburst $Q_p \ge 1000\text{ m}^3/\text{s}$, or ground depth $\ge 1.5\text{m}$, the system triggers mandatory `RED_EVACUATE` without relying on probabilistic ML.
- **Machine Learning Fusion**: For nuanced, compound, pre-threshold states (e.g., heavy rain + rising river + high pore pressure), a GradientBoostingClassifier adjudicates between `GREEN_NORMAL`, `YELLOW_WATCH`, and `ORANGE_ALERT`.
- **Evacuation Urgency Index ($EUI$)**:
  $$EUI = \frac{\text{Required Evacuation Time}}{\text{Flood Arrival Lead Time}}$$
  If $EUI > 1.0$ and arterial road egress is blocked or severed, the system issues `VERTICAL_SHELTER_IN_PLACE` advisories to prevent evacuees from becoming trapped on submerged mountain roads.

## 3. Universal Contract
Every call to `predict(input)` returns:
- `prediction`: reach/settlement ID, alert level (`GREEN_NORMAL`, `YELLOW_WATCH`, `ORANGE_ALERT`, `RED_EVACUATE`), urgency tier, evacuation strategy, lead time, required evacuation time, EUI, actionable recommendations, hazard synthesis, and OASIS CAP v1.2 compliant message payload.
- `confidence`: confidence score.
- `uncertainty`: 80% CI on lead time and required evacuation time.
- `data_quality`: score based on input completeness.
- `model_version`: `1.0.0`
- `applicability`: `UPPER_BEAS_KULLU_MANALI_CORRIDOR`
- `provenance`: `NDMA_CAP_PROTOCOL + CWC_FLOOD_CRITERIA + MULTI_HAZARD_SYNTHESIS`
