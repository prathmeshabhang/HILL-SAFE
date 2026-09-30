"""
backend/app/services/ingestion/ingestion_service.py
===================================================
Orchestration service for ingesting ground station telemetry and satellite metadata,
validating through quality gates, enforcing deduplication, and persisting to database.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from backend.app.database.models.telemetry import SensorStationModel, SensorObservationModel
from backend.app.database.models.ingestion import DataIngestionRunModel, DataQualityRecordModel
from backend.app.services.ingestion.quality_gate import quality_gate, QualityState
from backend.app.services.ingestion.adapters.base import NormalizedObservation
from backend.app.services.ingestion.schemas import (
    RainGaugeReading,
    RiverWaterLevelReading,
    GeotechnicalSensorReading,
)
from backend.app.core.logging import get_logger

logger = get_logger("floody.ingestion.service")


class TelemetryIngestionService:
    def __init__(self):
        self.gate = quality_gate

    def ingest_normalized_observation(
        self,
        db: Session,
        obs: NormalizedObservation,
        ingestion_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Primary ingestion pipeline:
        1. Spatial Bounds Validation
        2. Temporal Freshness Evaluation
        3. Physical Bounds Check
        4. Idempotency / Duplicate Check
        5. Model M9 Anomaly Screening
        6. Persistence to Database (Observation + Quality Record)
        """
        # 1. Geographic Validation
        self.gate.validate_spatial_bounds(obs.latitude, obs.longitude)

        # 2. Temporal Validation & Freshness
        freshness = self.gate.validate_temporal_freshness(obs.timestamp)
        quality_state = freshness["quality_state"]

        # 3. Physical Plausibility Validation
        self.gate.validate_physical_limits(obs.values)

        # 4. Idempotency Check: prevent duplicate logical records
        if obs.idempotency_hash:
            existing = (
                db.query(SensorObservationModel)
                .filter_by(idempotency_hash=obs.idempotency_hash)
                .first()
            )
            if existing:
                logger.info(f"Duplicate observation detected for hash {obs.idempotency_hash[:10]}... skipping insertion.")
                return {
                    "status": "DUPLICATE_IGNORED",
                    "observation_id": existing.id,
                    "station_id": existing.station_id,
                    "is_duplicate": True,
                    "quality_state": existing.quality_state,
                }

        # 5. Station Auto-Registration if not exists
        station = db.query(SensorStationModel).filter_by(id=obs.station_id).first()
        if not station:
            station = SensorStationModel(
                id=obs.station_id,
                name=f"{obs.source_id} Station {obs.station_id}",
                station_type=f"{obs.source_id}_STATION",
                latitude=obs.latitude,
                longitude=obs.longitude,
                elevation_m=obs.elevation_m,
                river_basin="Upper Beas Basin",
                is_active=True,
                last_heartbeat=obs.timestamp,
            )
            db.add(station)

        # 6. M9 Anomaly Screening
        rain_val = float(obs.values.get("rainfall_rate_mmh") or 0.0)
        water_val = float(obs.values.get("water_level_m") or 0.0)
        pwp_val = float(obs.values.get("pore_pressure_kpa") or 0.0)
        disp_val = float(obs.values.get("displacement_mm") or 0.0)

        m9_res = self.gate.check_anomalies_m9([{
            "rainfall_rate": rain_val,
            "soil_moisture": min(85.0, 30.0 + rain_val * 1.2),
            "water_level": max(1.0, water_val),
            "tilt_degrees": 0.0,
        }])
        is_anom = m9_res.get("is_anomalous", False)
        anom_reason = "; ".join(m9_res.get("flags", [])) if is_anom else None

        if is_anom and quality_state == QualityState.FRESH.value:
            quality_state = QualityState.DEGRADED.value

        # 7. Persistence
        db_obs = SensorObservationModel(
            station_id=obs.station_id,
            data_source_id=obs.source_id,
            idempotency_hash=obs.idempotency_hash,
            timestamp=obs.timestamp,
            rainfall_rate_mmh=obs.values.get("rainfall_rate_mmh"),
            water_level_m=obs.values.get("water_level_m"),
            pore_pressure_kpa=obs.values.get("pore_pressure_kpa"),
            displacement_mm=obs.values.get("displacement_mm"),
            acoustic_emission_db=obs.values.get("acoustic_emission_db"),
            is_anomalous=is_anom,
            anomaly_score=0.95 if is_anom else 0.0,
            anomaly_reason=anom_reason,
            quality_state=quality_state,
            provenance_json=str(obs.provenance),
        )
        db.add(db_obs)
        station.last_heartbeat = obs.timestamp

        # Record Quality Record
        q_rec = DataQualityRecordModel(
            id=str(uuid.uuid4()),
            ingestion_run_id=ingestion_run_id,
            source_id=obs.source_id,
            station_or_scene_id=obs.station_id,
            observation_timestamp=obs.timestamp,
            quality_state=quality_state,
            rule_evaluated="QUALITY_GATE_M9_FUSION",
            passed="PASS" if not is_anom else "DEGRADED",
            rejection_reason=anom_reason,
            details_json=str(freshness),
        )
        db.add(q_rec)
        db.commit()

        return {
            "status": "INGESTED",
            "observation_id": db_obs.id,
            "station_id": obs.station_id,
            "is_duplicate": False,
            "quality_state": quality_state,
            "freshness": freshness,
            "is_anomalous": is_anom,
            "anomaly_reason": anom_reason,
        }

    def compute_source_event_id(self, packet: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 event ID for strict deduplication & tamper detection."""
        import hashlib
        source_id = packet.get("source_id", "FIELD_IOT")
        station_id = packet.get("station_id", "UNKNOWN_STN")
        device_id = packet.get("device_id", "")
        sensor_id = packet.get("sensor_id", "")
        measurement_type = packet.get("measurement_type", "GENERAL")
        seq = str(packet.get("sequence_number", ""))
        observed_at = packet.get("observed_at") or packet.get("timestamp") or ""
        if isinstance(observed_at, datetime.datetime):
            obs_str = observed_at.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            obs_str = str(observed_at)[:19].replace(" ", "T")
        key = f"{source_id}:{station_id}:{device_id}:{sensor_id}:{measurement_type}:{seq}:{obs_str}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def ingest_telemetry_packet(self, db: Session, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingests a standardized v3.4 field telemetry packet.
        Enforces UTC normalization, temporal validation, deterministic idempotency,
        and integrity validation on payload replay.
        """
        from backend.app.core.errors import FloodyShieldException

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        observed_raw = packet.get("observed_at") or packet.get("timestamp")
        if not observed_raw:
            raise FloodyShieldException(
                message="Missing mandatory timestamp 'observed_at'",
                error_code="TELEMETRY_INVALID_TIMESTAMP",
                status_code=422,
            )

        # 1. Parse timestamps to UTC
        if isinstance(observed_raw, datetime.datetime):
            observed_at = observed_raw if observed_raw.tzinfo else observed_raw.replace(tzinfo=datetime.timezone.utc)
        else:
            try:
                observed_at = datetime.datetime.fromisoformat(str(observed_raw).replace("Z", "+00:00"))
            except Exception:
                raise FloodyShieldException(
                    message=f"Malformed ISO-8601 timestamp '{observed_raw}'",
                    error_code="TELEMETRY_INVALID_TIMESTAMP",
                    status_code=422,
                )

        received_raw = packet.get("received_at")
        if received_raw:
            if isinstance(received_raw, datetime.datetime):
                received_at = received_raw if received_raw.tzinfo else received_raw.replace(tzinfo=datetime.timezone.utc)
            else:
                received_at = datetime.datetime.fromisoformat(str(received_raw).replace("Z", "+00:00"))
        else:
            received_at = now_utc

        processed_at = now_utc

        # 2. Temporal validation
        skew_seconds = (observed_at - now_utc).total_seconds()
        if skew_seconds > 7200.0:  # > 120 minutes future
            raise FloodyShieldException(
                message=f"Clock skew exceeded: observation timestamp is {skew_seconds/60:.1f} minutes in the future",
                error_code="TELEMETRY_FUTURE_TIMESTAMP",
                status_code=422,
            )

        latency_seconds = (now_utc - observed_at).total_seconds()
        if latency_seconds > 86400.0:  # > 24 hours
            temporal_state = "EXPIRED"
            quality_state = "EXPIRED"
        elif latency_seconds > 21600.0:  # > 6 hours
            temporal_state = "STALE"
            quality_state = "STALE"
        elif latency_seconds > 3600.0:  # > 1 hour
            temporal_state = "LATE"
            quality_state = "FRESH"
        elif skew_seconds > 300.0:
            temporal_state = "INVALID"
            quality_state = "CRITICAL_ERROR"
        else:
            temporal_state = "VALID"
            quality_state = "FRESH"

        # 3. Deterministic Idempotency & Replay / Tamper Detection
        source_event_id = packet.get("source_event_id") or self.compute_source_event_id(packet)
        existing = db.query(SensorObservationModel).filter(SensorObservationModel.source_event_id == source_event_id).first()
        incoming_val = float(packet.get("value", 0.0))

        if existing:
            # Check if payload was tampered with on replay
            if existing.value is not None and abs(existing.value - incoming_val) > 1e-5:
                raise FloodyShieldException(
                    message=f"Telemetry integrity violation: Event ID '{source_event_id}' was already recorded with value {existing.value}, conflicting with incoming value {incoming_val}",
                    error_code="TELEMETRY_INTEGRITY_VIOLATION",
                    status_code=409,
                )
            logger.info(f"Duplicate packet received for event ID {source_event_id[:12]}... returning existing.")
            return {
                "status": "DUPLICATE",
                "source_event_id": source_event_id,
                "observation_id": existing.id,
                "station_id": existing.station_id,
                "temporal_state": existing.temporal_state,
                "quality_state": existing.quality_state,
                "provenance": existing.provenance,
                "environment": existing.environment,
                "is_duplicate": True,
            }

        # 4. Map measurement type to column
        station_id = packet.get("station_id", "STN_AUT_01")
        source_id = packet.get("source_id", "UPPER_BEAS_IOT")
        m_type = packet.get("measurement_type", "RAINFALL").upper()
        unit = packet.get("unit", "")
        seq = packet.get("sequence_number")
        device_id = packet.get("device_id")
        sensor_id = packet.get("sensor_id")
        provenance = str(packet.get("provenance", "REAL")).upper()
        environment = str(packet.get("environment", "FIELD")).upper()
        initial_qc = packet.get("qc_flags")

        rainfall_rate = incoming_val if "RAIN" in m_type else None
        water_level = incoming_val if "WATER_LEVEL" in m_type or "RIVER" in m_type else None
        pore_pressure = incoming_val if "PORE" in m_type or "PRESSURE" in m_type else None
        displacement = incoming_val if "DISPLACEMENT" in m_type or "TILT" in m_type else None

        # Real-time Stream QC: Flatline and Sudden Jump Detection
        detected_flags: List[str] = []
        if initial_qc:
            detected_flags.append(str(initial_qc))

        prev_records = (
            db.query(SensorObservationModel)
            .filter(
                SensorObservationModel.station_id == station_id,
                SensorObservationModel.measurement_type == m_type,
            )
            .order_by(SensorObservationModel.timestamp.desc())
            .limit(5)
            .all()
        )

        if prev_records:
            recent_vals = [incoming_val] + [r.value for r in prev_records if r.value is not None]
            if self.gate.check_flatlining(recent_vals):
                detected_flags.append("QC_FLATLINE")

            last_rec = prev_records[0]
            if last_rec.timestamp and last_rec.value is not None:
                last_ts = last_rec.timestamp if last_rec.timestamp.tzinfo else last_rec.timestamp.replace(tzinfo=datetime.timezone.utc)
                dt_sec = abs((observed_at - last_ts).total_seconds())
                if self.gate.check_rate_of_change(incoming_val, last_rec.value, dt_sec, m_type):
                    detected_flags.append("QC_SPIKE")

        if any(f in detected_flags for f in ("QC_FLATLINE", "QC_SPIKE")):
            if quality_state == "FRESH":
                quality_state = "DEGRADED"

        qc_flags_str = ",".join(detected_flags) if detected_flags else None

        # Ensure station exists
        station = db.query(SensorStationModel).filter_by(id=station_id).first()
        if not station:
            station = SensorStationModel(
                id=station_id,
                name=f"Field Station {station_id}",
                station_type="MET_HYDRO_IOT",
                latitude=packet.get("latitude", 31.75),
                longitude=packet.get("longitude", 77.20),
                elevation_m=packet.get("elevation_m", 1200.0),
                river_basin="Upper Beas Basin",
                is_active=True,
                last_heartbeat=observed_at,
            )
        else:
            prev_hb = station.last_heartbeat
            if prev_hb:
                if prev_hb.tzinfo is None:
                    prev_hb = prev_hb.replace(tzinfo=datetime.timezone.utc)
                station.last_heartbeat = max(prev_hb, observed_at)
            else:
                station.last_heartbeat = observed_at

        # 5. Persist Observation
        obs_record = SensorObservationModel(
            station_id=station_id,
            device_id=device_id,
            sensor_id=sensor_id,
            data_source_id=source_id,
            source_event_id=source_event_id,
            idempotency_hash=source_event_id,
            timestamp=observed_at,
            observed_at=observed_at,
            received_at=received_at,
            processed_at=processed_at,
            measurement_type=m_type,
            value=incoming_val,
            unit=unit,
            sequence_number=seq,
            rainfall_rate_mmh=rainfall_rate,
            water_level_m=water_level,
            pore_pressure_kpa=pore_pressure,
            displacement_mm=displacement,
            quality_state=quality_state,
            temporal_state=temporal_state,
            provenance=provenance,
            environment=environment,
            qc_flags=qc_flags_str,
            provenance_json=str({
                "source": source_id,
                "device_id": device_id,
                "sensor_id": sensor_id,
                "provenance": provenance,
                "environment": environment,
                "firmware_version": packet.get("firmware_version"),
                "provenance_type": "OBSERVED",
            }),
        )
        db.add(obs_record)
        db.commit()
        db.refresh(obs_record)

        return {
            "status": "INGESTED",
            "observation_id": obs_record.id,
            "source_event_id": source_event_id,
            "station_id": station_id,
            "temporal_state": temporal_state,
            "quality_state": quality_state,
            "provenance": provenance,
            "environment": environment,
            "qc_flags": qc_flags_str,
            "is_duplicate": False,
        }

    def ingest_telemetry_batch(self, db: Session, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processes a batch of field telemetry packets."""
        results = []
        accepted = 0
        duplicates = 0
        rejected = 0

        for pkt in packets:
            try:
                res = self.ingest_telemetry_packet(db, pkt)
                results.append(res)
                if res.get("is_duplicate"):
                    duplicates += 1
                else:
                    accepted += 1
            except Exception as e:
                rejected += 1
                results.append({
                    "status": "REJECTED",
                    "error": str(e),
                    "packet_station": pkt.get("station_id"),
                    "packet_seq": pkt.get("sequence_number"),
                })

        return {
            "total_packets": len(packets),
            "total": len(packets),
            "accepted": accepted,
            "ingested": accepted,
            "duplicates": duplicates,
            "rejected": rejected,
            "results": results,
        }

    def ingest_rainfall(self, db: Session, reading: RainGaugeReading) -> Dict[str, Any]:
        """Backward-compatible helper for RainGaugeReading schemas."""
        norm = NormalizedObservation(
            station_id=reading.station_id,
            source_id="IMD_AWS",
            timestamp=reading.timestamp,
            latitude=31.95,
            longitude=77.10,
            elevation_m=1250.0,
            values={"rainfall_rate_mmh": reading.rainfall_rate_mmh, "accumulated_24h_mm": reading.accumulated_24h_mm},
            idempotency_hash=f"IMD_AWS:{reading.station_id}:{reading.timestamp.isoformat()}",
            provenance={"source": "RainGaugeReading", "source_version": "v3.3"},
        )
        return self.ingest_normalized_observation(db, norm)

    def ingest_river_stage(self, db: Session, reading: RiverWaterLevelReading) -> Dict[str, Any]:
        """Backward-compatible helper for RiverWaterLevelReading schemas."""
        norm = NormalizedObservation(
            station_id=reading.station_id,
            source_id="CWC_RIVER",
            timestamp=reading.timestamp,
            latitude=31.90,
            longitude=77.15,
            elevation_m=1080.0,
            values={"water_level_m": reading.water_level_m, "discharge_m3s": reading.discharge_m3s},
            idempotency_hash=f"CWC_RIVER:{reading.station_id}:{reading.timestamp.isoformat()}",
            provenance={"source": "RiverWaterLevelReading", "source_version": "v3.3"},
        )
        return self.ingest_normalized_observation(db, norm)


ingestion_service = TelemetryIngestionService()

