# FLOODY SHIELD v3.3 — End-to-End Operational Disaster Lifecycle Flow

**System**: FLOODY SHIELD  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Verified By**: `backend/tests/test_e2e_scenario.py`  

---

## 1. Complete Operational Disaster Lifecycle

The diagram below traces a catastrophic monsoon storm scenario through every stage of the FLOODY SHIELD v3.3 architecture:

```mermaid
sequenceDiagram
    autonumber
    participant AWS as IMD Rain Gauge / CWC Stage
    participant Ingest as Ingestion & Quality Gate
    participant DB as PostgreSQL / PostGIS DB
    participant Orch as Model Orchestration DAG
    participant Risk as Unified Risk Engine
    participant AlertSvc as Alert Lifecycle Service
    participant WS as WebSocket Hub (/ws/v1/events)
    participant EOC as Incident Commander Console
    participant Siren as NDMA Sachet / Sirens

    Note over AWS,Siren: PHASE 1: OBSERVATION & QUALITY GATING
    AWS->>Ingest: Ingest raw storm telemetry (72 mm/h rain, 7.4m river stage)
    Ingest->>Ingest: Validate spatial bounds, clock skew, physical limits, M9 anomaly
    Ingest->>DB: Persist SensorObservation (OBSERVED, Idempotent SHA-256)
    Ingest->>WS: Broadcast TELEMETRY_INGESTED event

    Note over AWS,Siren: PHASE 2: TOPOLOGICAL MODEL ORCHESTRATION
    Ingest->>Orch: Trigger hazard DAG execution for Incident
    Orch->>DB: Log M1, M2, M4, M6, M7, PWP, M10, M11, M12 ModelRuns (PREDICTED/MODELLED)
    Orch->>Risk: Pass multi-hazard outputs to Unified Risk Engine

    Note over AWS,Siren: PHASE 3: RISK FUSION & DRAFT CREATION
    Risk->>Risk: Compute joint hazard probability & socio-economic vulnerability
    Risk->>DB: Persist authoritative RiskState (CRITICAL, score=0.88)
    Risk->>AlertSvc: Threat exceeds red threshold -> Auto-generate Alert Draft
    AlertSvc->>DB: Persist AlertDispatch (status=PENDING_APPROVAL)
    AlertSvc->>WS: Broadcast ALERT_DRAFT_CREATED event

    Note over AWS,Siren: PHASE 4: COMMANDER AUTHORIZATION (LIFE-SAFETY GATE)
    WS->>EOC: Display red alert draft on Commander dashboard
    EOC->>AlertSvc: POST /alerts/{id}/authorize (Commander token, badge=HPSDMA_CMD_01)
    AlertSvc->>AlertSvc: Verify RBAC role == SENIOR_INCIDENT_COMMANDER
    AlertSvc->>AlertSvc: Generate bilingual ITU-T X.1303 CAP v1.2 XML
    AlertSvc->>DB: Transition alert status to DISPATCHED
    AlertSvc->>DB: Insert append-only AuditLog with SHA-256 hash chaining

    Note over AWS,Siren: PHASE 5: PUBLIC DISPATCH & CONFIRMATION
    AlertSvc->>WS: Broadcast ALERT_DISPATCHED event
    WS->>Siren: Trigger Aut & Larji riverbed sirens; push to mobile broadcast
    Siren->>AlertSvc: POST /alerts/{id}/acknowledge (Squad 4, channel=EOC_RADIO)
    AlertSvc->>DB: Record AlertAcknowledgement (status=CONFIRMED)
    AlertSvc->>WS: Broadcast ALERT_ACKNOWLEDGED event
```

---

## 2. End-to-End Test Verification

The complete 8-step lifecycle above is validated in `backend/tests/test_e2e_scenario.py`:
- `test_heavy_rainfall_end_to_end_scenario`:
  1. Weather telemetry ingestion & normalization
  2. River stage observation ingestion & normalization
  3. Topological DAG execution across 17 model nodes
  4. Unified Risk State synthesis ($R_{\text{composite}} \ge 0.80$)
  5. Automated alert draft creation in `PENDING_APPROVAL`
  6. Cryptographic Commander authorization & CAP v1.2 generation
  7. Downstream radio/siren field acknowledgement
  8. Tamper-evident SHA-256 audit hash chain verification

All 8 steps pass with 100% determinism.
