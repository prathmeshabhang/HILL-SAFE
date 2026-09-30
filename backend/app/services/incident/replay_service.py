"""
backend/app/services/incident/replay_service.py
===============================================
Historical Disaster Scenario Replay Service for FLOODY SHIELD.
Reconstructs historical events (e.g. July 2023 Beas Flood, 2021 flash floods)
through the full data-to-decision pipeline without broadcasting real external alerts.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.database.models.incident import IncidentModel
from backend.app.database.models.audit import AuditLogModel
from backend.app.orchestration.engine import model_orchestrator
from backend.app.services.risk.engine import unified_risk_engine

logger = get_logger("floody.incident.replay")


class HistoricalReplayService:
    def __init__(self):
        self.orchestrator = model_orchestrator
        self.risk_engine = unified_risk_engine

    def replay_scenario(
        self,
        db: Session,
        scenario_name: str = "July_2023_Upper_Beas_Compound_Flood",
        rainfall_intensity_mmh: float = 85.0,
        dam_height_m: float = 40.0,
        impounded_volume_m3: float = 12_000_000.0,
        river_water_level_m: float = 8.2,
    ) -> Dict[str, Any]:
        """
        Executes complete multi-hazard timeline replay.
        Marks all output artifacts as REPLAY / EXERCISE to ensure zero false public alarms.
        """
        replay_id = f"REPLAY-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Commencing historical disaster replay {replay_id}: {scenario_name}")

        # 1. Create Incident record marked EXERCISE
        incident = IncidentModel(
            id=replay_id,
            incident_type="HISTORICAL_REPLAY_SIMULATION",
            severity_level="CRITICAL",
            trigger_source="HISTORICAL_REPLAY_ARCHIVE",
            trigger_location=f"Upper Beas Corridor ({scenario_name})",
            latitude=31.85,
            longitude=77.15,
            dam_height_m=dam_height_m,
            impounded_volume_m3=impounded_volume_m3,
            rainfall_rate_mmh=rainfall_intensity_mmh,
            status="EXERCISE",
            summary=f"Historical exercise simulation of {scenario_name}. Mode: REPLAY.",
        )
        db.add(incident)
        db.commit()

        # 2. Execute full model orchestrator DAG
        inputs = {
            "rainfall_intensity_mmh": rainfall_intensity_mmh,
            "river_water_level_m": river_water_level_m,
            "dam_height_m": dam_height_m,
            "impounded_volume_m3": impounded_volume_m3,
            "location_name": scenario_name,
            "mode": "REPLAY",
        }
        model_results = self.orchestrator.execute_pipeline(db, inputs)

        # 3. Synthesize unified RiskState explicitly marked as REPLAY
        risk_state = self.risk_engine.synthesize_risk_state(
            db=db,
            incident_id=replay_id,
            location_name=scenario_name,
            initial_observations=inputs,
            orchestrator_results=model_results,
            data_mode="REPLAY",
        )

        # 4. Audit Trail Entry
        audit_entry = AuditLogModel(
            id=str(uuid.uuid4()),
            action="HISTORICAL_REPLAY_COMPLETED",
            actor_id="OPERATIONAL_TRAINING_SYSTEM",
            actor_role="SIMULATION_ENGINE",
            target_entity_type="Incident",
            target_entity_id=replay_id,
            changes=f"Replayed {scenario_name}. Status EXERCISE. Models evaluated: {len(model_results)}.",
        )
        db.add(audit_entry)
        db.commit()

        logger.info(f"Historical replay {replay_id} finished. Overall risk: {risk_state['overall_risk_level']}")

        return {
            "replay_id": replay_id,
            "scenario_name": scenario_name,
            "mode": "REPLAY",
            "statutory_safety_notice": "THIS IS A HISTORICAL SIMULATION REPLAY. NO PUBLIC ALERTS WERE ISSUED.",
            "incident": incident.to_dict(),
            "models_evaluated": {k: v.state.value for k, v in model_results.items()},
            "risk_state": risk_state,
        }


replay_service = HistoricalReplayService()
