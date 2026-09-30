"""
fusion_engine.py — Transparent Multi-Hazard Fusion & Zone Synthesis
====================================================================
Combines:
  - Flood Susceptibility (S_flood)
  - Landslide Susceptibility (S_slide)
  - Observed Development Pressure (P_dev)
  - Development-Induced Hazard Risk (R_dev)
  - Satellite Epistemic Quality & Confidence

Synthesizes:
  1. Multi-Hazard Composite Risk Map [0.0, 1.0]
  2. Critical Development Zones (CDZ): High development intersecting active hazard
  3. Candidate Lower-Hazard Development Zones: Low flood, low slide, gentle slope, safe HAND
  4. Explicit Pixel-Level Confidence and Epistemic Uncertainty
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.development_detection.pressure_engine import DevelopmentPressureResult
from ml.satellite_hazard.development_risk.hazard_risk_model import DevelopmentRiskResult
from ml.satellite_hazard.flood.flood_susceptibility import FloodAnalysisResult
from ml.satellite_hazard.landslide.landslide_susceptibility import LandslideAnalysisResult
from ml.satellite_hazard.terrain.terrain_engine import TerrainFeatures


@dataclass
class MultiHazardFusionResult:
    shape: Tuple[int, int]
    multi_hazard_risk_score: np.ndarray        # [0.0, 1.0]
    critical_development_mask: np.ndarray      # High development in high hazard
    candidate_safe_zone_mask: np.ndarray       # Low hazard, gentle slope, candidate development
    confidence_map: np.ndarray                 # [0.0, 1.0]
    uncertainty_map: np.ndarray                # [0.0, 1.0]
    critical_zone_area_pct: float
    candidate_safe_area_pct: float
    statutory_disclaimer: str


class MultiHazardFusionEngine:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def fuse(
        self,
        flood_res: FloodAnalysisResult,
        landslide_res: LandslideAnalysisResult,
        dev_pressure: DevelopmentPressureResult,
        dev_risk: DevelopmentRiskResult,
        terrain: TerrainFeatures,
        valid_mask: np.ndarray,
    ) -> MultiHazardFusionResult:
        s_f = flood_res.susceptibility_score
        s_l = landslide_res.susceptibility_score
        p_d = dev_pressure.development_pressure_score
        r_d = dev_risk.development_hazard_risk_score
        slope = terrain.slope_deg
        hand = terrain.height_above_nearest_drainage_m
        twi = terrain.topographic_wetness_index

        # 1. Multi-Hazard Composite Risk (Decoupled Fusion)
        # Avoid simple averaging: an extreme flood in a flat plain OR an extreme slide on a cliff
        # represents extreme hazard. Compound areas are penalized further.
        composite_risk = np.maximum(s_f, s_l) * (1.0 + 0.25 * (s_f * s_l))
        composite_risk = np.clip(composite_risk, 0.0, 1.0).astype(np.float32)

        # 2. Critical Development Zones (CDZ)
        # Areas where high observed development pressure intersects high flood or landslide susceptibility
        is_cdz = (
            (p_d >= self.config.critical_dev_pressure_min) &
            ((s_f >= self.config.critical_hazard_susceptibility_min) |
             (s_l >= self.config.critical_hazard_susceptibility_min))
        )

        # 3. Candidate Lower-Hazard Development Zones (Section 14)
        # Low flood (<0.30), low slide (<0.30), gentle slope (<18 deg), low TWI (<7.5), safe HAND (>20m)
        is_candidate_safe = (
            (s_f <= self.config.candidate_safe_flood_max) &
            (s_l <= self.config.candidate_safe_landslide_max) &
            (slope <= self.config.candidate_safe_slope_max_deg) &
            (twi <= self.config.candidate_safe_twi_max) &
            (hand >= 20.0) &
            (~flood_res.active_water_mask)
        )

        # 4. Confidence & Epistemic Uncertainty Estimation (Section 18)
        # - High confidence where observations are valid (not cloud-masked) and terrain is well-modeled
        base_conf = valid_mask.copy()
        # Reduce confidence on extreme sheer cliffs (>60 deg) due to DEM radar layover/shadow
        steep_cliff = slope > 60.0
        base_conf[steep_cliff] = base_conf[steep_cliff] * 0.75
        confidence = np.clip(base_conf, 0.10, 0.98).astype(np.float32)
        uncertainty = (1.0 - confidence).astype(np.float32)

        cdz_pct = float(np.mean(is_cdz) * 100.0)
        safe_pct = float(np.mean(is_candidate_safe) * 100.0)

        return MultiHazardFusionResult(
            shape=composite_risk.shape,
            multi_hazard_risk_score=composite_risk,
            critical_development_mask=is_cdz,
            candidate_safe_zone_mask=is_candidate_safe,
            confidence_map=confidence,
            uncertainty_map=uncertainty,
            critical_zone_area_pct=round(cdz_pct, 2),
            candidate_safe_area_pct=round(safe_pct, 2),
            statutory_disclaimer=self.config.safe_zone_disclaimer,
        )
