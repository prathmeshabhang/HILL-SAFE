"""
hazard_output_contract.py — Clean Individual Hazard Output Contract
====================================================================
Defines the canonical structured output for each hazard model.
Each hazard output is kept separate and must NOT be collapsed into a
single composite number without explicit labelling.

DESIGN PRINCIPLE:
    flood_m2_probability
    flood_unet_probability
    landslide_m6_susceptibility
    landslide_m7_trigger
    natural_dam_candidate_score

    Each carries: value, model_id, version, data_source, validation_status,
    confidence_quality, timestamp, and semantic_meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Individual Hazard Output Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SingleHazardOutput:
    """
    Structured output for ONE model's spatial prediction.
    This is the atomic unit of a hazard output contract.
    """
    model_id: str                      # e.g. "M2", "M7", "U-Net"
    model_version: str                 # e.g. "v1.0-lgbm350"
    semantic_meaning: str              # What the value means (SUSCEPTIBILITY vs TRIGGER PROBABILITY vs INUNDATION)
    probability_grid: np.ndarray       # 2D float32 raster in [0.0, 1.0]
    data_source: str                   # Where the input data came from
    spatial_resolution_m: float        # Grid cell size in meters
    inference_timestamp: str           # ISO8601 timestamp of when inference was run
    validation_status: str             # One of: VALIDATED, VALIDATION_PENDING, FALLBACK_HEURISTIC
    confidence_quality: str            # One of: HIGH, MEDIUM, LOW, DEGRADED
    known_limitations: str             # Plain-text statement of limitations for this output
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Strictly enforce probability bounds
        if self.probability_grid.ndim != 2:
            raise ValueError(f"probability_grid must be 2D, got shape {self.probability_grid.shape}")
        mn = float(np.nanmin(self.probability_grid))
        mx = float(np.nanmax(self.probability_grid))
        if mn < -1e-5 or mx > 1.0 + 1e-5:
            raise ValueError(
                f"probability_grid contains out-of-range values: min={mn:.6f}, max={mx:.6f}. "
                "All values must be in [0.0, 1.0]."
            )

    @property
    def shape(self):
        return self.probability_grid.shape

    def area_above_threshold(self, threshold: float) -> float:
        """Returns fraction (0.0–1.0) of valid pixels above threshold."""
        valid = self.probability_grid > 0
        if not np.any(valid):
            return 0.0
        return float(np.mean(self.probability_grid[valid] >= threshold))

    def pct_above_threshold(self, threshold: float) -> float:
        """Returns percentage (0.0–100.0) of valid pixels above threshold."""
        return round(self.area_above_threshold(threshold) * 100.0, 2)

    def summary_statistics(self) -> Dict[str, float]:
        """Returns percentile statistics over valid (>0) pixels."""
        valid_vals = self.probability_grid[self.probability_grid > 0]
        if len(valid_vals) == 0:
            return {}
        return {
            "min": round(float(np.min(valid_vals)), 6),
            "max": round(float(np.max(valid_vals)), 6),
            "mean": round(float(np.mean(valid_vals)), 6),
            "median": round(float(np.median(valid_vals)), 6),
            "std": round(float(np.std(valid_vals)), 6),
            "p01": round(float(np.percentile(valid_vals, 1)), 6),
            "p05": round(float(np.percentile(valid_vals, 5)), 6),
            "p25": round(float(np.percentile(valid_vals, 25)), 6),
            "p75": round(float(np.percentile(valid_vals, 75)), 6),
            "p95": round(float(np.percentile(valid_vals, 95)), 6),
            "p99": round(float(np.percentile(valid_vals, 99)), 6),
            "valid_pixels": int(np.sum(self.probability_grid > 0)),
            "total_pixels": int(self.probability_grid.size),
        }


@dataclass
class MultiHazardOutputBundle:
    """
    The complete set of individual model outputs from one scene inference run.
    Individual outputs are preserved; fusion is computed separately and labelled
    as a HEURISTIC COMPOSITE.
    """
    scene_id: str
    inference_timestamp: str
    scene_data_type: str            # "SIMULATED_SYNTHETIC" or "REAL_SATELLITE"

    # Individual hazard outputs — kept SEPARATE
    flood_m2: Optional[SingleHazardOutput]
    flood_unet: Optional[SingleHazardOutput]
    landslide_m6: Optional[SingleHazardOutput]
    landslide_m7: Optional[SingleHazardOutput]
    natural_dam_score: Optional[SingleHazardOutput]

    # Heuristic fusion — explicitly labelled and separate from individual outputs
    heuristic_flood_fusion: Optional[SingleHazardOutput] = None   # 0.6*UNet + 0.4*M2
    heuristic_landslide_fusion: Optional[SingleHazardOutput] = None  # M6 × (0.35 + 0.65*M7)

    def available_models(self):
        """Returns list of model IDs with non-None outputs."""
        available = []
        for attr in ["flood_m2", "flood_unet", "landslide_m6", "landslide_m7", "natural_dam_score"]:
            out = getattr(self, attr)
            if out is not None:
                available.append(out.model_id)
        return available

    def degradation_summary(self) -> Dict[str, str]:
        """
        Returns a degradation status per model.
        If a model is unavailable, confidence is reduced and the UI should warn users.
        """
        status = {}
        for attr, label in [
            ("flood_m2", "M2 Flood Susceptibility"),
            ("flood_unet", "U-Net Active Inundation"),
            ("landslide_m6", "M6 Landslide Susceptibility"),
            ("landslide_m7", "M7 Dynamic Trigger"),
            ("natural_dam_score", "Natural Dam Candidate"),
        ]:
            out = getattr(self, attr)
            if out is None:
                status[label] = "UNAVAILABLE — model output absent; confidence reduced"
            elif out.validation_status == "FALLBACK_HEURISTIC":
                status[label] = "DEGRADED — ML artifact missing, heuristic fallback active"
            else:
                status[label] = f"AVAILABLE — {out.validation_status}"
        return status


# ---------------------------------------------------------------------------
# Factory: Build from SpatialMLEngine results
# ---------------------------------------------------------------------------

def build_hazard_bundle_from_engine(
    scene_id: str,
    inference_timestamp: str,
    landslide_result,          # LandslideMLInferenceResult
    flood_result,              # FloodMLInferenceResult (optional)
    natural_dam_score_grid: Optional[np.ndarray] = None,
) -> MultiHazardOutputBundle:
    """
    Builds a MultiHazardOutputBundle from SpatialMLEngine output objects.
    Preserves separation of individual model outputs.
    """
    from datetime import datetime

    # --- M6 Landslide Susceptibility ---
    m6_out = SingleHazardOutput(
        model_id="M6",
        model_version=getattr(landslide_result, "m6_model_version", "RandomForest_350Trees_v1.0"),
        semantic_meaning=(
            "STATIC_LANDSLIDE_SUSCEPTIBILITY: Probability of geomorphic failure based on "
            "static terrain, lithology, proximity to roads and river. "
            "NOT a current trigger probability — a baseline potential."
        ),
        probability_grid=landslide_result.m6_susceptibility_score.astype(np.float32),
        data_source="Copernicus DEM GLO-30 + ESA WorldCover + GSI Lithology (proxied by elevation band)",
        spatial_resolution_m=30.0,
        inference_timestamp=inference_timestamp,
        validation_status="VALIDATED",
        confidence_quality="HIGH",
        known_limitations=(
            "Lithology code is proxied from elevation bands (not actual GSI map), "
            "LULC derived from spectral indices rather than external ESA product."
        ),
        extra_metadata={"feature_importances": getattr(landslide_result, "m6_feature_importances", {})},
    )

    # --- M7 Dynamic Trigger ---
    m7_out = SingleHazardOutput(
        model_id="M7",
        model_version=getattr(landslide_result, "m7_model_version", "LGBM_350Rounds_v1.0"),
        semantic_meaning=(
            "DYNAMIC_TRIGGER_PROBABILITY: P(Landslide | current rainfall, antecedent rain, "
            "soil moisture, slope, susceptibility class). "
            "Conditioned on storm scenario inputs — NOT an unconditional annual frequency."
        ),
        probability_grid=landslide_result.m7_trigger_probability.astype(np.float32),
        data_source=(
            "M6 susceptibility output + Copernicus DEM slope + "
            "Uniform constant rainfall inputs (25mm/1h, 85mm/3d) + "
            "NDMI proxy soil moisture (18+clip((NDMI+0.35)/0.95,0,1)*72)"
        ),
        spatial_resolution_m=30.0,
        inference_timestamp=inference_timestamp,
        validation_status="VALIDATED",
        confidence_quality="MEDIUM",
        known_limitations=(
            "1. Rainfall inputs are spatially uniform constants — no IMD DWR spatial grid integration. "
            "2. Soil moisture is a satellite proxy (NDMI-based), not measured volumetric water content. "
            "3. Synthetic simulation scene has NDMI at only 4 distinct values — real scenes will show "
            "   more heterogeneous M7 output. "
            "4. ECE=0.0432 measured on latitude-block spatial holdout of the SAME training dataset — "
            "   not an independent external event validation."
        ),
        extra_metadata={"feature_importances": getattr(landslide_result, "m7_feature_importances", {})},
    )

    # --- Heuristic Landslide Fusion (M6 × trigger amplifier) ---
    landslide_fusion_out = SingleHazardOutput(
        model_id="LandslideFusion",
        model_version="HeuristicCombine_v1.0",
        semantic_meaning=(
            "HEURISTIC_COMPOSITE_LANDSLIDE_RISK: M6_susceptibility × (0.35 + 0.65 × M7_trigger). "
            "NOT a statistically fitted probability. Expert heuristic weighting only."
        ),
        probability_grid=landslide_result.combined_landslide_risk.astype(np.float32),
        data_source="M6 + M7 outputs (see individual models)",
        spatial_resolution_m=30.0,
        inference_timestamp=inference_timestamp,
        validation_status="VALIDATION_PENDING",
        confidence_quality="MEDIUM",
        known_limitations=(
            "Combination weights (0.35 base + 0.65 trigger amplifier) are expert heuristics, "
            "not fitted by statistical regression or cross-validated against event holdouts."
        ),
    )

    # --- Flood outputs ---
    m2_out = None
    unet_out = None
    flood_fusion_out = None
    if flood_result is not None:
        if getattr(flood_result, "m2_flood_probability", None) is not None:
            m2_out = SingleHazardOutput(
                model_id="M2",
                model_version=getattr(flood_result, "m2_model_version", "XGBoost_Calibrated_v1.0"),
                semantic_meaning=(
                    "FLOOD_OCCURRENCE_SUSCEPTIBILITY: P(Flash Flood Occurrence | "
                    "topography, rainfall intensity, CWC gauge, antecedent moisture). "
                    "Calibrated XGBoost with isotonic calibration — probabilities are "
                    "empirically calibrated against 20% spatial holdout."
                ),
                probability_grid=flood_result.m2_flood_probability.astype(np.float32),
                data_source=(
                    "Copernicus DEM + Sentinel-2 NDMI (soil moisture proxy) + "
                    "CWC simulated gauge readings + uniform rainfall inputs"
                ),
                spatial_resolution_m=30.0,
                inference_timestamp=inference_timestamp,
                validation_status="VALIDATED",
                confidence_quality="HIGH",
                known_limitations=(
                    "CWC gauge value (6.2m) and rise rate (0.35m/hr) are constant defaults — "
                    "not real-time readings. Spatial holdout validation only; "
                    "no independent external event holdout available."
                ),
                extra_metadata={"feature_importances": getattr(flood_result, "m2_feature_importances", {})},
            )

        if getattr(flood_result, "unet_inundation_probability", None) is not None:
            unet_out = SingleHazardOutput(
                model_id="U-Net",
                model_version=getattr(flood_result, "unet_model_version", "PyTorch_Multimodal_UNet_v1.0"),
                semantic_meaning=(
                    "ACTIVE_INUNDATION_PROBABILITY: P(Active water inundation at pixel) "
                    "from 9-channel SAR+optical U-Net segmentation. "
                    "Detected from real-time sensor fusion, not modelled susceptibility."
                ),
                probability_grid=flood_result.unet_inundation_probability.astype(np.float32),
                data_source="Sentinel-1 SAR VV/VH + Sentinel-2 B04/B03/B08/B11 + DEM/Slope/HAND",
                spatial_resolution_m=30.0,
                inference_timestamp=inference_timestamp,
                validation_status="VALIDATION_PENDING",
                confidence_quality="MEDIUM",
                known_limitations=(
                    "Validated against radar-topographic PSEUDO-GROUND-TRUTH (SAR backscatter "
                    "threshold + HAND mask) — NOT against independent mapped flood extents. "
                    "Dice=96.4-97.1% and IoU=93.0-94.3% are measured against pseudo-GT only."
                ),
            )

        if getattr(flood_result, "fused_flood_susceptibility", None) is not None:
            flood_fusion_out = SingleHazardOutput(
                model_id="FloodFusion",
                model_version="HeuristicFusion_60_40_v1.0",
                semantic_meaning=(
                    "HEURISTIC_COMPOSITE_FLOOD_RISK: 0.60×U-Net + 0.40×M2. "
                    "NOT a statistically fitted probability. Expert heuristic weighting only."
                ),
                probability_grid=flood_result.fused_flood_susceptibility.astype(np.float32),
                data_source="U-Net + M2 outputs (see individual models)",
                spatial_resolution_m=30.0,
                inference_timestamp=inference_timestamp,
                validation_status="VALIDATION_PENDING",
                confidence_quality="MEDIUM",
                known_limitations=(
                    "60/40 weighting is an expert heuristic — not fitted by statistical regression "
                    "or cross-validated against held-out events. Active water pixels are pinned to "
                    "flood_fused >= 0.90 regardless of M2 output."
                ),
            )

    # --- Natural dam score (optional) ---
    dam_out = None
    if natural_dam_score_grid is not None:
        dam_out = SingleHazardOutput(
            model_id="NaturalDam",
            model_version="8EvidenceScorer_v1.0",
            semantic_meaning=(
                "NATURAL_DAM_CANDIDATE_SCORE: Evidence-weighted composite score from "
                "8 physical indicators (channel blockage, SAR backscatter change, "
                "upstream lake expansion, etc.). "
                "Status: CANDIDATE_UNVERIFIED until authority field validation."
            ),
            probability_grid=natural_dam_score_grid.astype(np.float32),
            data_source="Sentinel-1 SAR + Sentinel-2 NDWI + DEM channel analysis",
            spatial_resolution_m=30.0,
            inference_timestamp=inference_timestamp,
            validation_status="VALIDATION_PENDING",
            confidence_quality="LOW",
            known_limitations=(
                "Candidate status only. No automated public siren from satellite detection alone. "
                "Must be independently field-validated by HPSDMA/CWC/NDMA before public action."
            ),
        )

    return MultiHazardOutputBundle(
        scene_id=scene_id,
        inference_timestamp=inference_timestamp,
        scene_data_type="SIMULATED_SYNTHETIC",   # Update to REAL_SATELLITE once actual data is used
        flood_m2=m2_out,
        flood_unet=unet_out,
        landslide_m6=m6_out,
        landslide_m7=m7_out,
        natural_dam_score=dam_out,
        heuristic_flood_fusion=flood_fusion_out,
        heuristic_landslide_fusion=landslide_fusion_out,
    )
