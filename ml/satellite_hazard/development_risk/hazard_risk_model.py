"""
hazard_risk_model.py — Development-Induced Hazard Risk Scoring Model
====================================================================
Evaluates:
  "Could new or intensified development in this location increase future flood or landslide risk?"

Couples:
  - Observed Development Pressure (P_dev)
  - Natural Hazard Susceptibility (S_flood, S_slide)
  - Terrain Fragility (Steep slope, high moisture accumulation)
  - Surface Disturbance (Vegetation loss, bare ground)

Outputs:
  - development_hazard_risk_score [0.0, 1.0]
  - Dominant contributing factors per spatial unit
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.development_detection.pressure_engine import DevelopmentPressureResult
from ml.satellite_hazard.flood.flood_susceptibility import FloodAnalysisResult
from ml.satellite_hazard.landslide.landslide_susceptibility import LandslideAnalysisResult
from ml.satellite_hazard.terrain.terrain_engine import TerrainFeatures


@dataclass
class DevelopmentRiskResult:
    shape: Tuple[int, int]
    development_hazard_risk_score: np.ndarray  # [0.0, 1.0]
    high_risk_mask: np.ndarray                 # Risk >= 0.60
    dominant_hazard_map: np.ndarray            # 1: Flood Dominant, 2: Landslide Dominant, 3: Compound
    high_risk_area_pct: float
    mean_risk_score: float


class DevelopmentHazardModel:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()

    def evaluate(
        self,
        dev_pressure: DevelopmentPressureResult,
        flood_res: FloodAnalysisResult,
        landslide_res: LandslideAnalysisResult,
        terrain: TerrainFeatures,
    ) -> DevelopmentRiskResult:
        p_dev = dev_pressure.development_pressure_score
        s_flood = flood_res.susceptibility_score
        s_slide = landslide_res.susceptibility_score

        # Max hazard exposure confronting the development
        compound_hazard = np.maximum(s_flood, s_slide)

        # Non-linear coupling: Development in high-hazard terrain amplifies risk non-linearly
        # When development pressure meets fragile terrain (cutting slopes or constricting floodways)
        risk_score = p_dev * compound_hazard * (1.0 + 0.35 * (s_flood * s_slide))
        risk_score = np.clip(risk_score, 0.0, 1.0).astype(np.float32)

        # Determine dominant hazard per cell
        # 0: None, 1: Flood Dominant, 2: Landslide Dominant, 3: Compound Multi-Hazard
        dominant_map = np.zeros(p_dev.shape, dtype=np.uint8)
        is_flood_dom = (s_flood > s_slide + 0.15) & (s_flood > 0.40)
        is_slide_dom = (s_slide > s_flood + 0.15) & (s_slide > 0.40)
        is_compound = (s_flood >= 0.40) & (s_slide >= 0.40)

        dominant_map[is_flood_dom] = 1
        dominant_map[is_slide_dom] = 2
        dominant_map[is_compound] = 3

        high_risk = risk_score >= 0.60
        high_pct = float(np.mean(high_risk) * 100.0)
        mean_r = float(np.mean(risk_score))

        return DevelopmentRiskResult(
            shape=p_dev.shape,
            development_hazard_risk_score=risk_score,
            high_risk_mask=high_risk,
            dominant_hazard_map=dominant_map,
            high_risk_area_pct=round(high_pct, 2),
            mean_risk_score=round(mean_r, 4),
        )
