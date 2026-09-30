"""
landslide_susceptibility.py — Satellite & Terrain Landslide Susceptibility Mapping
==================================================================================
Combines:
  - Slope angle (Gaussian vulnerability peak at 35°-48°)
  - Profile & Plan Curvature (breaks of slope and convergent hollows)
  - Satellite NDVI (dense tree canopy root cohesion reduces susceptibility)
  - Terrain Ruggedness Index (TRI - jointed rocky fracturing)
  - Stream Power Index (SPI - toe undercutting)

Produces:
  - Continuous landslide susceptibility score [0.0, 1.0]
  - Qualitative susceptibility class (VERY_LOW to VERY_HIGH)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from ml.satellite_hazard.config import SatelliteProcessingConfig
from ml.satellite_hazard.spectral.index_generator import SpectralIndices
from ml.satellite_hazard.terrain.terrain_engine import TerrainFeatures


@dataclass
class LandslideAnalysisResult:
    shape: Tuple[int, int]
    susceptibility_score: np.ndarray      # 2D float32 [0, 1] (Model M6 Random Forest expected probability)
    susceptibility_classes: np.ndarray    # 2D uint8 (0: Low, 1: Moderate, 2: High)
    high_susceptibility_area_pct: float
    mean_susceptibility_score: float
    trigger_probability: Optional[np.ndarray] = None     # 2D float32 [0, 1] (Model M7 LightGBM dynamic trigger)
    combined_landslide_risk: Optional[np.ndarray] = None # 2D float32 [0, 1] (fused risk)
    model_name: str = "Model_M6_RF_and_Model_M7_LGBM"
    model_version: str = "v1.0"
    m6_feature_importances: Optional[Dict[str, float]] = None
    m7_feature_importances: Optional[Dict[str, float]] = None
    inference_mode: str = "ML_INFERENCE"  # "ML_INFERENCE" or "FALLBACK_HEURISTIC"


class SatelliteLandslideModel:
    def __init__(self, config: Optional[SatelliteProcessingConfig] = None):
        self.config = config or SatelliteProcessingConfig()
        self._ml_engine = None

    @property
    def ml_engine(self):
        if self._ml_engine is None:
            try:
                from ml.satellite_hazard.spatial_ml_engine import SpatialMLEngine
                self._ml_engine = SpatialMLEngine()
            except Exception as e:
                print(f"[SatelliteLandslideModel] Warning initializing SpatialMLEngine: {e}")
                self._ml_engine = False
        return self._ml_engine

    def analyze(
        self,
        spectral: SpectralIndices,
        terrain: TerrainFeatures,
        event_rainfall_1h_mm: float = 25.0,
        antecedent_rain_3d_mm: float = 85.0,
    ) -> LandslideAnalysisResult:
        """
        Calculates spatial landslide susceptibility and dynamic triggering using:
          - Model M6: 350-Tree Random Forest for static geological & geomorphic susceptibility
          - Model M7: LightGBM for dynamic rainfall & soil saturation triggering
        Falls back to calibrated physical heuristics if ML artifacts are unavailable.
        """
        # 1. Attempt Authentic ML Inference via SpatialMLEngine
        if self.ml_engine and self.ml_engine.m6_model is not None:
            try:
                ml_res = self.ml_engine.infer_landslide_suite(
                    terrain=terrain,
                    spectral=spectral,
                    event_rainfall_1h_mm=event_rainfall_1h_mm,
                    antecedent_rain_3d_mm=antecedent_rain_3d_mm,
                )
                mean_score = float(np.mean(ml_res.m6_susceptibility_score))

                return LandslideAnalysisResult(
                    shape=terrain.shape,
                    susceptibility_score=ml_res.m6_susceptibility_score,
                    susceptibility_classes=ml_res.m6_susceptibility_classes,
                    high_susceptibility_area_pct=ml_res.high_susceptibility_area_pct,
                    mean_susceptibility_score=round(mean_score, 4),
                    trigger_probability=ml_res.m7_trigger_probability,
                    combined_landslide_risk=ml_res.combined_landslide_risk,
                    model_name="Model_M6_RF_and_Model_M7_LGBM",
                    model_version="v1.0",
                    m6_feature_importances=ml_res.m6_feature_importances,
                    m7_feature_importances=ml_res.m7_feature_importances,
                    inference_mode="ML_INFERENCE",
                )
            except Exception as ex:
                print(f"[SatelliteLandslideModel] ML inference failed ({ex}). Falling back to heuristic...")

        # 2. Fallback Heuristic / Physical Equations
        slope = terrain.slope_deg
        prof_curv = terrain.profile_curvature
        plan_curv = terrain.plan_curvature
        tri = terrain.terrain_ruggedness_index
        ndvi = spectral.ndvi

        slope_factor = np.exp(-((slope - 39.0) ** 2) / (2.0 * (11.5 ** 2)))
        curv_factor = np.clip((np.abs(prof_curv) * 20.0) + (np.maximum(-plan_curv, 0.0) * 15.0), 0.0, 1.0)
        veg_protection = np.clip((ndvi - 0.10) / 0.55, 0.0, 1.0)
        veg_vulnerability = 1.0 - (veg_protection * 0.75)
        tri_factor = np.clip(tri / 45.0, 0.0, 1.0)

        susceptibility = (
            0.50 * slope_factor +
            0.20 * curv_factor +
            0.18 * veg_vulnerability +
            0.12 * tri_factor
        )
        susceptibility[slope < 8.0] = susceptibility[slope < 8.0] * 0.15
        susceptibility = np.clip(susceptibility, 0.0, 1.0).astype(np.float32)

        classes = np.zeros(spectral.shape, dtype=np.uint8)
        classes[susceptibility >= 0.20] = 1
        classes[susceptibility >= 0.40] = 2
        classes[susceptibility >= 0.60] = 3
        classes[susceptibility >= 0.80] = 4

        high_pct = float(np.mean(susceptibility >= 0.60) * 100.0)
        mean_score = float(np.mean(susceptibility))

        return LandslideAnalysisResult(
            shape=spectral.shape,
            susceptibility_score=susceptibility,
            susceptibility_classes=classes,
            high_susceptibility_area_pct=round(high_pct, 2),
            mean_susceptibility_score=round(mean_score, 4),
            trigger_probability=None,
            combined_landslide_risk=susceptibility,
            model_name="Geomorphic_Heuristic_Baseline",
            model_version="fallback_v1.0",
            m6_feature_importances={"slope_deg": 0.50, "profile_curvature": 0.20, "ndvi": 0.18, "tri": 0.12},
            m7_feature_importances=None,
            inference_mode="FALLBACK_HEURISTIC",
        )
