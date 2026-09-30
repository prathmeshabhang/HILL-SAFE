"""GIS and Time-Series Export Generator for Pore-Water Pressure and Slope Stability.

Generates:
1. Spatial GeoTIFF rasters in data/satellite_output/:
   - pore_pressure_estimate_kpa.tif
   - pore_pressure_change_kpa.tif
   - slope_stability_indicator.tif
   - modelled_infinite_slope_fos.tif
   - landslide_risk_hydrological.tif
2. Temporal sequence of storm event snapshots in data/hazard_timeseries/2023-07-09/:
   - T_0, T_15, T_30, T_45, T_60
   - Manifest JSON with storm progression metrics for UI animation
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import tifffile

from .features import HydrologicalFeaturePipeline
from .physics import GeotechnicalParameters


def generate_spatial_geotiffs(
    output_dir: Optional[Path] = None,
    slope_grid: Optional[np.ndarray] = None,
    moisture_grid: Optional[np.ndarray] = None,
    rainfall_1h_mm: float = 25.0,
    antecedent_rain_3d_mm: float = 85.0,
    m6_susceptibility: Optional[np.ndarray] = None,
) -> Dict[str, Path]:
    """Generates and writes standard pore-pressure and slope stability GeoTIFFs to output_dir."""
    if output_dir is None:
        output_dir = Path(__file__).resolve().parents[3] / "data" / "satellite_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # If grids not provided, load or derive from existing satellite outputs
    if slope_grid is None or moisture_grid is None:
        # Load from existing satellite rasters if available
        m7_path = output_dir / "landslide_m7_trigger.tif"
        m6_path = output_dir / "landslide_m6_susceptibility.tif"

        if m7_path.exists() and m6_path.exists():
            base_shape = tifffile.imread(str(m7_path)).shape
        else:
            base_shape = (500, 400)

        rows, cols = base_shape
        # Create realistic Upper Beas slope profile (mean ~32 deg, 5 to 65 deg)
        y, x = np.mgrid[0:rows, 0:cols]
        slope_grid = 15.0 + 25.0 * np.sin(x / 35.0) ** 2 + 20.0 * np.cos(y / 40.0) ** 2
        slope_grid = np.clip(slope_grid, 2.0, 68.0).astype(np.float32)

        # Soil moisture proxy: ~35% - 85%
        moisture_grid = 45.0 + 25.0 * np.sin(y / 50.0) * np.cos(x / 50.0) + 15.0 * (slope_grid / 60.0)
        moisture_grid = np.clip(moisture_grid, 20.0, 92.0).astype(np.float32)

    if m6_susceptibility is None:
        m6_path = output_dir / "landslide_m6_susceptibility.tif"
        if m6_path.exists():
            m6_susceptibility = tifffile.imread(str(m6_path)).astype(np.float32)
        else:
            m6_susceptibility = np.clip(slope_grid / 60.0, 0.0, 1.0).astype(np.float32)

    r1h_arr = np.full_like(slope_grid, rainfall_1h_mm, dtype=np.float32)
    r3d_arr = np.full_like(slope_grid, antecedent_rain_3d_mm, dtype=np.float32)

    pipeline = HydrologicalFeaturePipeline()
    pwp_out, stab_out = pipeline.extract_features_spatial(
        slope_deg=slope_grid,
        moisture_pct=moisture_grid,
        rainfall_1h_mm=r1h_arr,
        antecedent_rain_3d_mm=r3d_arr,
    )

    # Hydrological landslide risk: combines susceptibility with instability (1 - SSI)
    # When slope is highly unstable (SSI -> 0), risk amplifies susceptibility
    hydrological_risk = np.clip(
        0.5 * m6_susceptibility + 0.5 * (1.0 - stab_out.slope_stability_indicator),
        0.0,
        1.0,
    ).astype(np.float32)

    rasters = {
        "pore_pressure_estimate_kpa.tif": pwp_out.pore_pressure_kpa,
        "pore_pressure_change_kpa.tif": pwp_out.delta_pore_pressure_kpa,
        "slope_stability_indicator.tif": stab_out.slope_stability_indicator,
        "modelled_infinite_slope_fos.tif": stab_out.factor_of_safety,
        "landslide_risk_hydrological.tif": hydrological_risk,
    }

    saved_files = {}
    for filename, data in rasters.items():
        dest = output_dir / filename
        tifffile.imwrite(str(dest), data.astype(np.float32))
        saved_files[filename] = dest

    return saved_files


def generate_timeseries_animation_snapshots(
    base_output_dir: Optional[Path] = None,
    event_date: str = "2023-07-09",
    shape: Tuple[int, int] = (500, 400),
) -> Dict[str, Any]:
    """Generates 5 temporal snapshots simulating the 2023-07-09 cloudburst storm progression.

    Snapshots:
      T_0:  Pre-storm baseline (Rain=5 mm/h, Antecedent=40 mm)
      T_15: Early convective rain (Rain=25 mm/h, Antecedent=60 mm)
      T_30: Peak cloudburst (Rain=65 mm/h, Antecedent=85 mm)
      T_45: Extreme storm saturation (Rain=95 mm/h, Antecedent=110 mm)
      T_60: Post-peak high saturation / failure crisis (Rain=40 mm/h, Antecedent=140 mm)
    """
    if base_output_dir is None:
        base_output_dir = Path(__file__).resolve().parents[3] / "data" / "hazard_timeseries"
    target_dir = base_output_dir / event_date
    target_dir.mkdir(parents=True, exist_ok=True)

    rows, cols = shape
    y, x = np.mgrid[0:rows, 0:cols]
    slope = 15.0 + 25.0 * np.sin(x / 35.0) ** 2 + 20.0 * np.cos(y / 40.0) ** 2
    slope = np.clip(slope, 2.0, 68.0).astype(np.float32)

    scenarios = [
        {"timestep": "T_0", "minutes": 0, "rain_1h": 5.0, "rain_3d": 40.0, "base_moist": 35.0, "desc": "Pre-storm baseline"},
        {"timestep": "T_15", "minutes": 15, "rain_1h": 25.0, "rain_3d": 60.0, "base_moist": 55.0, "desc": "Early convective cell"},
        {"timestep": "T_30", "minutes": 30, "rain_1h": 65.0, "rain_3d": 85.0, "base_moist": 75.0, "desc": "Peak cloudburst intensity"},
        {"timestep": "T_45", "minutes": 45, "rain_1h": 95.0, "rain_3d": 110.0, "base_moist": 88.0, "desc": "Extreme infiltration & saturation"},
        {"timestep": "T_60", "minutes": 60, "rain_1h": 40.0, "rain_3d": 140.0, "base_moist": 92.0, "desc": "Maximum transient pore pressure & slope failure window"},
    ]

    pipeline = HydrologicalFeaturePipeline()
    manifest_entries = []

    for sc in scenarios:
        t_id = sc["timestep"]
        t_dir = target_dir / t_id
        t_dir.mkdir(parents=True, exist_ok=True)

        moist_grid = np.clip(sc["base_moist"] + 10.0 * np.sin(y / 40.0), 15.0, 95.0).astype(np.float32)
        r1h_grid = np.full_like(slope, sc["rain_1h"], dtype=np.float32)
        r3d_grid = np.full_like(slope, sc["rain_3d"], dtype=np.float32)

        pwp, stab = pipeline.extract_features_spatial(
            slope_deg=slope,
            moisture_pct=moist_grid,
            rainfall_1h_mm=r1h_grid,
            antecedent_rain_3d_mm=r3d_grid,
        )

        pwp_path = t_dir / "pore_pressure_kpa.tif"
        ssi_path = t_dir / "slope_stability_indicator.tif"
        fos_path = t_dir / "factor_of_safety.tif"

        tifffile.imwrite(str(pwp_path), pwp.pore_pressure_kpa)
        tifffile.imwrite(str(ssi_path), stab.slope_stability_indicator)
        tifffile.imwrite(str(fos_path), stab.factor_of_safety)

        mean_u = float(round(np.mean(pwp.pore_pressure_kpa), 2))
        max_u = float(round(np.max(pwp.pore_pressure_kpa), 2))
        mean_ssi = float(round(np.mean(stab.slope_stability_indicator), 3))
        critical_pct = float(round(np.mean(stab.critical_failure_mask) * 100.0, 2))

        entry = {
            "timestep": t_id,
            "minutes_from_onset": sc["minutes"],
            "description": sc["desc"],
            "rainfall_rate_mm_h": sc["rain_1h"],
            "antecedent_3d_mm": sc["rain_3d"],
            "mean_pore_pressure_kpa": mean_u,
            "max_pore_pressure_kpa": max_u,
            "mean_slope_stability_indicator": mean_ssi,
            "critical_slope_area_pct": critical_pct,
            "files": {
                "pore_pressure_tif": str(pwp_path.relative_to(base_output_dir.parent)),
                "slope_stability_tif": str(ssi_path.relative_to(base_output_dir.parent)),
                "factor_of_safety_tif": str(fos_path.relative_to(base_output_dir.parent)),
            },
        }
        manifest_entries.append(entry)

    manifest = {
        "event_date": event_date,
        "region": "Upper Beas Catchment (Kullu - Manali)",
        "model_engine": "FLOODY_SHIELD_PWP_SLOPE_STABILITY_V1.0",
        "scientific_disclaimer": "Direct pore-water pressure validation data are currently unavailable.",
        "snapshots": manifest_entries,
    }

    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest
