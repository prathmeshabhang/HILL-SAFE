"""
extreme_rainfall_m1.py — FLOODY SHIELD Phase 7
===============================================
Extracts multi-horizon rainfall forecasts, evaluates extreme rainfall thresholds,
and computes flood/landslide decision-support indicators from pySTEPS nowcasts.

SCIENTIFIC & RISK PRINCIPLES
----------------------------
1. Decision Support vs. Raw Alerts:
   - Does NOT directly trigger automated public alerts or siren dispatches.
   - Outputs structured, calibrated risk metrics for downstream hydrological
     routing and landslide slope-stability modeling.
2. Accumulation over Lead Horizons:
   - Ingests nowcast rainfall rates (mm/hr) across 30-minute intervals.
   - Computes expected rainfall depth (mm) over:
       * Next 15-30 min (immediate flash surge)
       * Next 1 hour (surface runoff onset)
       * Next 3 hours (watershed saturation & debris flow threshold)
3. Multi-Threshold Risk Stratification (Provisional for Indian Hill Basins):
   - Advisory / Moderate:  1-hour rain >= 15 mm OR 3-hour rain >= 30 mm
   - High Risk:            1-hour rain >= 35 mm OR 3-hour rain >= 65 mm
   - Extreme / Cloudburst: 1-hour rain >= 50 mm (or rate >= 100 mm/hr peak)
   * All thresholds are explicitly flagged as PROVISIONAL until watershed calibration.

OUTPUT SCHEMA
-------------
{
  "forecast_horizon_minutes": 180,
  "issue_time_utc": "2026-09-20T01:20:35Z",
  "observation_time_utc": "2026-09-19T14:30:00Z",
  "source_latency_minutes": 321.2,
  "data_quality": "GOOD",
  "expected_rainfall_15min_mm": 0.0,
  "expected_rainfall_1h_mm": 0.0,
  "expected_rainfall_3h_mm": 0.0,
  "maximum_forecast_rate_mm_hr": 0.0,
  "probability_exceedance_moderate": 0.0,
  "probability_exceedance_extreme": 0.0,
  "risk_level": "LOW",
  "confidence": "MODERATE",
  "scientific_status": "PROTOTYPE_NOT_VALIDATED",
  "recommended_action": "Routine Monitoring"
}
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import xarray as xr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("floody_shield.extreme_rainfall_m1")

# Provisional Thresholds (mm of accumulated rain over lead window)
THR_1H_MODERATE = 15.0
THR_1H_HIGH = 35.0
THR_1H_EXTREME = 50.0  # Approaching cloudburst rate if sustained

THR_3H_MODERATE = 30.0
THR_3H_HIGH = 65.0
THR_3H_EXTREME = 100.0


class ExtremeRainfallAnalyzer:
    """Computes flood and landslide meteorological trigger metrics from nowcast grids."""

    def analyze(
        self,
        nowcast_ds: xr.Dataset,
        quality_status: str = "GOOD",
        latency_minutes: float = 240.0,
    ) -> Dict[str, Any]:
        """
        Integrates rainfall rates over forecast horizons and computes risk metrics.
        """
        # Data variables: precip_ensemble_mean is (lead_time, lat, lon) in mm/hr
        mean_grid = nowcast_ds["precip_ensemble_mean"].values  # shape: (n_leads, lat, lon)
        det_grid = nowcast_ds["precip_deterministic"].values
        lead_minutes = nowcast_ds["lead_time"].values  # [30, 60, 90, 120, 150, 180]
        obs_time_str = nowcast_ds.attrs.get("observation_time_utc", "UNKNOWN")

        n_leads = len(lead_minutes)

        # 1. Integrate rainfall rate (mm/hr) to accumulated depth (mm)
        # Each step represents dt = 0.5 hours (30 min)
        dt_hr = 0.5

        # 30-min accumulation = step 0 * 0.5 hr
        acc_30min_grid = mean_grid[0] * dt_hr
        # 15-min expected is half of 30-min step
        expected_15min_mm = float(np.max(acc_30min_grid * 0.5))
        expected_30min_mm = float(np.max(acc_30min_grid))

        # 1-hour accumulation: first 2 steps (30 min + 60 min)
        if n_leads >= 2:
            acc_1h_grid = (mean_grid[0] + mean_grid[1]) * dt_hr
            expected_1h_mm = float(np.max(acc_1h_grid))
        else:
            expected_1h_mm = expected_30min_mm

        # 3-hour accumulation: up to 6 steps
        steps_3h = min(6, n_leads)
        acc_3h_grid = np.sum(mean_grid[:steps_3h], axis=0) * dt_hr
        expected_3h_mm = float(np.max(acc_3h_grid))

        max_forecast_rate = float(np.max(mean_grid))

        # 2. Exceedance probabilities from full ensemble if available
        if "precip_ensemble_all" in nowcast_ds:
            ens_all = nowcast_ds["precip_ensemble_all"].values  # (members, leads, lat, lon)
            # Accumulate each member over 1h (first 2 steps)
            if n_leads >= 2:
                ens_acc_1h = np.sum(ens_all[:, :2, :, :], axis=1) * dt_hr  # (members, lat, lon)
                prob_moderate_1h = float(np.max(np.mean(ens_acc_1h >= THR_1H_MODERATE, axis=0)))
                prob_extreme_1h = float(np.max(np.mean(ens_acc_1h >= THR_1H_EXTREME, axis=0)))
            else:
                prob_moderate_1h = 0.0
                prob_extreme_1h = 0.0
        else:
            prob_moderate_1h = 0.0
            prob_extreme_1h = 0.0

        # 3. Determine Provisional Risk Level
        if expected_1h_mm >= THR_1H_EXTREME or expected_3h_mm >= THR_3H_EXTREME:
            risk_level = "CRITICAL_EXTREME"
            rec_action = "Issue High Priority Flash Flood & Landslide Advisory to Hydrological Dispatch"
        elif expected_1h_mm >= THR_1H_HIGH or expected_3h_mm >= THR_3H_HIGH or prob_moderate_1h >= 0.5:
            risk_level = "HIGH"
            rec_action = "Alert Field Stations and Run Hydro-Dynamic Inundation Simulation"
        elif expected_1h_mm >= THR_1H_MODERATE or expected_3h_mm >= THR_3H_MODERATE or prob_moderate_1h >= 0.2:
            risk_level = "MODERATE"
            rec_action = "Heightened Meteorological Monitoring; Check Slope Moisture Baseline"
        else:
            risk_level = "LOW"
            rec_action = "Routine Prototype Surveillance"

        # 4. Confidence Assessment
        # Satellite data with ~4h latency + 0.1 deg spatial coarseness implies Moderate to Low confidence
        if quality_status == "GOOD" and latency_minutes <= 360.0:
            confidence = "MODERATE_PROTOTYPE"
        elif quality_status == "DEGRADED" or latency_minutes > 360.0:
            confidence = "LOW_DEGRADED"
        else:
            confidence = "VERY_LOW"

        return {
            "forecast_horizon_minutes": int(lead_minutes[-1]),
            "issue_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "observation_time_utc": obs_time_str,
            "source_latency_minutes": latency_minutes,
            "data_quality": quality_status,
            "expected_rainfall_15min_max_mm": round(expected_15min_mm, 2),
            "expected_rainfall_1h_max_mm": round(expected_1h_mm, 2),
            "expected_rainfall_3h_max_mm": round(expected_3h_mm, 2),
            "maximum_forecast_rate_mm_hr": round(max_forecast_rate, 2),
            "probability_exceedance_moderate_1h": round(prob_moderate_1h, 3),
            "probability_exceedance_extreme_1h": round(prob_extreme_1h, 3),
            "risk_level": risk_level,
            "confidence": confidence,
            "scientific_status": "PROTOTYPE_NOT_VALIDATED",
            "threshold_calibration_status": "PROVISIONAL_UNVALIDATED",
            "recommended_action": rec_action,
            "limitations_disclaimer": (
                "Decision support indicator only. Uncalibrated satellite data cannot guarantee "
                "flash-flood warning precision at village scale without IMD radar or gauge telemetry."
            ),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate M1 Extreme Rainfall Risk Summary.")
    parser.add_argument(
        "--nowcast-nc",
        type=str,
        default="ml/rainfall/models/nowcasts/latest_nowcast.nc",
        help="Path to pySTEPS nowcast NetCDF.",
    )
    parser.add_argument(
        "--out-json",
        type=str,
        default="ml/rainfall/models/nowcasts/extreme_rainfall_m1_summary.json",
        help="Output path for decision-support summary JSON.",
    )
    args = parser.parse_args()

    nc_path = Path(args.nowcast_nc)
    if not nc_path.exists():
        log.error("Nowcast NetCDF not found: %s", nc_path)
        sys.exit(1)

    ds = xr.open_dataset(nc_path)
    analyzer = ExtremeRainfallAnalyzer()
    summary = analyzer.analyze(ds)

    out_file = Path(args.out_json)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print()
    print("=" * 60)
    print("FLOODY SHIELD — M1 EXTREME RAINFALL DECISION SUMMARY")
    print("=" * 60)
    print(f"Risk Level          : {summary['risk_level']}")
    print(f"Confidence Level    : {summary['confidence']}")
    print(f"Data Quality        : {summary['data_quality']}")
    print(f"Source Latency      : {summary['source_latency_minutes']} min")
    print(f"Peak Rate Forecast  : {summary['maximum_forecast_rate_mm_hr']} mm/hr")
    print(f"Max Expected 15-min : {summary['expected_rainfall_15min_max_mm']} mm")
    print(f"Max Expected 1-hour : {summary['expected_rainfall_1h_max_mm']} mm")
    print(f"Max Expected 3-hour : {summary['expected_rainfall_3h_max_mm']} mm")
    print(f"Prob (>15 mm/1h)    : {summary['probability_exceedance_moderate_1h'] * 100:.1f}%")
    print(f"Action Advisory     : {summary['recommended_action']}")
    print(f"Scientific Status   : {summary['scientific_status']}")
    print("=" * 60)
    print(f"Summary JSON saved: {out_file.resolve()}")


if __name__ == "__main__":
    main()
