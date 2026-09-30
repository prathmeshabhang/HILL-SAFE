"""
backend/app/orchestration/engine.py
===================================
Topological Graph Execution Engine for FLOODY SHIELD Model Orchestration.
Handles branch concurrency, failure propagation, explicit status transitions,
and execution persistence into ModelRun database records.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Set
import uuid
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.database.models.model_run import ModelRunModel
from backend.app.inference.adapters import get_model_adapter
from backend.app.orchestration.graph import MODEL_GRAPH, ModelNodeDef
from backend.app.orchestration.state import DependencyType, ExecutionState, ModelNodeResult

logger = get_logger("floody.orchestration.engine")


class ModelOrchestrator:
    """
    Executes the multi-hazard scientific pipeline according to its topological DAG.
    Isolates branch failures, preserves explicit execution states, and logs provenance.
    """

    def __init__(self, graph: Optional[Dict[str, ModelNodeDef]] = None):
        self.graph = graph or MODEL_GRAPH

    def execute_pipeline(
        self,
        db: Session,
        initial_inputs: Dict[str, Any],
        target_nodes: Optional[List[str]] = None,
    ) -> Dict[str, ModelNodeResult]:
        """
        Executes requested nodes (or entire graph) topologically.
        """
        nodes_to_run = target_nodes or list(self.graph.keys())
        results: Dict[str, ModelNodeResult] = {}
        completed_nodes: Set[str] = set()
        failed_nodes: Set[str] = set()

        logger.info(f"Starting orchestration pipeline for {len(nodes_to_run)} nodes")

        # Topological execution loop
        remaining = list(nodes_to_run)
        max_iterations = len(remaining) * 3
        iterations = 0

        while remaining and iterations < max_iterations:
            iterations += 1
            progress = False

            for model_id in list(remaining):
                node_def = self.graph.get(model_id)
                if not node_def:
                    remaining.remove(model_id)
                    continue

                # Check upstream dependencies
                deps = node_def.dependencies
                hard_deps_failed = [p for p, d_type in deps.items() if d_type == DependencyType.HARD and p in failed_nodes]
                all_deps_settled = all(p in completed_nodes or p in failed_nodes for p in deps.keys())

                if hard_deps_failed:
                    # Hard failure propagation
                    res = ModelNodeResult(
                        model_id=model_id,
                        model_name=node_def.model_name,
                        state=ExecutionState.CANCELLED,
                        error_message=f"Upstream hard dependency failed: {', '.join(hard_deps_failed)}",
                        evidence_status=node_def.evidence_status,
                    )
                    results[model_id] = res
                    failed_nodes.add(model_id)
                    remaining.remove(model_id)
                    self._persist_run(db, res)
                    progress = True
                    continue

                # If dependencies have settled, we can execute this node
                if all_deps_settled or node_def.is_root:
                    res = self._execute_node(db, node_def, initial_inputs, results)
                    results[model_id] = res
                    if res.state in (ExecutionState.COMPLETED, ExecutionState.DEGRADED):
                        completed_nodes.add(model_id)
                    else:
                        failed_nodes.add(model_id)
                    remaining.remove(model_id)
                    progress = True

            if not progress and remaining:
                # Deadlock detection / unresolvable circular dependency
                for model_id in remaining:
                    res = ModelNodeResult(
                        model_id=model_id,
                        model_name=self.graph[model_id].model_name,
                        state=ExecutionState.CANCELLED,
                        error_message="Deadlock: unresolved circular or missing dependencies",
                        evidence_status=self.graph[model_id].evidence_status,
                    )
                    results[model_id] = res
                    self._persist_run(db, res)
                break

        return results

    def _execute_node(
        self,
        db: Session,
        node_def: ModelNodeDef,
        initial_inputs: Dict[str, Any],
        prior_results: Dict[str, ModelNodeResult],
    ) -> ModelNodeResult:
        """Executes a single model node through its registered adapter."""
        model_id = node_def.model_id
        start_time = datetime.datetime.now(datetime.timezone.utc)
        t0 = time.perf_counter()

        # Gather inputs from initial payload + prior completed results
        node_input = self._build_node_input(model_id, initial_inputs, prior_results)
        input_serialized = json.dumps(node_input, sort_keys=True, default=str)
        input_hash = hashlib.sha256(input_serialized.encode("utf-8")).hexdigest()

        try:
            adapter = get_model_adapter(node_def.adapter_key)
            raw_res = adapter.predict(node_input)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            completed_time = datetime.datetime.now(datetime.timezone.utc)

            output_data = raw_res.get("output", {})
            output_serialized = json.dumps(output_data, sort_keys=True, default=str)
            output_hash = hashlib.sha256(output_serialized.encode("utf-8")).hexdigest()

            # Detect soft degradation from parent failures
            soft_degraded = any(
                prior_results[p].state in (ExecutionState.FAILED, ExecutionState.DEGRADED)
                for p, d_type in node_def.dependencies.items()
                if d_type in (DependencyType.SOFT, DependencyType.OPTIONAL) and p in prior_results
            )
            state = ExecutionState.DEGRADED if soft_degraded else ExecutionState.COMPLETED
            quality = "DEGRADED" if soft_degraded else "FRESH"

            result = ModelNodeResult(
                model_id=model_id,
                model_name=node_def.model_name,
                state=state,
                output=output_data,
                execution_time_ms=latency_ms,
                input_hash=input_hash,
                output_hash=output_hash,
                quality_state=quality,
                evidence_status=node_def.evidence_status,
                started_at=start_time,
                completed_at=completed_time,
            )
            self._persist_run(db, result)
            return result

        except Exception as exc:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            logger.error(f"Execution failed for model {model_id}: {exc}")
            result = ModelNodeResult(
                model_id=model_id,
                model_name=node_def.model_name,
                state=ExecutionState.FAILED,
                error_message=str(exc),
                execution_time_ms=latency_ms,
                input_hash=input_hash,
                output_hash="",
                quality_state="CRITICAL_ERROR",
                evidence_status=node_def.evidence_status,
                started_at=start_time,
                completed_at=datetime.datetime.now(datetime.timezone.utc),
            )
            self._persist_run(db, result)
            return result

    def _build_node_input(
        self,
        model_id: str,
        initial_inputs: Dict[str, Any],
        prior: Dict[str, ModelNodeResult],
    ) -> Dict[str, Any]:
        """Constructs appropriate scientific input vectors for each model node."""
        base = dict(initial_inputs.get(model_id, {}))

        if model_id == "M1":
            base.setdefault("station_id", initial_inputs.get("station_id", "STN_AUT_01"))
            base.setdefault("latitude", initial_inputs.get("latitude", 31.75))
            base.setdefault("longitude", initial_inputs.get("longitude", 77.20))
            base.setdefault("elevation_m", initial_inputs.get("elevation_m", 1050.0))
            base.setdefault("slope_deg", 28.0)
            base.setdefault("r_1h", initial_inputs.get("rainfall_intensity_mmh", 45.0))
            base.setdefault("rolling_intensity_mmh", initial_inputs.get("rainfall_intensity_mmh", 45.0))

        elif model_id == "M2":
            rain_1h = initial_inputs.get("rainfall_intensity_mmh", 55.0)
            if "M1" in prior and prior["M1"].output:
                rain_1h = prior["M1"].output.get("prediction", {}).get("intensity_mmh", rain_1h)
            base.setdefault("elevation", 1080.0)
            base.setdefault("slope", 12.0)
            base.setdefault("flow_accumulation", 1500.0)
            base.setdefault("dist_to_stream", 120.0)
            base.setdefault("land_cover", 2)
            base.setdefault("rainfall_1h", rain_1h)
            base.setdefault("rainfall_3h", rain_1h * 2.2)
            base.setdefault("rainfall_6h", rain_1h * 3.5)
            base.setdefault("rainfall_24h", rain_1h * 4.8)
            base.setdefault("antecedent_rain_3d", rain_1h * 5.5)
            base.setdefault("soil_moisture", 68.0)
            base.setdefault("river_level", initial_inputs.get("river_water_level_m", 5.2))
            base.setdefault("river_level_change_1h", 0.35)

        elif model_id == "M6":
            base.setdefault("elevation", 1100.0)
            base.setdefault("slope", 36.0)
            base.setdefault("aspect", 180.0)
            base.setdefault("curvature", 0.1)
            base.setdefault("lithology", 2)
            base.setdefault("dist_to_stream", 80.0)
            base.setdefault("land_cover", 1)

        elif model_id == "PWP_SSI":
            base.setdefault("slope_deg", 38.0)
            base.setdefault("pore_pressure_kpa", 45.0)
            base.setdefault("matric_suction_kpa", 2.0)

        elif model_id == "M7":
            susc_class = 2
            if "M6" in prior and prior["M6"].output:
                susc_class = prior["M6"].output.get("susceptibility_class", 2)
            rain_1h = initial_inputs.get("rainfall_intensity_mmh", 45.0)
            base.setdefault("susceptibility_class", susc_class)
            base.setdefault("slope", 38.0)
            base.setdefault("rain_1h", rain_1h)
            base.setdefault("rain_3d", rain_1h * 3.5)
            base.setdefault("soil_moisture", 72.0)

        elif model_id == "M8":
            base.setdefault("displacement_series_mm", [0.0, 1.2, 3.5, 7.8, 14.2])
            base.setdefault("time_interval_days", 12.0)

        elif model_id == "M10":
            rain_3h = initial_inputs.get("rainfall_intensity_mmh", 45.0) * 2.0
            base.setdefault("upstream_stage_m", initial_inputs.get("river_water_level_m", 4.2))
            base.setdefault("catchment_rainfall_3h_mm", rain_3h)

        elif model_id == "M11":
            stage = 4.5
            if "M10" in prior and prior["M10"].output:
                stage = prior["M10"].output.get("forecast_stage_m", stage)
            base.setdefault("stage_m", stage)
            base.setdefault("discharge_m3s", 450.0)
            base.setdefault("manning_n", 0.045)
            base.setdefault("channel_slope", 0.015)

        elif model_id == "M12":
            base.setdefault("dam_location", initial_inputs.get("location_name", "Larji_Sainj_Confluence"))
            base.setdefault("dam_height_m", initial_inputs.get("dam_height_m", 35.0))
            base.setdefault("impounded_volume_m3", initial_inputs.get("impounded_volume_m3", 8_500_000.0))
            base.setdefault("normal_river_discharge_m3s", 350.0)
            base.setdefault("trigger_type", "LANDSLIDE_DAM")
            base.setdefault("trigger_probability", 0.85)

        elif model_id == "M13":
            base.setdefault("settlement_id", "V_PANDOH")
            base.setdefault("flood_prob", 0.88)
            base.setdefault("flood_depth_m", 2.5)
            base.setdefault("landslide_prob", 0.45)
            base.setdefault("debris_flow_prob", 0.30)

        elif model_id == "M14":
            base.setdefault("asset_id", "A_NH3_AUT_TUNNEL")
            base.setdefault("flood_depth_m", 2.5)
            base.setdefault("flow_velocity_ms", 4.0)
            base.setdefault("debris_impact_flag", True)
            base.setdefault("inundation_duration_hours", 6.0)

        elif model_id == "M15":
            base.setdefault("max_flood_risk", 0.20)
            base.setdefault("max_landslide_risk", 0.20)
            base.setdefault("min_elevation_m", 1200.0)

        elif model_id == "M16":
            base.setdefault("origin_node", "V_BHUNTAR")
            base.setdefault("destination_node", "S_KULLU_COLLEGE")
            base.setdefault("simulate_nh3_closure", True)

        elif model_id == "M19":
            peak_q = 2800.0
            if "M12" in prior and prior["M12"].output:
                peak_q = prior["M12"].output.get("prediction", {}).get("peak_outflow_discharge_m3s", peak_q)
            base.setdefault("distance_km", 8.0)
            base.setdefault("peak_discharge_m3s", peak_q)

        elif model_id == "M17":
            arrival_mins = 25.0
            if "M19" in prior and prior["M19"].output:
                arrival_mins = prior["M19"].output.get("p50_minutes", arrival_mins)
            base.setdefault("reach_or_settlement_id", "AUT_PANDOH_CORRIDOR")
            base.setdefault("rainfall_intensity_mmh", initial_inputs.get("rainfall_intensity_mmh", 45.0))
            base.setdefault("flood_probability", 0.88)
            base.setdefault("river_water_level_m", 6.5)
            base.setdefault("warning_level_m", 5.0)
            base.setdefault("danger_level_m", 7.0)
            base.setdefault("hfl_m", 9.5)
            base.setdefault("flood_depth_m", 2.2)
            base.setdefault("flood_arrival_time_min", arrival_mins)
            base.setdefault("at_risk_population", 3500)

        elif model_id == "M18":
            p_raw = 0.85
            if "M17" in prior and prior["M17"].output:
                p_raw = prior["M17"].output.get("escalation_level", 2) * 0.4
            base.setdefault("uncalibrated_probability", min(0.99, max(0.01, p_raw)))
            base.setdefault("hazard_type", "FLASH_FLOOD")

        return base

    def _persist_run(self, db: Session, res: ModelNodeResult) -> None:
        """Saves model execution record to database."""
        try:
            record = ModelRunModel(
                id=str(uuid.uuid4()),
                model_id=res.model_id,
                model_name=res.model_name,
                model_version="3.3.0",
                artifact_hash=res.output_hash or None,
                evidence_status=res.evidence_status,
                started_at=res.started_at,
                completed_at=res.completed_at,
                execution_time_ms=res.execution_time_ms,
                input_hash=res.input_hash,
                output_hash=res.output_hash,
                output_summary=str(res.output)[:500] if res.output else None,
                status=res.state.value,
                quality_state=res.quality_state,
                error_message=res.error_message,
            )
            db.add(record)
            db.commit()
        except Exception as exc:
            logger.warning(f"Could not persist model run for {res.model_id}: {exc}")
            db.rollback()


model_orchestrator = ModelOrchestrator()
