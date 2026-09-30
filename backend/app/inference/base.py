"""
backend/app/inference/base.py
==============================
Abstract ModelAdapter interface for all FLOODY SHIELD analytical models.
Guarantees consistent signature, latency timing, input hashing, and provenance tracking.
"""

from __future__ import annotations

import abc
import hashlib
import json
import time
from typing import Any, Dict, Optional

from backend.app.core.errors import ModelInferenceError
from backend.app.core.logging import get_logger

logger = get_logger("floody.inference.base")


class ModelAdapter(abc.ABC):
    """
    Unified contract for all 20 predictive, physical, and decision models in FLOODY SHIELD.
    """

    model_id: str
    model_name: str
    version: str = "1.0.0"
    evidence_status: str = "PROTOTYPE_SIMULATED_DATA"

    def __init__(self):
        pass

    @abc.abstractmethod
    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Core prediction logic delegated to underlying ml/ package."""
        raise NotImplementedError

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public execution wrapper providing:
          1. Input hash calculation
          2. Latency measurement (execution_time_ms)
          3. Model metadata enrichment
          4. Robust error handling
        """
        payload_str = json.dumps(input_data, sort_keys=True, default=str)
        input_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        start_time = time.perf_counter()
        try:
            output = self.run_prediction(input_data)
        except Exception as exc:
            logger.error(f"Error during execution of model {self.model_id}: {exc}", exc_info=True)
            raise ModelInferenceError(
                message=f"Model {self.model_id} execution failed: {exc}",
                model_id=self.model_id,
                details={"input_hash": input_hash, "error": str(exc)},
            )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "version": self.version,
            "evidence_status": self.evidence_status,
            "execution_time_ms": round(elapsed_ms, 2),
            "input_hash": input_hash,
            "output": output,
        }
