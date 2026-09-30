"""
event_split.py — Event & Temporal Holdout Partitioning
======================================================
Implements event-based and temporal train/test partitioning.

If a dataset lacks discrete storm event identifiers or time-series timestamps,
this module explicitly flags:
  "VALIDATION NOT POSSIBLE WITH CURRENT DATA"
rather than generating synthetic or ungrounded claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import pandas as pd


@dataclass
class EventSplitResult:
    is_available: bool
    status_message: str
    train_indices: Optional[List[int]] = None
    test_indices: Optional[List[int]] = None
    held_out_events: Optional[List[str]] = None
    split_strategy: str = "EVENT_OR_TEMPORAL_HOLDOUT"


def create_event_holdout(
    df: pd.DataFrame,
    event_col: str = "event_id",
    test_fraction: float = 0.20,
) -> EventSplitResult:
    """Attempts to partition dataset by discrete historical disaster events."""
    if event_col not in df.columns:
        return EventSplitResult(
            is_available=False,
            status_message="VALIDATION NOT POSSIBLE WITH CURRENT DATA: No discrete historical event column found.",
            split_strategy="EVENT_HOLDOUT",
        )

    unique_events = df[event_col].unique()
    n_test = max(1, int(len(unique_events) * test_fraction))
    test_events = list(unique_events[-n_test:])
    train_events = list(unique_events[:-n_test])

    train_idx = df[df[event_col].isin(train_events)].index.tolist()
    test_idx = df[df[event_col].isin(test_events)].index.tolist()

    return EventSplitResult(
        is_available=True,
        status_message=f"Event holdout created: {len(test_events)} test events, {len(train_events)} train events.",
        train_indices=train_idx,
        test_indices=test_idx,
        held_out_events=[str(e) for e in test_events],
        split_strategy="EVENT_HOLDOUT",
    )


def create_temporal_holdout(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp",
    test_fraction: float = 0.20,
) -> EventSplitResult:
    """Attempts to partition dataset chronologically into earlier train / later test."""
    if timestamp_col not in df.columns:
        return EventSplitResult(
            is_available=False,
            status_message="VALIDATION NOT POSSIBLE WITH CURRENT DATA: No time-series timestamp column found.",
            split_strategy="TEMPORAL_HOLDOUT",
        )

    sorted_df = df.sort_values(timestamp_col)
    split_point = int(len(sorted_df) * (1.0 - test_fraction))

    train_idx = sorted_df.index[:split_point].tolist()
    test_idx = sorted_df.index[split_point:].tolist()

    return EventSplitResult(
        is_available=True,
        status_message=f"Temporal chronological split: {len(train_idx)} train, {len(test_idx)} test.",
        train_indices=train_idx,
        test_indices=test_idx,
        split_strategy="TEMPORAL_HOLDOUT",
    )
