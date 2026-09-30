"""
ml/model_registry/registry.py
============================
Central registry tracking model versions, hashes, training periods, and statuses.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ml.model_registry.schema import ModelMetadata, ModelStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_FILE = REPO_ROOT / "reports" / "model_registry.json"


class ModelRegistry:
    def __init__(self, registry_file: Path = DEFAULT_REGISTRY_FILE):
        self.registry_file = registry_file
        self.models: Dict[str, ModelMetadata] = {}
        self._load()

    def _load(self) -> None:
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for mid, entry in data.items():
                        entry["status"] = ModelStatus(entry["status"])
                        self.models[mid] = ModelMetadata(**entry)
            except Exception as e:
                print(f"[ModelRegistry] Warning loading registry: {e}")
        else:
            # Seed initial production frozen models
            self._seed_production_models()

    def _seed_production_models(self) -> None:
        """Populates frozen models M2, M4, M6, and M7."""
        initial = [
            ModelMetadata(
                model_id="M2",
                model_name="Calibrated XGBoost Flood Occurrence / Risk",
                version="1.0.0",
                artifact_path="ml/flood/m2_upper_beas_flood_model.joblib",
                sha256="a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b",
                training_dataset_id="upper_beas_flood_dataset.csv",
                feature_schema_version="m2_v1",
                training_period="Simulated 2018-2023 Monsoon",
                validation_period="July 2023 Flood Event",
                metrics={"recall": 1.0, "roc_auc_valid_absences": 0.875},
                limitations=["Valley floor saturation under extreme discharge"],
                status=ModelStatus.FROZEN,
                registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="M4",
                model_name="Multimodal 9-Channel Flood Inundation U-Net",
                version="1.0.0",
                artifact_path="data/satellite_output/flood_multimodal_unet.pt",
                sha256="45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07",
                training_dataset_id="upper_beas_july2023_scene",
                feature_schema_version="m4_9ch_v1",
                training_period="July 2023 Disaster Pass",
                validation_period="July 8-11, 2023 Ground Survey",
                metrics={"point_specificity": 0.75, "point_recall": 0.75, "internal_proxy_dice": 0.988},
                limitations=["2D full-scene external raster ground truth unavailable"],
                status=ModelStatus.FROZEN,
                registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="M6",
                model_name="Random Forest Landslide Susceptibility (350 trees)",
                version="1.0.0",
                artifact_path="ml/landslide/m6_beas_susceptibility_rf.joblib",
                sha256="e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c",
                training_dataset_id="upper_beas_landslide_dataset.csv",
                feature_schema_version="m6_10feats_v1",
                training_period="Historical Terrain Baseline",
                validation_period="2023 Landslide Scarp Inventory",
                metrics={"independent_specificity": 1.0, "independent_recall": 0.1667},
                limitations=["30m DEM slope smoothing; static model lacks dynamic rainfall forcing"],
                status=ModelStatus.FROZEN,
                registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="M7",
                model_name="LightGBM Dynamic Landslide Trigger (350 rounds)",
                version="1.0.0",
                artifact_path="ml/landslide/m7_beas_trigger_lgbm.joblib",
                sha256="f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a",
                training_dataset_id="upper_beas_landslide_dataset.csv",
                feature_schema_version="m7_dynamic_v1",
                training_period="Multi-Event Monsoon Simulation",
                validation_period="7 Multi-Year Storm Episodes (2018-2023)",
                metrics={"event_detection_recall": 1.0, "event_roc_auc": 1.0},
                limitations=["Threshold saturation at tau=0.50 on moderate rain without PWP safety factor"],
                status=ModelStatus.FROZEN,
                registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        ]
        for m in initial:
            self.models[m.model_id] = m
        self.save()

    def register_model(self, metadata: ModelMetadata) -> None:
        if not metadata.registered_at:
            metadata.registered_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.models[metadata.model_id] = metadata
        self.save()

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        return self.models.get(model_id)

    def list_models(self) -> List[ModelMetadata]:
        return list(self.models.values())

    def verify_artifact_hash(self, model_id: str) -> bool:
        meta = self.get_model(model_id)
        if not meta:
            return False
        path = REPO_ROOT / meta.artifact_path
        if not path.exists():
            return False
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest() == meta.sha256

    def save(self) -> None:
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        data = {mid: m.to_dict() for mid, m in self.models.items()}
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
