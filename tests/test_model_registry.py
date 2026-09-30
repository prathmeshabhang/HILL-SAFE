"""
test_model_registry.py — Unit Tests for Model Registry Subsystem
================================================================
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.model_registry.registry import ModelRegistry
from ml.model_registry.schema import ModelMetadata, ModelStatus


class TestModelRegistry(unittest.TestCase):

    def test_seeded_production_models(self):
        reg = ModelRegistry()
        models = reg.list_models()
        self.assertGreaterEqual(len(models), 4)

        # Verify M2, M4, M6, M7 exist and are FROZEN
        for mid in ["M2", "M4", "M6", "M7"]:
            m = reg.get_model(mid)
            self.assertIsNotNone(m, f"Model {mid} must be registered")
            self.assertEqual(m.status, ModelStatus.FROZEN)
            self.assertTrue(len(m.sha256) == 64)

    def test_artifact_hash_verification(self):
        reg = ModelRegistry()
        for mid in ["M2", "M4", "M6", "M7"]:
            is_valid = reg.verify_artifact_hash(mid)
            self.assertTrue(is_valid, f"Artifact hash for {mid} must match disk artifact exactly!")

    def test_register_and_query_new_model(self):
        reg = ModelRegistry()
        dummy = ModelMetadata(
            model_id="M_TEST",
            model_name="Test Model",
            version="0.1.0",
            artifact_path="none",
            sha256="0" * 64,
            training_dataset_id="dummy_data",
            feature_schema_version="v1",
            status=ModelStatus.DEVELOPMENT,
        )
        reg.register_model(dummy)
        retrieved = reg.get_model("M_TEST")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.status, ModelStatus.DEVELOPMENT)


if __name__ == "__main__":
    unittest.main()
