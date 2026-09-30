"""
temporal_leakage.py — Training vs External Independence Auditor
================================================================
Performs spatial and temporal overlap analysis between M6 training points
and the external landslide inventory to prevent data leakage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from ml.validation.external.projection import metric_distance_m


@dataclass
class IndependenceAuditRecord:
    """Detailed record of training vs external dataset independence."""
    training_dataset_identity: str
    external_dataset_identity: str
    overlap_check_method: str
    spatial_overlap_tolerance_m: float
    overlapping_events_count: int
    retained_independent_events_count: int
    overlap_result: str
    independence_status: str
    details: Dict[str, Any]


class IndependenceAuditor:
    def __init__(
        self,
        training_csv_path: Optional[Path | str] = None,
        spatial_overlap_tolerance_m: float = 35.0,  # Within 1 DEM pixel (~30m)
    ):
        self.training_csv_path = Path(
            training_csv_path
            or Path(__file__).resolve().parents[3] / "data" / "processed" / "upper_beas" / "upper_beas_landslide_dataset.csv"
        )
        self.spatial_overlap_tolerance_m = spatial_overlap_tolerance_m
        self._training_coords: Optional[np.ndarray] = None

    def _load_training_coords(self) -> np.ndarray:
        if self._training_coords is None:
            if not self.training_csv_path.exists():
                return np.empty((0, 2))
            df = pd.read_csv(self.training_csv_path, usecols=["lat", "lon"])
            self._training_coords = df[["lat", "lon"]].dropna().to_numpy()
        return self._training_coords

    def audit_independence(
        self,
        external_events: List[Any],  # ObservedLandslideEvent
        external_dataset_name: str,
    ) -> Tuple[List[Any], IndependenceAuditRecord]:
        """
        Audits external events against M6 training locations.
        Filters out any external event that is within spatial_overlap_tolerance_m of a training sample.
        Generates a transparent independence provenance record.
        """
        tr_coords = self._load_training_coords()
        has_training_data = len(tr_coords) > 0

        clean_events = []
        overlapping_events = []

        if not has_training_data:
            overlap_result = "TRAINING_COORDINATES_UNAVAILABLE"
            status = "TRAINING-EXTERNAL INDEPENDENCE: NOT VERIFIABLE"
            clean_events = list(external_events)
        else:
            # Check proximity to training points
            # To be efficient, use bounding box filtering per external event
            deg_tol = self.spatial_overlap_tolerance_m / 111000.0  # Approx degree window

            for ev in external_events:
                lat, lon = ev.latitude, ev.longitude
                # Fast bbox prefilter
                mask = (
                    (tr_coords[:, 0] >= lat - deg_tol) &
                    (tr_coords[:, 0] <= lat + deg_tol) &
                    (tr_coords[:, 1] >= lon - deg_tol) &
                    (tr_coords[:, 1] <= lon + deg_tol)
                )
                cand_tr = tr_coords[mask]

                is_dup = False
                for tr_lat, tr_lon in cand_tr:
                    dist = metric_distance_m(lat, lon, tr_lat, tr_lon)
                    if dist <= self.spatial_overlap_tolerance_m:
                        is_dup = True
                        break

                if is_dup:
                    overlapping_events.append(ev)
                else:
                    clean_events.append(ev)

            if len(overlapping_events) == 0:
                overlap_result = "NO_SPATIAL_CO_LOCATION_DETECTED"
                status = "TRAINING-EXTERNAL INDEPENDENCE: SPATIALLY DISJOINT (TEMPORALLY UNVERIFIABLE)"
            else:
                overlap_result = f"EXCLUDED_{len(overlapping_events)}_CO_LOCATED_EVENTS"
                status = "TRAINING-EXTERNAL INDEPENDENCE: OVERLAPPING SAMPLES EXCLUDED"

        # Check temporal coverage of training set
        # M6 training dataset has no discrete event timestamp column
        temporal_note = (
            "M6 training dataset upper_beas_landslide_dataset.csv contains catchment terrain "
            "samples without discrete event timestamp columns. While spatial co-location is "
            "strictly verified and filtered, exact historical event date independence cannot be "
            "proven from training metadata alone."
        )

        record = IndependenceAuditRecord(
            training_dataset_identity="upper_beas_landslide_dataset.csv",
            external_dataset_identity=external_dataset_name,
            overlap_check_method="METRIC_PROXIMITY_EXCLUSION (UTM-43N, buffer <= 35m)",
            spatial_overlap_tolerance_m=self.spatial_overlap_tolerance_m,
            overlapping_events_count=len(overlapping_events),
            retained_independent_events_count=len(clean_events),
            overlap_result=overlap_result,
            independence_status=status,
            details={
                "temporal_limitation": temporal_note,
                "total_input_external_events": len(external_events),
                "excluded_co_located_count": len(overlapping_events),
            },
        )

        return clean_events, record
