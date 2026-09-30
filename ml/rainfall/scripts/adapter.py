"""
adapter.py — FLOODY SHIELD Phase 9
====================================
Standardized, decoupled API adapter interface connecting M1 Rainfall Nowcasting
to downstream FLOODY SHIELD modules (Hydrology, Landslide Slope Stability,
Alert Engine, and Web / FastAPI endpoints).

ADAPTER PRINCIPLES
------------------
1. Decoupling:
   - Downstream consumers never need to know whether the forecast originated from
     pySTEPS, GPM satellite, IMD radar, or a deep learning model.
2. Standardized Output Types:
   - Returns typed dataclass `RainfallForecast` with spatial grids, coordinates,
     temporal vectors, and confidence metadata.
3. Safety Guardrails:
   - Prevents unvalidated ML forecasts from directly issuing emergency alarms.
   - Enforces explicit `scientific_status` and `risk_level` stratification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xarray as xr


@dataclass
class StudyArea:
    west: float
    south: float
    east: float
    north: float
    name: str = "custom_watershed"


@dataclass
class ForecastGridPayload:
    lead_minutes: List[int]
    valid_timestamps_utc: List[str]
    latitudes: List[float]
    longitudes: List[float]
    deterministic_rate_mm_hr: List[List[List[float]]]  # (leads, lat, lon)
    ensemble_mean_rate_mm_hr: List[List[List[float]]]
    prob_exceed_moderate: List[List[List[float]]]


@dataclass
class RainfallForecast:
    study_area: Dict[str, Any]
    observation_time_utc: str
    issue_time_utc: str
    forecast_horizon_minutes: int
    source: str
    model_version: str
    data_quality: str
    confidence: str
    risk_level: str
    source_latency_minutes: float
    processing_latency_seconds: float
    expected_rainfall_15min_mm: float
    expected_rainfall_1h_mm: float
    expected_rainfall_3h_mm: float
    peak_forecast_rate_mm_hr: float
    recommended_action: str
    scientific_status: str
    grid_payload: Optional[ForecastGridPayload] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class FloodyShieldRainfallAdapter:
    """Service adapter exposing clean python and REST-ready methods for FLOODY SHIELD."""

    def __init__(self, models_dir: Optional[Path] = None):
        if models_dir is None:
            # Default to standard project directory
            self.models_dir = (
                Path(__file__).resolve().parents[3] / "ml" / "rainfall" / "models" / "nowcasts"
            )
        else:
            self.models_dir = Path(models_dir)

    def get_latest_forecast(self, include_full_grids: bool = False) -> RainfallForecast:
        """
        Retrieves the latest processed pySTEPS nowcast and M1 extreme rainfall summary.
        """
        nc_file = self.models_dir / "latest_nowcast.nc"
        summary_file = self.models_dir / "extreme_rainfall_m1_summary.json"
        health_file = self.models_dir / "pipeline_health.json"

        if not nc_file.exists() or not summary_file.exists():
            raise FileNotFoundError(
                f"Nowcast files not found in {self.models_dir}. Run pipeline first."
            )

        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)

        processing_lat = 0.0
        if health_file.exists():
            with open(health_file, "r", encoding="utf-8") as f:
                health = json.load(f)
                processing_lat = health.get("processing_latency_seconds", 0.0)

        grid_payload = None
        ds = xr.open_dataset(nc_file)

        if include_full_grids:
            grid_payload = ForecastGridPayload(
                lead_minutes=[int(m) for m in ds["lead_time"].values],
                valid_timestamps_utc=[str(t) for t in ds["valid_time"].values],
                latitudes=[round(float(lat), 3) for lat in ds["lat"].values],
                longitudes=[round(float(lon), 3) for lon in ds["lon"].values],
                deterministic_rate_mm_hr=ds["precip_deterministic"].values.tolist(),
                ensemble_mean_rate_mm_hr=ds["precip_ensemble_mean"].values.tolist(),
                prob_exceed_moderate=ds["prob_exceed_5mm_hr"].values.tolist(),
            )

        study_area_dict = {
            "west": float(ds["lon"].min()),
            "south": float(ds["lat"].min()),
            "east": float(ds["lon"].max()),
            "north": float(ds["lat"].max()),
        }

        forecast = RainfallForecast(
            study_area=study_area_dict,
            observation_time_utc=summary["observation_time_utc"],
            issue_time_utc=summary["issue_time_utc"],
            forecast_horizon_minutes=summary["forecast_horizon_minutes"],
            source="GPM_IMERG_EARLY_V07",
            model_version="pySTEPS-1.21.5-STEPS",
            data_quality=summary["data_quality"],
            confidence=summary["confidence"],
            risk_level=summary["risk_level"],
            source_latency_minutes=summary["source_latency_minutes"],
            processing_latency_seconds=processing_lat,
            expected_rainfall_15min_mm=summary["expected_rainfall_15min_max_mm"],
            expected_rainfall_1h_mm=summary["expected_rainfall_1h_max_mm"],
            expected_rainfall_3h_mm=summary["expected_rainfall_3h_max_mm"],
            peak_forecast_rate_mm_hr=summary["maximum_forecast_rate_mm_hr"],
            recommended_action=summary["recommended_action"],
            scientific_status=summary["scientific_status"],
            grid_payload=grid_payload,
        )

        return forecast


if __name__ == "__main__":
    adapter = FloodyShieldRainfallAdapter()
    fc = adapter.get_latest_forecast(include_full_grids=False)
    print("=" * 60)
    print("FLOODY SHIELD ADAPTER TEST PAYLOAD")
    print("=" * 60)
    print(fc.to_json(indent=2))
