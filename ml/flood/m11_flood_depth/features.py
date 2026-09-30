"""
ml/flood/m11_flood_depth/features.py
====================================
Reach definitions, hydraulic geometry, and HAND feature extraction for Model M11.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

# Upper Beas River Channel Reaches (from upstream Palchan to downstream Pandoh)
BEAS_RIVER_REACHES = {
    "REACH_01_PALCHAN_MANALI": {
        "name": "Palchan to Old Manali Gorge",
        "length_km": 11.0,
        "slope": 0.024,
        "manning_n": 0.045,
        "bankfull_stage_m": 4.5,
        "top_width_m": 35.0,
        "floodplain_area_sqkm": 2.2,
    },
    "REACH_02_MANALI_PATLIKUHAL": {
        "name": "Manali to Patli Kuhal Valley",
        "length_km": 14.0,
        "slope": 0.015,
        "manning_n": 0.040,
        "bankfull_stage_m": 4.0,
        "top_width_m": 60.0,
        "floodplain_area_sqkm": 5.8,
    },
    "REACH_03_PATLIKUHAL_KULLU": {
        "name": "Patli Kuhal to Kullu Akhara Bazar",
        "length_km": 18.0,
        "slope": 0.010,
        "manning_n": 0.038,
        "bankfull_stage_m": 4.2,
        "top_width_m": 75.0,
        "floodplain_area_sqkm": 8.4,
    },
    "REACH_04_KULLU_BHUNTAR": {
        "name": "Kullu to Bhuntar Confluence",
        "length_km": 10.0,
        "slope": 0.008,
        "manning_n": 0.035,
        "bankfull_stage_m": 5.0,
        "top_width_m": 90.0,
        "floodplain_area_sqkm": 6.5,
    },
    "REACH_05_BHUNTAR_AUT": {
        "name": "Bhuntar to Aut Gorge",
        "length_km": 22.0,
        "slope": 0.006,
        "manning_n": 0.042,
        "bankfull_stage_m": 5.5,
        "top_width_m": 65.0,
        "floodplain_area_sqkm": 4.1,
    },
    "REACH_06_AUT_PANDOH": {
        "name": "Aut to Pandoh Dam Reservoir",
        "length_km": 15.0,
        "slope": 0.004,
        "manning_n": 0.032,
        "bankfull_stage_m": 6.5,
        "top_width_m": 120.0,
        "floodplain_area_sqkm": 9.2,
    },
}


def compute_wave_celerity_and_attenuation(
    discharge_m3s: float,
    reach_slope: float,
    manning_n: float = 0.040,
    channel_width_m: float = 60.0,
) -> Dict[str, float]:
    """
    Computes flood wave celerity c = 1.5 * v (m/s) using Manning hydraulic formula:
    v = (1/n) * R^(2/3) * S^(1/2)
    """
    q = max(10.0, discharge_m3s)
    # Estimate hydraulic radius R ~ y = (q * n / (w * sqrt(S)))^(3/5)
    sqrt_s = math.sqrt(max(0.001, reach_slope))
    depth = ((q * manning_n) / (channel_width_m * sqrt_s)) ** 0.6
    velocity = q / (channel_width_m * max(0.2, depth))
    celerity_mps = 1.5 * velocity  # Kinematic wave speed in wide channel
    return {
        "depth_m": round(depth, 3),
        "velocity_mps": round(velocity, 2),
        "celerity_mps": round(max(1.5, min(10.0, celerity_mps)), 2),
    }


def extract_m11_features(reading: Dict[str, Any]) -> Dict[str, float]:
    """Extracts features for Model M11."""
    stage = float(reading.get("source_stage_m", reading.get("current_stage_m", reading.get("water_level_m", 4.0))))
    q_in = float(reading.get("source_discharge_m3s", reading.get("discharge_m3s", stage * 120.0)))
    hand = float(reading.get("hand_m", 1.5))
    dist_river = float(reading.get("distance_to_river_m", 80.0))
    slope = float(reading.get("slope_deg", 6.0))
    elev = float(reading.get("elevation_m", 1200.0))
    lat = float(reading.get("latitude", 31.96))
    lon = float(reading.get("longitude", 77.11))

    return {
        "latitude": lat,
        "longitude": lon,
        "elevation_m": elev,
        "water_level_m": stage,
        "source_stage_m": stage,
        "source_discharge_m3s": q_in,
        "hand_m": hand,
        "distance_to_river_m": dist_river,
        "slope_deg": slope,
    }
