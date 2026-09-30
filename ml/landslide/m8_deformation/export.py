"""
ml/landslide/m8_deformation/export.py
=====================================
Registers Model M8 into the central FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ml.landslide.m8_deformation.train import DEFAULT_MODEL_PATH, train_m8_model
from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus


def register_m8_model() -> ModelMetadata:
    bundle, sha256, train_metrics = train_m8_model()

    repo_root = Path(__file__).resolve().parents[3]
    rel_path = str(DEFAULT_MODEL_PATH.relative_to(repo_root)).replace("\\", "/")

    meta = ModelMetadata(
        model_id="M8",
        model_name="Ground Movement & Slope Deformation Forecast Engine",
        version="1.0.0",
        artifact_path=rel_path,
        sha256=sha256,
        training_dataset_id="upper_beas_insar_gnss_creeping_slopes",
        feature_schema_version="m8_deformation_10feats_v1",
        training_period="Simulated Multi-Year Creep Series (Sentinel-1 InSAR & In-Situ Tilts)",
        validation_period="Holdout Creep & Tertiary Acceleration Benchmark",
        hyperparameters={"horizons": ["24h", "72h", "7d"], "n_estimators": 100, "learning_rate": 0.05, "max_depth": 5},
        metrics=train_metrics,
        limitations=[
            "InSAR C-band signal decorrelation in dense vegetative canopy or steep shadow slopes reduces precision",
            "Saito asymptotic failure prediction valid predominantly in progressive brittle and rotational shear failures",
        ],
        status=ModelStatus.INTERNAL_VALIDATED,
        registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    reg = ModelRegistry()
    reg.register_model(meta)
    return meta


if __name__ == "__main__":
    m = register_m8_model()
    print(f"Registered Model M8: {m.model_id} (SHA-256: {m.sha256})")
