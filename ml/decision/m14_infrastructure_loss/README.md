# Model M14: Infrastructure Damage & Loss Estimation Engine

## 1. Overview
Model M14 quantifies physical structural damage, direct economic losses (INR Lakhs), and lifeline service outages for key assets across the Upper Beas corridor (Kullu–Manali, Himachal Pradesh). It models stage-damage relationships, hydrodynamic impact pressure, debris battering loads, and prolonged standing water across roads, bridges, power substations, hospitals, water intakes, and commercial orchards.

## 2. Methodology & Curves
M14 grounds its estimates in NDMA Guidelines on Flash Floods and USACE Depth-Damage Tables adapted for mountain typologies:
- **Highways (NH-3)**: Pavement scour and shoulder erosion triggered at depths $>0.2\text{m}$, escalating to full sub-base wash-out when submerged under high-velocity currents ($v > 2\text{ m/s}$).
- **Bridges**: Soffit freeboard overtopping, hydrodynamic uplift drag, and boulder/debris battering.
- **Power Substations**: Equipment and transformer short-circuiting above plinth height ($1.2\text{m}$).
- **Hospitals**: Backup generator and medical gas damage causing critical emergency isolation.
- **Apple Orchards**: Root suffocation and sediment siltation destroying high-value agricultural yields.

## 3. Direct Economic Loss
$$\text{Direct Loss (INR Lakhs)} = \text{Replacement Value} \times \text{Structural Damage Ratio}$$

## 4. Universal Contract
Every call to `predict(input)` returns:
- `prediction`: asset ID, name, category, damage state (`NEGLIGIBLE_INTACT`, `SLIGHT_DAMAGE`, `MODERATE_DAMAGE`, `EXTENSIVE_DAMAGE`, `COLLAPSED_DESTROYED`), damage ratio, direct loss in Lakhs INR, outage hours, lifeline status, criticality score.
- `confidence`: confidence score.
- `uncertainty`: 80% CI on loss and damage ratio.
- `data_quality`: score based on asset inventory match.
- `model_version`: `1.0.0`
- `applicability`: `UPPER_BEAS_KULLU_MANALI_CORRIDOR`
- `provenance`: `NDMA_FLASH_FLOOD_GUIDELINES + USACE_DEPTH_DAMAGE_TABLES + BEAS_INFRA_INVENTORY`
