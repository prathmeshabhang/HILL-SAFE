"""
spatial_sampler.py — Spatial Leakage Prevention & Negative Sampling
====================================================================
Generates scientifically rigorous evaluation samples by enforcing a configurable
spatial exclusion buffer around historical landslides.
Prevents spatial autocorrelation leakage between failure scars and non-failure samples.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.validation.external.dataset_loader import ObservedLandslideEvent
from ml.validation.external.projection import metric_distance_m, wgs84_to_utm43n


@dataclass
class ValidationPoint:
    """An individual spatial validation point with ground-truth label."""
    point_id: str
    latitude: float
    longitude: float
    is_landslide: int          # 1 = observed landslide event, 0 = verified non-landslide
    dist_to_nearest_event_m: float
    source_description: str


@dataclass
class SamplingPlanReport:
    """Provenance metadata for spatial sampling."""
    strategy: str = "SPATIAL_EXCLUSION_BUFFER"
    exclusion_buffer_m: float = 500.0
    buffer_rationale: str = (
        "500 meters selected based on Himalayan geomorphology (Martha et al. 2010): "
        "covers typical debris flow runout length (200-400m) plus hillslope crown cracking buffer. "
        "Prevents sampling pseudo-negatives on actively destabilized slope units."
    )
    positive_count: int = 0
    negative_count: int = 0
    total_samples: int = 0
    negative_to_positive_ratio: float = 1.0
    random_seed: int = 42
    aoi_bounds: Tuple[float, float, float, float] = (76.80, 31.40, 77.45, 32.45)
    negative_sampling_limitation: str = (
        "Negatives represent locations without cataloged historical failures outside the 500m buffer. "
        "In remote mountain terrain, undetected/unreported historical slides cannot be completely excluded."
    )


class SpatialLeakageController:
    def __init__(
        self,
        exclusion_buffer_m: float = 500.0,
        negative_ratio: float = 1.0,
        random_seed: int = 42,
        aoi_min_lon: float = 76.80,
        aoi_max_lon: float = 77.45,
        aoi_min_lat: float = 31.40,
        aoi_max_lat: float = 32.45,
    ):
        self.exclusion_buffer_m = float(exclusion_buffer_m)
        self.negative_ratio = float(negative_ratio)
        self.random_seed = int(random_seed)
        self.aoi_min_lon = aoi_min_lon
        self.aoi_max_lon = aoi_max_lon
        self.aoi_min_lat = aoi_min_lat
        self.aoi_max_lat = aoi_max_lat

    def generate_evaluation_set(
        self,
        positive_events: List[ObservedLandslideEvent],
    ) -> Tuple[List[ValidationPoint], SamplingPlanReport]:
        """
        Creates positive points from observed landslides and samples negative points
        guaranteed to be strictly outside the exclusion buffer.
        """
        rng = np.random.RandomState(self.random_seed)

        # 1. Positives
        pos_points: List[ValidationPoint] = []
        pos_utm: List[Tuple[float, float]] = []

        for idx, ev in enumerate(positive_events):
            vp = ValidationPoint(
                point_id=f"pos_{ev.event_id}",
                latitude=ev.latitude,
                longitude=ev.longitude,
                is_landslide=1,
                dist_to_nearest_event_m=0.0,
                source_description=f"Observed: {ev.source_dataset} ({ev.landslide_type or 'landslide'})",
            )
            pos_points.append(vp)
            utm_x, utm_y = wgs84_to_utm43n(ev.latitude, ev.longitude)
            pos_utm.append((utm_x, utm_y))

        n_pos = len(pos_points)
        if n_pos == 0:
            report = SamplingPlanReport(
                exclusion_buffer_m=self.exclusion_buffer_m,
                positive_count=0,
                negative_count=0,
                total_samples=0,
                random_seed=self.random_seed,
            )
            return [], report

        # 2. Negatives
        n_neg_target = int(round(n_pos * self.negative_ratio))
        neg_points: List[ValidationPoint] = []

        pos_utm_arr = np.array(pos_utm)  # (N, 2)

        attempts = 0
        max_attempts = max(n_neg_target * 50, 1000)

        while len(neg_points) < n_neg_target and attempts < max_attempts:
            attempts += 1
            cand_lat = rng.uniform(self.aoi_min_lat, self.aoi_max_lat)
            cand_lon = rng.uniform(self.aoi_min_lon, self.aoi_max_lon)

            cand_x, cand_y = wgs84_to_utm43n(cand_lat, cand_lon)

            # Metric distance to all positive points
            dists = np.hypot(pos_utm_arr[:, 0] - cand_x, pos_utm_arr[:, 1] - cand_y)
            min_dist = float(np.min(dists))

            # Must be strictly outside exclusion buffer
            if min_dist >= self.exclusion_buffer_m:
                vp = ValidationPoint(
                    point_id=f"neg_{len(neg_points)+1}",
                    latitude=cand_lat,
                    longitude=cand_lon,
                    is_landslide=0,
                    dist_to_nearest_event_m=round(min_dist, 1),
                    source_description=(
                        f"Non-landslide sample outside {self.exclusion_buffer_m}m exclusion buffer "
                        f"(actual dist: {min_dist:.1f}m)"
                    ),
                )
                neg_points.append(vp)

        all_samples = pos_points + neg_points

        report = SamplingPlanReport(
            exclusion_buffer_m=self.exclusion_buffer_m,
            positive_count=len(pos_points),
            negative_count=len(neg_points),
            total_samples=len(all_samples),
            negative_to_positive_ratio=round(len(neg_points) / max(len(pos_points), 1), 2),
            random_seed=self.random_seed,
            aoi_bounds=(self.aoi_min_lon, self.aoi_min_lat, self.aoi_max_lon, self.aoi_max_lat),
        )

        return all_samples, report
