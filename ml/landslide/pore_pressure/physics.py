"""Physical models for pore-water pressure, effective stress, and slope stability.

Formulated on 1D infinite slope mechanics, Terzaghi effective stress theory,
and unsaturated soil mechanics (Fredlund & Rahardjo, 1993).

SCIENTIFIC STATUS & TERMINOLOGY NOTICE:
All slope stability metrics generated herein represent "modelled infinite-slope FoS
under representative assumptions", NOT engineering-grade Factor of Safety.
Geotechnical shear parameters (c', phi', H, gamma) are assumed representative constants
from published Himalayan colluvial literature (Martha et al., 2010; Catena 2025) because
site-specific borehole measurements are unavailable. Site-specific geotechnical investigation
is mandatory prior to civil engineering decisions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, Union
import numpy as np


class ParameterProvenanceTier(str, Enum):
    OBSERVED = "OBSERVED"                           # Direct field or authoritative instrument measurement
    DERIVED = "DERIVED"                             # Computed deterministically from observed/authoritative data
    ASSUMED_REPRESENTATIVE = "ASSUMED_REPRESENTATIVE"  # Literature assumption in absence of site-specific boreholes


# Parameter provenance registry defining value, provenance tier, physical units, plausible range, and source
PARAMETER_PROVENANCE_REGISTRY: Dict[str, Dict[str, Union[str, float, Tuple[float, float]]]] = {
    "cohesion_kpa": {
        "symbol": "c'",
        "value": 10.0,
        "units": "kPa",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (3.0, 25.0),
        "source": "Literature representative for Himalayan weathered phyllite/schist colluvium (Martha et al., 2010)",
        "sensitivity": "High sensitivity: 5 kPa decrease reduces dry FoS by ~0.25 on 35 deg slopes",
    },
    "friction_angle_deg": {
        "symbol": "phi'",
        "value": 32.0,
        "units": "degrees",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (26.0, 38.0),
        "source": "Literature representative for angular gravelly-sandy Himalayan slope debris",
        "sensitivity": "High sensitivity: 3 deg decrease reduces frictional resistance by ~10%",
    },
    "soil_thickness_m": {
        "symbol": "H",
        "value": 2.0,
        "units": "meters",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (0.5, 4.0),
        "source": "Mean regolith mantle thickness across Upper Beas valley slopes",
        "sensitivity": "Moderate sensitivity: governs failure plane depth and driving weight",
    },
    "gamma_bulk_kn_m3": {
        "symbol": "gamma_bulk",
        "value": 18.0,
        "units": "kN/m^3",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (16.0, 20.0),
        "source": "Standard unsaturated density of Himalayan sandy-silty colluvial deposits",
        "sensitivity": "Low sensitivity across plausible natural ranges",
    },
    "gamma_sat_kn_m3": {
        "symbol": "gamma_sat",
        "value": 20.0,
        "units": "kN/m^3",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (18.5, 22.0),
        "source": "Standard saturated density of Himalayan colluvium",
        "sensitivity": "Low sensitivity across plausible natural ranges",
    },
    "gamma_w_kn_m3": {
        "symbol": "gamma_w",
        "value": 9.81,
        "units": "kN/m^3",
        "provenance": ParameterProvenanceTier.DERIVED.value,
        "plausible_range": (9.80, 9.82),
        "source": "Fundamental physical constant for unit weight of fresh water at mountain temperatures",
        "sensitivity": "Constant physical reference",
    },
    "porosity": {
        "symbol": "n",
        "value": 0.40,
        "units": "dimensionless",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (0.30, 0.50),
        "source": "Representative void fraction of loosely consolidated mountain regolith",
        "sensitivity": "Governs available pore storage volume during rainfall infiltration",
    },
    "ksat_mm_h": {
        "symbol": "K_sat",
        "value": 15.0,
        "units": "mm/h",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (5.0, 50.0),
        "source": "Representative saturated hydraulic conductivity for silty-sandy loam regolith",
        "sensitivity": "Controls infiltration capacity during peak cloudburst bursts",
    },
    "phi_b_deg": {
        "symbol": "phi^b",
        "value": 15.0,
        "units": "degrees",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (10.0, 20.0),
        "source": "Fredlund & Rahardjo unsaturated shear strength angle for matric suction",
        "sensitivity": "Governs apparent suction cohesion contribution under partially saturated states",
    },
    "max_suction_kpa": {
        "symbol": "psi_max",
        "value": 50.0,
        "units": "kPa",
        "provenance": ParameterProvenanceTier.ASSUMED_REPRESENTATIVE.value,
        "plausible_range": (20.0, 100.0),
        "source": "Maximum capillary retention suction at residual dry saturation",
        "sensitivity": "Moderates dry-state hillslope cohesion bonus",
    },
}

# Standard defaults
DEFAULT_WATER_UNIT_WEIGHT = 9.81
DEFAULT_SOIL_BULK_UNIT_WEIGHT = 18.0
DEFAULT_SOIL_SAT_UNIT_WEIGHT = 20.0
DEFAULT_COHESION = 10.0
DEFAULT_FRICTION_ANGLE_DEG = 32.0
DEFAULT_SOIL_THICKNESS_M = 2.0
DEFAULT_POROSITY = 0.40
DEFAULT_KSAT_MM_H = 15.0
DEFAULT_DRAINAGE_TIMESCALE_H = 72.0
DEFAULT_PHI_B_DEG = 15.0
DEFAULT_MAX_SUCTION_KPA = 50.0


@dataclass(frozen=True)
class GeotechnicalParameters:
    """Geotechnical parameters for modelled infinite slope stability calculations.

    IMPORTANT: These parameters are ASSUMED REPRESENTATIVE values derived from published
    Himalayan regional literature, NOT site-specific borehole measurements.
    """
    cohesion_kpa: float = DEFAULT_COHESION
    friction_angle_deg: float = DEFAULT_FRICTION_ANGLE_DEG
    soil_thickness_m: float = DEFAULT_SOIL_THICKNESS_M
    gamma_bulk_kn_m3: float = DEFAULT_SOIL_BULK_UNIT_WEIGHT
    gamma_sat_kn_m3: float = DEFAULT_SOIL_SAT_UNIT_WEIGHT
    gamma_w_kn_m3: float = DEFAULT_WATER_UNIT_WEIGHT
    porosity: float = DEFAULT_POROSITY
    ksat_mm_h: float = DEFAULT_KSAT_MM_H
    phi_b_deg: float = DEFAULT_PHI_B_DEG
    max_suction_kpa: float = DEFAULT_MAX_SUCTION_KPA


def compute_effective_normal_stress(
    total_stress_kpa: Union[float, np.ndarray],
    pore_pressure_kpa: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Computes effective normal stress sigma' via Terzaghi's principle: sigma' = max(sigma - u, 0).

    Units: Total stress (kPa), Pore pressure (kPa) -> Effective normal stress (kPa).
    Soils cannot sustain tension across macro-discontinuities.
    """
    sigma_prime = total_stress_kpa - pore_pressure_kpa
    if isinstance(sigma_prime, np.ndarray):
        return np.maximum(sigma_prime, 0.0)
    return max(float(sigma_prime), 0.0)


def compute_hydrostatic_pore_pressure(
    water_table_height_m: Union[float, np.ndarray],
    slope_deg: Union[float, np.ndarray],
    gamma_w: float = DEFAULT_WATER_UNIT_WEIGHT,
) -> Union[float, np.ndarray]:
    """Computes positive pore-water pressure u (kPa) for a water table of height h_w (m)

    parallel to the slope surface:
        u = gamma_w * h_w * cos^2(theta)
    Dimensional consistency:
        [kN/m^3] * [m] * [dimensionless] = [kN/m^2] = [kPa].
    """
    theta_rad = np.radians(slope_deg)
    cos_theta = np.cos(theta_rad)
    u = gamma_w * water_table_height_m * (cos_theta ** 2)
    if isinstance(u, np.ndarray):
        return np.maximum(u, 0.0)
    return max(float(u), 0.0)


def compute_matric_suction(
    saturation_ratio: Union[float, np.ndarray],
    max_suction_kpa: float = DEFAULT_MAX_SUCTION_KPA,
) -> Union[float, np.ndarray]:
    """Computes unsaturated matric suction psi = u_a - u_w (kPa) as a function of saturation.

    Formula: psi = psi_max * (1 - S_r)^2
    Monotonic property:
    As saturation approaches 1.0 (water table reaches surface), matric suction vanishes smoothly.
    At S_r = 0, psi = psi_max.
    """
    s_clipped = np.clip(saturation_ratio, 0.0, 1.0)
    psi = max_suction_kpa * ((1.0 - s_clipped) ** 2)
    return psi


def compute_apparent_cohesion(
    matric_suction_kpa: Union[float, np.ndarray],
    phi_b_deg: float = DEFAULT_PHI_B_DEG,
) -> Union[float, np.ndarray]:
    """Computes apparent suction cohesion c_psi = psi * tan(phi^b) (kPa)

    based on Fredlund & Rahardjo (1993) unsaturated shear strength theory.
    """
    tan_phi_b = np.tan(np.radians(phi_b_deg))
    return matric_suction_kpa * tan_phi_b


def compute_transient_saturation_ratio(
    surface_moisture_proxy_pct: Optional[Union[float, np.ndarray]] = None,
    rainfall_1h_mm: Union[float, np.ndarray] = 0.0,
    antecedent_rain_3d_mm: Union[float, np.ndarray] = 0.0,
    twi: Optional[Union[float, np.ndarray]] = None,
    soil_thickness_m: float = DEFAULT_SOIL_THICKNESS_M,
    porosity: float = DEFAULT_POROSITY,
    ksat_mm_h: float = DEFAULT_KSAT_MM_H,
    initial_moisture_pct: Optional[Union[float, np.ndarray]] = None,
) -> Union[float, np.ndarray]:
    """Estimates dynamic saturation depth ratio m in [0, 1] from moisture proxy, rainfall, and terrain.

    m represents the fraction of soil mantle column that is saturated (h_w / H).

    SEMANTIC NOTICE:
    surface_moisture_proxy_pct is derived from Sentinel-2 NDMI optical/SWIR index,
    NOT volumetric in-situ soil moisture sensor data.
    """
    moist_input = surface_moisture_proxy_pct if surface_moisture_proxy_pct is not None else initial_moisture_pct
    if moist_input is None:
        moist_input = 40.0

    # Base saturation ratio from surface moisture proxy (typically 15% - 85%)
    s_base = np.clip(moist_input / 100.0, 0.0, 0.95)

    # Infiltration capacity and runoff routing
    # Short-term intense rainfall: limited by K_sat
    infil_1h = np.minimum(rainfall_1h_mm, ksat_mm_h)

    # Antecedent 3-day rainfall infiltration contribution (attenuated by drainage)
    infil_3d = antecedent_rain_3d_mm * 0.25

    # Total net water input depth in mm
    net_water_mm = infil_1h + infil_3d

    # Topographic Wetness Index (lateral flow concentration factor)
    if twi is not None:
        twi_factor = np.clip(1.0 + 0.08 * (twi - 8.0), 0.5, 2.0)
    else:
        twi_factor = 1.0

    net_water_effective_m = (net_water_mm / 1000.0) * twi_factor

    # Available pore storage depth: n * (1 - S_base) * H
    pore_storage_m = np.maximum(porosity * (1.0 - s_base) * soil_thickness_m, 0.05)
    delta_sat = net_water_effective_m / pore_storage_m

    m = np.clip(s_base * 0.4 + delta_sat * 0.6, 0.0, 1.0)
    return m


def compute_infinite_slope_fos(
    slope_deg: Union[float, np.ndarray],
    pore_pressure_kpa: Union[float, np.ndarray],
    matric_suction_kpa: Union[float, np.ndarray],
    params: Optional[GeotechnicalParameters] = None,
) -> Union[float, np.ndarray]:
    """Calculates modelled 1D Infinite Slope Factor of Safety (FoS) under representative assumptions.

    TERMINOLOGY NOTICE:
    This is a "modelled infinite-slope FoS under representative assumptions", NOT
    an engineering-grade Factor of Safety. Geotechnical design certification requires
    site-specific borehole investigation.

    Limit equilibrium formulation:
        Resisting Force = c' + c_psi + (sigma - u) * tan(phi')
        Driving Force   = gamma_total * H * sin(theta) * cos(theta)
        FoS = Resisting Force / Driving Force

    Dimensional consistency:
        Resisting: [kPa]
        Driving: [kN/m^3] * [m] * [dimensionless] = [kN/m^2] = [kPa]
        FoS: [kPa] / [kPa] = [dimensionless ratio]
    """
    if params is None:
        params = GeotechnicalParameters()

    theta_deg = np.maximum(slope_deg, 0.5)
    theta_rad = np.radians(theta_deg)
    sin_theta = np.sin(theta_rad)
    cos_theta = np.cos(theta_rad)

    # Unit weight blend based on saturation
    gamma_total = params.gamma_bulk_kn_m3 + (params.gamma_sat_kn_m3 - params.gamma_bulk_kn_m3) * np.clip(pore_pressure_kpa / (params.gamma_w_kn_m3 * params.soil_thickness_m + 1e-6), 0.0, 1.0)
    total_stress = gamma_total * params.soil_thickness_m * (cos_theta ** 2)
    effective_stress = compute_effective_normal_stress(total_stress, pore_pressure_kpa)
    c_apparent = compute_apparent_cohesion(matric_suction_kpa, params.phi_b_deg)

    tan_phi = np.tan(np.radians(params.friction_angle_deg))
    tau_resisting = params.cohesion_kpa + c_apparent + effective_stress * tan_phi
    tau_driving = gamma_total * params.soil_thickness_m * sin_theta * cos_theta
    tau_driving = np.maximum(tau_driving, 0.1)

    fos = tau_resisting / tau_driving

    if isinstance(fos, np.ndarray):
        return np.clip(fos, 0.05, 10.0)
    return float(np.clip(fos, 0.05, 10.0))


def compute_slope_stability_indicator(
    fos: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Computes the normalized Relative Slope Stability Indicator (SSI) in [0, 1].

    Formula: SSI = FoS / (1.0 + FoS)
    - At FoS = 1.0 (Limit Equilibrium), SSI = 0.50.
    - FoS < 1.0 (Unstable/Failing) -> SSI in [0.0, 0.50).
    - FoS > 1.0 (Stable) -> SSI in (0.50, 1.0].
    """
    ssi = fos / (1.0 + fos)
    if isinstance(ssi, np.ndarray):
        return np.clip(ssi, 0.0, 1.0)
    return float(np.clip(ssi, 0.0, 1.0))
