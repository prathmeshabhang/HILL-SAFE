"""
backend/app/services/analysis/flood_physics.py
===============================================
Flood Physics & Terrain-Aware Routing Engine for FLOODY SHIELD (Phase 04B).
Implements USDA NRCS / SCS-CN (Curve Number) rainfall-runoff estimation
coupled with Copernicus 30m DEM-derived topographic drainage and Manning routing.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.core.config import settings
from backend.app.services.analysis.base import AnalysisComponent, AnalysisStatus


class FloodPhysicsEngine(AnalysisComponent):
    """
    Decoupled physical flood intelligence component.
    Calculates direct runoff depth, retention volume, peak breach/hydrograph discharge,
    and terrain-routed time-to-peak using SCS-CN and 30m Copernicus DEM gradients.
    """

    # Class-level cache for expensive DEM raster preprocessing
    _DEM_CACHE: Dict[str, Any] = {}

    def __init__(self, dem_path: Optional[Path] = None):
        super().__init__(
            component_name="SCS_CN_TERRAIN_ROUTER",
            capability_name="Flood Intelligence",
            input_requirements=["rainfall_intensity_mmh"],
            output_type="HYDROLOGIC_RUNOFF_AND_ROUTING",
        )
        self.default_dem_path = dem_path or (
            settings.DATA_ROOT / "raw" / "scenes" / "upper_beas_july2023" / "COP30_DEM.tif"
        )
        # Standard catchment parameters for Upper Beas (Pandoh/Larji to Rohtang)
        self.default_catchment_area_km2 = 3274.0
        self.default_cn_ii = 74.0  # Composite CN for alpine forest, thin soil, rocky gorge
        self.manning_n = 0.045     # Mountain river bed with boulders
        self.main_channel_length_km = 85.0

    def _get_dem_properties(self, dem_path: Path) -> Tuple[Dict[str, float], bool]:
        """
        Loads or retrieves cached 30m DEM terrain parameters:
        mean elevation, elevation relief, average slope gradient, and drainage length.
        """
        cache_key = str(dem_path)
        if cache_key in self._DEM_CACHE:
            return self._DEM_CACHE[cache_key], True

        if not dem_path.exists():
            return {
                "min_elev_m": 850.0,
                "max_elev_m": 3950.0,
                "mean_elev_m": 2150.0,
                "relief_m": 3100.0,
                "mean_slope_deg": 32.5,
                "channel_gradient_m_m": 0.015,
                "flow_accumulation_max_cells": 1250000.0,
            }, False

        try:
            import tifffile
            elev = tifffile.imread(str(dem_path)).astype(np.float32)
            # Filter invalid or missing values
            valid_elev = elev[np.isfinite(elev) & (elev > 0)]
            if len(valid_elev) == 0:
                raise ValueError("DEM raster contains no valid positive elevation cells")

            min_e = float(np.min(valid_elev))
            max_e = float(np.max(valid_elev))
            mean_e = float(np.mean(valid_elev))
            relief = max_e - min_e

            # Compute approximate slope using 2D spatial gradients (30m cell resolution)
            dy, dx = np.gradient(elev, 30.0)
            slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
            mean_slope_deg = float(np.nanmean(np.degrees(slope_rad)))

            # Approximate river thalweg gradient across North-South axis
            gradient = max(0.005, relief / (self.main_channel_length_km * 1000.0))

            props = {
                "min_elev_m": round(min_e, 1),
                "max_elev_m": round(max_e, 1),
                "mean_elev_m": round(mean_e, 1),
                "relief_m": round(relief, 1),
                "mean_slope_deg": round(mean_slope_deg, 2),
                "channel_gradient_m_m": round(gradient, 4),
                "flow_accumulation_max_cells": float(elev.size),
            }
            self._DEM_CACHE[cache_key] = props
            return props, True
        except Exception:
            return {
                "min_elev_m": 850.0,
                "max_elev_m": 3950.0,
                "mean_elev_m": 2150.0,
                "relief_m": 3100.0,
                "mean_slope_deg": 32.5,
                "channel_gradient_m_m": 0.015,
                "flow_accumulation_max_cells": 1250000.0,
            }, False

    def calculate_scs_cn_runoff(
        self,
        rainfall_mm: float,
        cn_ii: float = 74.0,
        antecedent_rain_5d_mm: Optional[float] = None,
        soil_saturation_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes USDA Soil Conservation Service (SCS) Curve Number direct runoff.
        Adjusts CN for Antecedent Moisture Condition (AMC-I Dry, AMC-II Normal, AMC-III Wet).
        """
        # 1. Determine AMC Condition
        if soil_saturation_pct is not None:
            if soil_saturation_pct > 70.0:
                amc = "AMC_III"
            elif soil_saturation_pct < 40.0:
                amc = "AMC_I"
            else:
                amc = "AMC_II"
        elif antecedent_rain_5d_mm is not None:
            if antecedent_rain_5d_mm > 28.0:
                amc = "AMC_III"
            elif antecedent_rain_5d_mm < 13.0:
                amc = "AMC_I"
            else:
                amc = "AMC_II"
        else:
            amc = "AMC_II"

        # 2. Adjust Curve Number based on AMC
        if amc == "AMC_I":
            cn = cn_ii / (2.281 - (0.01281 * cn_ii))
        elif amc == "AMC_III":
            cn = cn_ii / (0.427 + (0.00573 * cn_ii))
        else:
            cn = cn_ii

        cn = float(np.clip(cn, 30.0, 98.0))

        # 3. Maximum potential soil water retention S (mm)
        s_retention_mm = (25400.0 / cn) - 254.0

        # 4. Initial abstraction Ia (surface storage, interception, initial infiltration)
        # Using standard lambda = 0.20
        initial_abstraction_mm = 0.20 * s_retention_mm

        # 5. Direct runoff depth Q (mm)
        if rainfall_mm > initial_abstraction_mm:
            runoff_depth_mm = ((rainfall_mm - initial_abstraction_mm) ** 2) / (
                rainfall_mm - initial_abstraction_mm + s_retention_mm
            )
        else:
            runoff_depth_mm = 0.0

        runoff_coeff = round(runoff_depth_mm / max(0.001, rainfall_mm), 3) if rainfall_mm > 0 else 0.0

        return {
            "amc_condition": amc,
            "effective_curve_number": round(cn, 1),
            "potential_retention_s_mm": round(s_retention_mm, 2),
            "initial_abstraction_ia_mm": round(initial_abstraction_mm, 2),
            "direct_runoff_depth_mm": round(runoff_depth_mm, 2),
            "runoff_coefficient": min(1.0, runoff_coeff),
        }

    def _run_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes unified SCS-CN runoff estimation and terrain-aware kinematic routing.
        """
        warnings: List[str] = []

        # 1. Extract Rainfall Inputs
        rain_rate = inputs.get("rainfall_intensity_mmh")
        if rain_rate is None:
            rain_rate = inputs.get("rainfall_rate_mmh") or inputs.get("rainfall_1h_mm") or 0.0

        accum_rain = inputs.get("accumulated_rainfall_mm")
        duration_h = float(inputs.get("rainfall_duration_hours") or 1.0)
        total_precip_mm = float(accum_rain if accum_rain is not None else rain_rate * duration_h)

        antecedent_5d = inputs.get("antecedent_rain_5d_mm") or inputs.get("antecedent_rain_3d_mm")
        soil_sat = inputs.get("soil_moisture_saturation_pct") or inputs.get("soil_saturation_pct")
        if soil_sat is None and "soil_moisture_volumetric" in inputs:
            # Approximate saturation from SMAP volumetric (assume porosity 0.45)
            soil_sat = min(100.0, (float(inputs["soil_moisture_volumetric"]) / 0.45) * 100.0)

        # 2. Extract Catchment & DEM Parameters
        area_km2 = float(inputs.get("catchment_area_km2") or self.default_catchment_area_km2)
        cn_nominal = float(inputs.get("curve_number_nominal") or self.default_cn_ii)
        dem_path = Path(inputs.get("dem_path") or self.default_dem_path)

        dem_props, dem_loaded = self._get_dem_properties(dem_path)
        if not dem_loaded:
            warnings.append(
                f"Copernicus 30m DEM file not found at {dem_path}. "
                "Utilizing calibrated Himalayan regional terrain parameters."
            )

        # 3. SCS-CN Calculation
        scs_res = self.calculate_scs_cn_runoff(
            rainfall_mm=total_precip_mm,
            cn_ii=cn_nominal,
            antecedent_rain_5d_mm=antecedent_5d,
            soil_saturation_pct=soil_sat,
        )

        q_depth_mm = scs_res["direct_runoff_depth_mm"]
        # Total runoff volume in million cubic meters (MCM)
        runoff_vol_mcm = (q_depth_mm / 1000.0) * (area_km2 * 1e6) / 1e6

        # 4. Kinematic Terrain Routing (Time of Concentration & Peak Discharge)
        # Using Kirpich-Manning channel celerity:
        slope = max(0.002, dem_props["channel_gradient_m_m"])
        # Manning velocity: v = (1/n) * R^(2/3) * S^(1/2)
        r_hydraulic = 3.0  # meters (Upper Beas main stem flood stage)
        v_flow_ms = (1.0 / self.manning_n) * (r_hydraulic ** (2.0 / 3.0)) * (slope ** 0.5)
        v_flow_ms = float(np.clip(v_flow_ms, 1.5, 6.0))

        # Time of concentration Tc in hours
        t_c_hours = (self.main_channel_length_km * 1000.0) / (v_flow_ms * 3600.0)
        # Peak time Tp in hours
        t_p_hours = (duration_h / 2.0) + (0.6 * t_c_hours)

        # SCS Triangular Unit Hydrograph Peak Discharge Qp (m3/s):
        # Qp = (0.208 * Area_km2 * Q_mm) / Tp_hours
        if t_p_hours > 0 and q_depth_mm > 0:
            peak_discharge_m3s = (0.208 * area_km2 * q_depth_mm) / t_p_hours
        else:
            peak_discharge_m3s = 0.0

        # Assess derived flood hazard tier
        if peak_discharge_m3s > 2500.0 or q_depth_mm > 70.0:
            hazard_tier = "CRITICAL"
        elif peak_discharge_m3s > 1500.0 or q_depth_mm > 40.0:
            hazard_tier = "HIGH"
        elif peak_discharge_m3s > 600.0 or q_depth_mm > 15.0:
            hazard_tier = "MODERATE"
        else:
            hazard_tier = "LOW"

        confidence = 0.90 if dem_loaded else 0.70

        return {
            "rainfall_depth_evaluated_mm": round(total_precip_mm, 2),
            "scs_cn": scs_res,
            "routing": {
                "catchment_area_km2": area_km2,
                "flow_velocity_ms": round(v_flow_ms, 2),
                "time_of_concentration_hours": round(t_c_hours, 2),
                "time_to_peak_hours": round(t_p_hours, 2),
                "peak_discharge_m3s": round(peak_discharge_m3s, 1),
                "runoff_volume_mcm": round(runoff_vol_mcm, 2),
                "flow_accumulation_peak_cells": dem_props["flow_accumulation_max_cells"],
            },
            "terrain_metrics": dem_props,
            "derived_hazard_tier": hazard_tier,
            "warnings": warnings,
            "confidence": confidence,
            "status_override": AnalysisStatus.READY.value if dem_loaded else AnalysisStatus.DEGRADED.value,
        }

    def get_evidence_metadata(self) -> Dict[str, Any]:
        return {
            "component": self.component_name,
            "capability": self.capability_name,
            "scientific_method": "USDA NRCS SCS-CN (TR-55) & Manning Kinematic Hydrograph Routing",
            "model_version": "4.1-PHYSICS",
            "dem_source": "Copernicus GLO-30 Digital Elevation Model (30m WGS-84/UTM)",
            "hydrologic_soil_group": "HSG B/C (Himalayan Sandy-Clay Loam with Outcrops)",
            "disclaimer": (
                "Runoff depths and discharge routing are deterministic physical estimations. "
                "They do not replace in-situ stage telemetry from CWC river gauges."
            ),
        }


# Global singleton
flood_physics_engine = FloodPhysicsEngine()
