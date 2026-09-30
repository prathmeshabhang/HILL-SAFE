"""
ml/flood/m10_water_level/export.py
==================================
Registers Model M10 into the central FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ml.flood.m10_water_level.train import DEFAULT_MODEL_PATH, train_m10_model
from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus


def register_m10_model() -> ModelMetadata:
    bundle, sha256, train_metrics = train_m10_model()

    repo_root = Path(__file__).resolve().parents[3]
    rel_path = str(DEFAULT_MODEL_PATH.relative_to(repo_root)).replace("\\", "/")

    meta = ModelMetadata(
        model_id="M10",
        model_name="River Water-Level & Stage Forecast Engine",
        version="1.0.0",
        artifact_path=rel_path,
        sha256=sha256,
        training_dataset_id="upper_beas_cwc_hydrographic_telemetry",
        feature_schema_version="m10_water_level_7feats_v1",
        training_period="Simulated Multi-Year CWC Hydrograph Series (Beas River Basin)",
        validation_period="Holdout Monsoon Storms & High Flood Level Crests",
        hyperparameters={"horizons": ["30m", "1h", "3h", "6h"], "n_estimators": 100, "learning_rate": 0.04, "max_depth": 5},
        metrics=train_metrics,
        limitations=[
            "Extrapolation accuracy degrades beyond +3h if localized cloudburst centers shift outside upstream sub-catchments",
            "Assumes natural riverbed geometry without sudden bridge pier debris dams or artificial barrage gate maneuvers",
        ],
        status=ModelStatus.INTERNAL_VALIDATED,
        registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    reg = ModelRegistry()
    reg.register_model(meta)
    return meta


if __name__ == "__main__":
    m = register_m10_model()
    print(f"Registered Model M10: {m.model_id} (SHA-256: {m.sha256})")
