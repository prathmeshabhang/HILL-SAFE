# FLOODY SHIELD v3.5 — Failure Injection & Resilience Report

**Project:** FLOODY SHIELD — Predict • Protect • Preserve  
**Target Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**Report Date:** 2026-09-21  
**Scope:** Fault Injection, Degraded Mode Handling, Edge-Case Resilience & Life-Safety Fail-Safe Verification  

---

## 1. Executive Summary

A core requirement for life-safety disaster systems is graceful degradation under hardware, communication, and software failures. FLOODY SHIELD v3.5 was subjected to comprehensive failure injection across the physical sensor interface, ingestion gateway, model orchestration DAG, and audit logging layers.

In all tested failure scenarios, the platform maintained its non-negotiable safety invariants:
- **No silent failures or unhandled exceptions crashing the service.**
- **No fake probabilities (0.0 or 0.5) emitted to hide missing model predictions.**
- **Explicit propagation of `DEGRADED`, `MODEL_UNAVAILABLE`, and `LOW_CONFIDENCE` states.**
- **Cryptographic detection of telemetry replay and audit trail tampering.**

---

## 2. Failure Mode Injection Matrix

| Failure Mode | Injected Condition | Expected Behavior | Observed System Reaction | Test Case | Status |
|---|---|---|---|---|---|
| **FM-1: Clock Skew (Extreme Future)** | Telemetry packet with timestamp +3 hours into future | Reject packet with HTTP 422 | Raised `TELEMETRY_FUTURE_TIMESTAMP` (HTTP 422), packet dropped | `test_temporal_classification_matrix` | **PASS** |
| **FM-2: Clock Skew (Slight Future)** | Telemetry packet with timestamp +10 mins into future | Accept but tag `INVALID` with `CRITICAL_ERROR` quality | Stored with `temporal_state="INVALID"`, `quality_state="CRITICAL_ERROR"` | `test_temporal_classification_matrix` | **PASS** |
| **FM-3: Telemetry Stale (Delayed)** | Telemetry packet > 6 hours old | Accept but tag `STALE` | Stored with `temporal_state="STALE"`, downstream models notified of age | `test_temporal_classification_matrix` | **PASS** |
| **FM-4: Replay Tampering Attack** | Ingest packet with existing `source_event_id` but altered metric value ($14.5 \to 999.9$) | Immediate rejection with HTTP 409 | Emitted `TELEMETRY_INTEGRITY_VIOLATION` (HTTP 409), rejected modified packet | `test_concurrent_replay_tampering_detection` | **PASS** |
| **FM-5: Model Crash / Unavailability** | Model M10 (Water Level Forecast) node raises unhandled timeout exception | Node marked `FAILED`, overall risk marked `DEGRADED` | Returned `model_health_state="DEGRADED_FAILURES_DETECTED"`, `confidence_state="LOW_CONFIDENCE"` | `test_model_failure_propagation_to_degraded_risk` | **PASS** |
| **FM-6: Mountain Packet Loss** | Simulated 60% random packet drop across all station feeds | Core system remains stable, station health updates to `DEGRADED` | Sensor health service flags missed heartbeats, prompts field inspection | `test_all_simulator_scenarios_generate_valid_packets` | **PASS** |
| **FM-7: Database Audit Tampering** | Direct SQL mutation of `actor_role` on historical audit record | Verification detects hash mismatch and flags breach | Returned `status="INTEGRITY_VIOLATION_DETECTED"`, identified corrupted record | `test_audit_hash_chain_tamper_evidence` | **PASS** |
| **FM-8: Unauthorized Alert Release** | Observer or Data Analyst attempting to authorize early warning | Immediate rejection with HTTP 403 | Blocked by RBAC gateway; public alert dispatch strictly prevented | `test_rbac_alert_authorization_matrix` | **PASS** |

---

## 3. Detailed Failure Mode Analyses

### Failure Mode FM-5: Model Crash & Scientific Fail-Safe Isolation
- **The Danger**: In standard software pipelines, if an ML component fails, developers often default to fallback values like $0.0$ or $0.5$. In flood forecasting, emitting $0.0$ would tell an incident commander that there is zero flood risk during a cloudburst, resulting in deaths. Emitting $0.5$ creates false certainty.
- **The FLOODY SHIELD Safeguard**: When M10 failed during stress testing:
  1. The DAG recorded `state="FAILED"` and preserved the exact error stack (`Sensor disconnection timeout`).
  2. The Unified Risk Engine noted `any_failed == True` and set:
     - `quality_state = "DEGRADED"`
     - `model_health_state = "DEGRADED_FAILURES_DETECTED"`
     - `confidence_state = "LOW_CONFIDENCE"`
  3. The composite risk score was evaluated using remaining available hazard branches without suppressing alerts.

### Failure Mode FM-7: Cryptographic Hash Chain Breach Detection
- **The Danger**: An insider or attacker with direct database access alters audit logs to hide an unauthorized action or alter historical evidence.
- **The FLOODY SHIELD Safeguard**: When `rec2.actor_role` was changed from `SYSTEM` to `UNAUTHORIZED_HACKER` directly in the database:
  - The calculated hash $H_2 = \text{SHA256}(\dots)$ deviated from the recorded `entry_hash`.
  - The verify-chain endpoint traversed the sequence and flagged:
    ```json
    {
      "status": "INTEGRITY_VIOLATION_DETECTED",
      "chain_intact": false,
      "corrupted_records": [
        {
          "record_id": "...",
          "index": 1,
          "action": "MODEL_RUN_COMPLETED"
        }
      ]
    }
    ```

---

## 4. Conclusion & Operational Pilot Readiness

The failure injection tests confirm that the platform is resilient against sensor telemetry corruption, network interruptions, model process crashes, and malicious tampering.
