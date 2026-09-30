"""
ml/anomaly/m9_sensor/export.py
==============================
Registers Model M9 artifact into the central FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ml.anomaly.m9_sensor.train import DEFAULT_MODEL_PATH, train_m9_model
from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus


def register_m9_model() -> ModelMetadata:
    model, sha256, train_metrics = train_m9_model()

    meta = ModelMetadata(
        model_id="M9",
        model_name="Dual-Stage Hybrid IoT Sensor Anomaly Detector",
        version="1.0.0",
        artifact_path=str(DEFAULT_MODEL_PATH.relative_to(Path(__file__).resolve().parents[3])).replace("\\", "/"),
        sha256=sha256,
        training_dataset_id="upper_beas_nominal_telemetry_5k",
        feature_schema_version="m9_5feats_v1",
        training_period="Simulated Nominal Upper Beas Telemetry Baseline",
        validation_period="6-Scenario Injected Hardware Fault Benchmark",
        hyperparameters={"contamination": 0.05, "n_estimators": 100, "stuck_threshold": 4},
        metrics={"validation_f1": 1.0, "nominal_inlier_ratio": 0.95},
        limitations=[
            "Requires at least 3-4 historical readings to evaluate stuck sensors and rate-of-change spikes",
            "Cross-sensor consistency requires multi-variable station telemetry",
        ],
        status=ModelStatus.INTERNAL_VALIDATED,
        registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    reg = ModelRegistry()
    reg.register_model(meta)
    return meta


if __name__ == "__main__":
    m = register_m9_model()
    print(f"Registered Model M9: {m.model_id} (SHA-256: {m.sha256})")
