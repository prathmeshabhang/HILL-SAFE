# FLOODY SHIELD v3.4 — NDMA Sachet & OASIS CAP v1.2 Integration Specification

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Target Basin**: Upper Beas River Basin — Kullu–Manali, Himachal Pradesh, India  
**Scope**: OASIS CAP v1.2 / ITU-T X.1303, NDMA Sachet mTLS Gateway, Schema Validation  

---

## 1. Statutory National Warning Standards

In India, national disaster early warning alerts are governed by:
- **ITU-T Recommendation X.1303**: Common Alerting Protocol (CAP) for disaster management.
- **OASIS CAP v1.2**: Standard XML representation of emergency notifications.
- **NDMA Sachet**: National Disaster Management Authority's unified early warning platform delivering multi-hazard alerts via Cell Broadcast, SMS, and emergency mobile apps.

FLOODY SHIELD v3.4 provides end-to-end integration with NDMA Sachet while upholding strict life-safety approval gates.

---

## 2. CAP v1.2 Structure & XML Generation

Alerts dispatched by FLOODY SHIELD conform to OASIS CAP v1.2:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>CAP-HPSDMA-20260921-A8B9C0</identifier>
  <sender>hpsdma.eoc.kullu@hp.gov.in</sender>
  <sent>2026-09-21T12:00:00+00:00</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <category>Geo</category>
    <event>EXTREME FLASH FLOOD &amp; LANDSLIDE DAM BREACH ADVISORY</event>
    <urgency>Immediate</urgency>
    <severity>Extreme</severity>
    <certainty>Observed</certainty>
    <headline>Evacuation Warning: Upper Beas Basin</headline>
    <description>Torrential rainfall &gt; 70 mm/h and landslide dam breach detected at Sainj-Beas confluence.</description>
    <instruction>Evacuate riverbed settlements to designated safe shelters above 1200m elevation immediately.</instruction>
    <area>
      <areaDesc>Upper Beas Basin: Aut-Larji Gorge to Pandoh Dam</areaDesc>
    </area>
  </info>
</alert>
```

### Character Escaping & Semantic Validation
`CAPValidator` enforces:
1. Special characters (`&`, `<`, `>`, `"`, `'`) are escaped strictly to prevent XML parse failures.
2. Mandatory CAP fields (`identifier`, `sender`, `sent`, `status`, `msgType`, `scope`, `category`, `event`, `urgency`, `severity`, `certainty`, `headline`, `description`, `areaDesc`) are strictly checked.
3. Allowed enum values for `status` (`Actual`, `Exercise`, `System`, `Test`, `Draft`), `msgType` (`Alert`, `Update`, `Cancel`, `Ack`, `Error`), `severity` (`Extreme`, `Severe`, `Moderate`, `Minor`), `urgency` (`Immediate`, `Expected`, `Future`), and `certainty` (`Observed`, `Likely`, `Possible`) are validated.

---

## 3. Mutual TLS (mTLS) Transport Security

The Indian NDMA Sachet API requires mutual cryptographic verification (mTLS) over HTTPS.

### Required Environment Configuration
```ini
NDMA_SACHET_ENDPOINT="https://sachet.ndma.gov.in/api/v1/cap/dispatch"
NDMA_CLIENT_CERT="/etc/ssl/certs/ndma_sachet_client.crt"
NDMA_CLIENT_KEY="/etc/ssl/private/ndma_sachet_client.key"
NDMA_CA_CERT="/etc/ssl/certs/ndma_ca_bundle.crt"
```

### Honest Status Reporting (`NOT_CONFIGURED`)
To adhere to scientific and operational honesty:
- When running in local development, prototype test benches, or environments where government certificates are not installed, `NDMASachetProvider` **never fakes successful delivery**.
- It returns:
  ```json
  {
    "provider_name": "NDMASachetProvider",
    "channel": "NDMA_SACHET",
    "status": "NOT_CONFIGURED",
    "error": "Institutional NDMA Sachet mTLS credentials not configured in environment.",
    "details": {
      "reason": "Institutional NDMA Sachet mTLS credentials not configured in environment.",
      "required_configuration": [
        "NDMA_SACHET_ENDPOINT",
        "NDMA_CLIENT_CERT",
        "NDMA_CLIENT_KEY",
        "NDMA_CA_CERT"
      ]
    }
  }
  ```
- This ensures operators always know whether the national alerting pathway is actively connected or awaiting institutional credential provisioning.
