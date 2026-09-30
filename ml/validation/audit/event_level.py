"""
event_level.py — Event-Level vs. Point-Level Independence Audit Layer
====================================================================
Prevents conflating clustered spatial points from a single storm
with independent event-level validation. Enforces mathematical invariants.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.validation.audit.schema import (
    EventIndependenceAudit,
    MetricResult,
    MetricStatus,
    ValidationUnit,
)


def audit_event_structure(
    df: pd.DataFrame,
    event_id_col: str = "rainfall_event_id",
    date_col: Optional[str] = "event_date",
    forcing_col: Optional[str] = "hazard_type",
) -> EventIndependenceAudit:
    """
    Analyzes whether evaluation samples represent distinct independent disaster events
    or spatial points clustered under a common meteorological storm event.
    """
    total_points = len(df)
    if total_points == 0:
        return EventIndependenceAudit(
            total_points=0,
            total_events=0,
            is_clustered_forcing=False,
            forcing_description="Empty dataset",
            primary_unit=ValidationUnit.POINT,
            event_ids=[],
        )

    if event_id_col in df.columns:
        event_ids = df[event_id_col].astype(str).unique().tolist()
        total_events = len(event_ids)
    elif date_col in df.columns and df[date_col].notna().any():
        event_ids = df[date_col].astype(str).unique().tolist()
        total_events = len(event_ids)
    else:
        event_ids = ["UNSPECIFIED_SINGLE_EPOCH"]
        total_events = 1

    # Invariant check
    if total_events > total_points:
        raise AssertionError(
            f"Event count invariant broken: total_events ({total_events}) cannot exceed total_points ({total_points})"
        )

    is_clustered = total_events < total_points
    primary_unit = ValidationUnit.EVENT if total_events == total_points else ValidationUnit.SPATIAL_SAMPLE

    forcing_desc = (
        f"Clustered spatial forcing: {total_points} spatial points observed across {total_events} distinct event(s)."
        if is_clustered
        else f"Event-level distribution: {total_points} independent observations matched 1:1 to unique events."
    )

    return EventIndependenceAudit(
        total_points=total_points,
        total_events=total_events,
        is_clustered_forcing=is_clustered,
        forcing_description=forcing_desc,
        primary_unit=primary_unit,
        event_ids=event_ids,
    )


def check_event_level_auc_eligibility(
    event_audit: EventIndependenceAudit,
) -> Optional[MetricResult]:
    """
    Enforces the rule that event-level ROC-AUC requires >= 2 independent events.
    If only 1 event exists (e.g. July 9-10 storm), marks event-level discrimination as NOT ESTIMABLE.
    """
    if event_audit.total_events < 2:
        return MetricResult(
            metric_name="event_level_roc_auc",
            value=None,
            status=MetricStatus.NOT_ESTIMABLE,
            reason=(
                f"not_estimable_due_to_single_event: evaluation dataset covers only {event_audit.total_events} event(s) "
                f"({event_audit.total_points} spatial points). Point-level spatial discrimination cannot be reported "
                f"as independent event-level validation."
            ),
            n=event_audit.total_events,
            unit=ValidationUnit.EVENT,
            is_threshold_dependent=False,
        )

    return None
