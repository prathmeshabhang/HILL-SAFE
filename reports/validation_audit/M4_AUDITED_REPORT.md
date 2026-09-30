# MODEL M4: MULTIMODAL FLOOD U-NET SCIENTIFIC AUDIT REPORT
**FLOODY SHIELD — Independent External Validation Stage A**  
*Problem Statement 26192 | Upper Beas Basin, Himachal Pradesh*  
*Validation Status: AUDITED & FROZEN | Validation Tier: PARTIALLY_VALIDATED*

---

## 1. Executive Summary & Audit Declaration

This report provides the audited external validation analysis of **Model M4 (Multimodal 9-Channel Flood U-Net)**. In strict accordance with scientific standards:
- **Zero Retraining**: Production weights (`ml/models/m4_multimodal_unet.pt`, SHA-256: `6056ea0e...`) remain strictly frozen.
- **Separation of Spatial Scales**: Explicit distinction between **Pixel-Level Segmentation** and **Point-Level Concordance**.
- **External 2D Ground-Truth Status**: Because authoritative 10-meter digital ground-truth flood rasters have not been released in open GIS format for the Upper Beas July 2023 disaster, **External 2D Dice and IoU are mathematically `NOT ESTIMABLE` / `NOT AVAILABLE`**.
- **Point Concordance Audit**: Evaluated against 24 ground-verified field points, achieving **ROC-AUC = 0.6806** and statistically significant separation between flooded and unflooded locations.

---

## 2. Frozen Model Specification

| Attribute | Specification |
|:---|:---|
| **Model ID** | M4 |
| **Model Architecture** | 9-Channel Multimodal U-Net (ResNet-34 Encoder + Attention Gates) |
| **Model Artifact** | `ml/models/m4_multimodal_unet.pt` |
| **Model SHA-256** | `6056ea0ecfc0c034b0718d0f19565548db3dbdf909ff7b3b642646638ba4b31a` |
| **Input Channels (9)** | Sentinel-1 VV, VH, VV/VH ratio, Copernicus DEM, Slope, HAND, Flow Accumulation, 24h Rainfall, River Proximity |
| **Spatial Resolution** | 10 meters per pixel |
| **Predefined Operating Threshold** | $\tau = 0.50$ (Locked prior to external evaluation) |

---

## 3. Disaggregation of Validation Scales

### 3.1 Scale 1: Internal Pixel-Level Segmentation (Scene Test Split)
- **Reference Mask**: Hydro-physically consistent SAR-HAND benchmark inundation mask.
- **Dice F1 Score**: $0.969 - 0.973$
- **Intersection-over-Union (IoU)**: $0.939 - 0.948$
- **Pixel Accuracy**: $0.976 - 0.979$
- **Scientific Role**: Rigorous internal architecture and convergence benchmark; **NOT** reported as independent external evidence.

### 3.2 Scale 2: External Point-Level Concordance ($N=24$ Field Points)
- **Flooded Field Sites ($N=12$)**: Mean predicted probability = **$0.6834 \pm 0.207$**
- **Unflooded Control Sites ($N=12$)**: Mean predicted probability = **$0.4804 \pm 0.218$**
- **Probability Separation**: $+0.2030$ higher probability on verified flooded sites ($p < 0.05$).

### 3.3 Scale 3: External 2D Pixel-Level Segmentation
- **External 2D Dice**: **`NOT ESTIMABLE`** (Pending authoritative open 10m raster).
- **External 2D IoU**: **`NOT ESTIMABLE`** (Pending authoritative open 10m raster).

---

## 4. Audited Metric Evaluation

### 4.1 Point Concordance Metrics ($N=24$ Points, $\tau = 0.50$)

| Metric | Measured Value | Audit Status | 95% Confidence Interval | Method / Rationale |
|:---|:---:|:---:|:---:|:---|
| **External 2D Dice** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Authoritative 10m open raster unreleased. Evaluation against unverified masks prohibited. |
| **External 2D IoU** | **NOT ESTIMABLE** | `NOT_ESTIMABLE` | — | Authoritative 10m open raster unreleased. |
| **Point ROC-AUC** | **0.6806** | `VALID` | [0.4444, 0.8889] | Bootstrap CI ($N=24 \ge 15$). Continuous discrimination between field points. |
| **Point PR-AUC** | **0.6976** | `VALID` | [0.4682, 0.8932] | Bootstrap CI ($N=24 \ge 15$). |
| **Point Recall (Sensitivity)** | **0.8333** (10/12) | `VALID` | **[0.5159, 0.9791]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Point Specificity** | **0.5000** (6/12) | `VALID` | **[0.2109, 0.7891]** | **Exact Clopper-Pearson** binomial CI at operating threshold $\tau = 0.50$. |
| **Point Precision** | 0.6250 (10/16) | `VALID` | [0.3543, 0.8480] | Exact Clopper-Pearson binomial CI at operating threshold $\tau = 0.50$. |
| **Point Accuracy** | 0.6667 (16/24) | `VALID` | [0.4468, 0.8437] | Exact Clopper-Pearson binomial CI at operating threshold $\tau = 0.50$. |
| **Brier Score** | 0.2289 | `VALID` | [0.1554, 0.3012] | Bootstrap CI ($N=24 \ge 15$). |

### 4.2 Strictly Independent Point Subset ($N=6$, $>500\,\text{m}$ Separation)
- **Recall ($\tau = 0.50$)**: $3 / 4 = 75.0\%$ (Exact 95% CI: $[0.1941, 0.9937]$).
- **Specificity ($\tau = 0.50$)**: $1 / 2 = 50.0\%$ (Exact 95% CI: $[0.0126, 0.9874]$).
- **Accuracy ($\tau = 0.50$)**: $4 / 6 = 66.7\%$ (Exact 95% CI: $[0.2228, 0.9567]$).

---

## 5. Physical Diagnosis of Complex Mountain Terrain Segmentation

1. **Radar Shadow & Layover**: In deeply incised Himalayan valleys (e.g. Parvati, Sainj), steep topography casts severe radar shadow on Sentinel-1 SAR imagery. M4's multimodal integration of HAND and slope mitigates, but does not completely eliminate, mountain shadow noise.
2. **Turbulent White Water vs Specular Reflection**: High-velocity mountain flash floods contain turbulent sediment-laden water and foam, which scatters radar backscatter differently from flat open-water specular reflection.

---

## 6. Conservative Claims & Scientific Boundaries

### Supported Claims
- Frozen Model M4 pixel predictions show statistically significant concordance with independent field flood points (mean $P=0.6834$ on flooded sites vs $0.4804$ on unflooded sites; Point ROC-AUC = **0.6806**).
- At threshold $\tau=0.50$, Model M4 captured **83.3%** of flooded disaster locations ($10/12$, 95% exact Clopper-Pearson CI: **[51.6%, 97.9%]**).
- Internally, M4 achieves high architectural convergence (Dice F1 $0.969 - 0.973$, IoU $0.939 - 0.948$) against the reference benchmark mask.

### Unsupported Claims (Prohibited)
- **Prohibited**: Claiming external 2D Dice or IoU on open independent data (currently `NOT ESTIMABLE`).
- **Prohibited**: Conflating internal benchmark metrics with independent external real-world ground truth.
- **Prohibited**: Stating that M4 provides 100% cloud-penetrating water detection without acknowledging mountain radar shadow effects.

---

## 7. Required Missing Evidence for Full Validation
1. **Authoritative Open 10m Delineation Rasters**: Vector or raster flood extent layers from NRSC Disaster Watch or Copernicus EMS Rapid Mapping for the Upper Beas scene.
2. **Multi-Sensor High-Resolution Imagery**: Post-event optical (PlanetScope 3m, Sentinel-2 cloud-free) imagery to cross-validate turbulent mountain torrents.
