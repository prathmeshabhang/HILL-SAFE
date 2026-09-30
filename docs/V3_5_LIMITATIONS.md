# FLOODY SHIELD v3.5 — System Limitations & Truthful Operational Boundary

**Target Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**System Version:** v3.5.0  
**Overall Readiness Classification:** LEVEL 1 — PROTOTYPE / RESEARCH DECISION-SUPPORT  

---

## 1. Truthful Status Declaration & Operational Boundary

> [!CAUTION]
> **NOT A FULLY AUTONOMOUS WARNING SYSTEM**  
> FLOODY SHIELD v3.5 is an advanced research prototype and supervised decision-support platform. It is **NOT** a certified standalone municipal warning system, nor does it replace the statutory roles of the India Meteorological Department (IMD), Central Water Commission (CWC), or National Disaster Management Authority (NDMA).

The platform enforces strict technical boundaries between what has been scientifically verified and what remains an active operational limitation.

---

## 2. Scientific & Model Limitations (M1–M20)

| Model | Subsystem | Declared Evidence Status | Known Physical & Scientific Limitations |
|---|---|---|---|
| **M1** | Radar / Optical Flow Nowcasting | Research Prototype | Limited lead-time (30–60 mins); radar beam blockage in deep Himalayan gorges (Pir Panjal / Dhauladhar shadows). |
| **M2** | Flash Flood Susceptibility / Random Forest | Preliminary External Evidence | Trained on historical event records; extreme out-of-distribution cloudburst events (>150 mm/h) have high epistemic uncertainty. |
| **M4** | Satellite Multimodal Segmentation | Research Prototype | Dependent on Sentinel-1 SAR orbital revisit times (6–12 days); optical Sentinel-2 imagery obscured during heavy monsoon cloud cover. |
| **M6** | Landslide Susceptibility | Retrained on Real Regional Inventory | Static susceptibility map based on slope, lithology, and drainage; does not account for dynamic pore-water transient fluctuations alone. |
| **M7** | Dynamic Landslide Triggering (LightGBM) | Preliminary External Evidence | Requires accurate short-term rainfall accumulations; rain gauge spatial sparsity in steep terrain can result in missed local triggers. |
| **M8** | Kinematic InSAR Deformation | Preliminary Regional Processing | InSAR line-of-sight (LOS) geometric distortions (layover and foreshortening) on north-east facing mountain slopes. |
| **M10** | Hydrological Stage Forecast | Preliminary Regional Model | Upstream tributary inflow rating curves can change drastically during massive riverbed scour or aggradation. |
| **M11** | Hydrodynamic Flood Depth (2D) | Benchmark Calibrated | High computational demand; requires high-resolution LiDAR DEM; SRTM/ALOS DEMs introduce elevation noise along riverbanks. |
| **M12** | Landslide Dam Breach & Cascade Surge | Physics-Calibrated Empirical | Landslide dam breach geometry and internal erosion parameters are estimated empirically; actual dam composition affects breach hydrograph. |
| **M13–M14** | Vulnerability & HAZUS Infrastructure Loss | Empirical Engineering | Replacement costs and structural damage curves based on general Indian standards; requires local municipal asset census. |
| **M16** | Safe Evacuation Routing | Graph Decision Algorithmic | Road clearance calculations assume reported landslide points; unmonitored road washouts between telemetry points may trap vehicles. |
| **M17–M18** | Warning Gating & Calibration | Conformal Calibration | Temperature scaling and Brier scores calibrated on historical test sets; uncalibrated under novel climate extremes. |

---

## 3. Telemetry & Hardware Boundaries

1. **Synthetic Telemetry vs. Live Deployment**:
   - The platform includes a high-fidelity synthetic telemetry generator (`tools.telemetry_simulator`) and historical replay engine (July 2023 catastrophe).
   - In the absence of physical sensor deployment along the Beas River, field data is marked with `provenance="SIMULATED"` and `environment="TEST"`.
2. **Terrain & Telemetry Dropout**:
   - 4G cellular service in the Aut-Larji gorge is vulnerable to landslides severing optical fiber backhauls.
   - Long-range LoRaWAN and satellite fallback are architected but require physical field deployment of repeaters on high ridge lines.
3. **Sensor Siltation & Damage**:
   - Himalayan rivers during flood conditions carry catastrophic boulder and silt loads. Physical river gauges are subject to debris impact and silt burying. Non-contact radar gauges must be mounted at least 10 meters above historical high water.

---

## 4. External Broadcast & Regulatory Integration Status

1. **NDMA Sachet Integration**:
   - The provider `NDMASachetProvider` is implemented with CAP v1.2 XML serialization and mTLS credentials configuration.
   - **Current Operational Status**: Explicitly reports `NOT_CONFIGURED` until state emergency management authorities grant live production credentials. The system NEVER fakes successful broadcast to NDMA Sachet.
2. **Physical Sirens & Public SMS Broadcast**:
   - Public alert dispatch channels are disabled in development and field pilot modes to prevent accidental public panic.
   - All dispatches require physical intervention by the designated Incident Commander.

---

## 5. Requirements for Advancement to Level 2 (Operational System)

To advance from **Level 1 (Research Prototype / Decision Support)** to **Level 2 (Operational System)**:
1. Physical installation and 6-month continuous field commissioning of the 5 pilot stations in Kullu, Manali, Bhuntar, Aut, and Larji.
2. Formal operational agreement and SOP sign-off with HPSDMA, DDMA Kullu, and BBMB (Bhakra Beas Management Board).
3. Integration of official mTLS certificates for production NDMA Sachet and CWC telemetry feeds.
4. Independent peer-reviewed validation of M1, M2, M6, and M7 against a full monsoon season of ground truth.
