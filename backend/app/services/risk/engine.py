"""
backend/app/services/risk/engine.py
===================================
Unified Multi-Hazard Risk State Engine for FLOODY SHIELD v3.3.
Synthesizes observations, physics models, ML predictions, and decision derivatives
into an authoritative, traceable, database-persisted RiskState.
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Dict, Optional
import uuid
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.core.provenance import (
    DataMode,
    OPERATIONAL_MODES,
    NON_OPERATIONAL_MODES,
    classify_provenance_mode,
    is_operational_provenance,
    normalize_provenance,
)
from backend.app.database.models.risk import RiskStateModel
from backend.app.orchestration.state import ModelNodeResult

logger = get_logger("floody.risk.engine")


class UnifiedRiskEngine:
    """
    Synthesizes multi-model pipeline outputs into a unified RiskState.
    Strictly categorizes data provenance as OBSERVED, PREDICTED, MODELLED, or DERIVED.
    Enforces the Live Data Safety Boundary: non-operational inputs are quarantined
    and can never silently produce an OPERATIONAL risk state.
    """

    VERSION = "3.4.0"
    FUSION_METHOD = "CONSERVATIVE_UPPER_BOUND_MAX_CONSEQUENCE"

    def synthesize_risk_state(
        self,
        db: Session,
        incident_id: Optional[str],
        location_name: str,
        initial_observations: Dict[str, Any],
        orchestrator_results: Dict[str, ModelNodeResult],
        data_mode: Optional[str] = None,
        auto_run_analytics: bool = True,
    ) -> Dict[str, Any]:
        """
        Combines model results into structured risk state and persists to database.
        Applies conservative non-operational tainting: if any input is synthetic,
        simulated, replay, proxy, or test, composite state is marked non-operational.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc)

        # Optional Phase 04B decoupled analytics auto-run
        if auto_run_analytics:
            from backend.app.services.analysis.orchestrator import decoupled_analysis_coordinator
            if "FLOOD_PHYSICS_ROUTING" not in orchestrator_results and "LANDSLIDE_AI_TRIGGER" not in orchestrator_results:
                analysis_results = decoupled_analysis_coordinator.execute_all(initial_observations)
                new_nodes = decoupled_analysis_coordinator.convert_to_orchestrator_nodes(analysis_results)
                for k, v in new_nodes.items():
                    if k not in orchestrator_results:
                        orchestrator_results[k] = v

        # 1. Extract and categorize values
        observed = {
            "rainfall_rate_mmh": initial_observations.get("rainfall_intensity_mmh", 0.0),
            "river_water_level_m": initial_observations.get("river_water_level_m", 0.0),
            "location_name": location_name,
            "category": "OBSERVED",
        }

        # Flood Branch
        m1_out = orchestrator_results.get("M1", ModelNodeResult(model_id="M1", model_name="")).output
        m2_out = orchestrator_results.get("M2", ModelNodeResult(model_id="M2", model_name="")).output
        m4_out = orchestrator_results.get("M4", ModelNodeResult(model_id="M4", model_name="")).output
        flood_physics_node = orchestrator_results.get("FLOOD_PHYSICS_ROUTING")

        flood_hazard = {
            "m1_nowcast_intensity_mmh": {
                "value": m1_out.get("prediction", {}).get("intensity_mmh"),
                "category": "PREDICTED",
            },
            "m2_flood_probability": {
                "value": m2_out.get("flood_probability", 0.0),
                "risk_tier": m2_out.get("risk_tier", "LOW"),
                "category": "PREDICTED",
            },
            "m4_satellite_segmentation": {
                "detected": m4_out.get("flood_inundation_detected", False),
                "category": "OBSERVED_REMOTE_SENSING",
            },
        }

        # Phase 04B: Integrate SCS-CN Direct Runoff & Terrain Routing
        if flood_physics_node and flood_physics_node.output:
            scs_out = flood_physics_node.output
            flood_hazard["scs_cn_routing"] = {
                "direct_runoff_depth_mm": scs_out.get("scs_cn", {}).get("direct_runoff_depth_mm"),
                "peak_discharge_m3s": scs_out.get("routing", {}).get("peak_discharge_m3s"),
                "time_to_peak_hours": scs_out.get("routing", {}).get("time_to_peak_hours"),
                "runoff_volume_mcm": scs_out.get("routing", {}).get("runoff_volume_mcm"),
                "derived_hazard_tier": scs_out.get("derived_hazard_tier"),
                "category": "MODELLED_PHYSICS",
            }

        # Landslide Branch
        m6_out = orchestrator_results.get("M6", ModelNodeResult(model_id="M6", model_name="")).output
        pwp_out = orchestrator_results.get("PWP_SSI", ModelNodeResult(model_id="PWP_SSI", model_name="")).output
        m7_out = orchestrator_results.get("M7", ModelNodeResult(model_id="M7", model_name="")).output
        m8_out = orchestrator_results.get("M8", ModelNodeResult(model_id="M8", model_name="")).output
        landslide_ai_node = orchestrator_results.get("LANDSLIDE_AI_TRIGGER")

        landslide_hazard = {
            "m6_susceptibility_class": {
                "value": m6_out.get("susceptibility_class", 1),
                "tier": m6_out.get("susceptibility_tier", "MODERATE"),
                "category": "MODELLED_STATIC",
            },
            "pwp_factor_of_safety": {
                "value": pwp_out.get("factor_of_safety", 1.5),
                "is_unstable": pwp_out.get("is_unstable", False),
                "category": "MODELLED_PHYSICS",
            },
            "m7_dynamic_trigger": {
                "triggered": m7_out.get("trigger_predicted", False),
                "category": "PREDICTED",
            },
            "m8_kinematic_deformation": {
                "velocity_mm_yr": m8_out.get("output", {}).get("velocity_mm_yr"),
                "category": "MODELLED_KINEMATICS",
            },
        }

        # Phase 04B: Integrate Landslide Intelligence AI Prediction
        if landslide_ai_node and landslide_ai_node.output:
            ai_out = landslide_ai_node.output
            landslide_hazard["landslide_ai_trigger"] = {
                "trigger_probability": ai_out.get("trigger_probability"),
                "trigger_predicted": ai_out.get("trigger_predicted"),
                "hazard_tier": ai_out.get("hazard_tier"),
                "geotech_alert": ai_out.get("geotech_alert", False),
                "category": "PREDICTED_AI",
            }

        # River & Cascade Branch
        m10_out = orchestrator_results.get("M10", ModelNodeResult(model_id="M10", model_name="")).output
        m11_out = orchestrator_results.get("M11", ModelNodeResult(model_id="M11", model_name="")).output
        m12_out = orchestrator_results.get("M12", ModelNodeResult(model_id="M12", model_name="")).output
        m19_out = orchestrator_results.get("M19", ModelNodeResult(model_id="M19", model_name="")).output

        cascade_hazard = {
            "m10_forecast_stage_m": {
                "value": m10_out.get("forecast_stage_m"),
                "category": "PREDICTED",
            },
            "m11_flood_depth_m": {
                "value": m11_out.get("inundation_depth_m"),
                "category": "MODELLED_HYDRODYNAMIC",
            },
            "m12_peak_breach_discharge_m3s": {
                "value": m12_out.get("prediction", {}).get("peak_outflow_discharge_m3s"),
                "category": "MODELLED_EMPIRICAL_PHYSICS",
            },
            "m19_time_to_impact_mins": {
                "value": m19_out.get("p50_minutes"),
                "category": "MODELLED_CELERITY",
            },
        }

        # Impact Branch
        m13_out = orchestrator_results.get("M13", ModelNodeResult(model_id="M13", model_name="")).output
        m14_out = orchestrator_results.get("M14", ModelNodeResult(model_id="M14", model_name="")).output

        population_impact = {
            "vulnerability": m13_out,
            "category": "MODELLED_SOCIAL_GIS",
        }
        infrastructure_impact = {
            "infrastructure_loss": m14_out,
            "category": "MODELLED_HAZUS_ENGINEERING",
        }

        # Decision Derivatives
        m17_out = orchestrator_results.get("M17", ModelNodeResult(model_id="M17", model_name="")).output
        m18_out = orchestrator_results.get("M18", ModelNodeResult(model_id="M18", model_name="")).output

        # Multi-Hazard Fusion Formula: Conservative Upper-Bound
        # Maximum of normalized component risks
        p_flood = float(m2_out.get("flood_probability") or 0.2)
        if flood_physics_node and flood_physics_node.output:
            q_peak = float(flood_physics_node.output.get("routing", {}).get("peak_discharge_m3s") or 0.0)
            if q_peak > 2500.0:
                p_flood = max(p_flood, 0.85)
            elif q_peak > 1500.0:
                p_flood = max(p_flood, 0.65)
            elif q_peak > 600.0:
                p_flood = max(p_flood, 0.40)

        p_slide = 0.8 if m7_out.get("trigger_predicted") else (0.4 if m6_out.get("susceptibility_class", 1) >= 2 else 0.15)
        if landslide_ai_node and landslide_ai_node.output:
            ai_prob = float(landslide_ai_node.output.get("trigger_probability") or 0.0)
            p_slide = max(p_slide, ai_prob)

        p_cascade = 0.85 if m12_out.get("prediction", {}).get("peak_outflow_discharge_m3s", 0) > 1000.0 else 0.25

        max_risk_score = max(p_flood, p_slide, p_cascade)

        if max_risk_score >= 0.75:
            overall_risk_level = "CRITICAL"
        elif max_risk_score >= 0.50:
            overall_risk_level = "HIGH"
        elif max_risk_score >= 0.25:
            overall_risk_level = "MODERATE"
        else:
            overall_risk_level = "LOW"

        confidence_score = float(m18_out.get("calibrated_probability") or (1.0 - m18_out.get("expected_brier_error", 0.15)))

        # Quality State Propagation: if any core model was degraded, mark overall risk state DEGRADED
        any_degraded = any(r.state == "DEGRADED" for r in orchestrator_results.values())
        any_failed = any(r.state == "FAILED" for r in orchestrator_results.values())
        if any_failed:
            quality_state = "DEGRADED"
            model_health_state = "DEGRADED_FAILURES_DETECTED"
            confidence_state = "LOW_CONFIDENCE"
        elif any_degraded:
            quality_state = "DEGRADED"
            model_health_state = "DEGRADED"
            confidence_state = "MODERATE_CONFIDENCE"
        else:
            quality_state = "FRESH"
            model_health_state = "HEALTHY"
            confidence_state = "HIGH_CONFIDENCE" if confidence_score >= 0.75 else "MODERATE_CONFIDENCE"

        # Provenance & Data Mode Evaluation
        detected_provenances = []
        if initial_observations.get("provenances"):
            detected_provenances.extend(initial_observations.get("provenances"))
        elif initial_observations.get("observation_provenances"):
            detected_provenances.extend(initial_observations.get("observation_provenances"))

        for field_name in ("provenance", "data_mode", "mode", "rainfall_provenance", "river_provenance"):
            val = initial_observations.get(field_name)
            if val:
                detected_provenances.append(str(val))

        for r in orchestrator_results.values():
            if isinstance(r.output, dict):
                p = r.output.get("provenance") or r.output.get("data_mode")
                if p:
                    detected_provenances.append(str(p))
                if r.output.get("is_synthetic"):
                    detected_provenances.append("SYNTHETIC")
                if r.output.get("is_proxy"):
                    detected_provenances.append("PROXY_DATA")

        if data_mode:
            norm_explicit = normalize_provenance(data_mode)
            if norm_explicit == DataMode.OPERATIONAL.value and detected_provenances:
                comp_mode, is_op = classify_provenance_mode(detected_provenances)
                if not is_op:
                    final_data_mode = DataMode.MIXED.value if any(p in OPERATIONAL_MODES for p in detected_provenances) else comp_mode
                    is_operational = False
                else:
                    final_data_mode = DataMode.OPERATIONAL.value
                    is_operational = True
            else:
                final_data_mode = norm_explicit
                is_operational = norm_explicit in OPERATIONAL_MODES
        elif detected_provenances:
            final_data_mode, is_operational = classify_provenance_mode(detected_provenances)
        else:
            final_data_mode = DataMode.SIMULATION.value
            is_operational = False

        provenance = {
            "engine": "UnifiedRiskEngine",
            "version": self.VERSION,
            "fusion_method": self.FUSION_METHOD,
            "formula": "overall_risk = max(P_flood, P_landslide, P_cascade)",
            "models_evaluated": list(orchestrator_results.keys()),
            "timestamp": timestamp.isoformat(),
            "confidence_state": confidence_state,
            "model_health_state": model_health_state,
            "data_mode": final_data_mode,
            "is_operational": is_operational,
            "taint_rule": "CONSERVATIVE_NON_OPERATIONAL_TAINTING",
            "input_provenances": detected_provenances,
        }

        # 2. Persist RiskState to Database
        risk_record = RiskStateModel(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            timestamp=timestamp,
            location_name=location_name,
            latitude=initial_observations.get("latitude", 31.75),
            longitude=initial_observations.get("longitude", 77.20),
            flood_hazard_json=json.dumps(flood_hazard, default=str),
            landslide_hazard_json=json.dumps(landslide_hazard, default=str),
            cascade_hazard_json=json.dumps(cascade_hazard, default=str),
            population_impact_json=json.dumps(population_impact, default=str),
            infrastructure_impact_json=json.dumps(infrastructure_impact, default=str),
            overall_risk_level=overall_risk_level,
            confidence_score=confidence_score,
            quality_state=quality_state,
            provenance_json=json.dumps(provenance, default=str),
        )
        db.add(risk_record)
        db.commit()

        logger.info(
            f"Synthesized and persisted RiskState {risk_record.id}: {overall_risk_level} "
            f"(mode={final_data_mode}, is_operational={is_operational}, confidence={confidence_score:.2f})"
        )

        return {
            "risk_state_id": risk_record.id,
            "incident_id": incident_id,
            "timestamp": timestamp.isoformat(),
            "location_name": location_name,
            "overall_risk_level": overall_risk_level,
            "max_risk_score": max_risk_score,
            "confidence_score": confidence_score,
            "confidence_state": confidence_state,
            "model_health_state": model_health_state,
            "quality_state": quality_state,
            "data_mode": final_data_mode,
            "is_operational": is_operational,
            "observed": observed,
            "hazards": {
                "flood": flood_hazard,
                "landslide": landslide_hazard,
                "cascade": cascade_hazard,
            },
            "impact": {
                "population": population_impact,
                "infrastructure": infrastructure_impact,
            },
            "decision_support": {
                "warning_action": m17_out.get("warning_action"),
                "escalation_level": m17_out.get("escalation_level"),
                "calibrated_probability": m18_out.get("calibrated_probability"),
            },
            "provenance": provenance,
        }

    def validate_operational_eligibility(self, observations: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Quarantine Gate: Validates that observations are 100% OPERATIONAL before entering operational risk pipeline.
        Returns (is_eligible, reason).
        """
        for obs in observations:
            prov = obs.get("provenance") or obs.get("data_mode") or "SIMULATED"
            if not is_operational_provenance(prov):
                return (
                    False,
                    f"Quarantine rejection: Observation from station '{obs.get('station_id', 'UNKNOWN')}' has non-operational provenance '{prov}'.",
                )
        return True, "All observations verified operational."

    def get_current_risk(self, db: Session, location_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        query = db.query(RiskStateModel)
        if location_name:
            query = query.filter(RiskStateModel.location_name == location_name)
        record = query.order_by(RiskStateModel.timestamp.desc()).first()
        return record.to_dict() if record else None

    def get_risk_history(
        self,
        db: Session,
        incident_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = db.query(RiskStateModel)
        if incident_id:
            query = query.filter(RiskStateModel.incident_id == incident_id)
        records = query.order_by(RiskStateModel.timestamp.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in records]

    def get_incident_risk(self, db: Session, incident_id: str) -> Optional[Dict[str, Any]]:
        record = (
            db.query(RiskStateModel)
            .filter(RiskStateModel.incident_id == incident_id)
            .order_by(RiskStateModel.timestamp.desc())
            .first()
        )
        return record.to_dict() if record else None


unified_risk_engine = UnifiedRiskEngine()
