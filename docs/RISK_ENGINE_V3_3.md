# FLOODY SHIELD v3.3 — Unified Multi-Hazard Risk Fusion Engine

**System**: FLOODY SHIELD  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Module**: `backend/app/services/risk/engine.py`  

---

## 1. Unified Risk State Concept

In complex mountainous terrain, disaster impacts rarely stem from a single hazard in isolation. Heavy rainfall simultaneously triggers hillslope failures, debris flows, riverbed siltation, and damming.

The `UnifiedRiskEngine` synthesizes outputs from upstream model adapters into an authoritative, system-wide `RiskStateModel` and spatial `RiskZoneModel` corridors.

```
      FLOOD SCORE               LANDSLIDE SCORE           CASCADE SCORE
   (M2 Risk + M10/M11)        (M6 Suscept. + M7 Trigger) (M12 Dam Breach Surge)
            │                             │                       │
            └──────────────────────┬──────┴───────────────────────┘
                                   ▼
                   Non-Linear Hazard Fusion Formula:
    Risk = 1.0 - (1 - Flood) * (1 - Landslide) * (1 - Cascade)
                                   │
                                   ▼
                   Exposure & Vulnerability Amplification:
                 Fused = min(1.0, Fused * (1.0 + 0.3 * V_pop))
                                   │
                                   ▼
    [ LOW (<0.30) | MODERATE (0.30-0.60) | HIGH (0.60-0.80) | CRITICAL (>=0.80) ]
```

---

## 2. Mathematical Risk Fusion Formulation

### 2.1 Hazard Co-occurrence Probabilities
Assuming independent trigger interactions at any specific geographical point, the joint probability of at least one hazard exceeding safe operational thresholds is given by:
$$P_{\text{hazard}} = 1 - \prod_{k \in \{\text{flood, landslide, cascade}\}} (1 - S_k)$$

where:
- $S_{\text{flood}} = \max(M2_{\text{prob}}, \min(1.0, M10_{\text{level}} / 8.0))$
- $S_{\text{landslide}} = \max(M7_{\text{prob}}, M6_{\text{prob}})$
- $S_{\text{cascade}} = M12_{\text{prob}}$

### 2.2 Socio-Economic Vulnerability Amplification
To account for exposed population clusters, the raw hazard probability is scaled by the normalized population vulnerability index $V_{\text{pop}} \in [0.0, 1.0]$:
$$R_{\text{composite}} = \min\left(1.0, P_{\text{hazard}} \times (1.0 + \omega_v \cdot V_{\text{pop}})\right)$$
where default calibration weight $\omega_v = 0.30$.

### 2.3 Operational Risk Tiers
- **`LOW`** ($R_{\text{composite}} < 0.30$): Routine monitoring; green advisory.
- **`MODERATE`** ($0.30 \le R_{\text{composite}} < 0.60$): Enhanced surveillance; yellow alert; field teams stand by.
- **`HIGH`** ($0.60 \le R_{\text{composite}} < 0.80$): Orange alert; pre-draft evacuation advisories prepared.
- **`CRITICAL`** ($R_{\text{composite}} \ge 0.80$): Red alert; automated draft creation in `PENDING_APPROVAL`; siren sounding recommended upon Commander authorization.

---

## 3. Strict Provenance Categorization

The Unified Risk State records the lineage of every input variable:
- **`OBSERVED`**: Real-time river gauges, rain gauges, IoT sensors.
- **`PREDICTED`**: Machine-learned probabilities ($M1, M2, M6, M7, M10$).
- **`MODELLED`**: Hydrodynamic water depth, slope stability factor of safety, dam breach peak discharge ($PWP, M11, M12, M19$).
- **`DERIVED`**: Composite risk score, safe-zone selection, evacuation path geometry ($M13, M14, M15, M16, M17, M18$).
