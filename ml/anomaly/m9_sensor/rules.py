"""
ml/anomaly/m9_sensor/rules.py
=============================
Stage 1 Deterministic Rules Engine for Model M9.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ml.anomaly.m9_sensor.schema import SensorAnomalyType

M9_PHYSICAL_LIMITS = {
    "rainfall_rate_mmh": (0.0, 300.0, 80.0),      # min, max, max_15m_delta
    "water_level_m": (0.0, 25.0, 4.0),
    "soil_moisture_pct": (0.0, 100.0, 35.0),
    "tilt_deg": (-90.0, 90.0, 25.0),
    "pore_pressure_kpa": (0.0, 250.0, 50.0),
    "temperature_c": (-30.0, 50.0, 15.0),
}


class DeterministicRulesEngine:
    def __init__(self, stuck_threshold: int = 4):
        self.stuck_threshold = stuck_threshold

    def evaluate(
        self,
        current: Dict[str, float],
        history: Optional[Sequence[Dict[str, float]]] = None,
    ) -> Tuple[bool, SensorAnomalyType, List[str], str]:
        """
        Evaluates Stage 1 deterministic physical rules.
        Returns: (is_anomalous, anomaly_type, flags, recommended_action)
        """
        flags: List[str] = []

        # 1. Physical limits
        for var, (low, high, max_delta) in M9_PHYSICAL_LIMITS.items():
            if var in current and current[var] is not None:
                val = float(current[var])
                if val < low:
                    flags.append(f"NEGATIVE_VALUE: {var}={val:.2f} < {low}")
                    return True, SensorAnomalyType.PHYSICAL_RANGE_VIOLATION, flags, "REJECT_READING_CALIBRATE_ZERO"
                if val > high:
                    flags.append(f"CEILING_EXCEEDED: {var}={val:.2f} > {high}")
                    return True, SensorAnomalyType.PHYSICAL_RANGE_VIOLATION, flags, "REJECT_READING_DISPATCH_FIELD_CHECK"

        # 2. Rate of change spikes
        if history and len(history) >= 1:
            prev = history[-1]
            for var, (_, _, max_delta) in M9_PHYSICAL_LIMITS.items():
                if var in current and var in prev:
                    if current[var] is not None and prev[var] is not None:
                        delta = abs(float(current[var]) - float(prev[var]))
                        if delta > max_delta:
                            flags.append(f"UNPHYSICAL_SPIKE: delta({var})={delta:.2f} > {max_delta}")
                            return True, SensorAnomalyType.RATE_OF_CHANGE_SPIKE, flags, "FLAG_AND_RETRY_SMOOTHING"

        # 3. Stuck sensor detection
        if history and len(history) >= self.stuck_threshold:
            for var in ["water_level_m", "soil_moisture_pct", "pore_pressure_kpa"]:
                if var in current and current[var] is not None:
                    val = float(current[var])
                    if val > 0.05:  # Non-zero baseline
                        past_vals = [h.get(var) for h in history[-self.stuck_threshold:] if h.get(var) is not None]
                        if len(past_vals) == self.stuck_threshold and all(abs(float(p) - val) < 1e-4 for p in past_vals):
                            flags.append(f"STUCK_SENSOR: {var} frozen at {val:.3f} for {self.stuck_threshold} cycles")
                            return True, SensorAnomalyType.STUCK_SENSOR, flags, "ALERT_TECHNICIAN_HARDWARE_REBOOT"

        return False, SensorAnomalyType.NONE, [], "MAINTAIN_NORMAL_STREAM"
