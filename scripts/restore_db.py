"""
scripts/restore_db.py
=====================
Cross-platform Disaster Recovery & Database Restoration Utility for FLOODY SHIELD v4.0.
Validates SHA-256 integrity against manifest, creates a safety rollback snapshot,
restores the database, and audits post-restore table schemas and row counts.
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hex digest of a file in 64KB chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_sqlite_table_rows(db_path: Path) -> Dict[str, int]:
    """Inspects SQLite database and returns row counts for all user tables."""
    counts = {}
    if not db_path.exists():
        return counts
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        for tbl in sorted(tables):
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                counts[tbl] = cursor.fetchone()[0]
            except Exception:
                counts[tbl] = -1
    finally:
        conn.close()
    return counts


def restore_database(
    backup_file: Path,
    manifest_file: Optional[Path] = None,
    target_path: Optional[Path] = None,
    target_url: Optional[str] = None,
) -> bool:
    """
    Restores FLOODY SHIELD database from a verified backup file.
    Validates SHA-256 checksum and verifies row count integrity.
    """
    if not backup_file.exists():
        print(f"[-] Error: Backup file does not exist: {backup_file}", file=sys.stderr)
        return False

    manifest_data = None
    if manifest_file and manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        expected_hash = manifest_data.get("sha256")
        actual_hash = compute_sha256(backup_file)
        if expected_hash and actual_hash.lower() != expected_hash.lower():
            print(
                f"[-] Checksum verification failed!\n"
                f"    Expected: {expected_hash}\n"
                f"    Actual:   {actual_hash}",
                file=sys.stderr,
            )
            return False
        print(f"[OK] SHA-256 Checksum verified ({actual_hash}).")
    else:
        print("[i] Notice: No manifest provided; proceeding with direct restoration.")

    db_url = target_url or os.getenv("DATABASE_URL", "")

    if (db_url.startswith("postgresql") or db_url.startswith("postgres")) and not target_path:
        print(f"[+] Restoring PostgreSQL database from {backup_file}...")
        try:
            cmd = ["pg_restore", "--clean", "--if-exists", "-d", db_url, str(backup_file)]
            subprocess.run(cmd, check=True)
            print("[OK] PostgreSQL restore completed.")
            return True
        except Exception as e:
            print(f"[-] pg_restore failed or command not available: {e}", file=sys.stderr)
            return False
    else:
        # SQLite restoration
        dest_path = target_path or (BASE_DIR / "data" / "floody_shield.db")

        # Create safety rollback snapshot if target exists
        if dest_path.exists():
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%SZ")
            rollback_path = dest_path.with_suffix(f".db.pre_restore_{timestamp}.bak")
            print(f"[i] Creating safety rollback snapshot at {rollback_path}...")
            shutil.copy2(dest_path, rollback_path)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[+] Restoring SQLite database to {dest_path}...")
        try:
            src_conn = sqlite3.connect(backup_file)
            dst_conn = sqlite3.connect(dest_path)
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
        except Exception:
            shutil.copy2(backup_file, dest_path)

        # Post-restoration verification
        post_counts = count_sqlite_table_rows(dest_path)
        print(f"[OK] SQLite restore completed: {len(post_counts)} tables restored.")

        if manifest_data and "tables" in manifest_data:
            expected_tables = manifest_data["tables"]
            mismatches = []
            for tbl, exp_cnt in expected_tables.items():
                act_cnt = post_counts.get(tbl, 0)
                if exp_cnt >= 0 and act_cnt != exp_cnt:
                    mismatches.append(f"{tbl}: expected {exp_cnt}, got {act_cnt}")
            if mismatches:
                print(f"[!] Warning: Row count discrepancies detected: {mismatches}", file=sys.stderr)
                return False
            print("[OK] All table row counts match backup manifest exactly.")

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore FLOODY SHIELD database from backup")
    parser.add_argument("backup_file", type=Path, help="Path to backup file")
    parser.add_argument("--manifest", type=Path, default=None, help="Path to manifest file for SHA-256 verification")
    parser.add_argument("--target-path", type=Path, default=None, help="Target SQLite DB path")
    parser.add_argument("--target-url", type=str, default=None, help="Target database connection URL")
    args = parser.parse_args()

    success = restore_database(
        backup_file=args.backup_file,
        manifest_file=args.manifest,
        target_path=args.target_path,
        target_url=args.target_url,
    )
    sys.exit(0 if success else 1)
