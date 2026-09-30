"""
evidence_scorer.py — Multi-Evidence Scoring & Candidate Classification Engine
==============================================================================
Fuses 8 physical and remote sensing evidence indicators to evaluate natural landslide
dam candidates without falsely triggering on artificial dams, bridges, or seasonal water.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.natural_dam.config import NaturalDamConfig


@dataclass
class EvidenceIndicator:
    name: str
    description: str
    weight: float
    score: float      # Normalized 0.0 to 1.0
    passed: bool
    details: str


@dataclass
class NaturalDamCandidate:
    dam_id: str
    river_name: str
    lat: float
    lon: float
    elevation_m: float
    probability: float          # 0.0 to 1.0 (calibrated multi-evidence score)
    confidence: float           # 0.0 to 1.0 (sensor coverage & data quality)
    data_quality: str           # "EXCELLENT", "GOOD", "DEGRADED", "POOR"
    observation_freshness: str  # e.g., "6 hours ago"
    candidate_tier: str         # "HIGH_CONFIDENCE_CANDIDATE", "LIKELY", "POSSIBLE", "NO_EVIDENCE"
    status: str                 # "MONITOR", "INVESTIGATE", "HIGH_PRIORITY_INVESTIGATION", "AUTHORITY_VALIDATION_REQUIRED"
    evidence_indicators: List[EvidenceIndicator]
    indicators_passed_count: int
    total_indicators_count: int
    false_positive_rejected: bool
    rejection_reason: Optional[str]


class MultiEvidenceScorer:
    def __init__(self, config: Optional[NaturalDamConfig] = None):
        self.config = config or NaturalDamConfig()

    def score_candidate(
        self,
        dam_id: str,
        river_name: str,
        lat: float,
        lon: float,
        elevation_m: float,
        # Evidence metrics
        obstruction_score: float,           # 0.0 to 1.0
        upstream_water_expansion_pct: float, # e.g., 35.0%
        downstream_water_reduction_pct: float, # e.g., 22.0%
        debris_source_prob: float,          # 0.0 to 1.0
        is_narrow_v_gorge: bool,            # True/False
        sar_backscatter_delta_db: float,    # e.g., -4.5 dB
        optical_ndvi_drop: float,           # e.g., 0.28
        antecedent_rainfall_mm: float,      # e.g., 85.0 mm
        # Metadata
        freshness_str: str = "4 hours ago",
        has_clear_optical: bool = True,
        is_false_positive_structure: bool = False,
        false_positive_reason: Optional[str] = None,
    ) -> NaturalDamCandidate:
        """
        Calculates calibrated multi-evidence score and determines candidate tier.
        """
        # If explicitly flagged as a known artificial dam/bridge, reject immediately
        if is_false_positive_structure:
            return NaturalDamCandidate(
                dam_id=dam_id,
                river_name=river_name,
                lat=lat,
                lon=lon,
                elevation_m=elevation_m,
                probability=0.0,
                confidence=0.95,
                data_quality="EXCELLENT",
                observation_freshness=freshness_str,
                candidate_tier="NO_EVIDENCE",
                status="MONITOR",
                evidence_indicators=[],
                indicators_passed_count=0,
                total_indicators_count=8,
                false_positive_rejected=True,
                rejection_reason=false_positive_reason,
            )

        w = self.config.evidence_weights

        # 1. River obstruction
        s_obs = min(1.0, max(0.0, obstruction_score))
        pass_obs = s_obs >= 0.50
        ind_obs = EvidenceIndicator("river_obstruction", "Physical channel blockage / narrowing", w["river_obstruction"], s_obs, pass_obs, f"Blockage score: {s_obs:.2f}")

        # 2. Upstream water accumulation
        s_up = min(1.0, max(0.0, upstream_water_expansion_pct / 50.0))
        pass_up = upstream_water_expansion_pct >= self.config.min_upstream_water_expansion_pct
        ind_up = EvidenceIndicator("upstream_water_accumulation", "Expanding water surface upstream", w["upstream_water_accumulation"], s_up, pass_up, f"Expansion: +{upstream_water_expansion_pct:.1f}%")

        # 3. Downstream flow reduction
        s_down = min(1.0, max(0.0, downstream_water_reduction_pct / 40.0))
        pass_down = downstream_water_reduction_pct >= self.config.min_downstream_water_drop_pct
        ind_down = EvidenceIndicator("downstream_flow_reduction", "Downstream water/flow signature drop", w["downstream_flow_reduction"], s_down, pass_down, f"Reduction: -{downstream_water_reduction_pct:.1f}%")

        # 4. Landslide/debris source
        s_deb = min(1.0, max(0.0, debris_source_prob))
        pass_deb = s_deb >= 0.50
        ind_deb = EvidenceIndicator("landslide_debris_source", "Connected steep slope failure/scar", w["landslide_debris_source"], s_deb, pass_deb, f"Debris prob: {s_deb:.2f}")

        # 5. Topographic gorge barrier
        s_top = 1.0 if is_narrow_v_gorge else 0.35
        pass_top = is_narrow_v_gorge
        ind_top = EvidenceIndicator("topographic_barrier_fit", "Narrow V-shaped gorge profile", w["topographic_barrier_fit"], s_top, pass_top, "V-shaped mountain gorge constriction")

        # 6. SAR backscatter change
        s_sar = min(1.0, max(0.0, -sar_backscatter_delta_db / 6.0))
        pass_sar = sar_backscatter_delta_db <= self.config.sar_specular_drop_db
        ind_sar = EvidenceIndicator("sar_backscatter_change", "Radar specular reflection transition", w["sar_backscatter_change"], s_sar, pass_sar, f"SAR delta: {sar_backscatter_delta_db:.1f} dB")

        # 7. Optical spectral change
        s_opt = min(1.0, max(0.0, optical_ndvi_drop / 0.40))
        pass_opt = optical_ndvi_drop >= 0.15
        ind_opt = EvidenceIndicator("optical_spectral_change", "Multispectral vegetation/water shift", w["optical_spectral_change"], s_opt, pass_opt, f"NDVI drop: {optical_ndvi_drop:.2f}")

        # 8. Rainfall trigger
        s_rain = min(1.0, max(0.0, antecedent_rainfall_mm / 100.0))
        pass_rain = antecedent_rainfall_mm >= 40.0
        ind_rain = EvidenceIndicator("rainfall_trigger_alignment", "Monsoon storm precipitation trigger", w["rainfall_trigger_alignment"], s_rain, pass_rain, f"Rainfall: {antecedent_rainfall_mm:.1f} mm")

        indicators = [ind_obs, ind_up, ind_down, ind_deb, ind_top, ind_sar, ind_opt, ind_rain]

        # Total weighted probability
        total_prob = sum(ind.weight * ind.score for ind in indicators)
        total_prob = round(float(np.clip(total_prob, 0.0, 1.0)), 3)

        passed_count = sum(1 for ind in indicators if ind.passed)

        # Assign tier
        tier = "NO_EVIDENCE"
        for t_name, t_min in self.config.tier_thresholds:
            if total_prob >= t_min:
                tier = t_name
                break

        # Operational status
        if tier == "HIGH_CONFIDENCE_CANDIDATE":
            status = "AUTHORITY_VALIDATION_REQUIRED"
        elif tier == "LIKELY":
            status = "HIGH_PRIORITY_INVESTIGATION"
        elif tier == "POSSIBLE":
            status = "INVESTIGATE"
        else:
            status = "MONITOR"

        quality = "EXCELLENT" if has_clear_optical else "GOOD"
        conf = 0.88 if has_clear_optical else 0.76

        return NaturalDamCandidate(
            dam_id=dam_id,
            river_name=river_name,
            lat=lat,
            lon=lon,
            elevation_m=elevation_m,
            probability=total_prob,
            confidence=conf,
            data_quality=quality,
            observation_freshness=freshness_str,
            candidate_tier=tier,
            status=status,
            evidence_indicators=indicators,
            indicators_passed_count=passed_count,
            total_indicators_count=len(indicators),
            false_positive_rejected=False,
            rejection_reason=None,
        )
