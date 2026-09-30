"""
config.py — Configuration & Damage Grading Thresholds for Model M20
====================================================================
Defines remote sensing thresholds, SAR coherence drop cutoffs, Copernicus EMS
structural damage classes, and NDRF/SDRF Rescue Prioritization Index weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class DamageAssessmentConfig:
    # 1. SAR Interferometric Coherence Loss Thresholds
    min_coherence_loss_severe: float = 0.45      # Severe decorrelation -> structural collapse
    min_coherence_loss_moderate: float = 0.25    # Moderate decorrelation -> inundation / partial damage
    min_backscatter_drop_db: float = -3.5        # Loss of double-bounce corner reflection

    # 2. Optical Spectral Degradation Thresholds
    min_ndbi_drop: float = 0.20                  # Loss of built-up spectral signature
    min_texture_entropy_loss: float = 0.30       # Disruption of geometric urban rooflines

    # 3. Copernicus EMS Damage Grading Tiers (0.0 to 1.0)
    damage_tiers: Tuple[Tuple[str, float], ...] = (
        ("DESTROYED", 0.75),           # Structural collapse, washed away by flood
        ("MAJOR_DAMAGE", 0.50),        # Frame compromise, partial roof/wall failure
        ("PARTIAL_DAMAGE", 0.25),      # Ground floor inundated, non-structural debris
        ("NEGLIGIBLE_INTACT", 0.0),    # Structurally sound, accessible
    )

    # 4. Rescue Prioritization Index (RPI) Weights (Sum = 1.0)
    rpi_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "damage_severity": 0.40,    # Ratio of destroyed/major damaged structures
            "vulnerable_population": 0.35, # Residents, elderly, hospital/school proximity
            "isolation_factor": 0.25,   # Severed roads, cut-off bridges, trapped settlements
        }
    )

    # 5. Statutory Engineering Notice
    statutory_notice: str = (
        "SATELLITE DAMAGE ESTIMATION: Building damage levels and road cut-offs are derived from "
        "Sentinel-1 SAR coherence loss and Sentinel-2 multispectral change. On-site structural "
        "safety inspection by qualified structural engineers remains mandatory prior to re-occupancy."
    )
