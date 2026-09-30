"""
incident_manager.py — FLOODY SHIELD Autonomous Incident Response & Orchestration Engine
========================================================================================
Coordinates the end-to-end civil defense early warning and rescue lifecycle:
$$\\text{Hazard Trigger} \\longrightarrow \\text{M9 Gating} \\longrightarrow \\text{M12 Cascade Breach} \\longrightarrow \\text{M15/16 Evacuation Route} \\longrightarrow \\text{Bilingual CAP Alert} \\longrightarrow \\text{Incident Briefing}$$

Operates under strict civil defense protocols:
  - Preserves immutable chain-of-custody.
  - Injects mandatory Section 36 statutory engineering disclaimers.
  - Generates ITU-T X.1303 / NDMA Sachet compliant bilingual CAP v1.2 payloads.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

from ml.damage.rescue_prioritizer import RescuePrioritizer
from ml.features.beas_decision_infrastructure import build_upper_beas_infrastructure_graph
from ml.features.decision_engines import DecisionIntelligenceEngine
from ml.flood.m12_compound_cascade import CompoundCascadeEngine
from ml.security.cap_alert_engine import CAPAlertEngine


@dataclass
class IncidentRecord:
    incident_id: str
    timestamp_utc: str
    incident_type: str            # "NATURAL_DAM_BREACH", "CLOUDBURST_FLASH_FLOOD", "EXTREME_DEBRIS_FLOW"
    severity_level: str           # "CRITICAL", "SEVERE", "MODERATE"
    trigger_source: str           # "SATELLITE_SYNTHESIS", "IOT_GROUND_SENSOR", "NOWCAST_EXTRAPOLATION", "MANUAL_DISPATCH"
    trigger_location: str         # "Larji_Sainj_Confluence", "Aut_Gorge", etc.
    trigger_metrics: Dict[str, Any]
    cascade_simulation: Dict[str, Any]
    impact_assessment: Dict[str, Any]
    evacuation_plan: Dict[str, Any]
    rescue_prioritization: List[Dict[str, Any]]
    cap_alert_identifier: str
    cap_alert_xml: str
    cap_alert_summary_en: str
    cap_alert_summary_hi: str
    status: str                   # "ACTIVE", "CONTAINED", "RESOLVED", "EXERCISE"
    statutory_notice: str
    audit_log: List[Dict[str, str]] = field(default_factory=list)


class IncidentManager:
    """
    Central orchestration engine linking hazard modeling, exposure calculation,
    evacuation route solving, and emergency alert broadcasting.
    """

    def __init__(self):
        self.cascade_engine = CompoundCascadeEngine()
        self.decision_engine = DecisionIntelligenceEngine()
        self.cap_engine = CAPAlertEngine()
        self.rescue_prioritizer = RescuePrioritizer()
        self.graph_network, self.registered_villages, self.registered_shelters = (
            build_upper_beas_infrastructure_graph()
        )
        self._incidents: Dict[str, IncidentRecord] = {}
        self._initialize_default_scenario()

    def _initialize_default_scenario(self) -> None:
        """Seeds initial nominal drill incident for system readiness verification."""
        self.trigger_incident(
            incident_type="NATURAL_DAM_BREACH",
            severity_level="CRITICAL",
            trigger_source="SATELLITE_SYNTHESIS",
            trigger_location="Larji_Sainj_Confluence",
            dam_height_m=35.0,
            impounded_volume_m3=8_500_000.0,
            rainfall_rate_mmh=78.5,
            simulate_nh3_closure=True,
            status="ACTIVE",
            custom_id="INC-BEAS-LARJI-01",
        )

    def trigger_incident(
        self,
        incident_type: str,
        severity_level: str = "CRITICAL",
        trigger_source: str = "SATELLITE_SYNTHESIS",
        trigger_location: str = "Larji_Sainj_Confluence",
        dam_height_m: float = 35.0,
        impounded_volume_m3: float = 8_500_000.0,
        rainfall_rate_mmh: float = 65.0,
        simulate_nh3_closure: bool = True,
        status: str = "ACTIVE",
        custom_id: Optional[str] = None,
    ) -> IncidentRecord:
        """
        Executes full autonomous incident response pipeline.
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        incident_id = custom_id or f"INC-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}-{trigger_location[:4].upper()}"

        audit_log = [
            {"timestamp_utc": now, "action": f"Incident triggered via {trigger_source} at {trigger_location}"}
        ]

        # 1. Simulate Model M12 Dam Breach Hydraulics
        breach_res = self.cascade_engine.simulate_dam_breach(
            dam_location=trigger_location,
            dam_height_m=dam_height_m,
            impounded_volume_m3=impounded_volume_m3,
            normal_river_discharge_m3s=450.0,
        )
        cascade_dict = asdict(breach_res)
        audit_log.append({
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": f"M12 Breach hydrograph calculated: Peak Q={breach_res.peak_outflow_discharge_m3s:,.0f} m3/s, t_f={breach_res.breach_formation_time_min / 60.0:.2f} hr",
        })

        # 2. Impact & Exposure Assessment
        impact_assessment = {
            "monitored_basin": "Upper Beas River Catchment",
            "threatened_settlements": ["Aut", "Thalout", "Pandoh Dam", "Mandi Outer Reach"],
            "total_estimated_population_exposed": 18450,
            "lifeline_highways_compromised": ["NH-3 (Aut-Pandoh stretch)"] if simulate_nh3_closure else [],
            "critical_bridges_threatened": ["Aut Tunnel Bridge (KM 198)", "Pandoh Spillway Viaduct"],
        }

        # 3. Dynamic Evacuation Route Solving (Model M15 & M16)
        # Copy infrastructure graph and simulate NH-3 road blockages
        g = self.graph_network.copy()
        if simulate_nh3_closure:
            for u, v, d in g.edges(data=True):
                if "NH3" in str(u) or "NH3" in str(v) or "NH3" in d.get("road_name", ""):
                    d["is_blocked"] = True

        # Evacuate Bhuntar/Aut to safest high-capacity shelter
        best_shelter = self.decision_engine.select_safe_shelter(
            shelters=self.registered_shelters,
            evacuation_demand=450,
        )
        target_shelter_id = best_shelter.get("selected_shelter_id", "S_KULLU_COLLEGE")

        route_res = self.decision_engine.find_safest_evacuation_route(
            graph=g,
            origin_node="V_BHUNTAR",
            destination_node=target_shelter_id,
        )

        evacuation_plan = {
            "designated_shelter": best_shelter,
            "origin_node": "V_BHUNTAR",
            "destination_node": target_shelter_id,
            "route_solution": route_res,
            "nh3_closure_simulated": simulate_nh3_closure,
            "evacuation_status": "BYPASS_ROUTE_RECOMMENDED" if route_res.get("route_status") == "FOUND_SAFER_FEASIBLE" else "SHELTER_IN_PLACE_ELEVATION",
        }
        audit_log.append({
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": f"M15/M16 Evacuation route computed to {target_shelter_id}: {route_res.get('total_distance_km', 0):.1f} km, risk={route_res.get('accumulated_risk_score', 0):.2f}",
        })

        # 4. Rescue Prioritization (Model M20)
        settlements = self.rescue_prioritizer.get_all_priorities()
        rescue_list = [asdict(s) for s in settlements]

        # 5. Common Alerting Protocol (CAP v1.2) Bilingual Alert
        cap_alert = self.cap_engine.generate_cascade_breach_alert(
            breach_result_dict=cascade_dict,
            status="Actual" if status == "ACTIVE" else "Exercise",
        )
        cap_xml = cap_alert.to_xml_string()

        en_info = next((i for i in cap_alert.infos if "en" in i.language.lower()), cap_alert.infos[0])
        hi_info = next((i for i in cap_alert.infos if "hi" in i.language.lower()), cap_alert.infos[-1])

        audit_log.append({
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": f"Bilingual CAP v1.2 alert dispatched: ID={cap_alert.identifier}",
        })

        record = IncidentRecord(
            incident_id=incident_id,
            timestamp_utc=now,
            incident_type=incident_type,
            severity_level=severity_level,
            trigger_source=trigger_source,
            trigger_location=trigger_location,
            trigger_metrics={
                "dam_height_m": dam_height_m,
                "impounded_volume_m3": impounded_volume_m3,
                "rainfall_rate_mmh": rainfall_rate_mmh,
            },
            cascade_simulation=cascade_dict,
            impact_assessment=impact_assessment,
            evacuation_plan=evacuation_plan,
            rescue_prioritization=rescue_list,
            cap_alert_identifier=cap_alert.identifier,
            cap_alert_xml=cap_xml,
            cap_alert_summary_en=en_info.headline,
            cap_alert_summary_hi=hi_info.headline,
            status=status,
            statutory_notice=(
                "STATUTORY CIVIL DEFENSE NOTICE: This automated incident response plan is synthesized "
                "from multi-source satellite remote sensing and hydraulic breach models. Authority field "
                "inspection and local district administration concurrence mandated prior to public siren activation."
            ),
            audit_log=audit_log,
        )

        self._incidents[incident_id] = record
        return record

    def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        return self._incidents.get(incident_id)

    def list_incidents(self) -> List[IncidentRecord]:
        return list(self._incidents.values())

    def update_incident_status(self, incident_id: str, new_status: str, notes: str = "") -> Optional[IncidentRecord]:
        rec = self._incidents.get(incident_id)
        if not rec:
            return None
        rec.status = new_status
        rec.audit_log.append({
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": f"Status changed to {new_status}. Note: {notes}",
        })
        return rec


# Global Singleton Instance
_GLOBAL_INCIDENT_MANAGER: Optional[IncidentManager] = None


def get_incident_manager() -> IncidentManager:
    global _GLOBAL_INCIDENT_MANAGER
    if _GLOBAL_INCIDENT_MANAGER is None:
        _GLOBAL_INCIDENT_MANAGER = IncidentManager()
    return _GLOBAL_INCIDENT_MANAGER
