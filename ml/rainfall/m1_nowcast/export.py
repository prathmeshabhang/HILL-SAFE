"""
ml/rainfall/m1_nowcast/export.py
================================
Registers Model M1 into the central FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus
from ml.rainfall.m1_nowcast.train import DEFAULT_MODEL_PATH, train_m1_model


def register_m1_model() -> ModelMetadata:
    bundle, sha256, train_metrics = train_m1_model()

    meta = ModelMetadata(
        model_id="M1",
        model_name="Multi-Horizon Extreme Rainfall Nowcasting Engine",
        version="1.0.0",
        artifact_path=str(DEFAULT_MODEL_PATH.relative_to(Path(__file__).resolve().parents[3])).replace("\\", "/"),
        sha256=sha256,
        training_dataset_id="upper_beas_monsoon_aws_timeseries",
        feature_schema_version="m1_14feats_v1",
        training_period="Simulated 2018-2023 Convective Cloudburst Telemetry",
        validation_period="Chronological Storm Holdout",
        hyperparameters={"horizons": ["15m", "30m", "1h", "3h", "6h", "24h"], "n_estimators": 120, "learning_rate": 0.04},
        metrics=train_metrics,
        limitations=[
            "Pure statistical extrapolation decays significantly beyond +3h without Doppler radar assimilation",
            "Orographic enhancement relies on DEM slope proxy without dynamic wind shear vectors",
        ],
        status=ModelStatus.INTERNAL_VALIDATED,
        registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    reg = ModelRegistry()
    reg.register_model(meta)
    return meta


if __name__ == "__main__":
    m = register_m1_model()
    print(f"Registered Model M1: {m.model_id} (SHA-256: {m.sha256})")
