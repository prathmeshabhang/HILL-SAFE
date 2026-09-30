"""
ml/flood/m12_cascade/features.py
================================
Feature extraction and scenario configuration for Model M12.
"""

from __future__ import annotations

from typing import Any, Dict


def extract_m12_features(reading: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts features for Model M12 Cascade Breach Simulation."""
    loc = str(reading.get("dam_location", "Larji_Sainj_Confluence"))
    h_dam = float(reading.get("dam_height_m", 35.0))
    v_imp = float(reading.get("impounded_volume_m3", 8_500_000.0))
    q_norm = float(reading.get("normal_river_discharge_m3s", reading.get("baseflow_m3s", 450.0)))
    trig_p = float(reading.get("trigger_probability", 0.85))

    return {
        "dam_location": loc,
        "dam_height_m": max(2.0, h_dam),
        "impounded_volume_m3": max(10_000.0, v_imp),
        "normal_river_discharge_m3s": max(10.0, q_norm),
        "trigger_probability": min(1.0, max(0.0, trig_p)),
    }
