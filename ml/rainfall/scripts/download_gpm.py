"""
download_gpm.py — FLOODY SHIELD Phase 1
========================================
Downloads NASA GPM IMERG Early Run half-hourly granules for a configurable
Indian study area using the earthaccess library (v0.17.0+).

SCIENTIFIC NOTES
----------------
- GPM IMERG Early Run (GPM_3IMERGHHE, v07) has ~4-hour latency.
- It is NOT instantaneous — it is a near-real-time satellite estimate.
- Spatial resolution: 0.1° × 0.1° (~11 km at equator).
- Temporal resolution: 30 minutes (half-hourly files).
- Values represent precipitation rate in mm/hr, NOT accumulated mm.
- This is suitable for prototype development and fallback operation.
- For operational flash-flood warning, higher-resolution IMD radar,
  INSAT/MOSDAC, or local rain-gauge data may be required.

PRODUCT IDENTIFIERS (as of earthaccess v0.17.0)
------------------------------------------------
  GPM_3IMERGHHE  — Early Run, half-hourly  (use this for nowcasting)
  GPM_3IMERGHL   — Late Run, half-hourly
  GPM_3IMERGDF   — Final Run, daily
  GPM_3IMERGDE   — Daily Early Run (not suitable for half-hourly nowcasting)

AUTHENTICATION
--------------
Credentials are read from:
  1. ~/.netrc  (recommended — set up once, never touched again)
  2. Interactive prompt  (fallback if .netrc is absent)
Credentials are NEVER stored in source code, .env, or any version-controlled file.

USAGE
-----
  # Basic — downloads last 3 hours for the default study area:
  python ml/rainfall/scripts/download_gpm.py

  # Custom area and time window:
  python ml/rainfall/scripts/download_gpm.py ^
      --west 73.0 --south 18.0 --east 74.5 --north 20.0 ^
      --hours 6 ^
      --out ml/rainfall/data/gpm

  # Fixed date range (useful for historical download):
  python ml/rainfall/scripts/download_gpm.py ^
      --start 2024-07-15T00:00:00Z ^
      --end   2024-07-15T06:00:00Z
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Dependency check — give a clear message if earthaccess is missing
# ---------------------------------------------------------------------------
try:
    import earthaccess
except ImportError:
    print(
        "ERROR: earthaccess is not installed.\n"
        "Activate your virtual environment and run:\n"
        "  pip install earthaccess\n",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("floody_shield.download_gpm")

# ---------------------------------------------------------------------------
# Defaults — override via command-line arguments
# ---------------------------------------------------------------------------

# Default study area: Himachal Pradesh / Uttarakhand foothills (prototype)
# Format: west, south, east, north  (decimal degrees, WGS84)
# IMPORTANT: This is a placeholder region used for prototype development only.
#            Replace with your actual watershed bounding box.
DEFAULT_WEST: float = 76.5
DEFAULT_SOUTH: float = 30.5
DEFAULT_EAST: float = 78.5
DEFAULT_NORTH: float = 32.0

# GPM IMERG Early Run — half-hourly (best for nowcasting, ~4 h latency)
# Verify at: https://cmr.earthdata.nasa.gov/search/granules?short_name=GPM_3IMERGHHE
PRODUCT_SHORT_NAME: str = "GPM_3IMERGHHE"
PRODUCT_VERSION: str = "07"

# How many recent hours to search when --hours is used
DEFAULT_HOURS_BACK: int = 3

# Minimum expected file size in bytes (a real GPM HDF5 is typically ~5–20 MB)
MIN_FILE_SIZE_BYTES: int = 100_000

# Retry settings for transient network errors
MAX_DOWNLOAD_RETRIES: int = 3
RETRY_DELAY_SECONDS: int = 10

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download GPM IMERG Early Run granules for a study area.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--west", type=float, default=DEFAULT_WEST, help="West longitude boundary")
    parser.add_argument("--south", type=float, default=DEFAULT_SOUTH, help="South latitude boundary")
    parser.add_argument("--east", type=float, default=DEFAULT_EAST, help="East longitude boundary")
    parser.add_argument("--north", type=float, default=DEFAULT_NORTH, help="North latitude boundary")
    parser.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_HOURS_BACK,
        help="Search this many hours back from now (ignored if --start/--end given)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start time in ISO 8601 format, e.g. 2024-07-15T00:00:00Z",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End time in ISO 8601 format, e.g. 2024-07-15T06:00:00Z",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="ml/rainfall/data/gpm",
        help="Output directory for downloaded HDF5 files",
    )
    parser.add_argument(
        "--short-name",
        type=str,
        default=PRODUCT_SHORT_NAME,
        help="NASA CMR short_name for the GPM product",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=PRODUCT_VERSION,
        help="NASA CMR product version string",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search only — do not download files",
    )
    return parser.parse_args()


def validate_bbox(west: float, south: float, east: float, north: float) -> None:
    """Validate bounding box values. Raise ValueError on bad inputs."""
    if not (-180.0 <= west <= 180.0):
        raise ValueError(f"west must be in [-180, 180], got {west}")
    if not (-180.0 <= east <= 180.0):
        raise ValueError(f"east must be in [-180, 180], got {east}")
    if not (-90.0 <= south <= 90.0):
        raise ValueError(f"south must be in [-90, 90], got {south}")
    if not (-90.0 <= north <= 90.0):
        raise ValueError(f"north must be in [-90, 90], got {north}")
    if west >= east:
        raise ValueError(f"west ({west}) must be less than east ({east})")
    if south >= north:
        raise ValueError(f"south ({south}) must be less than north ({north})")
    # Warn if the area is extremely large (likely a mistake)
    width = east - west
    height = north - south
    if width > 30.0 or height > 30.0:
        log.warning(
            "Study area is very large (%s° × %s°). GPM IMERG resolution is 0.1°. "
            "Consider using a smaller area to avoid downloading excessive data.",
            round(width, 2), round(height, 2),
        )


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse an ISO 8601 datetime string, always returning a UTC-aware datetime."""
    # Remove trailing Z and replace with +00:00 for fromisoformat()
    dt_str = dt_str.rstrip("Z")
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def file_already_downloaded(local_path: Path, min_size: int = MIN_FILE_SIZE_BYTES) -> bool:
    """Return True if the file exists and is at least min_size bytes."""
    return local_path.exists() and local_path.stat().st_size >= min_size


def fmt_dt(dt: datetime) -> str:
    """Format datetime as CMR-compatible ISO 8601 string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def authenticate() -> bool:
    """
    Authenticate with NASA Earthdata.

    Tries .netrc first (preferred — no password prompt needed).
    Falls back to interactive login if .netrc credentials are absent.

    Returns True on success, False on failure.
    """
    log.info("Authenticating with NASA Earthdata...")

    # Try .netrc silently first
    try:
        auth = earthaccess.login(strategy="netrc")
        if auth.authenticated:
            log.info("Authenticated via .netrc")
            return True
    except Exception:
        pass  # .netrc not present or credentials invalid — fall through

    # Interactive fallback
    log.info(
        "No valid .netrc credentials found.\n"
        "You will be prompted for your NASA Earthdata username and password.\n"
        "To avoid future prompts, create ~/.netrc with:\n"
        "  machine urs.earthdata.nasa.gov login <USERNAME> password <PASSWORD>\n"
        "and chmod 600 ~/.netrc   (on Linux/macOS) or restrict permissions on Windows."
    )
    try:
        auth = earthaccess.login(strategy="interactive")
        if auth.authenticated:
            log.info("Authenticated interactively")
            return True
    except Exception as e:
        log.error("Authentication failed: %s", e)
        return False

    log.error("All authentication strategies failed.")
    return False


def search_granules(
    short_name: str,
    version: str,
    start_time: datetime,
    end_time: datetime,
    west: float,
    south: float,
    east: float,
    north: float,
) -> list:
    """
    Search NASA CMR for GPM granules within the time range and bounding box.

    bounding_box argument format for earthaccess v0.17.0:
        (lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)
        = (west, south, east, north)

    This is passed as a 4-element TUPLE so that DataGranules.parameters()
    correctly unpacks it as: bounding_box(west, south, east, north).

    If passed as a LIST, parameters() will call bounding_box([...]) with
    ONE argument instead of four — causing the 'missing 3 required positional
    arguments' TypeError that was originally reported.
    """
    log.info("Searching: short_name=%s version=%s", short_name, version)
    log.info("  Time:     %s → %s", fmt_dt(start_time), fmt_dt(end_time))
    log.info("  BBox:     W=%.3f S=%.3f E=%.3f N=%.3f", west, south, east, north)

    # NOTE: bounding_box MUST be a tuple, not a list.
    #       The earthaccess.parameters() dispatcher only unpacks tuples.
    bbox: tuple[float, float, float, float] = (west, south, east, north)

    try:
        results = earthaccess.search_data(
            short_name=short_name,
            version=version,
            temporal=(fmt_dt(start_time), fmt_dt(end_time)),
            bounding_box=bbox,
        )
    except Exception as e:
        log.error("CMR search failed: %s", e)
        raise

    return results


def download_with_retry(
    granules: list,
    output_dir: Path,
    max_retries: int = MAX_DOWNLOAD_RETRIES,
    delay: int = RETRY_DELAY_SECONDS,
) -> list[Path]:
    """
    Download granules with retry on transient failure.

    Skips files that are already present and valid (deduplication).
    Returns list of paths to all successfully downloaded files.
    """
    downloaded: list[Path] = []

    for attempt in range(1, max_retries + 1):
        try:
            log.info("Download attempt %d / %d ...", attempt, max_retries)
            paths = earthaccess.download(granules, local_path=str(output_dir))

            for p in paths:
                file_path = Path(p)
                if not file_path.exists():
                    log.warning("Expected file not found after download: %s", p)
                    continue
                size = file_path.stat().st_size
                if size < MIN_FILE_SIZE_BYTES:
                    log.warning(
                        "File %s is suspiciously small (%d bytes). "
                        "It may be corrupted or incomplete.",
                        file_path.name, size,
                    )
                else:
                    log.info("  OK  %s  (%.2f MB)", file_path.name, size / 1_048_576)
                downloaded.append(file_path)
            return downloaded

        except KeyboardInterrupt:
            log.warning("Download interrupted by user.")
            raise
        except Exception as e:
            log.warning("Download attempt %d failed: %s", attempt, e)
            if attempt < max_retries:
                log.info("Retrying in %d seconds...", delay)
                time.sleep(delay)
            else:
                log.error("All %d download attempts failed.", max_retries)
                raise

    return downloaded


def check_already_downloaded(granules: list, output_dir: Path) -> tuple[list, list]:
    """
    Partition granules into (already_present, to_download).

    A granule is considered present if a file with the same base name
    already exists in output_dir and has a reasonable size.
    """
    present = []
    to_download = []

    for granule in granules:
        # earthaccess DataGranule objects expose data links
        try:
            links = granule.data_links(access="external")
            if not links:
                links = granule.data_links()
        except Exception:
            links = []

        found_locally = False
        for link in links:
            file_name = Path(link).name
            local_path = output_dir / file_name
            if file_already_downloaded(local_path):
                log.info("  SKIP (already downloaded)  %s", file_name)
                present.append(granule)
                found_locally = True
                break

        if not found_locally:
            to_download.append(granule)

    return present, to_download


def print_verification_guide(output_dir: Path) -> None:
    """Print instructions for verifying a downloaded GPM HDF5 file."""
    hdf5_files = list(output_dir.glob("*.HDF5")) + list(output_dir.glob("*.h5"))
    if not hdf5_files:
        return

    example = hdf5_files[0]
    print()
    print("=" * 60)
    print("HOW TO VERIFY THE DOWNLOADED FILE")
    print("=" * 60)
    print(f"  File:  {example}")
    print(f"  Size:  {example.stat().st_size / 1_048_576:.2f} MB")
    print()
    print("Run these PowerShell commands to inspect the file:")
    print()
    print(f'  & ".venv\\Scripts\\python.exe" -c "')
    print("  import h5py, pathlib")
    print(f"  p = pathlib.Path(r'{example}')")
    print("  with h5py.File(p, 'r') as f:")
    print("      f.visititems(lambda n, o: print(n, type(o).__name__))")
    print('  "')
    print()
    print("Or run Phase 2 script:")
    print("  & .venv\\Scripts\\python.exe ml\\rainfall\\scripts\\read_gpm.py")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args()

    # ---- Set up output directory ----
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    log.info("Output directory: %s", output_dir.resolve())

    # ---- Parse and validate time range ----
    if args.start and args.end:
        start_time = parse_iso_datetime(args.start)
        end_time = parse_iso_datetime(args.end)
        log.info("Using user-specified time range")
    else:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=args.hours)
        log.info("Using rolling window: last %d hours", args.hours)

    if start_time >= end_time:
        log.error("start_time (%s) must be before end_time (%s)", start_time, end_time)
        sys.exit(1)

    # ---- Validate bounding box ----
    try:
        validate_bbox(args.west, args.south, args.east, args.north)
    except ValueError as e:
        log.error("Invalid bounding box: %s", e)
        sys.exit(1)

    # ---- Print environment info ----
    log.info("earthaccess version: %s", earthaccess.__version__)
    log.info("Product: short_name=%s  version=%s", args.short_name, args.version)

    # ---- Authenticate ----
    if not authenticate():
        log.error(
            "Cannot proceed without authentication.\n"
            "Register at https://urs.earthdata.nasa.gov/ if you do not have an account."
        )
        sys.exit(1)

    # ---- Search ----
    try:
        granules = search_granules(
            short_name=args.short_name,
            version=args.version,
            start_time=start_time,
            end_time=end_time,
            west=args.west,
            south=args.south,
            east=args.east,
            north=args.north,
        )
    except Exception as e:
        log.error("Search failed: %s", e)
        log.error(
            "Possible causes:\n"
            "  1. The short_name or version is incorrect. Check at:\n"
            "     https://cmr.earthdata.nasa.gov/search/granules?short_name=%s\n"
            "  2. No granules exist for this time window yet (GPM latency ~4 h).\n"
            "  3. Network or firewall issue.",
            args.short_name,
        )
        sys.exit(1)

    log.info("Found %d granule(s)", len(granules))

    if not granules:
        log.warning(
            "No granules found. Possible causes:\n"
            "  1. GPM IMERG Early Run has ~4-hour latency. Try --hours 6 or --hours 12.\n"
            "  2. The short_name '%s' or version '%s' may be wrong.\n"
            "     Early Run half-hourly: GPM_3IMERGHHE  version=07\n"
            "     Late Run half-hourly:  GPM_3IMERGHL   version=07\n"
            "     Daily Early Run:       GPM_3IMERGDE   version=07  (NOT for nowcasting)\n"
            "  3. Your Earthdata account may not have permission to access this product.\n"
            "     Visit https://disc.gsfc.nasa.gov/ and approve the required EULA.\n"
            "  4. The bounding box may not overlap any granule swath.",
            args.short_name, args.version,
        )
        sys.exit(0)

    if args.dry_run:
        log.info("Dry run — not downloading. Found granules:")
        for g in granules:
            log.info("  %s", g)
        sys.exit(0)

    # ---- Skip already-downloaded files ----
    present_granules, granules_to_download = check_already_downloaded(granules, output_dir)
    log.info(
        "%d already downloaded, %d to download",
        len(present_granules), len(granules_to_download),
    )

    if not granules_to_download:
        log.info("All granules already present. Nothing to download.")
        print_verification_guide(output_dir)
        sys.exit(0)

    # ---- Download ----
    try:
        downloaded_paths = download_with_retry(granules_to_download, output_dir)
    except Exception as e:
        log.error("Download failed: %s", e)
        sys.exit(1)

    # ---- Summary ----
    log.info("=" * 50)
    log.info("Download complete.")
    log.info("  New files downloaded: %d", len(downloaded_paths))
    log.info("  Already present:      %d", len(present_granules))
    log.info("  Total available:      %d", len(granules))

    valid_files = [p for p in downloaded_paths if p.exists() and p.stat().st_size >= MIN_FILE_SIZE_BYTES]
    small_files = [p for p in downloaded_paths if p not in valid_files]
    if small_files:
        log.warning(
            "%d file(s) are suspiciously small and may be incomplete:",
            len(small_files),
        )
        for p in small_files:
            log.warning("  %s (%d bytes)", p.name, p.stat().st_size if p.exists() else 0)

    print_verification_guide(output_dir)

    log.info(
        "\nSCIENTIFIC REMINDER:\n"
        "  - GPM IMERG Early Run is near-real-time satellite rainfall ESTIMATE.\n"
        "  - Values are precipitation RATE (mm/hr), not accumulated rainfall.\n"
        "  - Spatial resolution: 0.1° × 0.1° (~11 km).\n"
        "  - Latency: approximately 4 hours after observation time.\n"
        "  - This product is for PROTOTYPE and RESEARCH purposes.\n"
        "  - Do NOT use as the sole basis for operational flood warnings."
    )


if __name__ == "__main__":
    main()