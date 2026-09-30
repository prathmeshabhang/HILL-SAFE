"""
backend/app/api/v1/endpoints/models.py
======================================
REST API endpoints for the 20-model analytical catalog,
model registry inspection, and ad-hoc adapter inference.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.core.errors import ResourceNotFoundError
from backend.app.inference.registry import model_registry_service
from backend.app.inference.adapters import get_model_adapter, ADAPTER_CLASSES

router = APIRouter(prefix="/api/v1/models", tags=["Model Registry & Inference (M1-M20)"])


class InferenceRequest(BaseModel):
    features: Dict[str, Any] = Field(..., description="Model-specific feature input dictionary")


@router.get("", summary="List all registered models in the 20-model ecosystem")
def list_models() -> Dict[str, Any]:
    """Returns catalog of models with their authoritative evidence status and version."""
    models = model_registry_service.list_registered_models()
    return {
        "status": "success",
        "total_registered_models": len(models),
        "target_basin": "Upper Beas River Basin (Kullu-Manali)",
        "models": models,
    }


@router.get("/{model_id}", summary="Get full model card and provenance metadata")
def get_model_detail(model_id: str) -> Dict[str, Any]:
    """Retrieves full specification, training period, validation evidence, and known limitations."""
    meta = model_registry_service.get_model_metadata(model_id.upper())
    if not meta:
        raise ResourceNotFoundError(resource_type="Model", resource_id=model_id)
    return {
        "status": "success",
        "model_id": model_id.upper(),
        "metadata": meta,
    }


@router.post("/{model_id}/predict", summary="Run inference on an analytical model via its adapter")
def predict_model(model_id: str, req: InferenceRequest) -> Dict[str, Any]:
    """Invokes the model adapter for the specified model ID."""
    key = model_id.upper()
    if key not in ADAPTER_CLASSES:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' does not have an active inference adapter. Registered: {list(ADAPTER_CLASSES.keys())}",
        )
    adapter = get_model_adapter(key)
    res = adapter.predict(req.features)
    return {
        "status": "success",
        "result": res,
    }
