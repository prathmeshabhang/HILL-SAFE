# FLOODY SHIELD v3.3 — Backend Architecture Specification

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Version**: 3.3.0 (Operational Monolith & Real-Time Data Platform)  
**Date**: September 2026  

---

## 1. Executive Summary

FLOODY SHIELD v3.3 transforms the research and prototype microservices of v3.2+ into an operational, enterprise-grade decision-support backend for Himalayan flash-flood, landslide, cascade-risk, infrastructure-damage, and evacuation-routing operations.

The architecture is built as a **Hardened Modular Monolith** in FastAPI and SQLAlchemy, running against PostgreSQL with PostGIS spatial extensions (with seamless SQLite fallback for testing and development environments).

```
+-----------------------------------------------------------------------------------+
|                           PRESENTATION & CLIENT LAYER                             |
|  - EOC Command Console (Web UI)        - Mobile Field Client (PWA/Android)        |
|  - Real-Time WebSocket Subscribers     - GIS Mapping / MapLibre Clients           |
+-----------------------------------------------------------------------------------+
                                         │  (HTTP / SSE / WebSocket)
                                         ▼
+-----------------------------------------------------------------------------------+
|                              FASTAPI API GATEWAY                                  |
|  - Request Context & Correlation ID Middleware                                    |
|  - CORS & Security Headers                                                        |
|  - RBAC Enforcement & Cryptographic JWT Verification                              |
|  - Structured FloodyShieldException Handler                                       |
+-----------------------------------------------------------------------------------+
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
+──────────────────+           +──────────────────+           +──────────────────+
| INGESTION & QC   |           | MODEL ORCHESTR.  |           | RISK & DECISION  |
| - IMD AWS        |           | - Topological DAG|           | - Unified Risk   |
| - GPM IMERG      |           | - Dependency Graph           | - Provenance     |
| - CWC River      |           | - Failure Isol.  |           | - CAP v1.2 Engine|
| - Sentinel SAR   |           | - Adapter Layer  |           | - Commander Gate |
| - IoT Stations   |           | - Model Runs Log |           | - Life-Safety    |
+──────────────────+           +──────────────────+           +──────────────────+
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         ▼
+-----------------------------------------------------------------------------------+
|                        DATABASE & PERSISTENCE LAYER                               |
|  - PostgreSQL 15 + PostGIS 3.3 (GeoAlchemy2)                                      |
|  - Alembic Bi-Directional Database Migrations                                     |
|  - Append-Only Tamper-Evident SHA-256 Audit Trail Hash Chaining                   |
|  - Strict Provenance: OBSERVED | PREDICTED | MODELLED | DERIVED                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Life-Safety Invariant (Strict Human Gateway)**:
   AI and physics models **never autonomously issue public alerts**. All hazard detections above alert thresholds automatically generate an alert draft with status `PENDING_APPROVAL`. Transition to `DISPATCHED` requires explicit cryptographic authorization and token validation by a verified `SENIOR_INCIDENT_COMMANDER`.
2. **Strict Data Provenance**:
   Every data point, model output, and decision record in the database is explicitly categorized:
   - `OBSERVED`: Raw or normalized in-situ and satellite sensor readings.
   - `PREDICTED`: Direct inferential outputs from ML/deep learning models (e.g. M1, M2, M6, M7).
   - `MODELLED`: Physics-based hydrodynamic and geotechnical simulations (e.g. PWP, M10, M11, M12).
   - `DERIVED`: Multi-source synthesized risk states, safe zones, and routing plans (e.g. M13, M14, M15, M16).
3. **Scientific Integrity & Artifact Preservation**:
   All 20 scientific and ML models (M1–M20) remain intact. Frozen model weights and artifact hashes (M2 Random Forest, M4 DeepLabV3+, M6 Random Forest, M7 LightGBM) are verified on startup and during test execution. Model failures are isolated and never collapse to artificial zero probabilities.
4. **Resilience & High-Availability**:
   All external data adapters feature timeout handling, retry logic, and fallback pipelines. Quality gates validate physical limits, detect clock skew, enforce spatial bounding, and screen for multivariate sensor anomalies via M9 Isolation Forests.

---

## 3. Directory Layout & Module Responsibilities

```text
backend/app/
├── api/
│   └── v1/
│       ├── endpoints/          # Granular REST Endpoints
│       │   ├── alerts.py       # CAP Alert lifecycle & acknowledgements
│       │   ├── audit.py        # Tamper-evident hash chain verification
│       │   ├── auth.py         # JWT authentication & RBAC user management
│       │   ├── dashboard.py    # Executive EOC operational summary
│       │   ├── gis.py          # PostGIS GeoJSON hazard & safe zone services
│       │   ├── health.py       # Kubernetes liveness & readiness probes
│       │   ├── incidents.py    # Incident tracking & historical replay
│       │   ├── models.py       # Model catalog & adapter inference
│       │   ├── pipeline.py     # End-to-end decision pipeline
│       │   └── telemetry_ingest.py # Multi-source observation ingestion
│       └── router.py           # Master API v1 Router
├── core/
│   ├── config.py               # Pydantic BaseSettings configuration
│   ├── errors.py               # Standardized hierarchical domain exceptions
│   ├── logging.py              # Structured JSON/Console logging
│   ├── request_context.py      # Request ID & tracing middleware
│   └── security.py             # Bcrypt password hashing & JWT handling
├── database/
│   ├── models/                 # SQLAlchemy 2.0 Declarative Models
│   │   ├── alert.py            # AlertDispatch & AlertAcknowledgement
│   │   ├── audit.py            # AuditLog with SHA-256 hash chaining
│   │   ├── incident.py         # Incident tracking
│   │   ├── ingestion.py        # DataIngestionRun & DataQualityRecord
│   │   ├── model_run.py        # ModelRun execution logs & output hashes
│   │   ├── risk.py             # RiskState & RiskZone
│   │   ├── spatial.py          # PostGIS Infrastructure, Safe Zones, Population
│   │   ├── telemetry.py        # SensorStation & SensorObservation
│   │   └── user.py             # UserModel with RBAC roles
│   └── session.py              # Engine factory, connection pooling, SQLite fallback
├── inference/
│   ├── adapters/               # Standardized Model Adapters (M1-M20)
│   └── registry.py             # Artifact verification & catalog service
├── orchestration/
│   ├── engine.py               # Topological DAG execution engine
│   ├── graph.py                # Pipeline dependency graph definition
│   └── state.py                # Node execution state & result tracking
├── services/
│   ├── alerts/                 # Alert lifecycle & dispatch service
│   ├── gis/                    # Spatial query & GeoJSON service
│   ├── incident/               # Incident replay & retrospective analysis
│   ├── ingestion/              # Data source adapters & quality gate
│   └── risk/                   # Unified multi-hazard risk fusion engine
└── websocket/
    ├── endpoint.py             # WebSocket endpoint /ws/v1/events
    ├── events.py               # Typed event schemas
    └── manager.py              # Connection pooling & broadcast engine
```

---

## 4. Operational Monolith Verification

The backend passes:
- **50 / 50** Backend Architecture & Integration Tests
- **10 / 10** Strict Life-Safety Critical Invariant Tests
- Full end-to-end heavy rainfall scenario simulation with OASIS CAP v1.2 generation and tamper-evident audit verification.
