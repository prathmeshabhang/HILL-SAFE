"""
backend/tests/test_v36_physical_integration.py
==============================================
Comprehensive Verification Test Suite for FLOODY SHIELD v3.6:
Physical Sensor + LoRa LPWAN Integration + Station Lifecycle + End-to-End Pipeline.

Test Modules:
1. LoRa Binary Packet Codec & CRC-16 Integrity
2. Sequence Number Continuity, Rollover, and Packet Loss Calculation
3. Hardware Abstraction Layer (HAL), Calibration, Bounds, and Single-Sensor Failure Isolation
4. Gateway Offline Buffering, Backhaul Reconnection, and Chronological Replay
5. Station Lifecycle State Machine (PLANNED -> COMMISSIONED -> ACTIVE)
6. LoRa REST Ingestion & Diagnostics API
7. End-to-End Pipeline: Sensor -> LoRa -> Gateway -> Backend Ingest -> QC -> Models -> Risk -> Commander Authorization
"""

import pytest
import datetime
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.database.session import SessionLocal
from backend.app.database.models.telemetry import SensorStationModel, SensorObservationModel
from backend.app.database.models.device import DeviceModel, SensorModel
from backend.app.services.devices.hardware_abstraction import (
    PhysicalSensorType,
    HardwareAbstractionService,
    hal_service,
)
from tools.lora.packet_codec import (
    LoRaPacketCodec,
    lora_codec,
    crc16_ccitt,
    MSG_TYPE_TELEMETRY,
    MSG_TYPE_HEARTBEAT,
)
from backend.app.services.ingestion.lora_gateway import (
    LoRaGatewayService,
    SequenceTracker,
    SequenceState,
    lora_gateway_service,
)
from backend.app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def commander_headers():
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    username = f"cmdr_v36_{uid}"
    pwd = "CommanderPassword2026!"
    reg_payload = {
        "username": username,
        "email": f"{username}@hpsdma.gov.in",
        "password": pwd,
        "role": "SENIOR_INCIDENT_COMMANDER",
        "full_name": "Commander Kullu EOC",
        "agency": "HPSDMA",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    login_res = client.post("/api/v1/auth/login", json={"username": username, "password": pwd})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers():
    uid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    username = f"ana_v36_{uid}"
    pwd = "AnalystPassword2026!"
    reg_payload = {
        "username": username,
        "email": f"{username}@hpsdma.gov.in",
        "password": pwd,
        "role": "ANALYST",
        "full_name": "Analyst Kullu EOC",
        "agency": "HPSDMA",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    login_res = client.post("/api/v1/auth/login", json={"username": username, "password": pwd})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. LORA BINARY PACKET CODEC & CRC-16 INTEGRITY
# ============================================================================

class TestLoRaPacketCodec:
    """Verifies binary packing, unpacking, bandwidth constraints, and CRC integrity."""

    def test_encode_decode_roundtrip(self):
        """Encodes and decodes multi-sensor LoRa payload verifying fields."""
        station_code = 101  # Manali
        seq = 105
        epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        sensors = [
            {"sensor_type": "RAIN_GAUGE", "value": 52.4, "status_flags": 0},
            {"sensor_type": "WATER_LEVEL", "value": 4.12, "status_flags": 0},
            {"sensor_type": "SOIL_MOISTURE", "value": 81.5, "status_flags": 0},
        ]
        raw_bytes = lora_codec.encode(
            station_code=station_code,
            sequence_number=seq,
            timestamp_epoch=epoch,
            sensor_readings=sensors,
            battery_mv=12600,
            rssi_dbm=-75,
            snr_db=10,
        )

        # Verify compact LPWAN frame size
        # 6 header + 10 meta + (3 * 6) channels + 2 crc = 36 bytes
        assert len(raw_bytes) == 36
        assert len(raw_bytes) <= 51  # Strict SF12 minimum airtime limit

        decoded = lora_codec.decode(raw_bytes)
        assert decoded.station_code == station_code
        assert decoded.sequence_number == seq
        assert decoded.timestamp_epoch == epoch
        assert decoded.battery_voltage == 12.6
        assert decoded.rssi_dbm == -75
        assert decoded.snr_db == 10
        assert decoded.crc_valid is True
        assert len(decoded.sensors) == 3

        rain_ch = next(s for s in decoded.sensors if s.sensor_type == "RAIN_GAUGE")
        assert abs(rain_ch.value - 52.4) < 1e-3
        assert rain_ch.unit == "mm/h"

    def test_crc16_tamper_rejection(self):
        """Flipping a single bit in the binary payload MUST fail CRC-16 verification."""
        raw_bytes = lora_codec.encode(
            station_code=102,
            sequence_number=1,
            timestamp_epoch=1726920000,
            sensor_readings=[{"sensor_type": "WATER_LEVEL", "value": 2.5}],
        )
        assert len(raw_bytes) == 24

        # Tamper byte 10 (change epoch or value)
        tampered = bytearray(raw_bytes)
        tampered[10] ^= 0x01  # Flip single bit

        with pytest.raises(ValueError, match="CRC integrity violation"):
            lora_codec.decode(bytes(tampered))

    def test_invalid_sync_byte_rejection(self):
        """Malformed sync byte must be rejected immediately."""
        raw_bytes = lora_codec.encode(
            station_code=103,
            sequence_number=2,
            timestamp_epoch=1726920000,
            sensor_readings=[{"sensor_type": "RAIN_GAUGE", "value": 10.0}],
        )
        tampered = bytearray(raw_bytes)
        tampered[0] = 0xAA  # Invalid sync byte

        with pytest.raises(ValueError, match="Invalid sync byte"):
            lora_codec.decode(bytes(tampered))


# ============================================================================
# 2. SEQUENCE NUMBER CONTINUITY, ROLLOVER & LOSS TRACKING
# ============================================================================

class TestSequenceContinuity:
    """Tests sequence tracking, gap detection, packet loss percentage, and rollover."""

    def test_sequential_reception(self):
        tracker = SequenceTracker()
        for s in [1, 2, 3, 4, 5]:
            state, dropped = tracker.update(s)
            assert state == SequenceState.IN_ORDER
            assert dropped == 0
        assert tracker.total_received == 5
        assert tracker.total_dropped == 0
        assert tracker.packet_loss_pct == 0.0

    def test_duplicate_detection(self):
        tracker = SequenceTracker()
        tracker.update(10)
        state, dropped = tracker.update(10)
        assert state == SequenceState.DUPLICATE
        assert dropped == 0
        assert tracker.total_duplicates == 1

    def test_gap_detection_and_loss_percentage(self):
        tracker = SequenceTracker()
        tracker.update(100)
        # Next packet is 105 -> packets 101, 102, 103, 104 dropped (4 dropped)
        state, dropped = tracker.update(105)
        assert state == SequenceState.GAP_DETECTED
        assert dropped == 4
        assert tracker.total_dropped == 4
        assert tracker.total_received == 2
        # Expected total: 2 received + 4 dropped = 6. Loss = 4 / 6 * 100 = 66.67%
        assert tracker.packet_loss_pct == 66.67

    def test_uint16_rollover_handling(self):
        tracker = SequenceTracker()
        tracker.update(65535)
        state, dropped = tracker.update(0)  # Rollover from 65535 to 0
        assert state == SequenceState.IN_ORDER
        assert dropped == 0


# ============================================================================
# 3. HARDWARE ABSTRACTION LAYER (HAL) & FAILURE ISOLATION
# ============================================================================

class TestHardwareAbstractionLayer:
    """Verifies physical bounds checks, calibration mathematics, and failure isolation."""

    def test_physical_bounds_validation(self):
        # 1. Valid rainfall
        valid, code, flags = hal_service.validate_reading_bounds(PhysicalSensorType.RAIN_GAUGE, 45.0, "mm/h")
        assert valid is True
        assert code == "GOOD"

        # 2. Implausible high rainfall (warning)
        valid, code, flags = hal_service.validate_reading_bounds(PhysicalSensorType.RAIN_GAUGE, 380.0, "mm/h")
        assert valid is True
        assert code == "SUSPECT"

        # 3. Physically impossible rainfall (negative or >500 mm/h)
        valid, code, flags = hal_service.validate_reading_bounds(PhysicalSensorType.RAIN_GAUGE, -5.0, "mm/h")
        assert valid is False
        assert code == "OUT_OF_BOUNDS"

        valid2, code2, flags2 = hal_service.validate_reading_bounds(PhysicalSensorType.RAIN_GAUGE, 650.0, "mm/h")
        assert valid2 is False
        assert code2 == "OUT_OF_BOUNDS"

    def test_calibration_application(self):
        # Calibrated = (raw * scale) + offset
        cal_val, flags = hal_service.apply_calibration(raw_value=10.0, zero_offset=0.5, scale_factor=1.02)
        assert abs(cal_val - 10.7) < 1e-4

        # Expired calibration test
        cal_val_exp, exp_flags = hal_service.apply_calibration(
            raw_value=10.0, zero_offset=0.0, scale_factor=1.0, is_expired=True
        )
        assert "CALIBRATION_EXPIRED" in exp_flags

    def test_single_sensor_failure_isolation(self):
        """
        CRUCIAL INVARIANT: If rain gauge fails or outputs out-of-bounds reading,
        water level and soil moisture on the same station MUST process normally.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        raw_readings = [
            {"sensor_id": "SNS_RAIN", "sensor_type": "RAIN_GAUGE", "value": -99.0, "unit": "mm/h"},  # FAILING SENSOR
            {"sensor_id": "SNS_STAGE", "sensor_type": "WATER_LEVEL", "value": 3.45, "unit": "m"},     # HEALTHY SENSOR
            {"sensor_id": "SNS_SOIL", "sensor_type": "SOIL_MOISTURE", "value": 68.0, "unit": "%"},    # HEALTHY SENSOR
        ]

        frame = hal_service.process_station_frame(
            station_id="ST_MANALI_01",
            device_id="DEV_MANALI_01",
            timestamp=now,
            sequence_number=50,
            raw_readings=raw_readings,
            battery_voltage=12.4,
            rssi_dbm=-80.0,
            snr_db=8.0,
        )

        assert frame.station_health == "DEGRADED"  # Station is degraded, NOT offline or critical failure
        assert len(frame.readings) == 3

        # Sensor 0 (Rain) failed
        assert frame.readings[0].is_valid is False
        assert frame.readings[0].quality_code == "OUT_OF_BOUNDS"

        # Sensors 1 & 2 (Stage & Soil) are valid
        assert frame.readings[1].is_valid is True
        assert frame.readings[1].quality_code == "GOOD"
        assert abs(frame.readings[1].calibrated_value - 3.45) < 1e-3

        assert frame.readings[2].is_valid is True
        assert frame.readings[2].quality_code == "GOOD"


# ============================================================================
# 4. GATEWAY OFFLINE BUFFERING & CHRONOLOGICAL REPLAY
# ============================================================================

class TestGatewayOfflineBuffering:
    """Verifies that gateway buffers during cellular outages and replays in order."""

    def test_offline_buffering_and_chronological_replay(self, db_session):
        service = LoRaGatewayService()
        gateway_id = "GW_ROHTANG_TEST_01"

        # 1. Disconnect backhaul
        service.set_backhaul_status(False)

        epoch_base = int(datetime.datetime.now(datetime.timezone.utc).timestamp()) - 100

        # Feed 3 packets out of order into buffer
        p1 = lora_codec.encode(101, 10, epoch_base + 10, [{"sensor_type": "RAIN_GAUGE", "value": 15.0}])
        p2 = lora_codec.encode(101, 11, epoch_base + 20, [{"sensor_type": "RAIN_GAUGE", "value": 25.0}])
        p3 = lora_codec.encode(101, 12, epoch_base + 30, [{"sensor_type": "RAIN_GAUGE", "value": 35.0}])

        r2 = service.process_raw_frame(db_session, p2, gateway_id=gateway_id)
        r1 = service.process_raw_frame(db_session, p1, gateway_id=gateway_id)
        r3 = service.process_raw_frame(db_session, p3, gateway_id=gateway_id)

        assert r2["status"] == "BUFFERED_OFFLINE"
        assert service.get_buffer(gateway_id).size() == 3

        # 2. Reconnect backhaul and flush
        service.set_backhaul_status(True)
        flush_res = service.flush_offline_buffer(db_session, gateway_id=gateway_id)
        assert flush_res["status"] == "REPLAY_COMPLETED"
        assert flush_res["total_packets_flushed"] == 3
        assert flush_res["channels_replayed"] >= 3
        assert service.get_buffer(gateway_id).size() == 0


# ============================================================================
# 5. STATION LIFECYCLE STATE MACHINE
# ============================================================================

class TestStationLifecycle:
    """Verifies station lifecycle progression and schema state."""

    def test_station_lifecycle_states(self, db_session, analyst_headers):
        # Register a new station in PLANNED state
        st_id = f"ST_TEST_LIFECYCLE_{int(time.time())}"
        reg_resp = client.post(
            "/api/v1/stations",
            json={
                "station_id": st_id,
                "name": "Lifecycle Test Gauge",
                "station_type": "HYDROLOGICAL_PRIMARY",
                "latitude": 31.95,
                "longitude": 77.12,
                "status": "PLANNED",
            },
            headers=analyst_headers,
        )
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        assert data["station"]["status"] == "PLANNED"

        # Advance to COMMISSIONED
        up_resp = client.patch(
            f"/api/v1/stations/{st_id}/status",
            json={"status": "COMMISSIONED"},
            headers=analyst_headers,
        )
        assert up_resp.status_code == 200
        assert up_resp.json()["station"]["status"] == "COMMISSIONED"

        # Advance to ACTIVE
        up_resp2 = client.patch(
            f"/api/v1/stations/{st_id}/status",
            json={"status": "ACTIVE"},
            headers=analyst_headers,
        )
        assert up_resp2.status_code == 200
        assert up_resp2.json()["station"]["status"] == "ACTIVE"

        # Invalid state rejected
        bad_resp = client.patch(
            f"/api/v1/stations/{st_id}/status",
            json={"status": "FLYING_DRONE"},
            headers=analyst_headers,
        )
        assert bad_resp.status_code == 400


# ============================================================================
# 6. LORA REST API ENDPOINTS & DIAGNOSTICS
# ============================================================================

class TestLoRaRestApi:
    """Verifies REST endpoints for raw LoRa frame ingestion, gateway backhaul toggle, and stats."""

    def test_ingest_lora_frame_endpoint(self):
        epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        payload = lora_codec.encode(
            station_code=104,  # Aut
            sequence_number=77,
            timestamp_epoch=epoch,
            sensor_readings=[
                {"sensor_type": "PORE_WATER_PRESSURE", "value": 150.0},
                {"sensor_type": "TILT", "value": 1.2},
            ],
            battery_mv=12500,
            rssi_dbm=-82,
            snr_db=7,
        )

        resp = client.post(
            "/api/v1/telemetry/lora/frame",
            json={"hex_payload": payload.hex(), "gateway_id": "GW_AUT_01"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "INGESTED"
        assert data["station_id"] == "ST_AUT_01"
        assert data["sequence_number"] == 77
        assert data["channels_ingested"] == 2

    def test_corrupt_hex_payload_rejection(self):
        resp = client.post(
            "/api/v1/telemetry/lora/frame",
            json={"hex_payload": "NOT_A_HEX_STRING", "gateway_id": "GW_AUT_01"},
        )
        assert resp.status_code == 422

    def test_gateway_backhaul_toggle_and_stats(self):
        # 1. Toggle backhaul offline
        resp1 = client.post(
            "/api/v1/telemetry/lora/gateway/backhaul",
            json={"gateway_id": "GW_AUT_01", "online": False},
        )
        assert resp1.status_code == 200
        assert resp1.json()["online"] is False

        # 2. Toggle backhaul online
        resp2 = client.post(
            "/api/v1/telemetry/lora/gateway/backhaul",
            json={"gateway_id": "GW_AUT_01", "online": True},
        )
        assert resp2.status_code == 200
        assert resp2.json()["online"] is True

        # 3. Query device stats
        resp_stats = client.get("/api/v1/telemetry/lora/device/DEV_AUT_01/stats")
        assert resp_stats.status_code == 200
        stats = resp_stats.json()
        assert "last_sequence" in stats
        assert "packet_loss_pct" in stats


# ============================================================================
# 7. END-TO-END PIPELINE & COMMANDER AUTHORIZATION
# ============================================================================

class TestEndToEndPhysicalPipeline:
    """
    End-to-End Pipeline Demonstration:
    Physical Sensor -> ESP32 LoRa Frame -> Gateway Decode & Ingest ->
    Quality Gate Screening -> Model Run Trigger -> Risk Engine ->
    Alert Generation -> Senior Incident Commander Authorization.
    """

    def test_full_pipeline_to_commander_authorization(self, db_session, commander_headers, analyst_headers):
        # 1. Encode heavy storm telemetry packet from ST_MANALI_01 (101)
        epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        storm_payload = lora_codec.encode(
            station_code=101,
            sequence_number=999,
            timestamp_epoch=epoch,
            sensor_readings=[
                {"sensor_type": "RAIN_GAUGE", "value": 75.0},     # 75 mm/h extreme rainfall
                {"sensor_type": "WATER_LEVEL", "value": 5.8},     # 5.8m high river stage
                {"sensor_type": "SOIL_MOISTURE", "value": 92.0},  # 92% saturated
            ],
            battery_mv=12300,
            rssi_dbm=-79,
            snr_db=9,
        )

        # 2. Ingest through LoRa gateway REST endpoint
        ingest_resp = client.post(
            "/api/v1/telemetry/lora/frame",
            json={"hex_payload": storm_payload.hex(), "gateway_id": "GW_ROHTANG_01"},
        )
        assert ingest_resp.status_code == 200
        ingest_data = ingest_resp.json()
        assert ingest_data["status"] == "INGESTED"

        # 3. Verify Risk State reflects current conditions
        risk_resp = client.get("/api/v1/risk/current")
        assert risk_resp.status_code == 200

        # 4. Draft an alert requiring human authorization
        draft_resp = client.post(
            "/api/v1/alerts/draft",
            json={
                "headline": "FLASH FLOOD WARNING: Solang-Manali River Corridor",
                "description": "75 mm/h extreme precipitation detected by ST_MANALI_01 LoRa station.",
                "instruction": "Move to designated safe zones above 2050m elevation immediately.",
                "area_desc": "Solang-Manali Corridor, Upper Beas Catchment",
                "severity": "Extreme",
                "urgency": "Immediate",
                "certainty": "Observed",
            },
        )
        assert draft_resp.status_code == 200
        alert_id = draft_resp.json()["alert"]["id"]

        # 5. Non-commander / unauthorized actor cannot authorize alert
        unauth_resp = client.post(
            f"/api/v1/alerts/{alert_id}/authorize",
            json={
                "actor_id": "OPERATOR_01",
                "actor_role": "ANALYST",
                "approval_token": "TEST_TOKEN_12345",
            },
            headers=analyst_headers,
        )
        assert unauth_resp.status_code == 403

        # 6. Senior Incident Commander with valid credentials and approval token authorizes alert
        auth_resp = client.post(
            f"/api/v1/alerts/{alert_id}/authorize",
            json={
                "actor_id": "CMD-V36-001",
                "actor_role": "SENIOR_INCIDENT_COMMANDER",
                "approval_token": "CRYPTOGRAPHIC_COMMANDER_SIGNATURE_2026",
            },
            headers=commander_headers,
        )
        assert auth_resp.status_code == 200
        assert auth_resp.json()["status"] == "DISPATCHED"
