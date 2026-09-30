"""
scripts/verify_backup_restore.py
================================
Automated End-to-End Disaster Recovery & Database Integrity Verification for FLOODY SHIELD v4.0.
Verifies:
  1. Full database backup generation with table row count manifests.
  2. SHA-256 cryptographic checksum calculation and verification.
  3. Clean restoration to a target database without data corruption.
  4. Post-restoration table presence, row counts, and data query verification.
  5. Tamper detection: verification fails if backup content is modified.
"""

import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.backup_db import backup_database, compute_sha256
from scripts.restore_db import restore_database, count_sqlite_table_rows
from backend.app.database.session import Base
import backend.app.database.models  # Register all 20 models


def verify_backup_and_restore() -> bool:
    print("=" * 72)
    print("FLOODY SHIELD v4.0: DISASTER RECOVERY & BACKUP/RESTORE VERIFICATION")
    print("=" * 72)

    work_dir = Path(tempfile.mkdtemp(prefix="floody_dr_test_"))
    try:
        source_db = work_dir / "source_test.db"
        backup_dir = work_dir / "backups"
        restored_db = work_dir / "restored_test.db"

        print(f"[*] Working temporary test directory: {work_dir}")

        # Step 1: Initialize full schema in source DB
        import sqlalchemy as sa
        eng = sa.create_engine(f"sqlite:///{source_db.as_posix()}")
        Base.metadata.create_all(bind=eng)
        print(f"[+] Initialized {len(Base.metadata.tables)} model tables in source DB.")

        # Step 2: Seed realistic records
        from sqlalchemy.orm import sessionmaker
        from backend.app.database.models.user import UserModel
        from backend.app.database.models.telemetry import SensorStationModel, SensorObservationModel
        from backend.app.database.models.incident import IncidentModel

        Session = sessionmaker(bind=eng)
        session = Session()

        # Seed Users
        u1 = UserModel(
            id="USR_EOC_01",
            username="commander_kullu",
            email="commander@hpsdma.gov.in",
            hashed_password="sha256_mock_hash",
            role="SENIOR_INCIDENT_COMMANDER",
            full_name="Col. V. Pathania",
            agency="HPSDMA EOC",
            is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        u2 = UserModel(
            id="USR_ANALYST_01",
            username="analyst_manali",
            email="analyst@hpsdma.gov.in",
            hashed_password="sha256_mock_hash",
            role="ANALYST",
            full_name="Dr. S. Negi",
            agency="HPSDMA Science Cell",
            is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add_all([u1, u2])

        # Seed Stations
        st1 = SensorStationModel(
            id="STN_BEAS_PALCHAN_01",
            name="Palchan Upper Beas Hydro Gauge",
            station_type="MET_HYDRO_IOT",
            latitude=32.3125,
            longitude=77.1648,
            elevation_m=2280.0,
            river_basin="Upper Beas Basin",
            status="ACTIVE",
            is_active=True,
            last_heartbeat=datetime.datetime.now(datetime.timezone.utc),
        )
        st2 = SensorStationModel(
            id="STN_BEAS_BHUNTAR_01",
            name="Bhuntar Confluence Gauge",
            station_type="MET_HYDRO_IOT",
            latitude=31.8790,
            longitude=77.1550,
            elevation_m=1090.0,
            river_basin="Upper Beas Basin",
            status="ACTIVE",
            is_active=True,
            last_heartbeat=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add_all([st1, st2])

        # Seed Observations
        now = datetime.datetime.now(datetime.timezone.utc)
        obs1 = SensorObservationModel(
            station_id="STN_BEAS_PALCHAN_01",
            data_source_id="UPPER_BEAS_IOT",
            source_event_id="EVT_PALCHAN_001",
            idempotency_hash="EVT_PALCHAN_001",
            timestamp=now,
            observed_at=now,
            measurement_type="WATER_LEVEL",
            value=3.45,
            unit="m",
            quality_state="FRESH",
            temporal_state="VALID",
            provenance="REAL_FIELD_OBSERVATION",
            environment="FIELD",
        )
        obs2 = SensorObservationModel(
            station_id="STN_BEAS_PALCHAN_01",
            data_source_id="UPPER_BEAS_IOT",
            source_event_id="EVT_PALCHAN_002",
            idempotency_hash="EVT_PALCHAN_002",
            timestamp=now,
            observed_at=now,
            measurement_type="RAINFALL",
            value=24.5,
            unit="mm/h",
            quality_state="FRESH",
            temporal_state="VALID",
            provenance="REAL_FIELD_OBSERVATION",
            environment="FIELD",
        )
        session.add_all([obs1, obs2])

        # Seed Incident
        inc1 = IncidentModel(
            id="INC_KULLU_2026_01",
            incident_type="FLASH_FLOOD",
            severity_level="WARNING",
            trigger_source="HYDROLOGICAL_CASCADE",
            trigger_location="Palchan Gorge",
            latitude=32.3125,
            longitude=77.1648,
            dam_height_m=0.0,
            impounded_volume_m3=0.0,
            rainfall_rate_mmh=24.5,
            status="ACTIVE",
            summary="Rapid discharge surge detected at Palchan.",
            created_at=now,
        )
        session.add(inc1)

        session.commit()
        session.close()
        eng.dispose()

        print("[+] Seeded test records: 2 users, 2 stations, 2 observations, 1 incident.")

        # Step 3: Run backup
        print("\n[*] Running backup_database()...")
        backup_file, manifest_file = backup_database(
            output_dir=backup_dir,
            source_path=source_db,
        )

        assert backup_file.exists(), "Backup file was not created!"
        assert manifest_file.exists(), "Manifest file was not created!"
        print(f"[PASS] Backup created: {backup_file.name}")
        print(f"[PASS] Manifest created: {manifest_file.name}")

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["system_version"] == "v4.0"
        assert manifest["tables"]["users"] == 2
        assert manifest["tables"]["sensor_stations"] == 2
        assert manifest["tables"]["sensor_observations"] == 2
        assert manifest["tables"]["incidents"] == 1
        assert manifest["total_rows"] == 7
        print(f"[PASS] Manifest metadata validated: 7 seeded rows across 4 tables verified.")

        # Step 4: Run restoration to a fresh location
        print("\n[*] Running restore_database() to target...")
        restore_success = restore_database(
            backup_file=backup_file,
            manifest_file=manifest_file,
            target_path=restored_db,
        )
        assert restore_success, "Restoration failed!"
        print("[PASS] Database restored successfully.")

        # Step 5: Verify restored database content & queries
        restored_eng = sa.create_engine(f"sqlite:///{restored_db.as_posix()}")
        RestoredSession = sessionmaker(bind=restored_eng)
        r_session = RestoredSession()

        restored_users = r_session.query(UserModel).all()
        assert len(restored_users) == 2
        assert {u.username for u in restored_users} == {"commander_kullu", "analyst_manali"}
        print("[PASS] Restored users table verified: all records intact.")

        restored_stations = r_session.query(SensorStationModel).all()
        assert len(restored_stations) == 2
        palchan = r_session.query(SensorStationModel).filter_by(id="STN_BEAS_PALCHAN_01").first()
        assert palchan is not None
        assert abs(palchan.latitude - 32.3125) < 1e-4
        assert palchan.status == "ACTIVE"
        print("[PASS] Restored sensor_stations table verified: coordinates and status intact.")

        restored_obs = r_session.query(SensorObservationModel).all()
        assert len(restored_obs) == 2
        assert {o.provenance for o in restored_obs} == {"REAL_FIELD_OBSERVATION"}
        print("[PASS] Restored sensor_observations verified: provenance tags intact.")

        r_session.close()
        restored_eng.dispose()

        # Step 6: Test tamper detection
        print("\n[*] Testing tamper resistance (corrupted backup detection)...")
        corrupt_backup = work_dir / "corrupted_backup.db"
        shutil.copy2(backup_file, corrupt_backup)
        # Flip bytes in corrupted backup
        with open(corrupt_backup, "r+b") as f:
            f.seek(50)
            f.write(b"\xFF\xFF\xFF\xFF")

        tamper_target = work_dir / "tamper_target.db"
        tamper_restored = restore_database(
            backup_file=corrupt_backup,
            manifest_file=manifest_file,
            target_path=tamper_target,
        )
        assert not tamper_restored, "Tampered backup should have been rejected by checksum check!"
        print("[PASS] Tamper detection verified: altered backup was rejected.")

        print("\n" + "=" * 72)
        print("ALL DISASTER RECOVERY & BACKUP/RESTORE VERIFICATIONS PASSED [100%]")
        print("=" * 72)
        return True

    finally:
        # Cleanup temporary files
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    success = verify_backup_and_restore()
    sys.exit(0 if success else 1)
