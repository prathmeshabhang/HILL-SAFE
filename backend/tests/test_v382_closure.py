"""
backend/tests/test_v382_closure.py
==================================
FLOODY SHIELD v3.8.2 - Final Scientific Closure & Reproducibility Verification Suite.

Tests that all scientific statements match repository evidence:
  1. Frozen model SHA-256 immutability
  2. v3.8.2 final scientific status matrix correctness
  3. Real dataset evidence audit verification
  4. Independent metric reproduction zero-discrepancy
  5. Readiness matrix categories and status constraints
  6. Field deployment reality declaration (0 in-situ)
  7. Automated claim guard verification
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from tools.verify_model_hashes import verify_models
from tools.validation.claim_guard import run_claim_guard
from tools.validation.reproduce_metrics import run_independent_reproduction


# ============================================================================
# 1. FROZEN MODEL BIT-IDENTICAL IMMUTABILITY
# ============================================================================

def test_v382_frozen_models_immutability():
    """Confirms all 4 frozen models retain bit-identical SHA-256 hashes."""
    assert verify_models() is True


# ============================================================================
# 2. FINAL SCIENTIFIC STATUS MATRIX
# ============================================================================

def test_v382_scientific_status_matrix():
    """Verifies that all 20 models are classified according to the v3.8.2 taxonomy."""
    csv_path = Path("reports/v3_8_2/final_scientific_status.csv")
    assert csv_path.exists(), "final_scientific_status.csv does not exist"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 20, f"Expected 20 models in final scientific status, got {len(rows)}"

    allowed_statuses = {
        "PRELIMINARY_EXTERNAL_EVIDENCE",
        "PROXY_VALIDATED_PROTOTYPE",
        "GLOBAL_EMPIRICAL_BENCHMARK",
        "SYNTHETIC_BENCHMARKED_PROTOTYPE",
        "PENDING_EXTERNAL_DATA",
    }

    status_counts = {}
    for r in rows:
        st = r["evidence_status"]
        assert st in allowed_statuses, f"Invalid status: {st} for model {r['model_id']}"
        status_counts[st] = status_counts.get(st, 0) + 1

    # Exact expected counts
    assert status_counts["PRELIMINARY_EXTERNAL_EVIDENCE"] == 3
    assert status_counts["PROXY_VALIDATED_PROTOTYPE"] == 2
    assert status_counts["GLOBAL_EMPIRICAL_BENCHMARK"] == 1
    assert status_counts["SYNTHETIC_BENCHMARKED_PROTOTYPE"] == 9
    assert status_counts["PENDING_EXTERNAL_DATA"] == 5


# ============================================================================
# 3. REAL DATASET EVIDENCE AUDIT
# ============================================================================

def test_v382_real_dataset_evidence():
    """Verifies that all Tier-1 authentic datasets have documented provenance."""
    json_path = Path("reports/v3_8_2/real_dataset_evidence.json")
    assert json_path.exists(), "real_dataset_evidence.json does not exist"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["audit_version"] == "v3.8.2"
    assert data["total_authentic_datasets"] == 5
    assert len(data["datasets"]) == 5

    for ds in data["datasets"]:
        assert ds["ground_truth_status"] != "NONE"
        assert ds["validation_status"] == "PRELIMINARY_EXTERNAL_EVIDENCE"
        assert len(ds["limitations"]) > 10


# ============================================================================
# 4. INDEPENDENT REPRODUCTION ENGINE
# ============================================================================

def test_v382_independent_reproduction():
    """Verifies that independent recalculation matches stored metrics within 1e-4."""
    report = run_independent_reproduction()
    assert report["audit_version"] == "v3.8.2"
    assert report["overall_status"] == "PASSED"

    for comp in report["comparisons"]:
        assert comp["reproduction_status"] == "MATCH"
        assert comp["difference"] <= 1e-4


# ============================================================================
# 5. READINESS MATRIX COMPLIANCE
# ============================================================================

def test_v382_readiness_matrix_categories():
    """Verifies the 15 operational readiness categories and status constraints."""
    csv_path = Path("reports/v3_8_2/final_readiness_matrix.csv")
    assert csv_path.exists(), "final_readiness_matrix.csv does not exist"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 15, f"Expected 15 categories, found {len(rows)}"

    valid_statuses = {"VERIFIED", "PARTIALLY_VERIFIED", "SIMULATED", "PENDING", "NOT_DEMONSTRATED"}
    for r in rows:
        assert r["status"] in valid_statuses, f"Invalid readiness status {r['status']}"

    # Specific category checks
    cat_map = {r["category"]: r for r in rows}
    assert cat_map["Field Deployment"]["status"] == "NOT_DEMONSTRATED"
    assert cat_map["Operational Reliability"]["status"] == "SIMULATED"
    assert cat_map["Telemetry"]["status"] == "SIMULATED"
    assert cat_map["LoRa"]["status"] == "SIMULATED"


# ============================================================================
# 6. CLAIM GUARD SCANNER
# ============================================================================

def test_v382_claim_guard_clean():
    """Verifies that automated claim scanner detects 0 ungrounded claims."""
    report = run_claim_guard(target_dirs=["tools", "ml"])
    assert report["audit_version"] == "v3.8.2"
    assert report["critical_count"] == 0
    assert report["high_count"] == 0
