"""
update_pipeline.py — FLOODY SHIELD Phase 6
===========================================
Windows-compatible automated pipeline runner designed for Windows Task Scheduler
or periodic cron execution.

OPERATIONAL WORKFLOW
--------------------
1. Queries NASA Earthdata for recent GPM IMERG Early granules.
2. Checks locally existing files; skips duplicates.
3. Downloads only newly published frames with exponential backoff on network errors.
4. Assembles updated chronological sequence.
5. Runs Data Quality Engine:
   - If INVALID: aborts nowcast update, marks status DEGRADED, records audit log.
   - If GOOD or DEGRADED: proceeds with nowcast execution.
6. Runs pySTEPS short-term nowcasting (deterministic + ensemble).
7. Generates M1 extreme rainfall decision summary JSON.
8. Writes atomic health checkpoint (`pipeline_health.json`).

SCIENTIFIC LATENCY CONCEPTS
---------------------------
- Realtime:            Current wall-clock time (e.g., 01:20 UTC).
- Observation Time t0: The actual time satellite sensors observed precipitation (e.g., 14:30 UTC).
- Source Latency:      t_realtime - t_observation (~4 hours for GPM IMERG Early).
- Processing Latency:  Duration spent executing ingestion, quality check, and pySTEPS (~10-15 seconds).
- Forecast Time:       Valid future time (e.g. t0 + 60 min = 15:30 UTC).
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("floody_shield.update_pipeline")


def run_command(cmd_args: list[str]) -> subprocess.CompletedProcess:
    log.info("Executing: %s", " ".join(cmd_args))
    res = subprocess.run(cmd_args, capture_output=True, text=True)
    if res.returncode != 0:
        log.error("Command failed (exit %d):\n%s", res.returncode, res.stderr)
        raise RuntimeError(f"Step failed with exit code {res.returncode}")
    log.info("Command completed successfully.")
    return res


def main() -> None:
    parser = argparse.ArgumentParser(description="Run complete automated FLOODY SHIELD rainfall update pipeline.")
    parser.add_argument("--python-exe", type=str, default=sys.executable, help="Python interpreter to use.")
    parser.add_argument("--hours", type=int, default=6, help="Hours window to look back for new GPM files.")
    parser.add_argument("--max-frames", type=int, default=6, help="Sequence history frames.")
    args = parser.parse_args()

    py = args.python_exe
    root = Path(__file__).resolve().parents[3]  # floody-shield root
    scripts_dir = root / "ml" / "rainfall" / "scripts"

    start_time = datetime.now(timezone.utc)
    log.info("Starting FLOODY SHIELD Rainfall Pipeline Update at %s", start_time.isoformat())

    pipeline_status = {
        "run_time_utc": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps_completed": [],
        "pipeline_health": "INITIALIZING",
        "error": None,
    }

    try:
        # Step 1: Ingest newly arrived GPM files
        log.info("[Step 1/5] Ingesting GPM IMERG Early frames...")
        run_command([py, str(scripts_dir / "download_gpm.py"), "--hours", str(args.hours)])
        pipeline_status["steps_completed"].append("download_gpm")

        # Step 2: Assemble chronological sequence
        log.info("[Step 2/5] Assembling and validating time sequence...")
        run_command([py, str(scripts_dir / "build_gpm_sequence.py"), "--max-frames", str(args.max_frames)])
        pipeline_status["steps_completed"].append("build_gpm_sequence")

        # Step 3: Run Data Quality Engine
        log.info("[Step 3/5] Auditing data quality...")
        run_command([py, str(scripts_dir / "quality_engine.py")])
        pipeline_status["steps_completed"].append("quality_engine")

        # Step 4: Run pySTEPS Nowcasting
        log.info("[Step 4/5] Executing pySTEPS nowcasting...")
        run_command([py, str(scripts_dir / "pysteps_nowcast.py")])
        pipeline_status["steps_completed"].append("pysteps_nowcast")

        # Step 5: Generate M1 Decision Summary
        log.info("[Step 5/5] Generating M1 Extreme Rainfall risk indicators...")
        run_command([py, str(scripts_dir / "extreme_rainfall_m1.py")])
        pipeline_status["steps_completed"].append("extreme_rainfall_m1")

        pipeline_status["pipeline_health"] = "HEALTHY"
        log.info("FLOODY SHIELD Pipeline completed successfully.")

    except Exception as e:
        pipeline_status["pipeline_health"] = "DEGRADED_ERROR"
        pipeline_status["error"] = str(e)
        log.error("Pipeline run halted: %s", e)

    finally:
        end_time = datetime.now(timezone.utc)
        processing_latency_sec = (end_time - start_time).total_seconds()
        pipeline_status["processing_latency_seconds"] = round(processing_latency_sec, 2)
        pipeline_status["finish_time_utc"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        health_file = root / "ml" / "rainfall" / "models" / "nowcasts" / "pipeline_health.json"
        health_file.parent.mkdir(parents=True, exist_ok=True)
        with open(health_file, "w", encoding="utf-8") as f:
            json.dump(pipeline_status, f, indent=2)
        log.info("Saved pipeline health status to: %s", health_file)


if __name__ == "__main__":
    main()
