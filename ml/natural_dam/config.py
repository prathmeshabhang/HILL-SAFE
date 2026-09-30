"""
config.py — Configuration and Evidence Thresholds for Natural River Dam Detection
==================================================================================
Defines physical parameters, multi-evidence scoring weights, false-positive filters,
and classification bins for landslide-dam and natural river obstruction detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class NaturalDamConfig:
    # 1. Geographic & Hydrographic Thresholds
    min_slope_landslide_source_deg: float = 25.0    # Minimum terrain slope for steep slope failure
    max_distance_to_river_m: float = 500.0          # Max buffer to search for connected debris source
    min_river_width_reduction_pct: float = 40.0     # Width drop indicating possible physical damming
    min_upstream_water_expansion_pct: float = 20.0  # Upstream water surface growth
    min_downstream_water_drop_pct: float = 15.0     # Downstream flow/water attenuation
    sar_specular_drop_db: float = -4.0              # Delta sigma0 VV threshold for new water extent
    sar_debris_roughness_min_db: float = -11.0      # High SAR backscatter indicating boulder/debris deposit

    # 2. Multi-Evidence Scoring Weights (Sum = 1.0)
    # The weights reflect physical importance and remote sensing reliability.
    evidence_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "river_obstruction": 0.20,            # Physical blockage / width interruption
            "upstream_water_accumulation": 0.20,  # Expanding water surface behind obstruction
            "downstream_flow_reduction": 0.15,    # Significant downstream water attenuation
            "landslide_debris_source": 0.15,      # Connected steep slope failure / scar
            "topographic_barrier_fit": 0.10,      # Narrow V-shaped gorge profile & flow direction
            "sar_backscatter_change": 0.10,       # All-weather radar water/debris transition
            "optical_spectral_change": 0.05,      # NDWI/MNDWI/NDVI spectral shifts
            "rainfall_trigger_alignment": 0.05,   # Antecedent rainfall supporting slope failure
        }
    )

    # 3. Confidence Classification Tiers
    # Strictly models evidence level, NOT field certainty.
    tier_thresholds: Tuple[Tuple[str, float], ...] = (
        ("HIGH_CONFIDENCE_CANDIDATE", 0.75),
        ("LIKELY", 0.55),
        ("POSSIBLE", 0.35),
        ("NO_EVIDENCE", 0.0),
    )

    # 4. Outburst Risk Classification Tiers
    outburst_risk_levels: Tuple[str, ...] = (
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
        "INSUFFICIENT_DATA",
    )

    # 5. False-Positive Exclusion Zones (Known Artificial Dams & Major Structures in Upper Beas)
    known_artificial_structures: List[Dict[str, float]] = field(
        default_factory=lambda: [
            {"name": "Pandoh_Dam_Spillway", "lat": 31.6708, "lon": 77.0583, "radius_m": 800.0},
            {"name": "Larji_Hydroelectric_Barrage", "lat": 31.7167, "lon": 77.2167, "radius_m": 600.0},
            {"name": "Aut_Tunnel_NH3_Bridge", "lat": 31.7483, "lon": 77.2081, "radius_m": 350.0},
            {"name": "Bhuntar_Confluence_Bridge", "lat": 31.8789, "lon": 77.1554, "radius_m": 300.0},
        ]
    )
