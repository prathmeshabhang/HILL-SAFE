"""
ml.validation.external — External Real-World Scientific Validation Package
==========================================================================
Provides independent, frozen-model validation against authoritative external
historical landslide inventories for FLOODY SHIELD.
"""

from ml.validation.external.schema import (
    ExternalDatasetRecord,
    ExternalValidationSample,
    ExternalValidationState,
    FrozenModelContract,
)
from ml.validation.external.projection import (
    metric_distance_m,
    utm43n_to_wgs84,
    validate_coordinates,
    wgs84_to_utm43n,
)
from ml.validation.external.dataset_loader import (
    ExternalLandslideLoader,
    LoadedExternalInventory,
    ObservedLandslideEvent,
)
from ml.validation.external.temporal_leakage import (
    IndependenceAuditRecord,
    IndependenceAuditor,
)
from ml.validation.external.spatial_sampler import (
    SamplingPlanReport,
    SpatialLeakageController,
    ValidationPoint,
)
from ml.validation.external.feature_extractor import (
    FeatureExtractionProvenance,
    M6FeatureExtractor,
)
from ml.validation.external.frozen_evaluator import (
    BaselineComparisonRecord,
    ExternalEvaluationResult,
    FrozenM6Evaluator,
    SpatialCaptureRates,
)
from ml.validation.external.export_maps import ExternalValidationMapExporter

__all__ = [
    "ExternalDatasetRecord",
    "ExternalValidationSample",
    "ExternalValidationState",
    "FrozenModelContract",
    "metric_distance_m",
    "utm43n_to_wgs84",
    "validate_coordinates",
    "wgs84_to_utm43n",
    "ExternalLandslideLoader",
    "LoadedExternalInventory",
    "ObservedLandslideEvent",
    "IndependenceAuditRecord",
    "IndependenceAuditor",
    "SamplingPlanReport",
    "SpatialLeakageController",
    "ValidationPoint",
    "FeatureExtractionProvenance",
    "M6FeatureExtractor",
    "BaselineComparisonRecord",
    "ExternalEvaluationResult",
    "FrozenM6Evaluator",
    "SpatialCaptureRates",
    "ExternalValidationMapExporter",
]
