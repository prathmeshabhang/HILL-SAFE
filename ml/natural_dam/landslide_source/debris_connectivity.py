"""
debris_connectivity.py — Landslide Scar & Slope Debris Connectivity Detector
=============================================================================
Identifies hillslope failures (scars, debris flows, rockfalls) located within
500 meters of the river channel and evaluates their spatial connection to the dam.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ml.natural_dam.config import NaturalDamConfig


@dataclass
class DebrisSourceEvidence:
    has_connected_debris_source: bool
    scar_location: Tuple[float, float]
    distance_to_channel_m: float
    flank_slope_deg: float
    ndvi_vegetation_loss: float
    debris_source_probability: float
    failure_mechanism: str  # "COHESIVE_ROCK_SLIDE", "DEBRIS_AVALANCHE", "UNVERIFIED"


class LandslideSourceDetector:
    def __init__(self, config: Optional[NaturalDamConfig] = None):
        self.config = config or NaturalDamConfig()

    def evaluate_connectivity(
        self,
        dam_lat: float,
        dam_lon: float,
        scar_lat: float,
        scar_lon: float,
        slope_deg: float,
        pre_ndvi: float,
        post_ndvi: float,
        antecedent_rain_mm: float,
    ) -> DebrisSourceEvidence:
        """
        Determines whether a documented terrain scar is physically connected to the river blockage.
        """
        # Distance calculation
        dy = (scar_lat - dam_lat) * 111000.0
        dx = (scar_lon - dam_lon) * 94000.0
        dist_m = math.sqrt(dx * dx + dy * dy)

        # Vegetation loss: landslides strip forest cover (NDVI drops substantially)
        ndvi_loss = max(0.0, pre_ndvi - post_ndvi)

        # Failure criteria: steep mountain flank (>25 deg) and proximity within 500m of channel
        is_steep = slope_deg >= self.config.min_slope_landslide_source_deg
        is_proximal = dist_m <= self.config.max_distance_to_river_m
        has_veg_loss = ndvi_loss >= 0.20

        # Debris source probability
        p_slope = min(1.0, slope_deg / 45.0)
        p_prox = max(0.0, 1.0 - (dist_m / self.config.max_distance_to_river_m))
        p_loss = min(1.0, ndvi_loss / 0.50)
        p_rain = min(1.0, antecedent_rain_mm / 150.0)

        debris_prob = round(float(0.35 * p_slope + 0.30 * p_prox + 0.20 * p_loss + 0.15 * p_rain), 3)
        is_connected = bool(is_steep and is_proximal and (has_veg_loss or debris_prob >= 0.60))

        if slope_deg >= 38.0:
            mechanism = "COHESIVE_ROCK_SLIDE"
        elif slope_deg >= 25.0:
            mechanism = "DEBRIS_AVALANCHE"
        else:
            mechanism = "UNVERIFIED"

        return DebrisSourceEvidence(
            has_connected_debris_source=is_connected,
            scar_location=(scar_lat, scar_lon),
            distance_to_channel_m=round(dist_m, 1),
            flank_slope_deg=round(slope_deg, 1),
            ndvi_vegetation_loss=round(ndvi_loss, 3),
            debris_source_probability=debris_prob,
            failure_mechanism=mechanism,
        )
