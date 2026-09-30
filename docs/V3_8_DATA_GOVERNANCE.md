# FLOODY SHIELD v3.8 — Scientific Validation Data Governance & Registry

**Standard:** FAIR (Findable, Accessible, Interoperable, Reusable) Scientific Data Principles  
**Registry Implementation:** `tools/validation/registry.py`  
**Manifest:** `data/validation_datasets/manifest.json`  

---

## 1. Governance Principles

1. **Cryptographic Immutability**: Every validation dataset is hashed via SHA-256 upon intake. Any bit-level file alteration breaks validation verification.
2. **Lifecycle State Progression**: Datasets must strictly follow authorized state transitions:
   `DISCOVERED` $\to$ `ACQUIRED` $\to$ `QUALITY_CHECKED` $\to$ `VALIDATION_READY` $\to$ `USED_FOR_VALIDATION` (or `REJECTED` / `EXPIRED`).
3. **Data Provenance Transparency**: Every dataset record specifies the authoritative source agency, geographic scope, temporal extent, sample size ($N$), and whether the data is `REAL`, `SIMULATED`, or `REPLAY`.
4. **Zero Fabrication**: Synthetic data is strictly barred from passing as independent external validation evidence. If external real-world ground truth does not exist for a model, its status remains `PENDING_EXTERNAL_DATA`.

---

## 2. Dataset Inventory Summary

| Dataset ID | Name | Target Model(s) | Source Agency | Sample Size ($N$) | Lifecycle State | SHA-256 Verified |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `EXT_VAL_M6_BEAS_STABLE_SLOPES` | Upper Beas Landslide & Slope Stability Catalog | M6 | GSI / HPSDMA / Zenodo | 520 points | `VALIDATION_READY` | **YES** |
| `EXT_VAL_M7_HIMALAYAN_STORM_LANDSLIDES` | Himachal Pradesh Storm-Landslide Trigger Catalog | M7 | Zenodo (Catena 2025) | 115 episodes | `VALIDATION_READY` | **YES** |
| `EXT_VAL_M10_CWC_THALOUT_STAGE` | CWC Thalout River Stage & Discharge Observations | M2, M10 | CWC / BBMB | 850 records | `VALIDATION_READY` | **YES** |
| `EXT_VAL_M11_SATELLITE_FLOOD_DELINEATION` | Sentinel-1 / RISAT-1 SAR Flood Extent Polygons | M4, M11 | ISRO NRSC / Copernicus | 3 zones | `VALIDATION_READY` | **YES** |
| `EXT_VAL_M19_FLASH_FLOOD_PROPAGATION` | Mountain Channel Flash Flood Wave Celerity Archive | M19 | BBMB / CWC / HPSDMA | 55 events | `VALIDATION_READY` | **YES** |
| `EXT_VAL_M20_POST_EVENT_DAMAGE_SURVEY` | Kullu-Manali Structural Damage Field Inspection | M13, M14, M20 | HPSDMA / PWD | 510 structures | `VALIDATION_READY` | **YES** |
