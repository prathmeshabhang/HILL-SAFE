"""
ml/data_ingestion/deformation/insar_gnss.py
==========================================
Sentinel-1 Multi-Temporal InSAR and Continuous GNSS Slope Deformation Ingestion Pipeline.
Loads real or processed Line-of-Sight (LOS) displacement, calculates velocity (mm/day)
and Saito tertiary creep acceleration proxies for M8 Ground Movement forecasting.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_sensor_range, check_spatial_bounds


@dataclass
class DeformationProfilePoint:
    site_id: str
    timestamp: str              # ISO 8601 UTC
    latitude: float
    longitude: float
    elevation_m: float
    los_displacement_mm: float  # Cumulative Line-of-Sight displacement
    velocity_mm_day: float      # Instantaneous or 12-day velocity
    acceleration_mm_day2: float # Second derivative (Saito acceleration proxy)
    coherence: float            # InSAR coherence [0.0, 1.0]
    monitoring_type: str        # INSAR_SENTINEL1 | GNSS_CONTINUOUS | EXTENSOMETER
    quality_flag: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InSARDeformationLoader:
    """
    Ingests and audits multi-temporal slope deformation profiles across Upper Beas monitored slopes.
    Computes velocity and acceleration while filtering out decorrelated noise.
    """

    def __init__(self, min_coherence: float = 0.35):
        self.min_coherence = min_coherence
        self.provenance = DatasetProvenance(
            dataset_id="deformation_insar_gnss",
            provenance_type=ProvenanceType.DERIVED,
            source_agency="ESA Copernicus Sentinel-1 / COMET LiCSAR / ISRO",
            geographic_aoi="Upper Beas Basin Creeping Slopes",
            temporal_coverage="2018-2023 Multi-Temporal InSAR Stack",
            spatial_resolution="15-30 m Point PS/DS Targets",
            license_type="CC-BY 4.0 Open Scientific Data",
            doi_or_url="https://comet.nerc.ac.uk/COMET-LiCS-portal/",
            is_field_verified=False,
            citation="Sentinel-1 InSAR Multi-Temporal Coherent Scatterer Time Series",
        )

    def parse_time_series(
        self,
        site_id: str,
        lat: float,
        lon: float,
        elevation_m: float,
        raw_samples: List[Dict[str, Any]],
        monitoring_type: str = "INSAR_SENTINEL1",
    ) -> Dict[str, Any]:
        """
        Parses an entire time series for a single monitoring site, computing velocity
        and acceleration using forward/central differences.
        """
        is_spatial_ok, spatial_err = check_spatial_bounds(lat, lon, elevation_m)
        if not is_spatial_ok:
            return {"site_id": site_id, "error": spatial_err, "points": []}

        # Sort samples chronologically
        sorted_samples = sorted(raw_samples, key=lambda x: str(x.get("timestamp", "")))
        points: List[DeformationProfilePoint] = []

        prev_disp: Optional[float] = None
        prev_time: Optional[datetime.datetime] = None
        prev_vel: Optional[float] = None

        for item in sorted_samples:
            ts_str = item.get("timestamp")
            disp_mm = float(item.get("los_displacement_mm", 0.0))
            coh = float(item.get("coherence", 1.0))

            if not ts_str:
                continue

            curr_time = datetime.datetime.fromisoformat(ts_str)

            # Check coherence threshold for InSAR
            if monitoring_type == "INSAR_SENTINEL1" and coh < self.min_coherence:
                continue

            vel_mm_day = 0.0
            acc_mm_day2 = 0.0

            if prev_time is not None and prev_disp is not None:
                dt_days = max(0.01, (curr_time - prev_time).total_seconds() / 86400.0)
                vel_mm_day = (disp_mm - prev_disp) / dt_days

                if prev_vel is not None:
                    acc_mm_day2 = (vel_mm_day - prev_vel) / dt_days

            # Physical sensor range checks
            is_range_ok, range_err = check_sensor_range("displacement_mm", disp_mm)
            quality_flag = "VALID" if is_range_ok else "RANGE_VIOLATION"

            point = DeformationProfilePoint(
                site_id=site_id,
                timestamp=ts_str,
                latitude=lat,
                longitude=lon,
                elevation_m=elevation_m,
                los_displacement_mm=round(disp_mm, 2),
                velocity_mm_day=round(vel_mm_day, 3),
                acceleration_mm_day2=round(acc_mm_day2, 4),
                coherence=round(coh, 3),
                monitoring_type=monitoring_type,
                quality_flag=quality_flag,
            )
            points.append(point)

            prev_disp = disp_mm
            prev_time = curr_time
            prev_vel = vel_mm_day

        return {
            "site_id": site_id,
            "total_samples": len(raw_samples),
            "valid_coherent_points": len(points),
            "points": [p.to_dict() for p in points],
        }
