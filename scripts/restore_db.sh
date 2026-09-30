#!/usr/bin/env bash
# scripts/restore_db.sh
# Production database restore script for FLOODY SHIELD
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

python3 "$PROJECT_ROOT/scripts/restore_db.py" "$@"
