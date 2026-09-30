"""
backend/app/inference/adapters/decision_adapters.py
===================================================
Model Adapters for Decision, Impact, Evacuation, and Post-Disaster Models (M13, M14, M15, M16, M17, M18, M19, M20).
"""

from __future__ import annotations

from typing import Any, Dict

from backend.app.inference.base import ModelAdapter


class M13VulnerabilityAdapter(ModelAdapter):
    model_id = "M13"
    model_name = "Settlement & Population Vulnerability Exposure"
    version = "1.0.0"
    evidence_status = "REAL_GIS_RULES"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.decision.m13_vulnerability.infer import predict_vulnerability_exposure
        from ml.decision.m13_vulnerability.schema import M13ExposureInput
        inp = M13ExposureInput(
            settlement_id=input_data.get("settlement_id", "V_BHUNTAR"),
            month=int(input_data.get("month", 7)),
            flood_prob=float(input_data.get("flood_prob", 0.5)),
            flood_depth_m=float(input_data.get("flood_depth_m", 1.0)),
            landslide_prob=float(input_data.get("landslide_prob", 0.3)),
            debris_flow_prob=float(input_data.get("debris_flow_prob", 0.2)),
            river_distance_m=float(input_data.get("river_distance_m", 150.0)),
        )
        res = predict_vulnerability_exposure(inp)
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)


class M14InfrastructureAdapter(ModelAdapter):
    model_id = "M14"
    model_name = "Infrastructure Damage & Economic Loss"
    version = "1.0.0"
    evidence_status = "REAL_GIS_RULES"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.decision.m14_infrastructure_loss.infer import predict_infrastructure_loss
        from ml.decision.m14_infrastructure_loss.schema import M14DamageInput
        inp = M14DamageInput(
            asset_id=input_data.get("asset_id", "A_NH3_AUT_TUNNEL"),
            flood_depth_m=float(input_data.get("flood_depth_m", 1.5)),
            flow_velocity_ms=float(input_data.get("flow_velocity_ms", 2.0)),
            debris_impact_flag=bool(input_data.get("debris_impact_flag", False)),
            inundation_duration_hours=float(input_data.get("inundation_duration_hours", 3.0)),
        )
        res = predict_infrastructure_loss(inp)
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)


class M15SafeZoneAdapter(ModelAdapter):
    model_id = "M15"
    model_name = "Multi-Criteria Safe-Zone & Shelter Selection"
    version = "1.0.0"
    evidence_status = "REAL_GIS_RULES"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.features.beas_decision_infrastructure import build_upper_beas_infrastructure_graph
        from ml.features.decision_engines import DecisionIntelligenceEngine
        _, _, registered_shelters = build_upper_beas_infrastructure_graph()
        engine = DecisionIntelligenceEngine()
        evacuation_demand = int(input_data.get("evacuation_demand", 250))
        res = engine.select_safe_shelter(
            shelters=registered_shelters,
            evacuation_demand=evacuation_demand,
        )
        return res or {"status": "NO_FEASIBLE_SHELTER_WITH_CAPACITY"}


class M16EvacuationRoutingAdapter(ModelAdapter):
    model_id = "M16"
    model_name = "Risk-Weighted Dijkstra Safe Evacuation Routing"
    version = "1.0.0"
    evidence_status = "REAL_GIS_RULES"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.features.beas_decision_infrastructure import build_upper_beas_infrastructure_graph
        from ml.features.decision_engines import DecisionIntelligenceEngine
        graph_network, _, _ = build_upper_beas_infrastructure_graph()
        g = graph_network.copy()

        if input_data.get("simulate_nh3_closure", True):
            for u, v, d in g.edges(data=True):
                if "NH3" in str(u) or "NH3" in str(v) or "NH3" in d.get("road_name", ""):
                    d["is_blocked"] = True

        engine = DecisionIntelligenceEngine()
        route = engine.find_safest_evacuation_route(
            graph=g,
            origin_node=input_data.get("origin_node", "V_BHUNTAR"),
            destination_node=input_data.get("destination_node", "S_KULLU_COLLEGE"),
        )
        return route


class M17WarningGatingAdapter(ModelAdapter):
    model_id = "M17"
    model_name = "Multi-Threshold Early Warning Gating"
    version = "1.0.0"
    evidence_status = "ML_PROTOTYPE"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.decision.m17_warning_gating.infer import issue_early_warning_and_evacuation
        from ml.decision.m17_warning_gating.schema import M17WarningInput
        inp = M17WarningInput(
            reach_or_settlement_id=input_data.get("reach_or_settlement_id", "SETTLEMENT_01"),
            rainfall_intensity_mmh=float(input_data.get("rainfall_intensity_mmh", 45.0)),
            rainfall_3h_mm=float(input_data.get("rainfall_3h_mm", 75.0)),
            flood_probability=float(input_data.get("flood_probability", 0.65)),
            river_water_level_m=float(input_data.get("river_water_level_m", 5.5)),
            warning_level_m=float(input_data.get("warning_level_m", 5.0)),
            danger_level_m=float(input_data.get("danger_level_m", 7.0)),
            hfl_m=float(input_data.get("hfl_m", 9.5)),
            flood_depth_m=float(input_data.get("flood_depth_m", 0.8)),
            flood_arrival_time_min=float(input_data.get("flood_arrival_time_min", 60.0)),
            landslide_probability=float(input_data.get("landslide_probability", 0.3)),
            at_risk_population=int(input_data.get("at_risk_population", 1500)),
        )
        res = issue_early_warning_and_evacuation(inp)
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)


class M18CalibrationAdapter(ModelAdapter):
    model_id = "M18"
    model_name = "Isotonic & Platt Risk Calibration"
    version = "1.0.0"
    evidence_status = "SYNTHETIC_CALIBRATION_PROTOTYPE"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.calibration.m18_calibration.infer import calibrate
        from ml.calibration.m18_calibration.schema import M18CalibrationInput
        inp = M18CalibrationInput(
            source_model=input_data.get("source_model", "M2_FLOOD_RISK"),
            raw_probability=float(input_data.get("raw_probability", 0.70)),
            data_quality=float(input_data.get("data_quality", 0.90)),
        )
        res = calibrate(inp)
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)


class M19TimeToImpactAdapter(ModelAdapter):
    model_id = "M19"
    model_name = "Hydrodynamic Time-to-Impact Forecaster"
    version = "1.0.0"
    evidence_status = "PHYSICS_POC"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.impact.m19_time_to_impact.infer import predict
        from ml.impact.m19_time_to_impact.schema import M19TimeToImpactInput, ImpactType
        inp = M19TimeToImpactInput(
            impact_type=ImpactType.FLOOD_INUNDATION,
            distance_km=float(input_data.get("distance_km", 10.0)),
            peak_discharge_m3s=float(input_data.get("peak_discharge_m3s", 1200.0)),
            data_quality=float(input_data.get("data_quality", 0.85)),
        )
        res = predict(inp)
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)


class M20DamageAssessmentAdapter(ModelAdapter):
    model_id = "M20"
    model_name = "Copernicus EMS 4-Tier Post-Disaster Damage Assessment"
    version = "1.0.0"
    evidence_status = "CHANGE_DETECTION_ONLY"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.assessment.m20_damage_assessment.infer import assess
        from ml.assessment.m20_damage_assessment.schema import (
            M20DamageInput,
            SatelliteObservation,
        )
        sat = SatelliteObservation(
            ndvi_pre=float(input_data.get("ndvi_pre", 0.55)),
            ndvi_post=float(input_data.get("ndvi_post", 0.25)),
            ndwi_pre=float(input_data.get("ndwi_pre", -0.10)),
            ndwi_post=float(input_data.get("ndwi_post", 0.40)),
            sar_coherence_pre=float(input_data.get("sar_coherence_pre", 0.80)),
            sar_coherence_post=float(input_data.get("sar_coherence_post", 0.35)),
        )
        inp = M20DamageInput(
            asset_id=input_data.get("asset_id", "A_NH3_AUT_TUNNEL"),
            hazard_type=input_data.get("hazard_type", "FLOOD"),
            satellite=sat,
            flood_depth_m=float(input_data.get("flood_depth_m", 1.5)),
            asset_category=input_data.get("asset_category", "road"),
            data_quality=float(input_data.get("data_quality", 0.90)),
        )
        res = assess(inp)
        return res.to_dict() if hasattr(res, "to_dict") else vars(res)
