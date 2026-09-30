"""
build_gpm_sequence.py — FLOODY SHIELD Phase 3
===============================================
Constructs a quality-checked, chronologically sorted, uniformly gridded
time sequence of spatial rainfall frames suitable for pySTEPS rainfall nowcasting.

KEY REQUIREMENTS & SCIENTIFIC PRINCIPLES
----------------------------------------
1. Input Dimension Ordering:
   - pySTEPS expects rainfall arrays with dimensions: (time, y, x) or (time, lat, lon).
2. Temporal Resolution & Regularity:
   - GPM IMERG Early Run files are issued at 30-minute intervals (nominal dt = 30 min).
   - The sequence must detect missing time steps or irregular intervals.
3. Coordinate Consistency:
   - Checks that all grids share identical spatial extents, shapes, and coordinates.
4. Transparent Missing Data Handling:
   - Never replaces large missing regions with zeros without warning.
   - Calculates and records NaN percentage and valid pixel statistics per frame.
5. Minimum History Requirement:
   - Optical flow / advection estimation requires at least 3 consecutive frames (e.g. t-60, t-30, t0).
   - If fewer than the minimum threshold are available, flags sequence as insufficient.

OUTPUT FORMATS
--------------
- Saves (time, y, x) sequence as:
    1. CF-compliant NetCDF (`ml/rainfall/data/processed/gpm_sequence_latest.nc`)
    2. NumPy 3D array (`ml/rainfall/data/processed/gpm_sequence_latest.npy`)
    3. Detailed audit metadata (`ml/rainfall/data/processed/gpm_sequence_meta.json`)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np
import xarray as xr

# Re-use robust extraction helper from Phase 2
from read_gpm import (
    DEFAULT_EAST,
    DEFAULT_NORTH,
    DEFAULT_SOUTH,
    DEFAULT_WEST,
    decode_gpm_time,
    discover_dataset_path,
    read_and_clip_gpm,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("floody_shield.build_gpm_sequence")

# GPM nominal interval is 30 minutes
EXPECTED_TIMESTEP_MINUTES = 30
MINIMUM_REQUIRED_FRAMES = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a chronological (time, y, x) sequence from GPM granules.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--gpm-dir",
        type=str,
        default="ml/rainfall/data/gpm",
        help="Directory containing downloaded GPM HDF5 files.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="ml/rainfall/data/processed",
        help="Output directory for the processed sequence.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=6,
        help="Maximum number of most recent consecutive frames to assemble.",
    )
    parser.add_argument("--west", type=float, default=DEFAULT_WEST, help="West longitude")
    parser.add_argument("--south", type=float, default=DEFAULT_SOUTH, help="South latitude")
    parser.add_argument("--east", type=float, default=DEFAULT_EAST, help="East longitude")
    parser.add_argument("--north", type=float, default=DEFAULT_NORTH, help="North latitude")
    return parser.parse_args()


def inspect_file_timestamp(file_path: Path) -> datetime:
    """Quickly inspect HDF5 timestamp without reading full arrays."""
    with h5py.File(file_path, "r") as h5:
        time_var_path = discover_dataset_path(h5, ["Grid/time", "time"])
        time_raw = int(h5[time_var_path][0])
        return decode_gpm_time(time_raw)


def build_sequence(
    gpm_files: List[Path],
    west: float,
    south: float,
    east: float,
    north: float,
    max_frames: int = 6,
) -> Tuple[xr.Dataset, Dict[str, Any]]:
    """
    Sorts files chronologically, validates time intervals, checks grid consistency,
    and returns an xarray Dataset of shape (time, lat, lon) with full metadata.
    """
    if not gpm_files:
        raise ValueError("No GPM files provided to assemble sequence.")

    # 1. Read timestamp for each file and sort chronologically
    file_time_pairs: List[Tuple[datetime, Path]] = []
    log.info("Indexing timestamps across %d candidate files...", len(gpm_files))
    for f in gpm_files:
        try:
            t = inspect_file_timestamp(f)
            file_time_pairs.append((t, f))
        except Exception as err:
            log.warning("Skipping unreadable or corrupted file %s: %s", f.name, err)

    if not file_time_pairs:
        raise ValueError("No valid GPM files could be indexed for timestamps.")

    # Deduplicate by timestamp and sort ascending
    file_time_pairs.sort(key=lambda item: item[0])
    unique_pairs: List[Tuple[datetime, Path]] = []
    seen_times = set()
    for t, f in file_time_pairs:
        if t in seen_times:
            log.warning("Duplicate timestamp detected at %s: skipping %s", t.isoformat(), f.name)
            continue
        seen_times.add(t)
        unique_pairs.append((t, f))

    # Take the latest N frames up to max_frames
    selected_pairs = unique_pairs[-max_frames:]
    log.info(
        "Selected %d chronological frames (earliest: %s, latest: %s)",
        len(selected_pairs),
        selected_pairs[0][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        selected_pairs[-1][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    if len(selected_pairs) < MINIMUM_REQUIRED_FRAMES:
        log.warning(
            "Selected %d frames is less than recommended minimum (%d) for optical flow / pySTEPS nowcasting.",
            len(selected_pairs),
            MINIMUM_REQUIRED_FRAMES,
        )

    # 2. Check temporal gaps
    gaps: List[Dict[str, Any]] = []
    for i in range(1, len(selected_pairs)):
        dt_minutes = (selected_pairs[i][0] - selected_pairs[i - 1][0]).total_seconds() / 60.0
        if abs(dt_minutes - EXPECTED_TIMESTEP_MINUTES) > 5.0:
            gap_info = {
                "from": selected_pairs[i - 1][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": selected_pairs[i][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "interval_minutes": dt_minutes,
                "expected_minutes": EXPECTED_TIMESTEP_MINUTES,
            }
            gaps.append(gap_info)
            log.warning(
                "Temporal gap/irregularity detected: %.1f min between %s and %s",
                dt_minutes,
                gap_info["from"],
                gap_info["to"],
            )

    # 3. Read and clip each frame
    datasets: List[xr.Dataset] = []
    frames_meta: List[Dict[str, Any]] = []
    ref_coords: Optional[Tuple[np.ndarray, np.ndarray]] = None

    for t, fpath in selected_pairs:
        ds, meta = read_and_clip_gpm(
            file_path=fpath,
            west=west,
            south=south,
            east=east,
            north=north,
        )

        curr_lats = ds["lat"].values
        curr_lons = ds["lon"].values

        if ref_coords is None:
            ref_coords = (curr_lats, curr_lons)
        else:
            # Check coordinate alignment
            if not np.array_equal(ref_coords[0], curr_lats) or not np.array_equal(ref_coords[1], curr_lons):
                raise ValueError(f"Coordinate mismatch detected in file {fpath.name} against sequence reference!")

        datasets.append(ds)
        frames_meta.append(meta)

    # 4. Concatenate along time dimension into a unified (time, lat, lon) dataset
    combined_ds = xr.concat(datasets, dim="time")

    precip_seq = combined_ds["precipitation"].values  # shape: (n_time, n_lat, n_lon)
    total_elements = precip_seq.size
    nan_count = int(np.isnan(precip_seq).sum())
    nan_percent = (nan_count / total_elements) * 100.0 if total_elements > 0 else 0.0

    valid_vals = precip_seq[~np.isnan(precip_seq)]
    max_rate = float(np.max(valid_vals)) if len(valid_vals) > 0 else 0.0
    mean_rate = float(np.mean(valid_vals)) if len(valid_vals) > 0 else 0.0

    # 5. Build sequence metadata
    sequence_meta = {
        "num_frames": len(selected_pairs),
        "shape": list(precip_seq.shape),  # [time, lat/y, lon/x]
        "dimension_order": ["time", "lat", "lon"],
        "start_time_utc": selected_pairs[0][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time_utc": selected_pairs[-1][0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nominal_timestep_minutes": EXPECTED_TIMESTEP_MINUTES,
        "temporal_gaps": gaps,
        "is_continuous": len(gaps) == 0,
        "spatial_bounding_box": {
            "west": float(west),
            "south": float(south),
            "east": float(east),
            "north": float(north),
        },
        "spatial_resolution_deg": 0.1,
        "units": "mm/hr",
        "variable_nature": "instantaneous_precipitation_rate",
        "total_pixels_in_sequence": total_elements,
        "nan_pixels": nan_count,
        "nan_percentage": round(nan_percent, 2),
        "max_precipitation_rate_mm_hr": max_rate,
        "mean_precipitation_rate_mm_hr": round(mean_rate, 4),
        "source_product": "GPM_3IMERGHHE_V07",
        "frames": [
            {
                "file": m["source_file"],
                "time_utc": m["observation_time_utc"],
                "valid_pixels": m["valid_pixels"],
                "nan_pixels": m["nan_pixels"],
                "max_rate": m["max_rate_mm_per_hr"],
            }
            for m in frames_meta
        ],
    }

    combined_ds.attrs.update(
        {
            "title": "FLOODY SHIELD — Chronological GPM Rainfall Sequence",
            "time_coverage_start": sequence_meta["start_time_utc"],
            "time_coverage_end": sequence_meta["end_time_utc"],
            "temporal_resolution": f"{EXPECTED_TIMESTEP_MINUTES} minutes",
            "number_of_timesteps": len(selected_pairs),
            "has_temporal_gaps": str(len(gaps) > 0),
        }
    )

    return combined_ds, sequence_meta


def main() -> None:
    args = parse_args()
    gpm_dir = Path(args.gpm_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gpm_files = sorted(list(gpm_dir.glob("*.HDF5")) + list(gpm_dir.glob("*.h5")))
    if not gpm_files:
        log.error("No GPM HDF5 files found in %s", gpm_dir.resolve())
        sys.exit(1)

    log.info("Found %d GPM file(s) in %s", len(gpm_files), gpm_dir)

    try:
        ds_seq, meta = build_sequence(
            gpm_files=gpm_files,
            west=args.west,
            south=args.south,
            east=args.east,
            north=args.north,
            max_frames=args.max_frames,
        )
    except Exception as e:
        log.error("Failed to assemble sequence: %s", e, exc_info=True)
        sys.exit(1)

    # Summary report
    print()
    print("=" * 60)
    print("GPM TIME SEQUENCE AUDIT REPORT")
    print("=" * 60)
    print(f"Number of frames  : {meta['num_frames']}")
    print(f"Sequence shape    : {meta['shape']} -> (time, lat/y, lon/x)")
    print(f"Coverage start    : {meta['start_time_utc']}")
    print(f"Coverage end      : {meta['end_time_utc']}")
    print(f"Temporal interval : {meta['nominal_timestep_minutes']} min (Continuous: {meta['is_continuous']})")
    if meta["temporal_gaps"]:
        print(f"WARNING: Found {len(meta['temporal_gaps'])} gap(s):")
        for g in meta["temporal_gaps"]:
            print(f"  - {g['from']} to {g['to']} ({g['interval_minutes']} min)")
    print(f"Total grid points : {meta['total_pixels_in_sequence']}")
    print(f"NaN percentage    : {meta['nan_percentage']}%")
    print(f"Max observed rate : {meta['max_precipitation_rate_mm_hr']} mm/hr")
    print(f"Mean observed rate: {meta['mean_precipitation_rate_mm_hr']} mm/hr")
    print("=" * 60)

    # Save outputs
    nc_out = out_dir / "gpm_sequence_latest.nc"
    npy_out = out_dir / "gpm_sequence_latest.npy"
    meta_out = out_dir / "gpm_sequence_meta.json"

    ds_seq.to_netcdf(nc_out)
    log.info("Saved NetCDF sequence: %s", nc_out)

    np.save(npy_out, ds_seq["precipitation"].values)
    log.info("Saved NumPy (time, y, x) array: %s", npy_out)

    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    log.info("Saved Sequence metadata: %s", meta_out)

    print()
    print("Phase 3 complete. Sequence prepared and ready for pySTEPS input.")


if __name__ == "__main__":
    main()
