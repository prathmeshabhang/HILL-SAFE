"""
ml/flood/m12_cascade/physics.py
===============================
Geotechnical and hydraulic formulations for landslide dam breach and outburst wave routing.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

GRAVITY = 9.81  # m/s^2


def compute_froehlich_breach_parameters(
    dam_height_m: float,
    impounded_volume_m3: float,
) -> Dict[str, float]:
    """
    Froehlich (2008) empirical breach parameters:
    Peak Outflow:
        Q_p = 0.607 * (V_w ^ 0.295) * (H_d ^ 1.24)
    Breach Formation Time:
        t_f = 0.0177 * sqrt(V_w / (g * H_d^2)) [hours]
    Average Breach Width:
        B_avg = 0.27 * (V_w ^ 0.32) * (H_d ^ 0.04) [meters]
    """
    h_d = max(2.0, dam_height_m)
    v_w = max(10_000.0, impounded_volume_m3)

    q_peak_breach = 0.607 * (v_w ** 0.295) * (h_d ** 1.24)
    t_f_hours = 0.0177 * math.sqrt(v_w / (GRAVITY * (h_d ** 2)))
    t_f_min = max(5.0, t_f_hours * 60.0)
    b_avg = 0.27 * (v_w ** 0.32) * (h_d ** 0.04)

    return {
        "peak_breach_discharge_m3s": round(q_peak_breach, 2),
        "breach_formation_time_min": round(t_f_min, 2),
        "average_breach_width_m": round(b_avg, 2),
    }


def compute_costa_peak_outflow(
    dam_height_m: float,
    impounded_volume_m3: float,
) -> float:
    """
    Costa (1985) empirical peak outflow for landslide dam failures:
    Q_p = 0.00013 * (P_E ^ 0.60)
    where P_E is potential energy of impounded water = gamma_w * V_w * H_d (Joules)
    """
    h_d = max(2.0, dam_height_m)
    v_w = max(10_000.0, impounded_volume_m3)
    gamma_w = 9810.0  # N/m^3
    p_e = gamma_w * v_w * h_d
    q_costa = 0.00013 * (p_e ** 0.60)
    return float(round(q_costa, 2))
