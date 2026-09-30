"""
backend/app/decision/pipeline.py
================================
End-to-End Multi-Hazard Decision Pipeline for FLOODY SHIELD.
Orchestrates observations, model inference, impact calculation, evacuation routing,
and drafts statutory NDMA CAP v1.2 alerts awaiting Commander sign-off.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.database.models.incident import IncidentModel
from backend.app.database.models.alert import AlertDispatchModel
from backend.app.database.models.evacuation import EvacuationRouteModel
from backend.app.database.models.model_run import ModelRunModel
from backend.app.inference.adapters import get_model_adapter

logger = get_logger("floody.decision.pipeline")


class HazardDecisionPipeline:
    """
    Coordinates the full hazard chain from telemetry input to decision support.
    """

    def run_pipeline(
        self,
        db: Session,
        incident_id: Optional[str] = None,
        location_name: str = "Larji_Sainj_Confluence",
        rainfall_intensity_mmh: float = 65.0,
        dam_height_m: float = 35.0,
        impounded_volume_m3: float = 8_500_000.0,
        simulate_nh3_closure: bool = True,
        data_mode: str = "SIMULATION",
    ) -> Dict[str, Any]:
        inc_id = incident_id or f"INC-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Initiating decision pipeline for incident {inc_id} at {location_name} (mode={data_mode})")

        # 1. Register or update Incident in DB
        incident = db.query(IncidentModel).filter_by(id=inc_id).first()
        if not incident:
            inc_status = "ACTIVE" if data_mode.upper() == "OPERATIONAL" else "EXERCISE"
            incident = IncidentModel(
                id=inc_id,
                incident_type="NATURAL_DAM_BREACH",
                severity_level="CRITICAL",
                trigger_source="SATELLITE_SYNTHESIS",
                trigger_location=location_name,
                dam_height_m=dam_height_m,
                impounded_volume_m3=impounded_volume_m3,
                rainfall_rate_mmh=rainfall_intensity_mmh,
                status=inc_status,
                summary=f"Automated pipeline evaluation for compound breach at {location_name}. Mode: {data_mode}.",
            )
            db.add(incident)
            db.commit()

        # 2. Step 3: Predictive Hazard Inference (M1, M2, M12, PWP)
        m1_res = get_model_adapter("M1").predict({
            "station_id": "STN_AUT_01",
            "latitude": 31.75,
            "longitude": 77.20,
            "elevation_m": 1050.0,
            "slope_deg": 28.0,
            "r_1h": rainfall_intensity_mmh,
            "rolling_intensity_mmh": rainfall_intensity_mmh,
        })
        self._record_run(db, m1_res)

        m12_res = get_model_adapter("M12").predict({
            "dam_location": location_name,
            "dam_height_m": dam_height_m,
            "impounded_volume_m3": impounded_volume_m3,
            "normal_river_discharge_m3s": 350.0,
            "trigger_type": "LANDSLIDE_DAM",
            "trigger_probability": 0.85,
        })
        self._record_run(db, m12_res)

        pwp_res = get_model_adapter("PWP_SSI").predict({
            "slope_deg": 38.0,
            "pore_pressure_kpa": 45.0,
            "matric_suction_kpa": 2.0,
        })
        self._record_run(db, pwp_res)

        # 3. Step 4: Impact Assessment (M13, M14)
        m13_res = get_model_adapter("M13").predict({
            "settlement_id": "V_PANDOH",
            "flood_prob": 0.90,
            "flood_depth_m": 2.5,
            "landslide_prob": 0.45,
            "debris_flow_prob": 0.30,
        })
        self._record_run(db, m13_res)

        m14_res = get_model_adapter("M14").predict({
            "asset_id": "A_NH3_AUT_TUNNEL",
            "flood_depth_m": 2.5,
            "flow_velocity_ms": 4.0,
            "debris_impact_flag": True,
            "inundation_duration_hours": 6.0,
        })
        self._record_run(db, m14_res)

        # 4. Step 5: Safe-Zone and Evacuation Routing (M15, M16, M19)
        m15_res = get_model_adapter("M15").predict({
            "max_flood_risk": 0.20,
            "max_landslide_risk": 0.20,
            "min_elevation_m": 1200.0,
        })
        self._record_run(db, m15_res)

        m16_res = get_model_adapter("M16").predict({
            "origin_node": "V_BHUNTAR",
            "destination_node": "S_KULLU_COLLEGE",
            "simulate_nh3_closure": simulate_nh3_closure,
        })
        self._record_run(db, m16_res)

        # Persist Evacuation Route
        route_info = m16_res["output"]
        evac_record = EvacuationRouteModel(
            id=str(uuid.uuid4()),
            incident_id=inc_id,
            origin_name="Bhuntar Settlement",
            destination_safe_zone="Kullu College Ground",
            distance_km=route_info.get("total_distance_km", 14.5),
            estimated_duration_min=45.0,
            clearance_status=route_info.get("route_status", "FOUND_SAFER_FEASIBLE"),
            route_geojson=str(route_info.get("path_nodes", [])),
        )
        db.add(evac_record)

        m19_res = get_model_adapter("M19").predict({
            "distance_km": 8.0,
            "peak_discharge_m3s": m12_res["output"].get("prediction", {}).get("peak_outflow_discharge_m3s", 2800.0),
        })
        self._record_run(db, m19_res)

        # 5. Step 6: Early Warning Gating & Calibration (M17, M18)
        m17_res = get_model_adapter("M17").predict({
            "reach_or_settlement_id": "AUT_PANDOH_CORRIDOR",
            "rainfall_intensity_mmh": rainfall_intensity_mmh,
            "flood_probability": 0.92,
            "river_water_level_m": 7.5,
            "warning_level_m": 5.0,
            "danger_level_m": 7.0,
            "hfl_m": 9.5,
            "flood_depth_m": 2.5,
            "flood_arrival_time_min": m19_res["output"].get("p50_minutes", 25.0),
            "at_risk_population": 4200,
        })
        self._record_run(db, m17_res)

        # 6. Step 7: Draft CAP Alert (Awaiting Human Commander Approval)
        if data_mode.upper() == "OPERATIONAL":
            cap_id = f"CAP-HPSDMA-{datetime.date.today().strftime('%Y%m%d')}-{inc_id[-4:]}"
        else:
            cap_id = f"CAP-{data_mode.upper()}-HPSDMA-{datetime.date.today().strftime('%Y%m%d')}-{inc_id[-4:]}"
        alert_draft = AlertDispatchModel(
            id=str(uuid.uuid4()),
            incident_id=inc_id,
            cap_identifier=cap_id,
            alert_type="Alert",
            severity="Extreme",
            urgency="Immediate",
            certainty="Observed",
            headline="FLASH FLOOD & LANDSLIDE DAM OUTBURST EVACUATION ADVISORY",
            description=(
                f"Model M12 predicts potential outburst flood along Beas river from {location_name}. "
                f"Peak estimated discharge: {m12_res['output'].get('prediction', {}).get('peak_outflow_discharge_m3s', 0):.0f} m3/s. "
                "Move to designated safe zones immediately."
            ),
            instruction="Avoid valley floor and NH-3 river reach. Follow Model M16 designated bypass evacuation route.",
            area_desc=f"Upper Beas Corridor from {location_name} downstream to Pandoh Dam",
            authorized_by="PENDING_COMMANDER_SIGN_OFF",
            status="PENDING_APPROVAL",
        )
        db.add(alert_draft)
        db.commit()

        logger.info(f"Pipeline complete for {inc_id}. Draft alert created: {cap_id} [PENDING_APPROVAL]")

        return {
            "incident_id": inc_id,
            "status": "AWAITING_COMMANDER_AUTHORIZATION",
            "draft_alert_id": alert_draft.id,
            "cap_identifier": cap_id,
            "hazard_summary": {
                "m1_rainfall_nowcast": m1_res["output"].get("prediction", {}),
                "m12_cascade_breach": m12_res["output"].get("prediction", {}),
                "pwp_slope_stability": pwp_res["output"],
            },
            "impact_summary": {
                "vulnerability": m13_res["output"],
                "infrastructure_loss": m14_res["output"],
            },
            "evacuation_support": {
                "safest_route": route_info,
                "time_to_impact_min": m19_res["output"].get("p50_minutes"),
            },
            "warning_gating": m17_res["output"],
        }

    def _record_run(self, db: Session, model_res: Dict[str, Any]) -> None:
        """Saves execution provenance to the ModelRun table."""
        try:
            run = ModelRunModel(
                id=str(uuid.uuid4()),
                model_id=model_res["model_id"],
                model_name=model_res["model_name"],
                execution_time_ms=model_res["execution_time_ms"],
                input_hash=model_res["input_hash"],
                output_summary=str(model_res["output"])[:500],
                status="SUCCESS",
            )
            db.add(run)
            db.commit()
        except Exception as exc:
            logger.warning(f"Could not record model run for {model_res.get('model_id')}: {exc}")
            db.rollback()


decision_pipeline = HazardDecisionPipeline()
