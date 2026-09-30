"""
sar_coherence_engine.py — Sentinel-1 SAR Interferometric Coherence Loss & Damage Proxy
========================================================================================
Implements SAR Damage Proxy Mapping (DPM) based on:
  1. Interferometric Coherence Loss: Delta Gamma = Gamma_pre - Gamma_post.
     Stable urban structures maintain high coherence (0.75-0.95). Structural destruction,
     wall collapse, and silt inundation cause catastrophic phase decorrelation (Delta Gamma > 0.45).
  2. Double-Bounce Backscatter Depletion: Intact buildings exhibit strong right-angle
     corner reflection. Collapsed or submerged structures lose 3.5 dB to 8 dB of VV backscatter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np


@dataclass
class SARCoherenceAnalysis:
    mean_coherence_pre: float
    mean_coherence_post: float
    mean_coherence_loss: float
    backscatter_drop_db: float
    damage_proxy_index: float  # Normalized 0.0 to 1.0
    decorrelation_severity: str  # "EXTREME", "SEVERE", "MODERATE", "LOW"


class SARCoherenceEngine:
    """Computes radar phase decorrelation and backscatter change for damage proxy mapping."""

    def compute_damage_proxy(
        self,
        coherence_pre: np.ndarray,
        coherence_post: np.ndarray,
        sar_vv_pre_db: np.ndarray,
        sar_vv_post_db: np.ndarray,
    ) -> Tuple[np.ndarray, SARCoherenceAnalysis]:
        """
        Computes pixel-level Damage Proxy Map (DPM) and summary statistics.
        """
        # Coherence loss: Delta Gamma = Gamma_pre - Gamma_post
        delta_gamma = np.maximum(0.0, coherence_pre - coherence_post)

        # Backscatter change: Delta Sigma0 = Sigma0_post - Sigma0_pre
        delta_vv = sar_vv_post_db - sar_vv_pre_db
        # In urban collapse/flood, backscatter typically drops (negative delta_vv)
        amplitude_loss = np.maximum(0.0, -delta_vv)

        # Damage Proxy Index (DPI) fusing phase decorrelation (0.65) and amplitude loss (0.35)
        # Scaled so that delta_gamma of 0.50 and amplitude drop of 5dB produces ~0.85
        dpi_grid = np.clip(
            (delta_gamma / 0.60) * 0.65 + (amplitude_loss / 6.0) * 0.35,
            0.0,
            1.0,
        ).astype(np.float32)

        mean_pre = float(np.mean(coherence_pre))
        mean_post = float(np.mean(coherence_post))
        mean_loss = float(np.mean(delta_gamma))
        mean_drop = float(np.mean(amplitude_loss))
        mean_dpi = float(np.mean(dpi_grid))

        if mean_loss >= 0.45 or mean_dpi >= 0.70:
            severity = "EXTREME"
        elif mean_loss >= 0.30 or mean_dpi >= 0.45:
            severity = "SEVERE"
        elif mean_loss >= 0.15:
            severity = "MODERATE"
        else:
            severity = "LOW"

        stats = SARCoherenceAnalysis(
            mean_coherence_pre=round(mean_pre, 3),
            mean_coherence_post=round(mean_post, 3),
            mean_coherence_loss=round(mean_loss, 3),
            backscatter_drop_db=round(mean_drop, 2),
            damage_proxy_index=round(mean_dpi, 3),
            decorrelation_severity=severity,
        )

        return dpi_grid, stats
