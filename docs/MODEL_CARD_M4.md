# Model Card: M4 Multimodal 9-Channel Flood U-Net
**FLOODY SHIELD — SIH Problem Statement 26192: Flash Flood & Landslide Prediction System for Hilly Regions**  
*Predict • Protect • Preserve*  
*Model Version: v1.0-multimodal-unet | Framework: PyTorch 2.2+ | Card Updated: 2026-09-20*

---

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model ID** | M4 |
| **Model Full Name** | Multimodal 9-Channel Flood Inundation U-Net |
| **Algorithm** | Encoder-Decoder U-Net with ResNet-34 Backbone and Squeeze-and-Excitation Attention Gates |
| **Artifact Path** | `data/satellite_output/flood_multimodal_unet.pt` |
| **Artifact SHA-256** | `804896f2f85cacff05a9cc852c3d8a1a65a0246c971e6f36e291454a54023d8a` (Strictly Frozen) |
| **Inference Raster** | `data/satellite_output/flood_unet_inundation.tif` (10m grid, Upper Beas AOI) |
| **Training Pipeline** | `ml/satellite_hazard/flood/segmentation/train_unet.py` |
| **Validation Script** | [`ml/validation/external/evaluate_m4_strengthened.py`](file:///c:/Users/Prathmesh%20Abhang/OneDrive/Desktop/floody-shield/ml/validation/external/evaluate_m4_strengthened.py) |
| **Validation Status** | **`PROXY_VALIDATED_PROTOTYPE`** |
| **Benchmark Gap** | Minimum benchmark: 500+ labelled scenes. Current: 1 disaster event period with SAR-HAND proxy masks (not authoritative field GT); N=24 point-level external evaluation (not scene-level). Internal Dice=0.973 is against proxy masks — NOT external ground truth (as the card states). Research-grade validation requires Copernicus EMS or NRSC flood extent rasters. |

---

## 2. Model Purpose & Semantic Meaning

Model M4 performs **pixel-level semantic segmentation of water inundation** at 10-meter ground resolution:
$$P(\text{Inundated Pixel} = 1 \mid \text{Sentinel-1 SAR}, \text{Sentinel-2 Optical}, \text{HAND Topography})$$

M4 fuses active microwave radar (penetrates clouds and monsoon rain) with multispectral optical bands and hydrologic elevation to delineate flood extents across rugged Himalayan valleys.

---

## 3. Training Data & Internal Proxy Masks

| Field | Value |
|:------|:------|
| **Dataset Source** | Upper Beas Sentinel-1 & Sentinel-2 image tiles (July 2023 disaster period) |
| **Spatial Resolution**| 10 meters per pixel |
| **Internal Benchmark Mask** | SAR backscatter thresholding combined with HAND drainage limits (SAR-HAND hydro-physical proxy). |
| **Internal Performance** | $\text{Dice} = 0.973, \text{IoU} = 0.948, \text{Accuracy} = 0.978$ |
| **CRITICAL DISCLAIMER** | The internal 0.973 Dice score represents **model convergence against internal physical proxy masks**, NOT independent external ground truth. Conflating internal proxy Dice with external real-world accuracy is scientifically prohibited. |

---

## 4. Input Features (9 Satellite & Topographic Bands)

1. `SAR_VV`: Sentinel-1 GRD VV polarization backscatter amplitude (dB)
2. `SAR_VH`: Sentinel-1 GRD VH polarization backscatter amplitude (dB)
3. `SAR_Ratio`: Cross-polarization ratio (VV / VH)
4. `S2_Red`: Sentinel-2 Level-2A Band 4 (Red, 10m)
5. `S2_Green`: Sentinel-2 Level-2A Band 3 (Green, 10m)
6. `S2_Blue`: Sentinel-2 Level-2A Band 2 (Blue, 10m)
7. `S2_NIR`: Sentinel-2 Level-2A Band 8 (Near-Infrared, 10m)
8. `NDWI`: Normalized Difference Water Index $(\text{Green} - \text{NIR}) / (\text{Green} + \text{NIR})$
9. `HAND`: Height Above Nearest Drainage from 10m DEM (meters)

---

## 5. External Evaluation Data & Authoritative Ground Truth Status

### 5.1 2D Raster Ground Truth Declaration
Authoritative independent 10-meter digital flood extent rasters (such as vector shapefiles or GeoTIFFs from Copernicus EMS or ISRO/NRSC Disaster Management Support) remain unreleased in open GIS formats for this specific scene. Consequently:

$$\mathbf{Authoritative\ 2D\ Ground\ Truth:}\quad \text{\textbf{FULL\_SCENE\_EXTERNAL\_GROUND\_TRUTH\_UNAVAILABLE}}$$

### 5.2 External Ground Point Concordance Data ($N=24$)
Empirical validation was performed against 24 surveyed ground locations from the July 8–11, 2023 disaster event:
- 12 verified inundated field sites (washed away infrastructure, highway breach points).
- 12 verified unflooded upland benches.

---

## 6. External Validation Performance

### 6.1 Point Concordance Results ($N=24$, Locked $\tau = 0.50$)

| Metric | Sample Value | Exact 95% Clopper-Pearson CI | Scientific Significance |
|:-------|:------------:|:----------------------------:|:------------------------|
| **Recall (Sensitivity)** | **50.0%** (6/12) | **[21.09%, 78.91%]** | 6 of 12 flooded sites detected at pixel level |
| **Specificity** | **75.0%** (9/12) | **[42.81%, 94.51%]** | 9 of 12 unflooded benches correctly rejected |
| **Accuracy** | **62.5%** (15/24) | **[40.59%, 81.20%]** | Overall point-pixel concordance |
| **Directional Separation** | $\Delta\bar{p} = \mathbf{+0.2215}$ | — | Flooded mean $\hat{p} = 0.4776$ vs. Unflooded mean $\hat{p} = 0.2561$ |
| **Point ROC-AUC** | **0.4583** | — | Linear corridor point discrimination |
| **Brier Score** | **0.3760** | — | Probability calibration error |

### 6.2 Statistical Sanity Check on Significance Claims
Earlier claims of "$p < 0.05$" were audited:
- Naive Mann-Whitney test: $p = 0.7507$; Cluster-adjusted test: $p = 1.0000$.
- Because observation points are clustered along a single river channel and share reach-level hydrologic forcing, claiming classical i.i.d. $p < 0.05$ significance is **scientifically invalid**. The $+0.2215$ probability shift is qualified as **descriptive directional evidence**.

---

## 7. Known Limitations & Failure Modes

1. **Mountain Shadow Radar Layover**: Deep V-shaped Himalayan gorges cause radar shadow and layover, reducing backscatter contrast in narrow reaches.
2. **Turbid Fast-Moving Floodwater**: High sediment load and turbulent standing waves increase radar surface roughness, diminishing the characteristic specular backscatter drop of calm water.
3. **Vegetation Canopy Obscuration**: Flooded riverbanks under dense alder/pine canopy are partially obscured in optical Sentinel-2 bands.

---

## 8. Intended Operational Use & Prohibited Misuse

- **Intended Use**: Post-event rapid satellite flood mapping to identify broad inundation corridors along the Beas River.
- **PROHIBITED Misuse**:
  - Do NOT cite internal 0.973 Dice score as external real-world accuracy.
  - Do NOT use M4 output to certify individual property-level insurance claims without ground survey confirmation.
  - Do NOT claim 2D full-scene external validation until open GIS rasters from official space agencies become available.
