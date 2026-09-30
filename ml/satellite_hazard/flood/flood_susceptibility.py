"""
flood_susceptibility.py — Satellite-Derived Flood Extent & Spatial Susceptibility
================================================================================
Combines:
  - Satellite MNDWI (active water surface and flood expansion)
  - Topographic Wetness Index (TWI - moisture accumulation)
  - Height Above Nearest Drainage (HAND - low-lying river corridor inundation)
  - Slope (flat valley floors vs steep runoff shedding)

Produces:
  - Continuous flood susceptibility score [0.0, 1.0]
  - Active floodwater mask (binary)
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
class FloodAnalysisResult:
    shape: Tuple[int, int]
    susceptibility_score: np.ndarray      # 2D float32 [0, 1] (fused flood susceptibility)
    active_water_mask: np.ndarray         # 2D bool
    susceptibility_classes: np.ndarray    # 2D uint8 (0: Very Low, 1: Low, 2: Moderate, 3: High, 4: Very High)
    high_susceptibility_area_pct: float
    active_water_area_pct: float
    m2_flood_probability: Optional[np.ndarray] = None          # 2D float32 [0, 1] (Model M2 Calibrated XGBoost)
    unet_inundation_probability: Optional[np.ndarray] = None   # 2D float32 [0, 1] (9-Ch PyTorch U-Net)
    model_name: str = "Multimodal_UNet_and_Model_M2_XGBoost"
    model_version: str = "v1.0"
    m2_feature_importances: Optional[Dict[str, float]] = None
    inference_mode: str = "ML_INFERENCE"  # "ML_INFERENCE" or "FALLBACK_HEURISTIC"


class SatelliteFloodModel:
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
                print(f"[SatelliteFloodModel] Warning initializing SpatialMLEngine: {e}")
                self._ml_engine = False
        return self._ml_engine

    def analyze(
        self,
        spectral: SpectralIndices,
        terrain: TerrainFeatures,
        stack_9ch: Optional[np.ndarray] = None,
        event_rainfall_1h_mm: float = 25.0,
        antecedent_rain_3d_mm: float = 85.0,
        cwc_river_level_m: float = 6.2,
        cwc_rate_of_rise_m_hr: float = 0.35,
    ) -> FloodAnalysisResult:
        """
        Calculates spatial flood inundation and susceptibility using:
          - Model M4: 9-Channel Multimodal PyTorch U-Net for SAR + Optical flood segmentation
          - Model M2: Calibrated XGBoost for topo-hydrological susceptibility
        Falls back to calibrated physical heuristics if ML artifacts are unavailable or stack_9ch is None.
        """
        # 1. Attempt Authentic ML Inference via SpatialMLEngine
        if stack_9ch is not None and self.ml_engine and self.ml_engine.unet_model is not None:
            try:
                ml_res = self.ml_engine.infer_flood_suite(
                    stack_9ch=stack_9ch,
                    terrain=terrain,
                    spectral=spectral,
                    event_rainfall_1h_mm=event_rainfall_1h_mm,
                    antecedent_rain_3d_mm=antecedent_rain_3d_mm,
                    cwc_river_level_m=cwc_river_level_m,
                    cwc_rate_of_rise_m_hr=cwc_rate_of_rise_m_hr,
                )
                classes = np.zeros(spectral.shape, dtype=np.uint8)
                classes[ml_res.fused_flood_susceptibility >= 0.20] = 1
                classes[ml_res.fused_flood_susceptibility >= 0.40] = 2
                classes[ml_res.fused_flood_susceptibility >= 0.60] = 3
                classes[ml_res.fused_flood_susceptibility >= 0.80] = 4

                return FloodAnalysisResult(
                    shape=spectral.shape,
                    susceptibility_score=ml_res.fused_flood_susceptibility,
                    active_water_mask=ml_res.active_inundation_mask,
                    susceptibility_classes=classes,
                    high_susceptibility_area_pct=ml_res.high_flood_area_pct,
                    active_water_area_pct=ml_res.active_inundation_area_pct,
                    m2_flood_probability=ml_res.m2_flood_probability,
                    unet_inundation_probability=ml_res.unet_inundation_probability,
                    model_name="Multimodal_UNet_and_Model_M2_XGBoost",
                    model_version="v1.0",
                    m2_feature_importances=ml_res.m2_feature_importances,
                    inference_mode="ML_INFERENCE",
                )
            except Exception as ex:
                print(f"[SatelliteFloodModel] ML inference failed ({ex}). Falling back to heuristic...")

        # 2. Fallback Heuristic / Physical Equations
        mndwi = spectral.mndwi
        twi = terrain.topographic_wetness_index
        hand = terrain.height_above_nearest_drainage_m
        slope = terrain.slope_deg

        # Active Water Detection: High MNDWI (>0.05) and low slope (<12 deg)
        active_water = (mndwi > 0.05) & (slope < 12.0)

        # Continuous Topo-Hydrological Flood Susceptibility
        # - HAND: 0m = extreme risk (1.0), >55m = minimal risk (0.0)
        hand_factor = np.clip(1.0 - (hand / 55.0), 0.0, 1.0)

        # - TWI: High TWI (>10) = high moisture collection
        twi_factor = np.clip((twi - 4.0) / 8.0, 0.0, 1.0)

        # - Slope: Flat valley bottoms (<6 deg) pond water; steep slopes shed water
        slope_factor = np.clip(1.0 - (slope / 22.0), 0.0, 1.0)

        # - Spectral moisture: NDMI saturation
        moisture_factor = np.clip((spectral.ndmi + 0.10) / 0.70, 0.0, 1.0)

        # Multi-factor weighted fusion
        susceptibility = (
            0.40 * hand_factor +
            0.25 * twi_factor +
            0.20 * slope_factor +
            0.15 * moisture_factor
        )

        # Water bodies and active flood zones immediately pegged to very high susceptibility
        susceptibility[active_water] = np.maximum(susceptibility[active_water], 0.88)
        susceptibility = np.clip(susceptibility, 0.0, 1.0).astype(np.float32)

        # Discretize into 5 standard classes
        classes = np.zeros(spectral.shape, dtype=np.uint8)
        classes[susceptibility >= 0.20] = 1
        classes[susceptibility >= 0.40] = 2
        classes[susceptibility >= 0.60] = 3
        classes[susceptibility >= 0.80] = 4

        high_pct = float(np.mean(susceptibility >= 0.60) * 100.0)
        water_pct = float(np.mean(active_water) * 100.0)

        return FloodAnalysisResult(
            shape=spectral.shape,
            susceptibility_score=susceptibility,
            active_water_mask=active_water,
            susceptibility_classes=classes,
            high_susceptibility_area_pct=round(high_pct, 2),
            active_water_area_pct=round(water_pct, 2),
            m2_flood_probability=None,
            unet_inundation_probability=None,
            model_name="Topo_Hydrologic_Heuristic_Baseline",
            model_version="v1.0",
            m2_feature_importances=None,
            inference_mode="FALLBACK_HEURISTIC",
        )
