# FLOODY SHIELD v3.4 — Disaster Recovery & Database Backup Specification

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Scope**: Backup Automation, Cryptographic Manifests, Integrity Verification, Rollback Procedures  

---

## 1. Disaster Recovery Objectives

- **RPO (Recovery Point Objective)**: $\le 1\text{ hour}$ during active monsoon/cyclone seasons; $\le 6\text{ hours}$ dry season.
- **RTO (Recovery Time Objective)**: $\le 15\text{ minutes}$ for complete database restoration.
- **Data Integrity**: Cryptographic SHA-256 validation mandatory before any backup is restored to prevent data corruption.

---

## 2. Automated Backup Execution (`scripts/backup_db.py` / `backup_db.sh`)

FLOODY SHIELD includes a cross-platform backup utility supporting both SQLite (prototype) and PostgreSQL (production):

### Usage
```bash
# Execute backup
python scripts/backup_db.py --out ./backups

# Linux bash wrapper
bash scripts/backup_db.sh
```

### Process Flow
1. **Engine Detection**: Inspects `DATABASE_URL`.
   - If PostgreSQL: invokes `pg_dump --format=c` for compressed binary dumps.
   - If SQLite: executes atomic snapshot of `data/floody_shield.db`.
2. **SHA-256 Checksum**: Computes byte-exact SHA-256 checksum over the output file.
3. **Manifest Creation**: Writes a JSON metadata manifest file containing:
   - `timestamp_utc`: ISO-8601 UTC timestamp.
   - `backup_file`: Output filename.
   - `size_bytes`: File size in bytes.
   - `sha256`: Hexadecimal SHA-256 hash.
   - `system_version`: System version (`v3.4`).
   - `engine`: `postgresql` or `sqlite`.

---

## 3. Database Restoration & Rollback (`scripts/restore_db.py` / `restore_db.sh`)

### Usage
```bash
python scripts/restore_db.py backups/floody_shield_sqlite_20260921_123658Z.db \
    --manifest backups/floody_shield_manifest_20260921_123658Z.json
```

### Safety Features
1. **Pre-Restoration Verification**: If `--manifest` is provided, the script recomputes the SHA-256 checksum of the backup file and matches it against the manifest. If hashes do not match, restoration aborts immediately.
2. **Rollback Snapshot**: Before overwriting the active database, a safety snapshot is created at `data/floody_shield.db.pre_restore_bak`. If any restoration step fails, the previous operational state can be restored instantly.
3. **Clean Restore**:
   - For PostgreSQL: executes `pg_restore --clean --if-exists`.
   - For SQLite: safely replaces the database file.

---

## 4. Crontab Schedule for Linux EOC Servers

```cron
# Every hour during monsoon season (June to September)
0 * * 6,7,8,9 * /opt/floody-shield/scripts/backup_db.sh >> /var/log/floody_backup.log 2>&1

# Every 6 hours during non-monsoon season
0 */6 * 1-5,10-12 * /opt/floody-shield/scripts/backup_db.sh >> /var/log/floody_backup.log 2>&1
```
