"""
backend/app/services/devices/health_service.py
==============================================
Operational Health and Diagnostic Engine for Field IoT Devices and Stations.
Computes battery health, packet loss, data freshness, calibration age, and operational states.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.database.models.telemetry import SensorStationModel, SensorObservationModel
from backend.app.database.models.device import (
    DeviceModel,
    SensorModel,
    DeviceHeartbeatModel,
)


class SensorHealthService:
    """Calculates real-time device and station operational metrics."""

    def evaluate_device_health(self, db: Session, device_id: str) -> Dict[str, Any]:
        device = db.query(DeviceModel).filter(DeviceModel.device_id == device_id).first()
        if not device:
            return {
                "device_id": device_id,
                "status": "OFFLINE",
                "error": f"Device {device_id} not found",
            }

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        last_seen = device.last_seen_at
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=datetime.timezone.utc)

        # 1. Freshness & Latency
        freshness_minutes = (now_utc - last_seen).total_seconds() / 60.0 if last_seen else 999999.0

        # 2. Heartbeats and Packet Statistics (past 24h)
        since_24h = now_utc - datetime.timedelta(hours=24)
        heartbeats = (
            db.query(DeviceHeartbeatModel)
            .filter(DeviceHeartbeatModel.device_id == device_id, DeviceHeartbeatModel.timestamp >= since_24h)
            .order_by(DeviceHeartbeatModel.timestamp.desc())
            .all()
        )
        packet_count = len(heartbeats)
        # Expected: 1 packet per 5 minutes = 288 packets/day
        expected_packets = 288
        packet_loss_pct = max(0.0, min(100.0, (1.0 - (packet_count / expected_packets)) * 100.0)) if device.status == "ACTIVE" else 0.0

        # 3. Battery Health
        battery = device.battery_level or 100.0
        battery_state = "CRITICAL" if battery < 15.0 else ("DEGRADED" if battery < 30.0 else "HEALTHY")

        # 4. Signal Strength (RSSI)
        signal = device.signal_strength or -75.0
        signal_state = "POOR" if signal < -110.0 else ("MODERATE" if signal < -90.0 else "EXCELLENT")

        # 5. Sensors & Calibration Age
        sensors = db.query(SensorModel).filter(SensorModel.device_id == device_id).all()
        calibration_needed = False
        sensor_summaries = []
        for s in sensors:
            next_cal = s.next_calibration_at
            if next_cal and next_cal.tzinfo is None:
                next_cal = next_cal.replace(tzinfo=datetime.timezone.utc)
            is_calib_expired = bool(next_cal and next_cal < now_utc)
            if is_calib_expired:
                calibration_needed = True
            sensor_summaries.append({
                "sensor_id": s.sensor_id,
                "sensor_type": s.sensor_type,
                "is_active": s.is_active,
                "calibration_status": "EXPIRED" if is_calib_expired else s.calibration_status,
                "last_calibration": s.last_calibration_at.isoformat() if s.last_calibration_at else None,
            })

        # 6. Synthesize Operational Health Status
        if device.status == "RETIRED":
            operational_status = "RETIRED"
        elif device.status == "PLANNED":
            operational_status = "PLANNED"
        elif freshness_minutes > 1440.0:  # >24 hours
            operational_status = "OFFLINE"
        elif battery < 15.0:
            operational_status = "CRITICAL"
        elif freshness_minutes > 360.0:  # >6 hours
            operational_status = "STALE"
        elif calibration_needed:
            operational_status = "CALIBRATION_REQUIRED"
        elif battery < 30.0 or signal < -110.0 or packet_loss_pct > 50.0:
            operational_status = "DEGRADED"
        else:
            operational_status = "HEALTHY"

        uptime_pct = max(0.0, min(100.0, 100.0 - (packet_loss_pct * 0.5))) if operational_status != "OFFLINE" else 0.0

        return {
            "device_id": device_id,
            "station_id": device.station_id,
            "status": operational_status,
            "operational_status": operational_status,
            "hardware_lifecycle_status": device.status,
            "last_seen_at": last_seen.isoformat() if last_seen else None,
            "freshness_minutes": round(freshness_minutes, 1),
            "battery_level": battery,
            "battery_state": battery_state,
            "signal_strength_dbm": signal,
            "signal_state": signal_state,
            "packet_count_24h": packet_count,
            "packet_loss_pct": round(packet_loss_pct, 1),
            "uptime_pct": round(uptime_pct, 1),
            "calibration_required": calibration_needed,
            "sensors": sensor_summaries,
        }

    def evaluate_station_health(self, db: Session, station_id: str) -> Dict[str, Any]:
        station = db.query(SensorStationModel).filter(SensorStationModel.id == station_id).first()
        if not station:
            return {
                "station_id": station_id,
                "status": "OFFLINE",
                "error": f"Station {station_id} not found",
            }

        devices = db.query(DeviceModel).filter(DeviceModel.station_id == station_id).all()
        device_healths = [self.evaluate_device_health(db, d.device_id) for d in devices]

        if not device_healths:
            station_status = "ACTIVE" if station.is_active else "OFFLINE"
        elif any(d["status"] == "CRITICAL" for d in device_healths):
            station_status = "CRITICAL"
        elif any(d["status"] == "DEGRADED" for d in device_healths):
            station_status = "DEGRADED"
        elif all(d["status"] == "OFFLINE" for d in device_healths):
            station_status = "OFFLINE"
        elif any(d["status"] == "STALE" for d in device_healths):
            station_status = "STALE"
        else:
            station_status = "HEALTHY"

        return {
            "station_id": station_id,
            "station_name": station.name,
            "station_type": station.station_type,
            "status": station_status,
            "operational_state": station_status,
            "is_active": station.is_active,
            "device_count": len(devices),
            "total_devices": len(devices),
            "total_sensors": sum(len(d.get("sensors", [])) for d in device_healths),
            "devices": device_healths,
        }

    def get_health_summary(self, db: Session, window: str = "24h") -> Dict[str, Any]:
        """Calculates aggregated telemetry and hardware health across the entire basin."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        hours_map = {"24h": 24, "72h": 72, "7d": 168, "30d": 720}
        window_hours = hours_map.get(window, 24)
        cutoff = now_utc - datetime.timedelta(hours=window_hours)

        stations = db.query(SensorStationModel).all()
        station_evals = [self.evaluate_station_health(db, s.id) for s in stations]

        health_counts = {"HEALTHY": 0, "DEGRADED": 0, "CRITICAL": 0, "OFFLINE": 0, "STALE": 0}
        for se in station_evals:
            st = se.get("status", "OFFLINE")
            if st in health_counts:
                health_counts[st] += 1
            else:
                health_counts[st] = health_counts.get(st, 0) + 1

        active_count = sum(1 for s in stations if s.status == "ACTIVE" or s.is_active)

        # Observations in window
        obs_records = (
            db.query(SensorObservationModel)
            .filter(SensorObservationModel.timestamp >= cutoff)
            .all()
        )
        total_packets = len(obs_records)

        provenance_breakdown: Dict[str, int] = {}
        quality_breakdown: Dict[str, int] = {}
        for obs in obs_records:
            prov = getattr(obs, "provenance", "SIMULATED") or "SIMULATED"
            provenance_breakdown[prov] = provenance_breakdown.get(prov, 0) + 1
            q = obs.quality_state or "UNKNOWN"
            quality_breakdown[q] = quality_breakdown.get(q, 0) + 1

        # Packet delivery ratio calculation: 1 packet per 5 minutes = 12 pkts/hr per active station
        expected_per_station = window_hours * 12
        total_expected = max(1, active_count * expected_per_station)
        pdr = min(1.0, round(total_packets / total_expected, 4)) if active_count > 0 else (1.0 if total_packets > 0 else 0.0)

        return {
            "window": window,
            "window_hours": window_hours,
            "evaluated_at": now_utc.isoformat(),
            "total_stations": len(stations),
            "active_stations": active_count,
            "health_distribution": health_counts,
            "total_packets": total_packets,
            "packet_delivery_ratio": pdr,
            "provenance_breakdown": provenance_breakdown,
            "quality_breakdown": quality_breakdown,
            "stations": station_evals,
        }


sensor_health_service = SensorHealthService()

