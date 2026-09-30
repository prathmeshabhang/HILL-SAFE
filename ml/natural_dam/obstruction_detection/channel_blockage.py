"""
channel_blockage.py — River Channel Obstruction & Dam Barrier Detector
======================================================================
Identifies physical obstructions traversing a river corridor:
  - Sudden cross-sectional channel narrowing or complete channel pinch-off.
  - High-roughness SAR backscatter (> -11 dB) indicating rock avalanche or coarse debris deposit.
  - Cross-checks against false-positive infrastructure masks (artificial dams, barrages, bridges).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ml.natural_dam.config import NaturalDamConfig


@dataclass
class ObstructionEvidence:
    has_obstruction: bool
    blockage_location: Tuple[float, float]  # (lat, lon)
    obstruction_width_m: float
    width_reduction_pct: float
    sar_debris_backscatter_db: float
    is_false_positive_structure: bool
    false_positive_reason: Optional[str]
    evidence_score: float  # 0.0 to 1.0


class ChannelObstructionDetector:
    def __init__(self, config: Optional[NaturalDamConfig] = None):
        self.config = config or NaturalDamConfig()

    def evaluate_obstruction(
        self,
        lat: float,
        lon: float,
        pre_event_width_m: float,
        post_event_width_m: float,
        sar_backscatter_db: float,
        dem_slope_deg: float,
    ) -> ObstructionEvidence:
        """
        Evaluates physical river pinch-off and validates that the location
        is not a known artificial dam, bridge, or reservoir spillway.
        """
        # 1. False-Positive Check (Artificial Dams / Bridges)
        fp_detected = False
        fp_reason = None
        for struct in self.config.known_artificial_structures:
            dy = (struct["lat"] - lat) * 111000.0
            dx = (struct["lon"] - lon) * 94000.0
            dist_m = math.sqrt(dx * dx + dy * dy)
            if dist_m <= struct["radius_m"]:
                fp_detected = True
                fp_reason = f"Known artificial structure: {struct['name']} within {dist_m:.0f}m"
                break

        if fp_detected:
            return ObstructionEvidence(
                has_obstruction=False,
                blockage_location=(lat, lon),
                obstruction_width_m=post_event_width_m,
                width_reduction_pct=0.0,
                sar_debris_backscatter_db=sar_backscatter_db,
                is_false_positive_structure=True,
                false_positive_reason=fp_reason,
                evidence_score=0.0,
            )

        # 2. Width Constriction Ratio
        width_reduction_pct = max(0.0, ((pre_event_width_m - post_event_width_m) / max(pre_event_width_m, 1.0)) * 100.0)

        # 3. Roughness signature: Landslide rock/boulder blockages reflect high SAR backscatter (rough diffuse scattering)
        is_rough_debris = sar_backscatter_db >= self.config.sar_debris_roughness_min_db

        # 4. Obstruction scoring
        obstruction_detected = bool(width_reduction_pct >= self.config.min_river_width_reduction_pct and is_rough_debris)

        # Quantitative evidence score (0.0 to 1.0)
        w_score = min(1.0, width_reduction_pct / 80.0)
        sar_score = min(1.0, max(0.0, (sar_backscatter_db + 16.0) / 7.0))
        topog_score = 1.0 if dem_slope_deg > 18.0 else (dem_slope_deg / 18.0)
        total_score = round(float(0.50 * w_score + 0.35 * sar_score + 0.15 * topog_score), 3)

        return ObstructionEvidence(
            has_obstruction=obstruction_detected,
            blockage_location=(lat, lon),
            obstruction_width_m=round(post_event_width_m, 1),
            width_reduction_pct=round(width_reduction_pct, 1),
            sar_debris_backscatter_db=round(sar_backscatter_db, 2),
            is_false_positive_structure=False,
            false_positive_reason=None,
            evidence_score=total_score,
        )
