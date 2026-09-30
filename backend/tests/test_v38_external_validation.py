"""
backend/tests/test_v38_external_validation.py
==============================================
Integration & Unit Test Suite for FLOODY SHIELD v3.8 External Scientific Validation:
  1. Dataset Registry & Governance Lifecycle Transitions
  2. Cryptographic SHA-256 Dataset Verification
  3. Reference Dataset Schema, Completeness & Spatial/Temporal Split Integrity
  4. Hydrological & Statistical Metric Verification (NSE, KGE, PBIAS, Bootstrap CI)
  5. Validation Runner Accounting (All 20 Models M1-M20)
  6. Frozen Model SHA-256 Immutability Guarantee (M2, M4, M6, M7)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np
import pytest

from tools.validation.registry import (
    ValidationDatasetRegistry,
    DatasetLifecycleState,
    ALLOWED_TRANSITIONS,
)
from tools.validation.run_external_validation import (
    nse,
    kge,
    pbias,
    bootstrap_ci,
    ModelValidationRunner,
)
from tools.verify_model_hashes import verify_models, FROZEN_MODELS, REPO_ROOT


# ============================================================================
# 1. REGISTRY & LIFECYCLE GOVERNANCE TESTS
# ============================================================================

def test_validation_registry_manifest_and_datasets(tmp_path):
    """Verifies dataset registration, manifest persistence, and lookup."""
    test_file = tmp_path / "test_catalog.csv"
    test_file.write_text("id,val\n1,10\n2,20\n", encoding="utf-8")

    reg = ValidationDatasetRegistry(dataset_dir=tmp_path, manifest_path=tmp_path / "manifest.json")
    meta = reg.register_dataset(
        dataset_id="TEST_DS_01",
        name="Test Dataset",
        target_models=["M6"],
        source_agency="TEST_AGENCY",
        geographic_scope="Kullu",
        temporal_coverage="2023",
        sample_size=2,
        provenance="REAL",
        file_path=str(test_file),
        description="Test dataset for validation registry",
    )
    assert meta.dataset_id == "TEST_DS_01"
    assert len(meta.sha256_hash) == 64
    assert (tmp_path / "manifest.json").exists()

    # Re-instantiate and verify persistence
    reg2 = ValidationDatasetRegistry(dataset_dir=tmp_path, manifest_path=tmp_path / "manifest.json")
    loaded = reg2.get_dataset("TEST_DS_01")
    assert loaded is not None
    assert loaded.name == "Test Dataset"


def test_registry_lifecycle_state_machine(tmp_path):
    """Verifies valid and invalid lifecycle transitions."""
    test_file = tmp_path / "lifecycle_test.csv"
    test_file.write_text("a,b\n1,2\n", encoding="utf-8")

    reg = ValidationDatasetRegistry(dataset_dir=tmp_path, manifest_path=tmp_path / "manifest.json")
    reg.register_dataset(
        dataset_id="LC_TEST_01",
        name="Lifecycle Test",
        target_models=["M2"],
        source_agency="CWC",
        geographic_scope="Beas",
        temporal_coverage="2023",
        sample_size=1,
        provenance="REAL",
        file_path=str(test_file),
        description="Lifecycle testing",
        lifecycle_state=DatasetLifecycleState.DISCOVERED.value,
    )

    # Valid transition: DISCOVERED -> ACQUIRED
    meta = reg.transition_state("LC_TEST_01", DatasetLifecycleState.ACQUIRED)
    assert meta.lifecycle_state == DatasetLifecycleState.ACQUIRED.value

    # Valid transition: ACQUIRED -> QUALITY_CHECKED
    meta = reg.transition_state("LC_TEST_01", DatasetLifecycleState.QUALITY_CHECKED)
    assert meta.lifecycle_state == DatasetLifecycleState.QUALITY_CHECKED.value

    # Invalid transition: QUALITY_CHECKED -> DISCOVERED (not allowed)
    with pytest.raises(ValueError):
        reg.transition_state("LC_TEST_01", DatasetLifecycleState.DISCOVERED)


# ============================================================================
# 2. REFERENCE DATASET INTEGRITY & SAMPLE SIZES
# ============================================================================

def test_reference_datasets_exist_and_meet_sample_thresholds():
    """Verifies all reference datasets exist in data/validation_datasets and have adequate sample size."""
    dataset_dir = Path("data/validation_datasets")

    # M6: >= 500 stable slope controls & scarps
    m6_path = dataset_dir / "M6_stable_slope_controls.csv"
    assert m6_path.exists()
    with open(m6_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        m6_rows = list(reader)
    assert len(m6_rows) >= 500
    assert "observed_failure" in m6_rows[0]
    assert "slope_deg" in m6_rows[0]

    # M7: >= 100 storm landslide episodes
    m7_path = dataset_dir / "M7_storm_landslide_episodes.csv"
    assert m7_path.exists()
    with open(m7_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        m7_rows = list(reader)
    assert len(m7_rows) >= 100
    assert "rainfall_24h_mm" in m7_rows[0]
    assert "triggered" in m7_rows[0]

    # M10: >= 800 continuous hourly stage records
    m10_path = dataset_dir / "M10_cwc_thalout_water_level.csv"
    assert m10_path.exists()
    with open(m10_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        m10_rows = list(reader)
    assert len(m10_rows) >= 800

    # M11: Flood extent delineations
    m11_path = dataset_dir / "M11_satellite_flood_extents.json"
    assert m11_path.exists()
    with open(m11_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    assert geojson_data["type"] == "FeatureCollection"
    assert len(geojson_data["features"]) >= 3

    # M19: >= 50 flash flood propagation events
    m19_path = dataset_dir / "M19_time_to_impact_events.csv"
    assert m19_path.exists()
    with open(m19_path, "r", encoding="utf-8") as f:
        m19_rows = list(csv.DictReader(f))
    assert len(m19_rows) >= 50

    # M20: >= 500 damage ground truth survey points
    m20_path = dataset_dir / "M20_damage_assessment_ground_truth.csv"
    assert m20_path.exists()
    with open(m20_path, "r", encoding="utf-8") as f:
        m20_rows = list(csv.DictReader(f))
    assert len(m20_rows) >= 500


# ============================================================================
# 3. STATISTICAL & HYDROLOGICAL METRICS TESTS
# ============================================================================

def test_hydrological_metrics_calculations():
    """Verifies exact behavior of NSE, KGE, and PBIAS."""
    obs = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    # Perfect match
    assert nse(obs, obs) == 1.0
    assert kge(obs, obs) == 1.0
    assert pbias(obs, obs) == 0.0

    # Simulated with known offset (+5)
    sim = obs + 5.0
    val_nse = nse(obs, sim)
    assert val_nse < 1.0
    assert pbias(obs, sim) > 0.0  # Positive bias


def test_bootstrap_confidence_interval():
    """Verifies bootstrap CI generates valid bounds for sample size >= 30."""
    rng = np.random.default_rng(42)
    y_true = rng.integers(0, 2, size=100)
    y_pred = y_true.copy()
    y_pred[:15] = 1 - y_pred[:15]  # Introduce 15 errors

    def acc(yt, yp):
        return float(np.mean(yt == yp))

    lower, upper = bootstrap_ci(y_true, y_pred, acc, n_boot=200)
    assert not np.isnan(lower)
    assert not np.isnan(upper)
    assert 0.70 <= lower <= upper <= 0.95


# ============================================================================
# 4. VALIDATION RUNNER & FROZEN MODEL GUARANTEE
# ============================================================================

def test_frozen_model_artifacts_immutability():
    """Verifies all 4 frozen model artifacts are 100% bit-identical to frozen baseline."""
    assert verify_models() is True


def test_external_validation_runner_full_accounting():
    """Verifies the runner executes all M1-M20 and writes valid reports without fabricated scores."""
    runner = ModelValidationRunner()
    summary = runner.run_all()

    assert summary["floody_shield_version"] == "3.8.0"
    assert summary["total_models_evaluated"] == 20
    assert summary["frozen_models_immutability_verified"] is True

    model_ids = [m["model_id"] for m in summary["models"]]
    expected_ids = [f"M{i}" for i in range(1, 21)]
    assert model_ids == expected_ids

    # Verify that models with status PENDING_EXTERNAL_DATA have empty/zero metrics
    for m in summary["models"]:
        if m["status"] == "PENDING_EXTERNAL_DATA":
            assert m["metrics"] == {}
            assert m["sample_size"] == 0

    # Check generated files
    assert Path("reports/external_validation_summary.json").exists()
    assert Path("reports/external_validation_summary.csv").exists()
