# FLOODY SHIELD v3.4 — Production Deployment & Hardening Guide

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Scope**: Server Sizing, Environment Variables, Docker/Uvicorn Setup, PostGIS Configuration  

---

## 1. System Requirements & Sizing

| Resource | Minimum (Edge/Dev) | Recommended (Production EOC) |
| :--- | :--- | :--- |
| **CPU** | 4 Cores (x86_64) | 8–16 Cores (Intel Xeon / AMD EPYC) |
| **RAM** | 8 GB | 32 GB (to host UNet CPU tensors & rasters) |
| **Storage** | 50 GB SSD | 500 GB NVMe (for Sentinel SAR rasters & DB) |
| **OS** | Ubuntu 22.04 LTS / Windows Server 2022 | Ubuntu 22.04 LTS |
| **Database** | SQLite (prototype only) | PostgreSQL 15+ with PostGIS 3.3+ |
| **Python** | 3.11.x | 3.11.x |

---

## 2. Environment Configuration

Create a `.env` file in the project root:

```ini
# Application Configuration
APP_NAME="FLOODY SHIELD Decision Platform"
APP_VERSION="3.4.0"
ENVIRONMENT="production"
DEBUG=False
SECRET_KEY="<GENERATE_RANDOM_64_CHAR_HEX_KEY>"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database Configuration
# Production PostgreSQL + PostGIS:
DATABASE_URL="postgresql://floody:SecureDbPass2026@localhost:5432/floody_shield"

# CORS Configuration
CORS_ORIGINS=["https://eoc.hp.gov.in", "https://floody.hpsdma.nic.in"]

# NDMA Sachet Integration Credentials
NDMA_SACHET_ENDPOINT="https://sachet.ndma.gov.in/api/v1/cap/dispatch"
NDMA_CLIENT_CERT="/etc/ssl/certs/ndma_sachet_client.crt"
NDMA_CLIENT_KEY="/etc/ssl/private/ndma_sachet_client.key"
NDMA_CA_CERT="/etc/ssl/certs/ndma_ca_bundle.crt"
NDMA_TIMEOUT_SEC=15.0
NDMA_RETRY_COUNT=3

# External Sensor Data Directories
DATA_ROOT="./data"
MODEL_REGISTRY_PATH="./models/registry.json"
```

---

## 3. Database Initialization & Alembic Migrations

To apply database schema migrations in production:

```bash
# Verify Alembic status
alembic current

# Run migrations up to latest revision
alembic upgrade head
```

---

## 4. Production Service Execution (Systemd / Uvicorn)

For high-throughput deployment under Linux systemd:

`/etc/systemd/system/floody-shield.service`:
```ini
[Unit]
Description=FLOODY SHIELD v3.4 Disaster Early Warning Microservice
After=network.target postgresql.service

[Service]
User=floody
Group=floody
WorkingDirectory=/opt/floody-shield
EnvironmentFile=/opt/floody-shield/.env
ExecStart=/opt/floody-shield/.venv/bin/uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --proxy-headers \
    --forwarded-allow-ips='*'

Restart=always
RestartSec=5s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable floody-shield
sudo systemctl start floody-shield
```

---

## 5. Reverse Proxy & TLS Configuration (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name eoc.hpsdma.nic.in;

    ssl_certificate /etc/letsencrypt/live/eoc.hpsdma.nic.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/eoc.hpsdma.nic.in/privkey.pem;

    # Forward to Floody Shield ASGI backend
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Real-Time WebSocket Streaming Support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
    }
}
```
