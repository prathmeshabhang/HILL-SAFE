#!/usr/bin/env bash
# scripts/backup_db.sh
# Production database backup script for FLOODY SHIELD
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

python3 "$PROJECT_ROOT/scripts/backup_db.py" "$@"
