"""
ml/flood/m11_flood_depth/export.py
==================================
Registers Model M11 into the central FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ml.flood.m11_flood_depth.train import DEFAULT_MODEL_PATH, train_m11_model
from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus


def register_m11_model() -> ModelMetadata:
    bundle, sha256, train_metrics = train_m11_model()

    repo_root = Path(__file__).resolve().parents[3]
    rel_path = str(DEFAULT_MODEL_PATH.relative_to(repo_root)).replace("\\", "/")

    meta = ModelMetadata(
        model_id="M11",
        model_name="Flood Propagation & Inundation Depth Forecast Engine",
        version="1.0.0",
        artifact_path=rel_path,
        sha256=sha256,
        training_dataset_id="upper_beas_hecras_hand_floodplain_profiles",
        feature_schema_version="m11_depth_5feats_v1",
        training_period="Simulated Multi-Reach Hydrodynamic Calibrations (Palchan to Pandoh)",
        validation_period="Holdout High-Discharge Flood Scenarios",
        hyperparameters={"n_estimators": 100, "learning_rate": 0.05, "max_depth": 5},
        metrics=train_metrics,
        limitations=[
            "1D-HAND assumes hydrostatic lateral water surface elevation; dynamic momentum backwaters in narrow confluences are approximated",
            "Manning roughness n assumed uniform per reach without seasonal riparian brush variations",
        ],
        status=ModelStatus.INTERNAL_VALIDATED,
        registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    reg = ModelRegistry()
    reg.register_model(meta)
    return meta


if __name__ == "__main__":
    m = register_m11_model()
    print(f"Registered Model M11: {m.model_id} (SHA-256: {m.sha256})")
