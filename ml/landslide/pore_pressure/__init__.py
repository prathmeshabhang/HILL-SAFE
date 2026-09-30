"""Pore-Water Pressure and Slope Stability Layer for FLOODY SHIELD.

Physically grounded limit-equilibrium and transient saturation mechanics
integrated into the landslide susceptibility and trigger architecture.
"""

from .export import (
    generate_spatial_geotiffs,
    generate_timeseries_animation_snapshots,
)
from .features import (
    HYDROLOGICAL_ENGINEERED_FEATURES,
    M7_BASELINE_FEATURES,
    M7_EXTENDED_FEATURES,
    HydrologicalFeaturePipeline,
)
from .model import (
    PorePressureOutput,
    PoreWaterPressureEstimator,
    SlopeStabilityEngine,
    SlopeStabilityOutput,
)
from .physics import (
    DEFAULT_COHESION,
    DEFAULT_DRAINAGE_TIMESCALE_H,
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_KSAT_MM_H,
    DEFAULT_MAX_SUCTION_KPA,
    DEFAULT_PHI_B_DEG,
    DEFAULT_POROSITY,
    DEFAULT_SOIL_BULK_UNIT_WEIGHT,
    DEFAULT_SOIL_SAT_UNIT_WEIGHT,
    DEFAULT_SOIL_THICKNESS_M,
    DEFAULT_WATER_UNIT_WEIGHT,
    GeotechnicalParameters,
    compute_apparent_cohesion,
    compute_effective_normal_stress,
    compute_hydrostatic_pore_pressure,
    compute_infinite_slope_fos,
    compute_matric_suction,
    compute_slope_stability_indicator,
    compute_transient_saturation_ratio,
)
from .sensor import (
    MAX_PLAUSIBLE_RATE_KPA_PER_HR,
    VALID_MAX_PORE_PRESSURE_KPA,
    VALID_MIN_PORE_PRESSURE_KPA,
    PiezometerReading,
    SensorQualityAuditor,
    TensiometerReading,
    compare_model_with_sensor,
)
from .validation import (
    DATA_AVAILABILITY_AUDIT,
    MANDATORY_SCIENTIFIC_DISCLAIMER,
    run_data_leakage_audit,
    run_m7_integration_experiment,
)

__all__ = [
    # Physics
    "GeotechnicalParameters",
    "compute_effective_normal_stress",
    "compute_hydrostatic_pore_pressure",
    "compute_matric_suction",
    "compute_apparent_cohesion",
    "compute_transient_saturation_ratio",
    "compute_infinite_slope_fos",
    "compute_slope_stability_indicator",
    "DEFAULT_WATER_UNIT_WEIGHT",
    "DEFAULT_SOIL_BULK_UNIT_WEIGHT",
    "DEFAULT_SOIL_SAT_UNIT_WEIGHT",
    "DEFAULT_COHESION",
    "DEFAULT_FRICTION_ANGLE_DEG",
    "DEFAULT_SOIL_THICKNESS_M",
    "DEFAULT_POROSITY",
    "DEFAULT_KSAT_MM_H",
    "DEFAULT_DRAINAGE_TIMESCALE_H",
    "DEFAULT_PHI_B_DEG",
    "DEFAULT_MAX_SUCTION_KPA",
    # Sensor
    "PiezometerReading",
    "TensiometerReading",
    "SensorQualityAuditor",
    "compare_model_with_sensor",
    "VALID_MIN_PORE_PRESSURE_KPA",
    "VALID_MAX_PORE_PRESSURE_KPA",
    "MAX_PLAUSIBLE_RATE_KPA_PER_HR",
    # Model
    "PorePressureOutput",
    "SlopeStabilityOutput",
    "PoreWaterPressureEstimator",
    "SlopeStabilityEngine",
    # Features
    "HydrologicalFeaturePipeline",
    "M7_BASELINE_FEATURES",
    "HYDROLOGICAL_ENGINEERED_FEATURES",
    "M7_EXTENDED_FEATURES",
    # Export
    "generate_spatial_geotiffs",
    "generate_timeseries_animation_snapshots",
    # Validation
    "DATA_AVAILABILITY_AUDIT",
    "MANDATORY_SCIENTIFIC_DISCLAIMER",
    "run_data_leakage_audit",
    "run_m7_integration_experiment",
]
