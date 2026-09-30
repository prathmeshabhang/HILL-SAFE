"""M19 — Kinematic physics baseline for time-to-impact estimation.

Physical model
==============
Flood / outburst wave travel time
----------------------------------
    t = distance / wave_speed

Wave speed is estimated from Manning's velocity approximation when not
directly supplied by M12:
    V_channel = (1/n) * R^(2/3) * S^(1/2)
    (R = hydraulic radius ≈ depth for wide channels)

Debris-flow / landslide runout
-------------------------------
    Speed is estimated from Hungr (1995) empirical relation:
    V_runout ≈ 2.7 * sqrt(H)   [m/s]
    where H = vertical drop (m) = distance_km * 1000 * sin(slope_rad)

Uncertainty propagation
------------------------
    The P10–P90 spread is derived from ±30% parametric uncertainty on
    wave speed / runout speed.  This is a conservative but physically
    grounded bound — real Himalayan event data is not available for the
    Upper Beas corridor at this project stage.

References
----------
- Manning, R. (1891) — open-channel flow
- Hungr et al. (1995) — debris flow velocities
- NDMA (2010) — Flash Flood Guidance for Hilly States
- Froehlich (1987) — dam-breach outburst wave
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

# Manning's roughness for mountain rivers (rough boulders)
MANNING_N_MOUNTAIN = 0.045
# Upper Beas: Froehlich attenuation wave speed (calibrated in M12)
M12_DEFAULT_WAVE_SPEED_KMH = 21.0  # km/h


def _flood_wave_speed_kmh(
    channel_slope_pct: Optional[float],
    peak_discharge_m3s: Optional[float],
    floodplain_width_m: Optional[float],
    supplied_wave_speed_kmh: Optional[float],
) -> Tuple[float, str]:
    """
    Estimate flood-wave propagation speed (km/h).

    Priority:
    1. Directly supplied (e.g. from M12 output)
    2. Manning velocity proxy using discharge and channel geometry
    3. Default M12-calibrated value (21 km/h)
    """
    if supplied_wave_speed_kmh is not None and supplied_wave_speed_kmh > 0:
        return float(supplied_wave_speed_kmh), "supplied_from_m12"

    if (
        peak_discharge_m3s is not None
        and peak_discharge_m3s > 0
        and floodplain_width_m is not None
        and floodplain_width_m > 0
        and channel_slope_pct is not None
        and channel_slope_pct > 0
    ):
        slope_frac = channel_slope_pct / 100.0
        # Approximate depth from continuity: Q = V * A; A = W * d
        # Manning: V = (1/n)*d^(2/3)*S^(1/2) → V*W*d = Q → iterative
        # Simplified: d ~ (Q*n / (W*S^0.5))^0.6
        d = (
            peak_discharge_m3s
            * MANNING_N_MOUNTAIN
            / (floodplain_width_m * math.sqrt(slope_frac))
        ) ** 0.6
        d = max(0.5, d)
        v_ms = (1 / MANNING_N_MOUNTAIN) * (d ** (2 / 3)) * math.sqrt(slope_frac)
        v_kmh = v_ms * 3.6
        return float(v_kmh), "manning_proxy"

    return M12_DEFAULT_WAVE_SPEED_KMH, "m12_default_21kmh"


def _landslide_runout_speed_kmh(
    distance_km: float,
    slope_angle_deg: Optional[float],
    debris_depth_m: Optional[float],
) -> Tuple[float, str]:
    """
    Estimate debris-flow/landslide runout speed (km/h) using Hungr (1995).

        V ≈ 2.7 * sqrt(H)    [m/s]

    where H = vertical drop = distance_km * 1000 * sin(slope_angle_rad).
    """
    angle = slope_angle_deg if slope_angle_deg is not None else 25.0  # typical Beas hillslope
    slope_rad = math.radians(max(5.0, min(angle, 60.0)))
    H_m = distance_km * 1000.0 * math.sin(slope_rad)
    H_m = max(1.0, H_m)
    v_ms = 2.7 * math.sqrt(H_m)
    v_kmh = v_ms * 3.6
    return float(v_kmh), "hungr_1995_empirical"


def estimate_travel_time(
    impact_type: str,
    distance_km: float,
    channel_slope_pct: Optional[float] = None,
    peak_discharge_m3s: Optional[float] = None,
    floodplain_width_m: Optional[float] = None,
    wave_speed_kmh: Optional[float] = None,
    slope_angle_deg: Optional[float] = None,
    debris_depth_m: Optional[float] = None,
    soil_saturation_ratio: float = 0.5,
) -> Dict[str, Any]:
    """
    Physics-based P10/P50/P90 travel-time estimate.

    Returns
    -------
    dict with keys: p10_min, p50_min, p90_min, speed_kmh, method, physics
    """
    distance_km = max(0.1, distance_km)

    if impact_type in ("FLOOD_INUNDATION", "DAM_BREACH_OUTBURST"):
        speed, method = _flood_wave_speed_kmh(
            channel_slope_pct, peak_discharge_m3s, floodplain_width_m, wave_speed_kmh
        )
    elif impact_type in ("LANDSLIDE_RUNOUT", "DEBRIS_FLOW"):
        speed, method = _landslide_runout_speed_kmh(
            distance_km, slope_angle_deg, debris_depth_m
        )
    else:  # COMBINED
        # Use flood wave speed as conservative (slower) estimate
        f_speed, f_method = _flood_wave_speed_kmh(
            channel_slope_pct, peak_discharge_m3s, floodplain_width_m, wave_speed_kmh
        )
        l_speed, l_method = _landslide_runout_speed_kmh(
            distance_km, slope_angle_deg, debris_depth_m
        )
        # Take the faster of the two (earliest hazard arrival)
        speed, method = (f_speed, f_method) if f_speed >= l_speed else (l_speed, l_method)

    # Soil saturation accelerates travel: +10% speed per 0.1 sat above 0.5
    sat_factor = 1.0 + max(0.0, (soil_saturation_ratio - 0.5)) * 1.0
    speed_adjusted = speed * sat_factor

    p50_min = (distance_km / speed_adjusted) * 60.0  # hours → minutes

    # P10 (faster): +30% speed → less time
    p10_min = (distance_km / (speed_adjusted * 1.30)) * 60.0
    # P90 (slower): −30% speed → more time
    p90_min = (distance_km / (speed_adjusted * 0.70)) * 60.0

    return {
        "p10_min": round(max(1.0, p10_min), 1),
        "p50_min": round(max(1.0, p50_min), 1),
        "p90_min": round(max(1.0, p90_min), 1),
        "speed_kmh": round(speed_adjusted, 2),
        "speed_source": method,
        "method": "KINEMATIC_BASELINE",
        "physics": {
            "distance_km": distance_km,
            "base_speed_kmh": round(speed, 2),
            "saturation_factor": round(sat_factor, 3),
            "adjusted_speed_kmh": round(speed_adjusted, 2),
            "uncertainty_band_pct": 30,
        },
    }
