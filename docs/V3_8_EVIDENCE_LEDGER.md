# FLOODY SHIELD v3.8 / v3.8.1 — Scientific Evidence Ledger

**Basin:** Upper Beas River Basin, Himachal Pradesh  
**Version:** v3.8.1 Audited Baseline  
**Audit Standard:** Strict Scientific Provenance Ledger  

---

## 1. Frozen Artifact Immutability Ledger

| Model ID | File Location | Expected SHA-256 Digest | Pre-Validation Check | Post-Validation Check | Immutability Status |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **M2** | `ml/flood/m2_upper_beas_flood_model.joblib` | `a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b` | **MATCH** | **MATCH** | **BIT-IDENTICAL** |
| **M4** | `data/satellite_output/flood_multimodal_unet.pt` | `45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07` | **MATCH** | **MATCH** | **BIT-IDENTICAL** |
| **M6** | `ml/landslide/m6_beas_susceptibility_rf.joblib` | `e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c` | **MATCH** | **MATCH** | **BIT-IDENTICAL** |
| **M7** | `ml/landslide/m7_beas_trigger_lgbm.joblib` | `f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a` | **MATCH** | **MATCH** | **BIT-IDENTICAL** |

---

## 2. Validation Dataset Cryptographic & Provenance Ledger

### 2.1 Authentic Real External Scientific Reference Datasets

| Dataset ID | Disk Path | Format | Provenance | Source Agency | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `EXT_REAL_M6_KULLU_LANDSLIDES_2023` | `data/external/m6/upper_beas/raw/kullu_upper_beas_landslides_2023_raw.csv` | CSV | **REAL** | GSI (Report M4EGG/C/NR/SU-PHP/2023/46620) | **VALIDATION_READY** |
| `EXT_REAL_M6_KULLU_CONTROLS_2023` | `data/external/m6/upper_beas/raw/kullu_upper_beas_stable_controls_raw.csv` | CSV | **REAL** | ASI / GSI / HPSDMA Bedrock Monitoring | **VALIDATION_READY** |
| `EXT_REAL_M7_PROCESSED_EVENTS` | `data/external/m6/upper_beas/processed/m7_external_event_dataset.csv` | CSV | **REAL** | GSI / HPSDMA July 2023 Disaster Survey | **VALIDATION_READY** |
| `EXT_REAL_M7_HIMALAYAN_STORM_CATALOG` | `data/external/events/himalayan_storm_landslide_catalog.csv` | CSV | **REAL** | GSI / HPSDMA / IMD / Catena 2025 | **VALIDATION_READY** |
| `EXT_REAL_M2_FLOOD_EVENTS_2023` | `data/external/flood/raw/upper_beas_flood_events_2023_raw.csv` | CSV | **REAL** | HPSDMA (PDNA 2023) / CWC / NRSC | **VALIDATION_READY** |

### 2.2 Synthetic Benchmark Simulation & Proxy Fixtures

| Dataset ID | Disk Path | Format | Provenance | Purpose | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `BENCHMARK_SYNTH_M6_SLOPES` | `data/validation_datasets/M6_stable_slope_controls.csv` | CSV | **SYNTHETIC** | Algorithmic test bench fixture (520 pts) | **SYNTHETIC_BENCHMARK** |
| `BENCHMARK_SYNTH_M7_STORMS` | `data/validation_datasets/M7_storm_landslide_episodes.csv` | CSV | **SYNTHETIC** | Pipeline regression test fixture (115 eps) | **SYNTHETIC_BENCHMARK** |
| `BENCHMARK_SYNTH_M10_CWC_STAGE` | `data/validation_datasets/M10_cwc_thalout_water_level.csv` | CSV | **SYNTHETIC** | River stage simulation benchmark (850 rows) | **SYNTHETIC_BENCHMARK** |
| `BENCHMARK_PROXY_M11_SAR_EXTENTS` | `data/validation_datasets/M11_satellite_flood_extents.json` | JSON | **PROXY** | Derived SAR microwave flood extents | **PROVISIONAL** |
| `BENCHMARK_SYNTH_M19_PROPAGATION` | `data/validation_datasets/M19_time_to_impact_events.csv` | CSV | **SYNTHETIC** | Wave celerity calculation fixture (55 eps) | **SYNTHETIC_BENCHMARK** |
| `BENCHMARK_SYNTH_M20_DAMAGE` | `data/validation_datasets/M20_damage_assessment_ground_truth.csv` | CSV | **SYNTHETIC** | Structural loss classifier stress test (510 pts) | **SYNTHETIC_BENCHMARK** |
