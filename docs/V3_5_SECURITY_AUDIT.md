# FLOODY SHIELD v3.5 — Security Audit & Threat Model Report

**Project:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**Security Classification:** LIFE-SAFETY OPERATIONAL CRITICAL  
**Audit Scope:** Authentication, Authorization (RBAC), Telemetry Integrity, Tamper-Evident Auditing & Gateway Defenses  

---

## 1. Threat Model & Operational Context

FLOODY SHIELD operates as a research-grade decision-support and early-warning platform for flash floods, landslides, and cascading debris flows. In emergency management, security breaches have direct life-safety implications:
1. **Rogue / False Alert Broadcast**: An adversary injecting spoofed telemetry to trigger mass panic or unnecessary evacuations.
2. **Alert Suppression**: Disabling alerts during an actual catastrophe, trapping populations in inundation zones.
3. **Telemetry Tampering / Replay Attacks**: Falsifying sensor readings or replaying past storm packets to mislead predictive models.
4. **Audit Log Erasure**: Covering up operational failures or unauthorized overrides.

---

## 2. Role-Based Access Control (RBAC) Matrix

Access control is strictly enforced via cryptographically signed JWT bearer tokens (`HS256`, 24-hour expiration):

| Resource / Endpoint | OBSERVER | DATA_ANALYST | FIELD_RESPONDER | SENIOR_INCIDENT_COMMANDER | SYSTEM_ADMIN |
|---|---|---|---|---|---|
| `GET /api/v1/telemetry/*` | Read | Read | Read | Read | Read |
| `POST /api/v1/telemetry` | Denied (401/403) | Ingest | Ingest | Ingest | Ingest |
| `GET /api/v1/risk/current` | Read | Read | Read | Read | Read |
| `POST /api/v1/alerts/draft` | Denied (403) | Create | Denied (403) | Create | Create |
| `POST /api/v1/alerts/{id}/authorize` | **DENIED (403)** | **DENIED (403)** | **DENIED (403)** | **AUTHORIZED (200)** | **DENIED (403)** |
| `POST /api/v1/alerts/{id}/cancel` | Denied (403) | Denied (403) | Denied (403) | Authorized (200) | Authorized (200) |
| `POST /api/v1/stations` | Denied (403) | Authorized (200) | Denied (403) | Authorized (200) | Authorized (200) |
| `GET /api/v1/audit/verify-chain` | Read | Read | Read | Read | Read |

### Statutory Life-Safety Authorization Gateway
- **REST Endpoint**: `POST /api/v1/alerts/{id}/authorize`
- **Enforcement**:
  1. `actor_role` must strictly equal `SENIOR_INCIDENT_COMMANDER`.
  2. `approval_token` must be non-empty and meet minimum length requirements.
  3. Action is cryptographically chained into `audit_logs` before alert status transitions to `DISPATCHED`.
  4. Any non-commander role attempting authorization receives HTTP 403 Forbidden.

---

## 3. Telemetry Gateway & Anti-Tampering Defenses

### 3.1 Deterministic SHA-256 Idempotency
Each incoming telemetry packet is hashed over its invariant attributes:
$$\text{source\_event\_id} = \text{SHA256}(\text{source\_id} + \text{station\_id} + \text{device\_id} + \text{sensor\_id} + \text{measurement\_type} + \text{sequence\_number} + \text{observed\_at})$$

- **Duplicate Submission**: If a packet with identical `source_event_id` and identical `value` is received again, the system acknowledges it safely (`is_duplicate: True`) without inserting duplicate rows.
- **Tampered Replay Attack**: If a packet with identical `source_event_id` is received with an altered `value` ($|v_{\text{existing}} - v_{\text{incoming}}| > 10^{-5}$), the gateway immediately aborts and returns:
  ```text
  HTTP 409 Conflict
  Code: TELEMETRY_INTEGRITY_VIOLATION
  ```

### 3.2 Temporal Validation & Anti-Skew Defense
Incoming packets are evaluated against UTC gateway time:
- $\Delta t > 120\text{ min}$ into future: HTTP 422 Unprocessable Entity (`TELEMETRY_FUTURE_TIMESTAMP`).
- $5\text{ min} < \Delta t \le 120\text{ min}$ into future: Flagged as `INVALID` with `CRITICAL_ERROR` quality state.
- $\Delta t > 24\text{ hours}$ in past: Flagged as `EXPIRED`.
- $\Delta t > 6\text{ hours}$ in past: Flagged as `STALE`.
- $\Delta t > 1\text{ hour}$ in past: Flagged as `LATE`.

---

## 4. WebSocket Security & Isolation

- **Authentication**: WebSocket handshake enforces token authentication.
- **Read-Only Event Streaming**: WebSockets operate strictly as event dispatch channels for live telemetry, model runs, and alert broadcasts.
- **Explicit Authorization Prohibition**:
  `WEBSOCKET_AUTHORIZATION_PROHIBITED`: The system explicitly disallows any attempt to authorize or dispatch emergency alerts over WebSocket connections. Life-safety authorization MUST pass through the REST gateway.

---

## 5. Tamper-Evident Audit Trail & Cryptographic Hash Chaining

The `audit_logs` table forms an append-only cryptographic hash chain:
$$H_i = \text{SHA256}(\text{record\_id} + \text{timestamp} + \text{action} + \text{actor\_id} + \text{actor\_role} + \text{target\_id} + \text{changes} + H_{i-1})$$

- **Verification Endpoint**: `GET /api/v1/audit/verify-chain`
- **Breach Detection**: If any record attribute is altered directly in the database, the hash verification immediately flags `INTEGRITY_VIOLATION_DETECTED` with the exact record index and mismatched hash.

---

## 6. Security Vulnerability Assessment & Posture

| Vulnerability Type | Risk Level | Mitigation Implemented |
|---|---|---|
| **SQL Injection (SQLi)** | Negligible | Full SQLAlchemy ORM 2.x parameterized query binding; zero raw string SQL concatenation. |
| **Cross-Site Scripting (XSS)** | Negligible | Strict Pydantic input models; XML entity escaping for CAP v1.2 alerts. |
| **Insecure Direct Object Reference (IDOR)** | Low | Station, device, and alert access verified via role hierarchies. |
| **Replay Attacks** | Mitigated | Deterministic SHA-256 idempotency and value tamper detection (409). |
| **Brute-Force Login** | Mitigated | Passlib bcrypt password hashing with configurable salt rounds and rate limits. |

**Audit Verdict**: The FLOODY SHIELD v3.5 backend platform enforces rigorous security boundaries suitable for supervised field pilot operations.
