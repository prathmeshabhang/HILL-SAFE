"""
ml/anomaly/m9_sensor/statistical.py
===================================
Stage 2 Rolling Statistical Filters & Cross-Sensor Consistency Checks for Model M9.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ml.anomaly.m9_sensor.schema import SensorAnomalyType


class StatisticalFilterEngine:
    def __init__(self, z_thresh: float = 3.5, mad_thresh: float = 4.0):
        self.z_thresh = z_thresh
        self.mad_thresh = mad_thresh

    def compute_rolling_stats(
        self,
        values: Sequence[float],
    ) -> Dict[str, float]:
        """Calculates rolling mean, std, median, and MAD for a series."""
        arr = np.asarray(values, dtype=float)
        if len(arr) < 3:
            return {"mean": float(np.mean(arr)) if len(arr) > 0 else 0.0, "std": 0.0, "mad": 0.0}
        
        mean = float(np.mean(arr))
        std = float(np.std(arr)) + 1e-6
        median = float(np.median(arr))
        mad = float(np.median(np.abs(arr - median))) + 1e-6
        return {"mean": mean, "std": std, "median": median, "mad": mad}

    def check_cross_sensor_consistency(
        self,
        current: Dict[str, float],
        history: Optional[Sequence[Dict[str, float]]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Differentiates genuine multi-hazard extreme events from sensor faults:
        - If rainfall is massive (>50 mm/h) and river rises -> AUTHENTIC STORM EVENT (Not an anomaly!)
        - If river level spikes by >2.5m with ZERO rainfall anywhere -> FAULT / UNPHYSICAL
        - If tilt angle spikes by >15 deg with ZERO soil moisture/rain -> SENSOR DRIFT
        """
        rain = float(current.get("rainfall_rate_mmh", 0.0))
        water = float(current.get("water_level_m", 0.0))
        soil = float(current.get("soil_moisture_pct", 0.0))
        tilt = float(current.get("tilt_deg", 0.0))

        if history and len(history) >= 2:
            prev_water = float(history[-1].get("water_level_m", water))
            water_rise = water - prev_water

            # Fast water rise with completely zero rainfall in history
            past_rain = sum(float(h.get("rainfall_rate_mmh", 0.0)) for h in history[-3:])
            if water_rise > 2.0 and past_rain < 0.1 and rain < 0.1:
                return True, "CROSS_SENSOR_INCONSISTENCY: Large water level rise (+{:.2f}m) observed with zero rainfall".format(water_rise)

            # High tilt displacement without moisture or rain
            prev_tilt = float(history[-1].get("tilt_deg", tilt))
            tilt_delta = abs(tilt - prev_tilt)
            if tilt_delta > 15.0 and soil < 25.0 and rain < 1.0:
                return True, "CROSS_SENSOR_INCONSISTENCY: Sudden tilt jerk ({:.1f} deg) on completely dry soil".format(tilt_delta)

        return False, None

    def is_authentic_storm_surge(self, current: Dict[str, float]) -> bool:
        """
        True multi-hazard storm events exhibit correlated rises across sensors:
        intense rain (>50 mm/h), elevated river level (>4.0m), and saturated soil (>60%).
        These must be preserved as authentic physical events, not sensor faults.
        """
        rain = float(current.get("rainfall_rate_mmh", 0.0))
        water = float(current.get("water_level_m", 0.0))
        soil = float(current.get("soil_moisture_pct", 0.0))
        return bool(rain >= 50.0 and water >= 4.0 and soil >= 60.0)
