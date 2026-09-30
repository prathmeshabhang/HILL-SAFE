"""Pore-Water Pressure and Slope Stability Estimation Models.

Coordinates the physical simulation of pore-water pressure generation,
suction depletion, effective normal stress reduction, and 1D infinite slope Factor of Safety.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union
import numpy as np

from .physics import (
    DEFAULT_SOIL_THICKNESS_M,
    GeotechnicalParameters,
    compute_effective_normal_stress,
    compute_hydrostatic_pore_pressure,
    compute_infinite_slope_fos,
    compute_matric_suction,
    compute_slope_stability_indicator,
    compute_transient_saturation_ratio,
)


@dataclass
class PorePressureOutput:
    """Output container for pore-water pressure estimation."""
    pore_pressure_kpa: np.ndarray          # Positive hydrostatic pressure at failure plane (u)
    delta_pore_pressure_kpa: np.ndarray    # Dynamic increase over dry baseline (Delta u)
    matric_suction_kpa: np.ndarray         # Apparent matric suction in unsaturated portion (psi)
    saturation_ratio: np.ndarray           # Soil column saturation ratio m in [0, 1]
    confidence_score: np.ndarray           # Modelled confidence score in [0, 1]


@dataclass
class SlopeStabilityOutput:
    """Output container for slope stability evaluation."""
    factor_of_safety: np.ndarray           # Theoretical infinite slope FoS
    slope_stability_indicator: np.ndarray  # Normalized Relative Slope Stability Indicator (SSI in [0, 1])
    effective_stress_kpa: np.ndarray       # Effective normal stress sigma' = sigma - u
    critical_failure_mask: np.ndarray      # Boolean mask where FoS < 1.0
    stability_class: np.ndarray            # 0=Critical (FoS < 1.0), 1=Marginal (1.0 <= FoS < 1.3), 2=Stable (FoS >= 1.3)


class PoreWaterPressureEstimator:
    """Estimates spatial and point pore-water pressure response from rainfall, moisture, and terrain."""

    def __init__(self, default_params: Optional[GeotechnicalParameters] = None):
        self.params = default_params or GeotechnicalParameters()

    def estimate_grid(
        self,
        slope_deg: np.ndarray,
        moisture_pct: Optional[np.ndarray] = None,
        rainfall_1h_mm: np.ndarray = None,
        antecedent_rain_3d_mm: np.ndarray = None,
        twi: Optional[np.ndarray] = None,
        soil_thickness_m: Optional[Union[float, np.ndarray]] = None,
        surface_moisture_proxy_pct: Optional[np.ndarray] = None,
    ) -> PorePressureOutput:
        """Computes pore-water pressure distribution across a 2D spatial grid.

        SEMANTIC DISTINCTION:
        surface_moisture_proxy_pct (or moisture_pct) is derived from Sentinel-2 NDMI,
        representing an optical/SWIR surface wetness proxy (18% - 90%), NOT volumetric
        in-situ soil moisture or direct piezometric pressure.

        Returns:
            PorePressureOutput with arrays matching input shape.
        """
        moist = surface_moisture_proxy_pct if surface_moisture_proxy_pct is not None else moisture_pct
        if moist is None:
            raise ValueError("Must provide surface_moisture_proxy_pct (or moisture_pct)")

        if rainfall_1h_mm is None:
            rainfall_1h_mm = np.zeros_like(slope_deg, dtype=np.float32)
        if antecedent_rain_3d_mm is None:
            antecedent_rain_3d_mm = np.zeros_like(slope_deg, dtype=np.float32)

        h_m = soil_thickness_m if soil_thickness_m is not None else self.params.soil_thickness_m

        # 1. Compute dynamic saturation ratio m(t) in [0, 1]
        m = compute_transient_saturation_ratio(
            surface_moisture_proxy_pct=moist,
            rainfall_1h_mm=rainfall_1h_mm,
            antecedent_rain_3d_mm=antecedent_rain_3d_mm,
            twi=twi,
            soil_thickness_m=self.params.soil_thickness_m,
            porosity=self.params.porosity,
            ksat_mm_h=self.params.ksat_mm_h,
        )

        # Baseline dry saturation ratio (antecedent & initial only)
        m_baseline = np.clip(moist / 100.0 * 0.4, 0.0, 1.0)

        # 2. Water table height h_w = m * H
        hw_m = m * h_m
        hw_base_m = m_baseline * h_m

        # 3. Positive pore-water pressure u = gamma_w * h_w * cos^2(theta)
        u_kpa = compute_hydrostatic_pore_pressure(
            water_table_height_m=hw_m,
            slope_deg=slope_deg,
            gamma_w=self.params.gamma_w_kn_m3,
        )

        u_base_kpa = compute_hydrostatic_pore_pressure(
            water_table_height_m=hw_base_m,
            slope_deg=slope_deg,
            gamma_w=self.params.gamma_w_kn_m3,
        )

        delta_u_kpa = np.maximum(u_kpa - u_base_kpa, 0.0)

        # 4. Matric suction in unsaturated zone
        psi_kpa = compute_matric_suction(
            saturation_ratio=m,
            max_suction_kpa=self.params.max_suction_kpa,
        )

        # 5. Scientific confidence score
        # High confidence when inputs are within normal physical limits;
        # degraded if rainfall or slope are in extreme uncalibrated domains
        conf = np.ones_like(u_kpa, dtype=np.float32) * 0.85
        conf = np.where((slope_deg < 0.0) | (slope_deg > 80.0), conf * 0.7, conf)
        conf = np.where((rainfall_1h_mm > 150.0), conf * 0.8, conf)
        conf = np.clip(conf, 0.20, 0.95)

        return PorePressureOutput(
            pore_pressure_kpa=u_kpa.astype(np.float32),
            delta_pore_pressure_kpa=delta_u_kpa.astype(np.float32),
            matric_suction_kpa=psi_kpa.astype(np.float32),
            saturation_ratio=m.astype(np.float32),
            confidence_score=conf.astype(np.float32),
        )

    def estimate_point(
        self,
        slope_deg: float,
        moisture_pct: Optional[float] = None,
        rainfall_1h_mm: float = 0.0,
        antecedent_rain_3d_mm: float = 0.0,
        twi: Optional[float] = None,
        surface_moisture_proxy_pct: Optional[float] = None,
    ) -> Dict[str, float]:
        """Convenience 1D scalar estimation for a single borehole or sensor site."""
        val = surface_moisture_proxy_pct if surface_moisture_proxy_pct is not None else moisture_pct
        if val is None:
            val = 40.0
        arr_slope = np.array([slope_deg], dtype=np.float32)
        arr_moist = np.array([val], dtype=np.float32)
        arr_r1h = np.array([rainfall_1h_mm], dtype=np.float32)
        arr_r3d = np.array([antecedent_rain_3d_mm], dtype=np.float32)
        arr_twi = np.array([twi], dtype=np.float32) if twi is not None else None

        res = self.estimate_grid(arr_slope, arr_moist, arr_r1h, arr_r3d, arr_twi)
        return {
            "pore_pressure_kpa": float(res.pore_pressure_kpa[0]),
            "delta_pore_pressure_kpa": float(res.delta_pore_pressure_kpa[0]),
            "matric_suction_kpa": float(res.matric_suction_kpa[0]),
            "saturation_ratio": float(res.saturation_ratio[0]),
            "confidence_score": float(res.confidence_score[0]),
        }


class SlopeStabilityEngine:
    """Evaluates spatial 1D infinite slope Factor of Safety and Relative Stability Indicator."""

    def __init__(self, default_params: Optional[GeotechnicalParameters] = None):
        self.params = default_params or GeotechnicalParameters()

    def evaluate_grid(
        self,
        slope_deg: np.ndarray,
        pore_pressure_kpa: np.ndarray,
        matric_suction_kpa: np.ndarray,
    ) -> SlopeStabilityOutput:
        """Computes Factor of Safety (FoS) and Relative Slope Stability Indicator (SSI) on grid."""
        fos = compute_infinite_slope_fos(
            slope_deg=slope_deg,
            pore_pressure_kpa=pore_pressure_kpa,
            matric_suction_kpa=matric_suction_kpa,
            params=self.params,
        )

        ssi = compute_slope_stability_indicator(fos)

        theta_rad = np.radians(np.maximum(slope_deg, 0.5))
        total_stress = self.params.gamma_bulk_kn_m3 * self.params.soil_thickness_m * (np.cos(theta_rad) ** 2)
        eff_stress = compute_effective_normal_stress(total_stress, pore_pressure_kpa)

        crit_mask = fos < 1.0

        stability_class = np.zeros_like(fos, dtype=np.int32)
        stability_class[fos >= 1.3] = 2  # Stable
        stability_class[(fos >= 1.0) & (fos < 1.3)] = 1  # Marginal
        stability_class[fos < 1.0] = 0  # Critical

        return SlopeStabilityOutput(
            factor_of_safety=fos.astype(np.float32),
            slope_stability_indicator=ssi.astype(np.float32),
            effective_stress_kpa=eff_stress.astype(np.float32),
            critical_failure_mask=crit_mask,
            stability_class=stability_class,
        )

    def evaluate_point(
        self,
        slope_deg: float,
        pore_pressure_kpa: float,
        matric_suction_kpa: float,
    ) -> Dict[str, Union[float, bool, str]]:
        """Convenience 1D scalar evaluation for a single location."""
        arr_slope = np.array([slope_deg], dtype=np.float32)
        arr_u = np.array([pore_pressure_kpa], dtype=np.float32)
        arr_psi = np.array([matric_suction_kpa], dtype=np.float32)

        res = self.evaluate_grid(arr_slope, arr_u, arr_psi)
        fos_val = float(res.factor_of_safety[0])
        ssi_val = float(res.slope_stability_indicator[0])
        cls_code = int(res.stability_class[0])
        cls_name = "CRITICAL" if cls_code == 0 else ("MARGINAL" if cls_code == 1 else "STABLE")

        return {
            "factor_of_safety": fos_val,
            "slope_stability_indicator": ssi_val,
            "effective_stress_kpa": float(res.effective_stress_kpa[0]),
            "critical_failure": bool(res.critical_failure_mask[0]),
            "stability_class": cls_name,
        }
