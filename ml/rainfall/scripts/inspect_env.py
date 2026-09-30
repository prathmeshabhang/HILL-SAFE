"""
inspect_env.py — FLOODY SHIELD Environment Inspector
======================================================
Run this FIRST to verify your environment before running any other script.

Usage:
    & .venv\\Scripts\\python.exe ml\\rainfall\\scripts\\inspect_env.py

This script:
  - Reports Python version
  - Reports all installed package versions
  - Inspects earthaccess API signatures
  - Checks that the output directory exists
  - Verifies .netrc credentials file presence (WITHOUT revealing passwords)
  - Lists any already-downloaded GPM files
"""

from __future__ import annotations

import importlib.metadata
import inspect
import os
import sys
from pathlib import Path


def header(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def section(title: str) -> None:
    print()
    print(f"--- {title} ---")


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------
header("FLOODY SHIELD — Environment Inspector")
print(f"Python executable : {sys.executable}")
print(f"Python version    : {sys.version}")


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------
section("Installed package versions")
packages = [
    "earthaccess",
    "pysteps",
    "numpy",
    "h5py",
    "xarray",
    "netCDF4",
    "pandas",
    "scipy",
    "matplotlib",
]
for pkg in packages:
    try:
        v = importlib.metadata.version(pkg)
        print(f"  {pkg:<15} {v}")
    except importlib.metadata.PackageNotFoundError:
        print(f"  {pkg:<15} NOT INSTALLED")


# ---------------------------------------------------------------------------
# earthaccess API inspection
# ---------------------------------------------------------------------------
section("earthaccess API signatures")
try:
    import earthaccess
    from earthaccess.search import DataGranules

    print(f"\n  earthaccess.__version__ = {earthaccess.__version__}")
    print(f"\n  earthaccess.search_data signature:")
    print(f"    {inspect.signature(earthaccess.search_data)}")
    print(f"\n  DataGranules.bounding_box signature:")
    print(f"    {inspect.signature(DataGranules.bounding_box)}")
    print(f"\n  DataGranules.parameters signature:")
    print(f"    {inspect.signature(DataGranules.parameters)}")

    # Show the dispatch logic comment
    print()
    print("  HOW bounding_box IS DISPATCHED:")
    print("    search_data(bounding_box=(W, S, E, N))")
    print("    => DataGranules.parameters(bounding_box=(W, S, E, N))")
    print("    => if isinstance(val, tuple): methods['bounding_box'](*val)")
    print("    => bounding_box(W, S, E, N)  OK  (tuple unpacked correctly)")
    print()
    print("  COMMON MISTAKE:")
    print("    STUDY_AREA = [W, S, E, N]  <-- list, NOT tuple")
    print("    search_data(bounding_box=STUDY_AREA)")
    print("    => methods['bounding_box']([W, S, E, N])  <-- 1 arg, not 4!")
    print("    => TypeError: missing 3 required positional arguments  FAIL")

except ImportError as e:
    print(f"  ERROR: Cannot import earthaccess: {e}")


# ---------------------------------------------------------------------------
# .netrc check
# ---------------------------------------------------------------------------
section(".netrc credential file")
netrc_path = Path.home() / ".netrc"
if netrc_path.exists():
    print(f"  Found: {netrc_path}")
    # Check if NASA Earthdata is mentioned — without printing the password
    try:
        content = netrc_path.read_text(encoding="utf-8")
        if "urs.earthdata.nasa.gov" in content:
            print("  [OK] Contains entry for urs.earthdata.nasa.gov")
        else:
            print("  [MISSING] Does NOT contain an entry for urs.earthdata.nasa.gov")
            print("    Add this to ~/.netrc (replace USERNAME and PASSWORD):")
            print("      machine urs.earthdata.nasa.gov login USERNAME password PASSWORD")
    except Exception as e:
        print(f"  WARNING: Could not read .netrc: {e}")
else:
    print(f"  Not found at: {netrc_path}")
    print()
    print("  To avoid interactive password prompts, create ~/.netrc:")
    print("  On Windows, create:  C:\\Users\\<YourUsername>\\.netrc")
    print("  Contents (replace USERNAME and PASSWORD):")
    print()
    print("    machine urs.earthdata.nasa.gov login USERNAME password PASSWORD")
    print()
    print("  Register at: https://urs.earthdata.nasa.gov/")


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
section("GPM output directory")
gpm_dir = Path("ml/rainfall/data/gpm")
print(f"  Checking: {gpm_dir.resolve()}")
if gpm_dir.exists():
    hdf5_files = list(gpm_dir.glob("*.HDF5")) + list(gpm_dir.glob("*.h5"))
    print(f"  [OK] Directory exists")
    print(f"  HDF5 files found: {len(hdf5_files)}")
    for f in hdf5_files[:10]:
        size_mb = f.stat().st_size / 1_048_576
        print(f"    {f.name}  ({size_mb:.2f} MB)")
    if len(hdf5_files) > 10:
        print(f"    ... and {len(hdf5_files) - 10} more")
else:
    print(f"  [NOT FOUND] Directory does not exist yet (it will be created on first download)")


# ---------------------------------------------------------------------------
# Quick sanity test for bounding_box dispatch
# ---------------------------------------------------------------------------
section("bounding_box dispatch sanity check")
try:
    from earthaccess.search import DataGranules

    # Test that the method accepts a 4-tuple correctly
    q = DataGranules()
    q.bounding_box(76.5, 30.5, 78.5, 32.0)
    print("  [OK] DataGranules.bounding_box(76.5, 30.5, 78.5, 32.0) works")

    # Test that tuple unpacking works as in parameters()
    bbox_tuple = (76.5, 30.5, 78.5, 32.0)
    q2 = DataGranules()
    q2.bounding_box(*bbox_tuple)
    print("  [OK] DataGranules.bounding_box(*(76.5, 30.5, 78.5, 32.0)) works")

    print()
    print("  Both forms work correctly in earthaccess", earthaccess.__version__)
    print("  search_data(bounding_box=(W,S,E,N)) will work correctly.")
except Exception as e:
    print(f"  [FAIL] ERROR: {e}")

print()
print("=" * 60)
print("Environment inspection complete.")
print("=" * 60)
