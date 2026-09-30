"""
ml/flood/m12_cascade/export.py
==============================
Registers Model M12 into the central FLOODY SHIELD Model Registry.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ml.flood.m12_cascade.train import DEFAULT_MODEL_PATH, train_m12_model
from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus


def register_m12_model() -> ModelMetadata:
    bundle, sha256, train_metrics = train_m12_model()

    repo_root = Path(__file__).resolve().parents[3]
    rel_path = str(DEFAULT_MODEL_PATH.relative_to(repo_root)).replace("\\", "/")

    meta = ModelMetadata(
        model_id="M12",
        model_name="Hazard Cascade & Landslide Dam Breach Engine",
        version="1.0.0",
        artifact_path=rel_path,
        sha256=sha256,
        training_dataset_id="froehlich_costa_111_dam_breach_case_studies",
        feature_schema_version="m12_cascade_breach_v1",
        training_period="Global & Himalayan Historical Landslide Dam Failure Database",
        validation_period="Himalayan Outburst Benchmarks (Pareechu, Sun Kosi, Chamoli)",
        hyperparameters={"wave_speed_kmh": 21.0, "attenuation_decay": 0.024},
        metrics=train_metrics,
        limitations=[
            "Empirical dam breach equations assume progressive overtopping erosion; instantaneous total block collapse produces steeper peak hydrographs",
            "Downstream wave translation assumes unobstructed channel without secondary tributary dams",
        ],
        status=ModelStatus.INTERNAL_VALIDATED,
        registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    reg = ModelRegistry()
    reg.register_model(meta)
    return meta


if __name__ == "__main__":
    m = register_m12_model()
    print(f"Registered Model M12: {m.model_id} (SHA-256: {m.sha256})")
