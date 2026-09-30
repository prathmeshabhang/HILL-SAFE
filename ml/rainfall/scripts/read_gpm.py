"""
read_gpm.py — FLOODY SHIELD Phase 2
====================================
Inspects and reads NASA GPM IMERG Early Run (HDF5) files.

SCIENTIFIC & DATA SPECIFICATIONS
--------------------------------
1. Variable:
   - In IMERG v07, the primary precipitation variable is `Grid/precipitation`
     (formerly `precipitationCal` in v06).
   - Rate vs. Accumulation: The units are `mm/hr` (instantaneous rainfall RATE).
     It is NOT accumulated rainfall in millimeters over the 30-minute window.
     Accumulated precipitation over 30 minutes would be: rate * 0.5 hours.
     We do NOT perform silent conversion; the rate is preserved with explicit metadata.
2. Grid Layout & Coordinates:
   - Raw dataset shape in HDF5: `(time=1, lon=3600, lat=1800)`
   - Dimensions:
       time: seconds since 1980-01-06 00:00:00 UTC
       lon:  center of 0.1° cells from -179.95 to 179.95
       lat:  center of 0.1° cells from -89.95 to 89.95
   - GIS / Modeling Standard:
       Standard meteorological & GIS convention requires grids as (lat, lon) i.e. (y, x)
       with latitude usually descending (North to South) or ascending with affine transform.
       We transpose to `(lat, lon)` and provide explicit spatial coordinate metadata.
3. Fill / Missing Values:
   - Fill value is -9999.9. Missing or unobserved pixels (< 0) are converted to `np.nan`.
4. Output:
   - Clips to configurable bounding box.
   - Saves processed NetCDF file (`.nc`) preserving complete CF-compliant metadata,
     and optional NumPy array (`.npy`) + JSON metadata.

USAGE
-----
  python ml/rainfall/scripts/read_gpm.py
  python ml/rainfall/scripts/read_gpm.py --file ml/rainfall/data/gpm/myfile.HDF5
  python ml/rainfall/scripts/read_gpm.py --west 76.5 --south 30.5 --east 78.5 --north 32.0
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import h5py
import numpy as np
import xarray as xr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("floody_shield.read_gpm")

# Default study area (Himachal Pradesh / Uttarakhand foothills)
DEFAULT_WEST = 76.5
DEFAULT_SOUTH = 30.5
DEFAULT_EAST = 78.5
DEFAULT_NORTH = 32.0

GPM_EPOCH = datetime(1980, 1, 6, 0, 0, 0, tzinfo=timezone.utc)
FILL_VALUE = -9999.9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect and process GPM IMERG HDF5 precipitation granules.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to specific GPM HDF5 file. If omitted, uses the latest file in GPM directory.",
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
        help="Directory to save processed NetCDF/npy files.",
    )
    parser.add_argument("--west", type=float, default=DEFAULT_WEST, help="West longitude")
    parser.add_argument("--south", type=float, default=DEFAULT_SOUTH, help="South latitude")
    parser.add_argument("--east", type=float, default=DEFAULT_EAST, help="East longitude")
    parser.add_argument("--north", type=float, default=DEFAULT_NORTH, help="North latitude")
    return parser.parse_args()


def discover_dataset_path(h5: h5py.File, candidate_names: list[str]) -> str:
    """Discover variable path dynamically inside HDF5 structure."""
    found: list[str] = []

    def visitor(name: str, obj: Any) -> None:
        if isinstance(obj, h5py.Dataset):
            for candidate in candidate_names:
                if name.endswith(candidate) or name == candidate:
                    found.append(name)

    h5.visititems(visitor)
    if not found:
        raise KeyError(
            f"None of candidate datasets {candidate_names} found in HDF5 file. "
            f"Available datasets: {[n for n, o in h5.items() if isinstance(o, h5py.Dataset)]}"
        )
    # Prefer exact match or shortest match if multiple
    found.sort(key=lambda s: len(s))
    return found[0]


def decode_gpm_time(time_seconds: int) -> datetime:
    """Decode GPM seconds since 1980-01-06 00:00:00 UTC into datetime."""
    return GPM_EPOCH + timedelta(seconds=int(time_seconds))


def read_and_clip_gpm(
    file_path: Path,
    west: float,
    south: float,
    east: float,
    north: float,
) -> Tuple[xr.Dataset, Dict[str, Any]]:
    """
    Open GPM HDF5 file, extract precipitation and quality variables,
    decode metadata, clip to bbox, and return an xarray Dataset and info dict.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    log.info("Opening GPM file: %s", file_path.name)

    with h5py.File(file_path, "r") as h5:
        # 1. Discover precipitation variable (handles v07 'precipitation' and v06 'precipitationCal')
        precip_var_path = discover_dataset_path(h5, ["Grid/precipitation", "precipitationCal", "precipitation"])
        lat_var_path = discover_dataset_path(h5, ["Grid/lat", "lat"])
        lon_var_path = discover_dataset_path(h5, ["Grid/lon", "lon"])
        time_var_path = discover_dataset_path(h5, ["Grid/time", "time"])
        
        # Optional quality index
        try:
            qual_var_path = discover_dataset_path(h5, ["Grid/precipitationQualityIndex", "precipitationQualityIndex"])
        except KeyError:
            qual_var_path = None

        log.info("Discovered dataset paths:")
        log.info("  Precipitation : %s", precip_var_path)
        log.info("  Latitude      : %s", lat_var_path)
        log.info("  Longitude     : %s", lon_var_path)
        log.info("  Time          : %s", time_var_path)
        if qual_var_path:
            log.info("  Quality Index : %s", qual_var_path)

        precip_ds = h5[precip_var_path]
        lat_ds = h5[lat_var_path]
        lon_ds = h5[lon_var_path]
        time_ds = h5[time_var_path]

        # Extract units and raw attributes
        raw_units = precip_ds.attrs.get("units", precip_ds.attrs.get("Units", b"mm/hr"))
        if isinstance(raw_units, bytes):
            raw_units = raw_units.decode("utf-8")

        raw_fill = precip_ds.attrs.get("_FillValue", FILL_VALUE)

        # Coordinate arrays
        lats = lat_ds[:].astype(np.float32)
        lons = lon_ds[:].astype(np.float32)
        time_raw = int(time_ds[0])
        obs_time = decode_gpm_time(time_raw)

        log.info("Observation time (UTC): %s", obs_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        log.info("Native Units: %s (Precipitation RATE)", raw_units)

        # Spatial clipping indices
        lon_mask = (lons >= west) & (lons <= east)
        lat_mask = (lats >= south) & (lats <= north)

        lon_indices = np.where(lon_mask)[0]
        lat_indices = np.where(lat_mask)[0]

        if len(lon_indices) == 0 or len(lat_indices) == 0:
            raise ValueError(
                f"Bounding box [{west}, {south}, {east}, {north}] does not intersect "
                f"grid coordinates (lon: {lons.min()}..{lons.max()}, lat: {lats.min()}..{lats.max()})"
            )

        lon_start, lon_end = lon_indices[0], lon_indices[-1] + 1
        lat_start, lat_end = lat_indices[0], lat_indices[-1] + 1

        sub_lons = lons[lon_start:lon_end]
        sub_lats = lats[lat_start:lat_end]

        # Slice raw precipitation: shape in file is (time=1, lon, lat)
        raw_precip_slice = precip_ds[0, lon_start:lon_end, lat_start:lat_end].astype(np.float32)

        # Transpose from (lon, lat) to (lat, lon) -> (y, x) for standard GIS & pySTEPS
        # file dim 0: lon, dim 1: lat -> transpose(1, 0) gives (lat, lon)
        precip_grid = np.transpose(raw_precip_slice)

        # Replace fill / invalid values with NaN
        precip_grid[precip_grid < 0.0] = np.nan

        # Read quality index if present
        if qual_var_path:
            qual_ds = h5[qual_var_path]
            raw_qual_slice = qual_ds[0, lon_start:lon_end, lat_start:lat_end].astype(np.float32)
            qual_grid = np.transpose(raw_qual_slice)
            qual_grid[qual_grid < 0.0] = np.nan
        else:
            qual_grid = np.full_like(precip_grid, np.nan)

    # Calculate statistics on clipped domain
    total_pixels = precip_grid.size
    nan_count = int(np.isnan(precip_grid).sum())
    valid_count = total_pixels - nan_count
    valid_data = precip_grid[~np.isnan(precip_grid)]

    min_val = float(np.min(valid_data)) if valid_count > 0 else float("nan")
    max_val = float(np.max(valid_data)) if valid_count > 0 else float("nan")
    mean_val = float(np.mean(valid_data)) if valid_count > 0 else float("nan")

    metadata = {
        "source_file": file_path.name,
        "observation_time_utc": obs_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "product": "GPM_3IMERGHHE_V07",
        "units": raw_units,
        "variable_type": "instantaneous_precipitation_rate",
        "variable_description": "Rainfall rate in mm/hr (NOT accumulated mm)",
        "bounding_box": {
            "west": float(west),
            "south": float(south),
            "east": float(east),
            "north": float(north),
        },
        "grid_shape": list(precip_grid.shape),  # [n_lat, n_lon] = [y, x]
        "resolution_deg": 0.1,
        "valid_pixels": valid_count,
        "nan_pixels": nan_count,
        "total_pixels": total_pixels,
        "min_rate_mm_per_hr": min_val,
        "max_rate_mm_per_hr": max_val,
        "mean_rate_mm_per_hr": mean_val,
    }

    # Build CF-compliant xarray Dataset
    time_coord = [np.datetime64(obs_time.strftime("%Y-%m-%dT%H:%M:%S"))]
    ds = xr.Dataset(
        data_vars={
            "precipitation": (
                ("time", "lat", "lon"),
                np.expand_dims(precip_grid, axis=0),
                {
                    "units": raw_units,
                    "long_name": "Instantaneous precipitation rate",
                    "standard_name": "precipitation_flux",
                    "description": "GPM IMERG Early Run precipitation rate in mm/hr",
                    "_FillValue": np.nan,
                },
            ),
            "quality_index": (
                ("time", "lat", "lon"),
                np.expand_dims(qual_grid, axis=0),
                {
                    "units": "unitless",
                    "long_name": "Precipitation quality index",
                    "description": "Microwave-infrared quality index",
                    "_FillValue": np.nan,
                },
            ),
        },
        coords={
            "time": time_coord,
            "lat": (
                "lat",
                sub_lats,
                {
                    "units": "degrees_north",
                    "long_name": "latitude",
                    "standard_name": "latitude",
                    "axis": "Y",
                },
            ),
            "lon": (
                "lon",
                sub_lons,
                {
                    "units": "degrees_east",
                    "long_name": "longitude",
                    "standard_name": "longitude",
                    "axis": "X",
                },
            ),
        },
        attrs={
            "title": "FLOODY SHIELD — Processed GPM IMERG Rainfall Grid",
            "source": "NASA GPM IMERG Early Run (v07)",
            "observation_time": obs_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "study_area_bbox": f"W={west}, S={south}, E={east}, N={north}",
            "spatial_resolution": "0.1 degree",
            "temporal_resolution": "30 minutes",
            "scientific_status": "PROTOTYPE_FALLBACK_SOURCE",
            "limitations": (
                "Satellite-based estimate with ~4h latency and 0.1 deg spatial resolution. "
                "Values are precipitation rate (mm/hr), not accumulated mm. "
                "Coarse resolution may not resolve localized hilly terrain flash-flood events."
            ),
        },
    )

    return ds, metadata


def main() -> None:
    args = parse_args()
    gpm_dir = Path(args.gpm_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolve file path
    if args.file:
        file_path = Path(args.file)
    else:
        candidates = sorted(list(gpm_dir.glob("*.HDF5")) + list(gpm_dir.glob("*.h5")))
        if not candidates:
            log.error("No GPM HDF5 files found in %s", gpm_dir.resolve())
            sys.exit(1)
        file_path = candidates[-1]  # Most recent file

    log.info("Processing: %s", file_path)

    # 2. Extract, clip, and build dataset
    try:
        ds, meta = read_and_clip_gpm(
            file_path=file_path,
            west=args.west,
            south=args.south,
            east=args.east,
            north=args.north,
        )
    except Exception as e:
        log.error("Failed to read GPM file: %s", e, exc_info=True)
        sys.exit(1)

    # 3. Print inspection summary
    print()
    print("=" * 60)
    print("GPM DATASET INSPECTION REPORT")
    print("=" * 60)
    print(f"Source file       : {meta['source_file']}")
    print(f"Observation time  : {meta['observation_time_utc']}")
    print(f"Variable          : precipitation")
    print(f"Units             : {meta['units']} (RATE, NOT ACCUMULATED mm)")
    print(f"Grid shape (y, x) : {meta['grid_shape']} -> (lat, lon)")
    print(f"Latitudes ({len(ds.lat)}) : {float(ds.lat.min()):.2f} to {float(ds.lat.max()):.2f}")
    print(f"Longitudes ({len(ds.lon)}) : {float(ds.lon.min()):.2f} to {float(ds.lon.max()):.2f}")
    print(f"Valid pixels      : {meta['valid_pixels']} / {meta['total_pixels']} ({meta['valid_pixels']/meta['total_pixels']*100:.1f}%)")
    print(f"Min rainfall rate : {meta['min_rate_mm_per_hr']} mm/hr")
    print(f"Max rainfall rate : {meta['max_rate_mm_per_hr']} mm/hr")
    print(f"Mean rainfall rate: {meta['mean_rate_mm_per_hr']:.3f} mm/hr")
    print("=" * 60)

    # 4. Save processed NetCDF and metadata JSON
    base_stem = file_path.stem
    nc_path = out_dir / f"{base_stem}_clipped.nc"
    json_path = out_dir / f"{base_stem}_meta.json"
    npy_path = out_dir / f"{base_stem}_precip.npy"

    ds.to_netcdf(nc_path)
    log.info("Saved CF-compliant NetCDF: %s", nc_path)

    # Also save 2D numpy array and metadata JSON for lightweight downstream use
    precip_array = ds["precipitation"].values[0]  # shape (lat, lon)
    np.save(npy_path, precip_array)
    log.info("Saved NumPy array: %s", npy_path)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    log.info("Saved metadata: %s", json_path)

    print()
    print("Verification complete. Outputs saved successfully in:")
    print(f"  {out_dir.resolve()}")


if __name__ == "__main__":
    main()