# M20 — Post-Event Damage Assessment: Technical Report

**FLOODY SHIELD | SIH-26192 | Remaining Models Series**

---

## Summary

M20 is the post-event situational awareness module.  It fuses pre/post satellite change indicators (NDVI, NDWI, SAR coherence) with physics proxies from M10/M11 to detect and characterize asset-level damage after a hazard event.

**External damage ground truth is unavailable for Upper Beas.**  Outputs are labelled `CHANGE_DETECTED` — not MINOR/MODERATE/SEVERE — because supervised classification requires field-survey labels.

---

## Indicator Architecture

### Remote Sensing Change Indicators

| Indicator | Formula | Threshold | Source |
|-----------|---------|-----------|--------|
| NDVI change | NDVI_pre − NDVI_post | ≥ 0.10 | Landsat-8/Sentinel-2 |
| NDWI change | NDWI_post − NDWI_pre | ≥ 0.08 | Sentinel-2 |
| SAR coherence drop | coh_pre − coh_post | ≥ 0.15 | Sentinel-1 |

### Physics Proxy Indicators

| Indicator | Damage Model | Source |
|-----------|-------------|--------|
| Flood depth (m) | Linear fragility: d/3.0 | M11 / NDMA curves |
| Flow velocity (m/s) | Drag: 0.5×ρ×v² / 50 kPa | M10 |
| Landslide runout (m) | Linear: runout/200 | M8/M19 |

### Fusion Weights

| Indicator | Weight |
|-----------|--------|
| Physics proxy | 0.40 |
| SAR coherence | 0.30 |
| NDWI | 0.18 |
| NDVI | 0.12 |

---

## Damage Classification Logic

```
change_detected = any indicator above threshold
               │
         ┌─────┴──────┐
         │            │
       False         True
         │            │
    NO_DAMAGE    labels_available?
                      │
               ┌──────┴──────┐
               │             │
              No            Yes
               │             │
        CHANGE_DETECTED   MINOR / MODERATE / SEVERE
```

---

## Validation Status

**EXTERNAL_DAMAGE_GROUND_TRUTH_UNAVAILABLE**

| Required Data | Status |
|--------------|--------|
| HPSDMA field survey (GPS + category) | Not provided |
| NRSC damage inventory | Not provided |
| HP PWD damage register | Not provided |
| Revenue khasra loss records | Not provided |

---

## Tests

`tests/test_m20_damage_assessment.py` — 11 tests: **11 PASSED**

---
*Generated: 2026-09-20 | FLOODY SHIELD v3.0 | SIH-26192*
