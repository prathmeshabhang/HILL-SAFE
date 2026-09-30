# FLOODY SHIELD v3.6 — PostgreSQL & PostGIS Backup/Restore Protocol

**System:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin, Kullu–Manali, Himachal Pradesh, India  
**Date:** September 2026  
**Scope:** Production Disaster Recovery (DR), Point-In-Time Recovery (PITR), Spatial Table Integrity, and PostGIS Extension Preservation.

---

## 1. Objectives and SLAs

| Metric | Target SLA | Definition |
|:---|:---|:---|
| **Recovery Point Objective (RPO)** | **< 15 minutes** | Maximum allowable data loss during disaster. Satisfied by WAL archiving. |
| **Recovery Time Objective (RTO)** | **< 30 minutes** | Total time to restore full operational service from cold storage backup. |
| **Integrity Assurance** | **100% SHA-256 Match** | Cryptographic verification of backup files before restore. |
| **Spatial Integrity** | **Zero Topology Errors** | PostGIS geometries (`Point`, `LineString`, `Polygon`) remain valid (`ST_IsValid`). |

---

## 2. Backup Architecture & Procedures

### 2.1 Backup Script Invocation

The automated backup utility is located at `scripts/backup_db.py`.

```bash
# Backup with automatic PostgreSQL / PostGIS detection:
python scripts/backup_db.py --output backups/

# Custom database URL:
DATABASE_URL="postgresql://floody:floody_secret@localhost:5432/floody_shield" python scripts/backup_db.py
```

### 2.2 Native `pg_dump` Execution

For production deployments, `pg_dump` is invoked in custom binary format (`--format=c`), which enables multi-threaded restore, selective schema restoration, and PostGIS topology preservation:

```bash
pg_dump \
  --format=c \
  --blobs \
  --no-owner \
  --no-privileges \
  --file="backups/floody_shield_pg_$(date +%Y%m%d_%H%M%SZ).dump" \
  "$DATABASE_URL"
```

### 2.3 PostGIS Extension Handling

To prevent extension conflicts during restoration on a newly provisioned database, extensions (`postgis`, `postgis_topology`) must exist in the target database before executing schema restore:

```sql
-- Target database initialization:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

---

## 3. Restoration Procedure

### 3.1 Restore Script Invocation

```bash
# Restore from manifest:
python scripts/restore_db.py --manifest backups/floody_shield_pg_20260921_140000Z.manifest.json

# Direct dump file restore:
pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --jobs=4 \
  --dbname="$DATABASE_URL" \
  "backups/floody_shield_pg_20260921_140000Z.dump"
```

### 3.2 Post-Restore Verification Checklist

1. **Schema & Migration Alignment**:
   ```bash
   alembic current
   # Expected output: c4b1829e5a10 (head)
   ```

2. **Row Count Verification**:
   ```sql
   SELECT count(*) FROM sensor_stations;
   SELECT count(*) FROM devices;
   SELECT count(*) FROM sensors;
   SELECT count(*) FROM sensor_observations;
   SELECT count(*) FROM alert_records;
   SELECT count(*) FROM audit_events;
   ```

3. **PostGIS Spatial Validity Check**:
   ```sql
   -- Verify all station and hazard polygons are valid geometries
   SELECT id, ST_IsValid(geometry) FROM spatial_features WHERE NOT ST_IsValid(geometry);
   -- Expected: 0 rows returned
   ```

4. **Tamper-Evident Audit Chain Check**:
   ```sql
   -- Verify that audit hash chaining is continuous and uncorrupted
   SELECT count(*) FROM audit_events WHERE signature_valid = false;
   -- Expected: 0 rows
   ```

---

## 4. Disaster Recovery Drill Schedule & Sign-Off

- **Scheduled Drills**: Executed monthly during low-flow season (Nov–Feb); bi-weekly during pre-monsoon ramp-up (May–June).
- **Storage Tiering**: Daily dumps retained for 30 days; weekly snapshots retained for 1 year in geo-redundant storage (Coldline/Archive).
- **Drill Sign-off**: Every restoration test requires sign-off from both the SRE Lead and the Incident Operations Officer.
