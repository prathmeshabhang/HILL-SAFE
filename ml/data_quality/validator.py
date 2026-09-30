"""
ml/data_quality/validator.py
===========================
Core validator engine performing multi-check quality audits across input records.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType
from ml.data_quality.rules import check_sensor_range, check_spatial_bounds
from ml.data_quality.rules import check_sensor_range, check_spatial_bounds
from ml.data_quality.schema import (
    DataLatencyRecord,
    DataQualityReport,
    FlagSeverity,
    FreshnessStatus,
    QualityFlag,
    QualityStatus,
)


class DataQualityValidator:
    """
    Validates streaming or tabular features against physical bounds,
    temporal continuity, stuck sensor patterns, spatial constraints, and real-time freshness.
    """

    def __init__(self, stuck_sensor_window: int = 4, freshness_threshold_seconds: float = 3600.0):
        self.stuck_sensor_window = stuck_sensor_window
        self.freshness_threshold_seconds = freshness_threshold_seconds

    def validate_record(
        self,
        sample_id: str,
        features: Dict[str, Any],
        provenance: Optional[DatasetProvenance] = None,
        recent_history: Optional[Sequence[Dict[str, Any]]] = None,
        observation_time_iso: Optional[str] = None,
        reference_now_iso: Optional[str] = None,
    ) -> DataQualityReport:
        flags: List[QualityFlag] = []
        checks_performed = 0
        checks_passed = 0
        latency_record: Optional[DataLatencyRecord] = None

        # 0. Check Freshness & Latency if timestamp is provided
        if observation_time_iso:
            checks_performed += 1
            try:
                t_obs = datetime.datetime.fromisoformat(observation_time_iso)
                t_now = datetime.datetime.fromisoformat(reference_now_iso) if reference_now_iso else datetime.datetime.now(datetime.timezone.utc)
                if t_obs.tzinfo is None and t_now.tzinfo is not None:
                    t_obs = t_obs.replace(tzinfo=datetime.timezone.utc)
                elif t_obs.tzinfo is not None and t_now.tzinfo is None:
                    t_now = t_now.replace(tzinfo=datetime.timezone.utc)

                age_sec = max(0.0, (t_now - t_obs).total_seconds())
                latency_sec = age_sec  # In real-time streaming, latency approximates age

                if age_sec <= self.freshness_threshold_seconds:
                    freshness = FreshnessStatus.FRESH
                    checks_passed += 1
                elif age_sec <= (self.freshness_threshold_seconds * 3.0):
                    freshness = FreshnessStatus.STALE
                    flags.append(QualityFlag(
                        code="STALE_DATA",
                        severity=FlagSeverity.WARNING,
                        message=f"Observation age {age_sec:.1f}s exceeds freshness threshold {self.freshness_threshold_seconds:.1f}s",
                        field_name="observation_time",
                        observed_value=observation_time_iso,
                    ))
                else:
                    freshness = FreshnessStatus.EXPIRED
                    flags.append(QualityFlag(
                        code="EXPIRED_DATA",
                        severity=FlagSeverity.CRITICAL,
                        message=f"Observation age {age_sec:.1f}s critically exceeds threshold (expired)",
                        field_name="observation_time",
                        observed_value=observation_time_iso,
                    ))

                latency_record = DataLatencyRecord(
                    observation_time=observation_time_iso,
                    ingestion_time=t_now.isoformat(),
                    latency_seconds=latency_sec,
                    age_seconds=age_sec,
                    freshness_status=freshness,
                )
            except Exception as e:
                flags.append(QualityFlag(
                    code="TIMESTAMP_PARSING_ERROR",
                    severity=FlagSeverity.WARNING,
                    message=f"Failed to parse timestamp {observation_time_iso}: {e}",
                    field_name="observation_time",
                    observed_value=observation_time_iso,
                ))

        # 1. Check Spatial Bounds if coordinates are provided
        if "latitude" in features and "longitude" in features:
            checks_performed += 1
            lat = features.get("latitude")
            lon = features.get("longitude")
            elev = features.get("elevation_m")
            if lat is not None and lon is not None:
                is_valid, msg = check_spatial_bounds(float(lat), float(lon), float(elev) if elev is not None else None)
                if is_valid:
                    checks_passed += 1
                else:
                    flags.append(QualityFlag(
                        code="SPATIAL_OUT_OF_BOUNDS",
                        severity=FlagSeverity.WARNING,
                        message=str(msg),
                        field_name="coordinates",
                        observed_value=(lat, lon),
                    ))

        # 2. Check Missingness and Physical Ranges for sensor fields
        for field_name, val in features.items():
            checks_performed += 1
            if val is None or (isinstance(val, float) and np.isnan(val)):
                flags.append(QualityFlag(
                    code="MISSING_VALUE",
                    severity=FlagSeverity.WARNING,
                    message=f"Field {field_name} is null or NaN",
                    field_name=field_name,
                    observed_value=val,
                ))
                continue

            if isinstance(val, (int, float)):
                is_valid, msg = check_sensor_range(field_name, float(val))
                if is_valid:
                    checks_passed += 1
                else:
                    flags.append(QualityFlag(
                        code="RANGE_VIOLATION",
                        severity=FlagSeverity.CRITICAL,
                        message=str(msg),
                        field_name=field_name,
                        observed_value=val,
                    ))
            else:
                checks_passed += 1

        # 3. Check for Stuck Sensor if history is provided
        if recent_history and len(recent_history) >= self.stuck_sensor_window:
            for field_name, val in features.items():
                if isinstance(val, (int, float)) and val > 0.0:
                    checks_performed += 1
                    past_vals = [h.get(field_name) for h in recent_history[-self.stuck_sensor_window:] if h.get(field_name) is not None]
                    if len(past_vals) == self.stuck_sensor_window and all(abs(p - val) < 1e-6 for p in past_vals):
                        flags.append(QualityFlag(
                            code="STUCK_SENSOR",
                            severity=FlagSeverity.WARNING,
                            message=f"Sensor {field_name} produced identical non-zero reading {val} across {self.stuck_sensor_window} consecutive cycles",
                            field_name=field_name,
                            observed_value=val,
                        ))
                    else:
                        checks_passed += 1

        # Calculate Score & Status
        if checks_performed > 0:
            score = checks_passed / checks_performed
        else:
            score = 1.0

        # Determine status
        has_critical = any(f.severity == FlagSeverity.CRITICAL for f in flags)
        if has_critical:
            score = min(score, 0.35)
            status = QualityStatus.CRITICAL_ERROR
        elif score < 0.75:
            status = QualityStatus.DEGRADED
        elif len(flags) > 0 and any(f.code == "MISSING_VALUE" for f in flags):
            status = QualityStatus.DEGRADED
        else:
            status = QualityStatus.VALID

        source = provenance.source_agency if provenance else "UNSPECIFIED"

        return DataQualityReport(
            sample_id=sample_id,
            quality_score=score,
            status=status,
            checks_performed=checks_performed,
            checks_passed=checks_passed,
            flags=flags,
            provenance_source=source,
            latency=latency_record,
            metadata={"provenance_type": provenance.provenance_type.value if provenance else "UNKNOWN"},
        )
