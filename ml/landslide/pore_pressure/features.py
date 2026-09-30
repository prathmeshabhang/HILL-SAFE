"""Feature engineering and bridge pipeline for pore-water pressure & slope stability.

Bridges geospatial terrain, soil moisture proxies, and rainfall observations into
physically grounded geotechnical features for downstream modeling and risk fusion.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .model import PorePressureOutput, PoreWaterPressureEstimator, SlopeStabilityEngine, SlopeStabilityOutput
from .physics import GeotechnicalParameters


M7_BASELINE_FEATURES = [
    "susceptibility_class",
    "slope_deg",
    "rainfall_1h",
    "antecedent_rain_3d",
    "soil_moisture_pct",
]

HYDROLOGICAL_ENGINEERED_FEATURES = [
    "pore_pressure_est_kpa",
    "delta_pore_pressure_kpa",
    "matric_suction_est_kpa",
    "effective_normal_stress_kpa",
    "slope_stability_indicator",
]

M7_EXTENDED_FEATURES = M7_BASELINE_FEATURES + HYDROLOGICAL_ENGINEERED_FEATURES


class HydrologicalFeaturePipeline:
    """Computes physical pore pressure and stability features from hydrological and terrain inputs."""

    def __init__(self, params: Optional[GeotechnicalParameters] = None):
        self.params = params or GeotechnicalParameters()
        self.pwp_estimator = PoreWaterPressureEstimator(self.params)
        self.stability_engine = SlopeStabilityEngine(self.params)

    def extract_features_df(
        self,
        df: pd.DataFrame,
        twi_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """Enriches a DataFrame with physically derived pore pressure and slope stability features.

        Guarantees zero future-leakage: all calculations depend strictly on instantaneous
        rainfall (rainfall_1h), antecedent rainfall (antecedent_rain_3d), and current soil moisture.
        """
        # Check for moisture column (either surface_moisture_proxy_pct or soil_moisture_pct)
        moist_col = "surface_moisture_proxy_pct" if "surface_moisture_proxy_pct" in df.columns else (
            "soil_moisture_pct" if "soil_moisture_pct" in df.columns else None
        )
        required = ["slope_deg", "rainfall_1h", "antecedent_rain_3d"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column in dataframe: {col}")
        if moist_col is None:
            raise ValueError("Missing required moisture proxy column in dataframe: 'surface_moisture_proxy_pct' or 'soil_moisture_pct'")

        slope = df["slope_deg"].values.astype(np.float32)
        moisture = df[moist_col].values.astype(np.float32)
        r1h = df["rainfall_1h"].values.astype(np.float32)
        r3d = df["antecedent_rain_3d"].values.astype(np.float32)

        twi = df[twi_col].values.astype(np.float32) if twi_col and twi_col in df.columns else None

        # 1. Estimate pore-water pressure and suction
        pwp_out = self.pwp_estimator.estimate_grid(
            slope_deg=slope,
            moisture_pct=moisture,
            rainfall_1h_mm=r1h,
            antecedent_rain_3d_mm=r3d,
            twi=twi,
        )

        # 2. Evaluate infinite slope stability and SSI
        stab_out = self.stability_engine.evaluate_grid(
            slope_deg=slope,
            pore_pressure_kpa=pwp_out.pore_pressure_kpa,
            matric_suction_kpa=pwp_out.matric_suction_kpa,
        )

        df_out = df.copy()
        df_out["pore_pressure_est_kpa"] = pwp_out.pore_pressure_kpa
        df_out["delta_pore_pressure_kpa"] = pwp_out.delta_pore_pressure_kpa
        df_out["matric_suction_est_kpa"] = pwp_out.matric_suction_kpa
        df_out["effective_normal_stress_kpa"] = stab_out.effective_stress_kpa
        df_out["modelled_infinite_slope_fos"] = stab_out.factor_of_safety
        df_out["slope_stability_indicator"] = stab_out.slope_stability_indicator

        return df_out

    def extract_features_spatial(
        self,
        slope_deg: np.ndarray,
        moisture_pct: Optional[np.ndarray] = None,
        rainfall_1h_mm: np.ndarray = None,
        antecedent_rain_3d_mm: np.ndarray = None,
        twi: Optional[np.ndarray] = None,
        surface_moisture_proxy_pct: Optional[np.ndarray] = None,
    ) -> Tuple[PorePressureOutput, SlopeStabilityOutput]:
        """Spatial 2D grid feature extraction for real-scene satellite rasters.

        surface_moisture_proxy_pct (or moisture_pct) is the Sentinel-2 NDMI moisture proxy.
        """
        moist = surface_moisture_proxy_pct if surface_moisture_proxy_pct is not None else moisture_pct
        if moist is None:
            raise ValueError("Must provide surface_moisture_proxy_pct (or moisture_pct)")

        pwp_out = self.pwp_estimator.estimate_grid(
            slope_deg=slope_deg,
            surface_moisture_proxy_pct=moist,
            rainfall_1h_mm=rainfall_1h_mm,
            antecedent_rain_3d_mm=antecedent_rain_3d_mm,
            twi=twi,
        )

        stab_out = self.stability_engine.evaluate_grid(
            slope_deg=slope_deg,
            pore_pressure_kpa=pwp_out.pore_pressure_kpa,
            matric_suction_kpa=pwp_out.matric_suction_kpa,
        )

        return pwp_out, stab_out
