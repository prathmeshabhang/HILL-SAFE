# Model Card — M20: Post-Event Damage Assessment

**Floody Shield — Predict • Protect • Preserve**
AOI: Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India

---

## 1. Model Overview

| Field | Value |
|-------|-------|
| Model ID | M20 |
| Full Name | Post-Event Damage Assessment Engine |
| Domain | Post-Event Assessment |
| Version | 1.0.0 |
| Status | CHANGE_DETECTION_ONLY |
| External Validation | EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE |

## 2. Purpose

M20 assesses **post-event asset-level damage** using:
1. Pre/post satellite imagery change indicators (NDVI, NDWI, SAR coherence)
2. Physics-based proxies from M10 (flood depth, velocity) and M11

The module is an **evidence aggregator**, NOT a supervised damage classifier.  Because no authoritative field-survey damage labels are available for the Upper Beas corridor, outputs are labelled `CHANGE_DETECTED` rather than MINOR/MODERATE/SEVERE.

## 3. Damage Indicators

| Indicator | Threshold | Physical Interpretation |
|-----------|-----------|------------------------|
| ΔNDVI | ≥ 0.10 | Vegetation loss (landslide scarp, flood washout) |
| ΔNDWI | ≥ 0.08 | Water body expansion / flood inundation |
| SAR coherence drop | ≥ 0.15 | Ground surface disturbance |
| Flood depth (M11) | ≥ 0.30 m | Minor structural impact begins |
| Flow velocity drag | ≥ 1.5 m/s | Structural drag pressure |
| Landslide runout | > 5.0 m reaching asset | Physical impact |

## 4. Fusion Architecture

```
NDVI change    (weight 0.12) ─┐
NDWI change    (weight 0.18) ─┤
SAR coherence  (weight 0.30) ─┼→ Weighted fusion → damage_probability [0,1]
Physics proxy  (weight 0.40) ─┘                              │
                                                             ▼
                                              No labels → CHANGE_DETECTED
                                              With labels → MINOR / MODERATE / SEVERE
```

## 5. Input / Output Contract

### Input
```python
M20DamageInput(
    asset_id="BRIDGE_NH3_KULLU",
    hazard_type="FLOOD",
    satellite=SatelliteObservation(
        ndvi_pre=0.65, ndvi_post=0.30,
        ndwi_pre=0.05, ndwi_post=0.60,
        sar_coherence_pre=0.82, sar_coherence_post=0.35,
    ),
    flood_depth_m=2.5,
    flow_velocity_ms=3.5,
    asset_category="bridge",
    data_quality=0.85,
)
```

### Output
```python
M20DamageOutput(
    asset_id="BRIDGE_NH3_KULLU",
    hazard_type="FLOOD",
    change_detected=True,
    damage_class="CHANGE_DETECTED",    # No labels → CHANGE_DETECTED
    damage_probability=0.872,
    damage_fraction=0.833,
    affected_area_m2=697.6,
    evidence_type="CHANGE_DETECTED",
    confidence=0.595,
    external_validation_note="EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE",
)
```

## 6. Damage Classes

| Class | Meaning | When Used |
|-------|---------|-----------|
| `NO_DAMAGE` | No change indicators exceed thresholds | Always available |
| `CHANGE_DETECTED` | Change detected; classification impossible without labels | No field survey labels |
| `MINOR` | < 20% structural loss | Only with supervised labels |
| `MODERATE` | 20–60% structural loss | Only with supervised labels |
| `SEVERE` | > 60% structural loss | Only with supervised labels |

## 7. Evidence Types

| Type | Meaning |
|------|---------|
| `CHANGE_DETECTED` | Remote sensing indicators triggered |
| `MODELLED` | Physics-proxy only (no RS imagery available) |
| `OBSERVED` | Field-surveyed ground truth (requires external data) |

## 8. Validation Status

**EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE**

Required for supervised validation:
- NDMA/HPSDMA post-disaster field survey records
- NRSC multi-temporal damage inventory (Sentinel-2 / Resourcesat-2)
- HP PWD damage assessment register (post July 2023)
- Revenue khasra-wise agricultural loss records

> [!CAUTION]
> Until authoritative ground truth is provided, do NOT interpret `CHANGE_DETECTED` outputs as validated damage classifications.  These are evidence indicators only.

## 9. Limitations

- Remote sensing indicators (NDVI, NDWI) require cloud-free pre/post imagery pairs
- SAR coherence requires temporally matched Sentinel-1 acquisitions (12-day repeat)
- Physics-proxy damage fraction is approximate (linear fragility; no site-specific vulnerability curves for all assets)
- No inventory of exact asset footprints (UTM polygons) is currently integrated

## 10. Life-Safety Architecture

M20 is a **post-event situational awareness** tool.  It does not directly trigger emergency responses.  Damage assessments inform resource prioritization, rescue deployment, and infrastructure repair scheduling through authorized human decision workflows.

---
*Generated: 2026-09-20 | FLOODY SHIELD v3.0 | SIH-26192*
