"""
backend/tests/test_v381_evidence_integrity.py
=============================================
FLOODY SHIELD v3.8.1 — Evidence Audit & Field-Evidence Integrity Test Suite.

Verifies:
  1. Frozen model SHA-256 immutability (M2, M4, M6, M7).
  2. Dataset manifest provenance classification honesty (SYNTHETIC vs REAL).
  3. Real external datasets presence and cryptographic integrity.
  4. Leakage audit engine spatial & temporal independence verification.
  5. Claim guard enforcement against overstated claims.
  6. Dynamic model status qualification (PRELIMINARY, PROXY, BENCHMARKED, PENDING).
  7. Field evidence decoupling (PROTOTYPE_STAGING for physical sensors).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from tools.validation.registry import (
    ValidationDatasetRegistry,
    DatasetLifecycleState,
)
from tools.validation.leakage_audit import run_full_leakage_audit
from tools.validation.claim_guard import run_claim_guard, CLAIM_RULES
from tools.validation.run_external_validation import ModelValidationRunner
from tools.verify_model_hashes import verify_models, FROZEN_MODELS, REPO_ROOT


# ============================================================================
# 1. FROZEN MODEL ARTIFACT IMMUTABILITY
# ============================================================================

def test_frozen_models_sha256_immutability():
    """Asserts all 4 frozen model artifacts are bit-for-bit identical to baseline."""
    assert verify_models() is True


# ============================================================================
# 2. DATASET MANIFEST PROVENANCE & LIFECYCLE HONESTY
# ============================================================================

def test_manifest_provenance_honesty():
    """Ensures synthetic benchmarks are never labeled as REAL ground truth."""
    manifest_path = Path("data/validation_datasets/manifest.json")
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == "3.8.1"
    for ds in manifest["datasets"]:
        prov = ds["provenance"].upper()
        state = ds["lifecycle_state"]

        if prov == "SYNTHETIC":
            assert state == DatasetLifecycleState.SYNTHETIC_BENCHMARK.value
            assert "synthetic" in ds["quality_notes"].lower() or "benchmark" in ds["quality_notes"].lower()
        elif prov == "PROXY":
            assert state == DatasetLifecycleState.PROVISIONAL.value
        elif prov == "REAL":
            assert state == DatasetLifecycleState.VALIDATION_READY.value
            assert Path(ds["file_path"]).exists()


def test_real_external_datasets_exist_and_hash_match():
    """Verifies all real external datasets match their cryptographic digests."""
    reg = ValidationDatasetRegistry()
    real_datasets = [ds for ds in reg.datasets.values() if ds.provenance == "REAL"]
    assert len(real_datasets) >= 4  # M6 raw, M6 controls, M7 catalog, M7 processed, M2 flood

    for ds in real_datasets:
        file_p = REPO_ROOT / ds.file_path
        assert file_p.exists()
        current_sha = reg.compute_sha256(file_p)
        assert current_sha == ds.sha256_hash


# ============================================================================
# 3. LEAKAGE AUDIT ENGINE
# ============================================================================

def test_leakage_audit_engine_execution():
    """Verifies that spatial proximity leakage (<500m) is accurately identified."""
    report = run_full_leakage_audit()
    assert report["audit_version"] in ["v3.8.1", "v3.8.2"]
    assert "spatial_leakage_audits" in report

    m6_audit = report["spatial_leakage_audits"]["m6_landslides_raw"]["summary"]
    assert m6_audit["total_evaluated"] == 20
    assert m6_audit["spatial_leakages"] > 0
    assert m6_audit["spatially_independent_accepted"] > 0

    flood_audit = report["spatial_leakage_audits"]["flood_events_raw"]["summary"]
    assert flood_audit["total_evaluated"] == 24
    assert flood_audit["spatial_leakages"] > 0
    assert flood_audit["spatially_independent_accepted"] > 0

    # Ensure report file was written
    out_file = Path("reports/v3_8_1/leakage_audit.json")
    assert out_file.exists()


# ============================================================================
# 4. SCIENTIFIC CLAIM GUARD
# ============================================================================

def test_claim_guard_detection():
    """Verifies claim guard rule engine scans code and documents."""
    report = run_claim_guard(target_dirs=["tools", "ml"])
    assert report["audit_version"] in ["v3.8.1", "v3.8.2"]
    assert "findings" in report
    assert Path("reports/v3_8_1/claim_guard_report.json").exists()


# ============================================================================
# 5. DYNAMIC MODEL EVIDENCE CLASSIFICATION
# ============================================================================

def test_evidence_status_dynamic_qualification():
    """Asserts all 20 models are qualified by actual evidence tiers."""
    runner = ModelValidationRunner()
    summary = runner.run_all()

    assert summary["total_models_evaluated"] == 20
    assert summary["frozen_models_immutability_verified"] is True

    valid_statuses = {
        "PRELIMINARY_EXTERNAL_EVIDENCE",
        "PROXY_VALIDATED_PROTOTYPE",
        "EMPIRICALLY_BENCHMARKED",
        "SYNTHETIC_BENCHMARKED_PROTOTYPE",
        "GLOBAL_EMPIRICAL_BENCHMARK",
        "PENDING_EXTERNAL_DATA",
    }

    status_map = {m["model_id"]: m["status"] for m in summary["models"]}
    for mid, status in status_map.items():
        assert status in valid_statuses, f"Model {mid} has invalid status {status}"

    # Verify pending models
    for pending_id in ["M1", "M3", "M5", "M8", "M13"]:
        assert status_map[pending_id] == "PENDING_EXTERNAL_DATA"
    assert status_map["M12"] in ["PENDING_EXTERNAL_DATA", "GLOBAL_EMPIRICAL_BENCHMARK"]

    # Verify M6, M7, M2 have preliminary external evidence
    assert status_map["M6"] == "PRELIMINARY_EXTERNAL_EVIDENCE"
    assert status_map["M7"] == "PRELIMINARY_EXTERNAL_EVIDENCE"
    assert status_map["M2"] == "PRELIMINARY_EXTERNAL_EVIDENCE"

    # Verify M4, M11 have proxy validation
    assert status_map["M4"] == "PROXY_VALIDATED_PROTOTYPE"
    assert status_map["M11"] == "PROXY_VALIDATED_PROTOTYPE"

    # Verify v3.8.1 reproduction files exist
    assert Path("reports/v3_8_1/external_validation_reproduction.json").exists()
    assert Path("reports/v3_8_1/model_evidence_matrix.csv").exists()


# ============================================================================
# 6. FIELD EVIDENCE STATUS DECOUPLING
# ============================================================================

def test_field_evidence_staging_declaration():
    """Verifies that physical sensor stations are marked as PROTOTYPE_STAGING."""
    status_file = Path("reports/v3_8_1/field_evidence_status.json")
    assert status_file.exists()

    with open(status_file, "r", encoding="utf-8") as f:
        status_data = json.load(f)

    assert status_data["hardware_pilot_status"]["stations_physically_deployed_in_river"] == 0
    assert status_data["hardware_pilot_status"]["operational_state"] == "PROTOTYPE_STAGING"
    for st in status_data["stations"]:
        assert st["status"] == "PROTOTYPE_STAGING"
        assert st["in_situ_verified"] is False
