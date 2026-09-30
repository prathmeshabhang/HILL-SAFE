# SATELLITE AI SPECIFICATION — FLOODY SHIELD
**SIH Problem Statement 26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
*Ministry of Home Affairs | NDRF & Disaster Management Division*

---

## 1. System Mathematical Architecture

The Satellite Hazard Intelligence and Development Risk Mapping engine transforms multispectral remote sensing rasters and terrain DEMs into continuous risk indicators without arbitrary universal thresholds.

```
       [SENTINEL-2 L2A]                     [COPERNICUS GLO-30 DEM]
              │                                        │
      Quality & Cloud Filter                   Terrain Feature Engine
       (SCL Mask 3, 8, 9, 10)                 (Slope, Aspect, Curvatures,
              │                                     TWI, SPI, TRI)
      Spectral Index Engine                            │
 (NDVI, NDWI, MNDWI, NDBI, NDMI)                       │
              │                                        │
              ├──────────────────┬─────────────────────┤
              ▼                  ▼                     ▼
     [Flood Susceptibility]  [Landslide Suscept.]  [Development Pressure]
              │                  │                     │
              └──────────────────┼─────────────────────┘
                                 ▼
                 [Development-Induced Hazard Model]
                                 │
                                 ▼
                     [Multi-Hazard Risk Fusion]
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
     [Critical Development Zones]    [Candidate Lower-Hazard Areas]
```

---

## 2. Derived Spectral Indices

All spectral calculations use normalized reflectances bounded in $[-1.0, 1.0]$:

1. **Normalized Difference Vegetation Index (NDVI)**:
   $$\text{NDVI} = \frac{\text{B8 (NIR)} - \text{B4 (Red)}}{\text{B8} + \text{B4} + \epsilon}$$
   Measures photosynthetic biomass. Vegetation loss ($\Delta \text{NDVI} < -0.20$) highlights deforestation, slope cutting, or scouring.

2. **Modified Normalized Difference Water Index (MNDWI)**:
   $$\text{MNDWI} = \frac{\text{B3 (Green)} - \text{B11 (SWIR1)}}{\text{B3} + \text{B11} + \epsilon}$$
   Superior to NDWI in mountain shadows because SWIR absorbs water strongly while suppressing shadow noise.

3. **Normalized Difference Built-up Index (NDBI)**:
   $$\text{NDBI} = \frac{\text{B11 (SWIR1)} - \text{B8 (NIR)}}{\text{B11} + \text{B8} + \epsilon}$$
   High values indicate built-up concrete, asphalt, compacted soil, and quarry surfaces.

4. **Normalized Difference Moisture Index (NDMI)**:
   $$\text{NDMI} = \frac{\text{B8 (NIR)} - \text{B11 (SWIR1)}}{\text{B8} + \text{B11} + \epsilon}$$
   Monitors canopy and surface moisture saturation.

---

## 3. Terrain Feature Numerical Algorithms

Derived using Horn’s $3 \times 3$ convolutional kernel over cell size $d = 30\,\text{m}$:

1. **Orthogonal Partial Derivatives**:
   $$p = \frac{\partial z}{\partial x} = \frac{(z_{++} + 2z_{+0} + z_{+-}) - (z_{-+} + 2z_{-0} + z_{--})}{8d}$$
   $$q = \frac{\partial z}{\partial y} = \frac{(z_{++} + 2z_{0+} + z_{-+}) - (z_{+-} + 2z_{0-} + z_{--})}{8d}$$

2. **Slope ($\beta$)**:
   $$\beta = \arctan\left(\sqrt{p^2 + q^2}\right) \times \frac{180}{\pi}$$

3. **Topographic Wetness Index (TWI)**:
   $$\text{TWI} = \ln\left(\frac{A}{\tan \beta + \epsilon}\right)$$
   Where $A$ is specific catchment drainage area ($\text{m}^2/\text{m}$). Valley bottoms exhibit high TWI ($>10$), predicting floodwater ponding.

4. **Terrain Ruggedness Index (TRI)**:
   $$\text{TRI} = \sqrt{\sum_{i=-1}^{1} \sum_{j=-1}^{1} (z_{i,j} - z_{0,0})^2}$$

---

## 4. Development Pressure & Induced Hazard Formulations

1. **Observed Development Pressure ($P_{\text{dev}} \in [0.0, 1.0]$)**:
   $$P_{\text{dev}} = \sigma\left(w_1 \cdot \text{NDBI} + w_2 \cdot (1 - \text{NDVI}) + w_3 \cdot \text{Prox}_{\text{road}} + w_4 \cdot \text{Prox}_{\text{river}}\right)$$

2. **Development-Induced Hazard Risk ($R_{\text{dev}} \in [0.0, 1.0]$)**:
   $$R_{\text{dev}} = P_{\text{dev}} \times \left(w_f \cdot S_{\text{flood}} + w_l \cdot S_{\text{slide}}\right) \times \text{Vulnerability Factor}$$

3. **Critical Development Zones (CDZ)**:
   Spatial units where $P_{\text{dev}} \ge 0.65$ AND ($S_{\text{flood}} \ge 0.70$ OR $S_{\text{slide}} \ge 0.70$).

4. **Candidate Lower-Hazard Development Zones**:
   Spatial units where $S_{\text{flood}} \le 0.30$, $S_{\text{slide}} \le 0.30$, $\beta \le 20^\circ$, and $\text{TWI} \le 7.5$.
