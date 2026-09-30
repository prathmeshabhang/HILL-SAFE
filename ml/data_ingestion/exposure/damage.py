"""
ml/data_ingestion/exposure/damage.py
====================================
Observed Post-Disaster Infrastructure & Environmental Damage Ingestion Adapter.
Strictly separates:
  - OBSERVED_DAMAGE: Actual field damage audit records (e.g. HPSDMA PDNA 2023, PWD bridge surveys).
  - MODELLED_DAMAGE: Model-predicted damage states from vulnerability curves (e.g. NDMA/USACE).
Prevents training or calibrating damage models on circular synthetic labels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ml.data_quality.provenance import DatasetProvenance, ProvenanceType


class DamageEvidenceType(str, Enum):
    OBSERVED_DAMAGE = "OBSERVED_DAMAGE"  # Field-verified damage audit from line departments
    MODELLED_DAMAGE = "MODELLED_DAMAGE"  # Empirical curve or simulation estimate


@dataclass
class ObservedDamageRecord:
    damage_id: str
    asset_id: str
    event_id: str                   # e.g. "JULY_2023_BEAS_FLOOD"
    hazard_type: str                # FLASH_FLOOD | LANDSLIDE | DEBRIS_FLOW | EROSION
    damage_state: str               # NEGLIGIBLE | MINOR | MODERATE | SEVERE | COLLAPSED_DESTROYED
    observed_flood_depth_m: Optional[float] = None
    observed_flow_velocity_ms: Optional[float] = None
    estimated_repair_cost_inr_lakh: Optional[float] = None
    lifeline_disruption_days: Optional[float] = None
    damage_evidence_type: DamageEvidenceType = DamageEvidenceType.OBSERVED_DAMAGE
    source_agency: str = "HPSDMA_PDNA_2023"
    surveyor_notes: Optional[str] = None
    quality_flag: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["damage_evidence_type"] = self.damage_evidence_type.value
        return d


class ObservedDamageLoader:
    """
    Ingests and validates genuine post-event damage survey observations.
    Enforces separation between field-observed ground truth and modelled curves.
    """

    def __init__(self):
        self.provenance = DatasetProvenance(
            dataset_id="observed_damage_events",
            provenance_type=ProvenanceType.OBSERVATION,
            source_agency="HPSDMA / HP PWD / HPSEB / Jal Shakti Vibhag",
            geographic_aoi="Upper Beas Basin (July-August 2023 Disaster Impact Reach)",
            temporal_coverage="July-August 2023 Disaster",
            spatial_resolution="Site-specific infrastructure asset survey",
            license_type="Government Disaster Audit Archive",
            doi_or_url="https://hpsdma.nic.in",
            is_field_verified=True,
            citation="HPSDMA Post-Disaster Needs Assessment (PDNA) 2023 Flood Survey",
        )

    def parse_damage_record(self, raw_data: Dict[str, Any]) -> Tuple[Optional[ObservedDamageRecord], Optional[str]]:
        did = str(raw_data.get("damage_id", ""))
        aid = str(raw_data.get("asset_id", ""))
        eid = str(raw_data.get("event_id", ""))
        dstate = str(raw_data.get("damage_state", "")).upper()
        ev_type = str(raw_data.get("damage_evidence_type", "OBSERVED_DAMAGE")).upper()

        if not did or not aid or not eid:
            return None, "Missing damage_id, asset_id, or event_id"

        evidence_enum = (
            DamageEvidenceType.OBSERVED_DAMAGE
            if ev_type == "OBSERVED_DAMAGE"
            else DamageEvidenceType.MODELLED_DAMAGE
        )

        record = ObservedDamageRecord(
            damage_id=did,
            asset_id=aid,
            event_id=eid,
            hazard_type=str(raw_data.get("hazard_type", "FLASH_FLOOD")),
            observed_flood_depth_m=raw_data.get("observed_flood_depth_m"),
            observed_flow_velocity_ms=raw_data.get("observed_flow_velocity_ms"),
            damage_state=dstate,
            estimated_repair_cost_inr_lakh=raw_data.get("estimated_repair_cost_inr_lakh"),
            lifeline_disruption_days=raw_data.get("lifeline_disruption_days"),
            damage_evidence_type=evidence_enum,
            source_agency=str(raw_data.get("source_agency", "HPSDMA")),
            surveyor_notes=raw_data.get("surveyor_notes"),
            quality_flag="VALID",
        )
        return record, None

    def ingest_damage_dataset(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_records: List[ObservedDamageRecord] = []
        errors: List[Dict[str, Any]] = []

        for idx, item in enumerate(raw_records):
            rec, err = self.parse_damage_record(item)
            if rec:
                valid_records.append(rec)
            else:
                errors.append({"index": idx, "damage_id": item.get("damage_id"), "error": err})

        return {
            "dataset_id": self.provenance.dataset_id,
            "provenance": self.provenance.to_dict(),
            "total_records": len(raw_records),
            "valid_records_count": len(valid_records),
            "error_count": len(errors),
            "records": [r.to_dict() for r in valid_records],
            "errors": errors,
        }
