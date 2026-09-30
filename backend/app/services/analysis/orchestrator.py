"""
backend/app/services/analysis/orchestrator.py
=============================================
Decoupled Execution Coordinator for Flood Physics and Landslide AI Pipelines.
Guarantees fault isolation: failures or timeouts in one domain never cascade to crash other domains.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from backend.app.core.logging import get_logger
from backend.app.orchestration.state import ExecutionState, ModelNodeResult
from backend.app.services.analysis.base import AnalysisComponent, AnalysisResult, AnalysisStatus
from backend.app.services.analysis.flood_physics import FloodPhysicsEngine, flood_physics_engine
from backend.app.services.analysis.landslide_ai import LandslideAIEngine, landslide_ai_engine

logger = get_logger("floody.analysis.orchestrator")


class DecoupledAnalysisCoordinator:
    """
    Coordinates decoupled execution of independent physical and machine learning analytical pipelines.
    Guarantees that an analytical failure in Landslide AI does not abort Flood Physics, and vice versa.
    """

    def __init__(
        self,
        physics_engine: Optional[FloodPhysicsEngine] = None,
        ai_engine: Optional[LandslideAIEngine] = None,
    ):
        self.physics_engine = physics_engine or flood_physics_engine
        self.ai_engine = ai_engine or landslide_ai_engine

    def execute_all(self, inputs: Dict[str, Any]) -> Dict[str, AnalysisResult]:
        """
        Executes both Flood Physics and Landslide AI independently.
        Catches all component exceptions to guarantee pipeline continuity.
        """
        results: Dict[str, AnalysisResult] = {}

        # 1. Execute Flood Physics
        try:
            results["flood_physics"] = self.physics_engine.execute(inputs)
        except Exception as exc:
            logger.error(f"Fatal error in flood physics pipeline: {exc}", exc_info=True)
            results["flood_physics"] = AnalysisResult(
                component_name=self.physics_engine.component_name,
                capability_name=self.physics_engine.capability_name,
                execution_status=AnalysisStatus.ERROR,
                data_mode=self.physics_engine.evaluate_provenance(inputs),
                confidence_score=0.0,
                errors=[str(exc)],
            )

        # 2. Execute Landslide AI
        try:
            results["landslide_ai"] = self.ai_engine.execute(inputs)
        except Exception as exc:
            logger.error(f"Fatal error in landslide AI pipeline: {exc}", exc_info=True)
            results["landslide_ai"] = AnalysisResult(
                component_name=self.ai_engine.component_name,
                capability_name=self.ai_engine.capability_name,
                execution_status=AnalysisStatus.ERROR,
                data_mode=self.ai_engine.evaluate_provenance(inputs),
                confidence_score=0.0,
                errors=[str(exc)],
            )

        return results

    def convert_to_orchestrator_nodes(
        self,
        analysis_results: Dict[str, AnalysisResult],
    ) -> Dict[str, ModelNodeResult]:
        """
        Converts AnalysisResult domain objects into ModelNodeResult objects compatible
        with the existing UnifiedRiskEngine.synthesize_risk_state orchestration dictionary.
        """
        nodes: Dict[str, ModelNodeResult] = {}

        if "flood_physics" in analysis_results:
            res = analysis_results["flood_physics"]
            status_map = {
                AnalysisStatus.READY: ExecutionState.COMPLETED,
                AnalysisStatus.DEGRADED: ExecutionState.DEGRADED,
                AnalysisStatus.STALE: ExecutionState.DEGRADED,
                AnalysisStatus.ERROR: ExecutionState.FAILED,
                AnalysisStatus.UNAVAILABLE: ExecutionState.FAILED,
            }
            node_state = status_map.get(res.execution_status, ExecutionState.COMPLETED)

            nodes["FLOOD_PHYSICS_ROUTING"] = ModelNodeResult(
                model_id="FLOOD_PHYSICS_ROUTING",
                model_name="Flood Intelligence (SCS-CN & DEM Routing)",
                state=node_state,
                output=res.output_payload,
                execution_time_ms=res.processing_duration_ms,
                quality_state=res.execution_status.value,
                evidence_status="OPERATIONAL" if res.is_operational() else "NON_OPERATIONAL",
                error_message="; ".join(res.errors) if res.errors else None,
            )

        if "landslide_ai" in analysis_results:
            res = analysis_results["landslide_ai"]
            status_map = {
                AnalysisStatus.READY: ExecutionState.COMPLETED,
                AnalysisStatus.DEGRADED: ExecutionState.DEGRADED,
                AnalysisStatus.STALE: ExecutionState.DEGRADED,
                AnalysisStatus.ERROR: ExecutionState.FAILED,
                AnalysisStatus.UNAVAILABLE: ExecutionState.FAILED,
            }
            node_state = status_map.get(res.execution_status, ExecutionState.COMPLETED)

            nodes["LANDSLIDE_AI_TRIGGER"] = ModelNodeResult(
                model_id="LANDSLIDE_AI_TRIGGER",
                model_name="Landslide Intelligence (LightGBM Booster)",
                state=node_state,
                output=res.output_payload,
                execution_time_ms=res.processing_duration_ms,
                quality_state=res.execution_status.value,
                evidence_status="OPERATIONAL" if res.is_operational() else "NON_OPERATIONAL",
                error_message="; ".join(res.errors) if res.errors else None,
            )

        return nodes


# Global singleton coordinator
decoupled_analysis_coordinator = DecoupledAnalysisCoordinator()
