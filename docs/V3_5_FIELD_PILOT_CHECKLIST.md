# FLOODY SHIELD v3.5 — Field Pilot Operational Checklists

**Target Basin:** Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**Version:** v3.5.0  

---

## 1. Pre-Commissioning Verification Checklist (Station Setup)

Complete this checklist for each of the 5 pilot stations (`ST_MANALI_01`, `ST_KULLU_01`, `ST_BHUNTAR_01`, `ST_AUT_01`, `ST_LARJI_01`) prior to activation:

- [ ] **Physical Mounting**: Sensor mast anchored against 120 km/h wind gusts and rockfall hazard.
- [ ] **Solar & Power**: Solar panels oriented true South ($30^\circ$ tilt); battery terminal voltage $\ge 12.6\text{ V}$.
- [ ] **Lightning Protection**: Earth ground rod installed; resistance $< 10\ \Omega$.
- [ ] **Primary Telemetry**: 4G LTE signal strength $\ge -85\text{ dBm}$ (RSRP).
- [ ] **Secondary Fallback**: LoRaWAN packet delivery rate $\ge 95\%$ over 10 test bursts.
- [ ] **Datum Calibration**: River gauge zero datum surveyed against Survey of India (SOI) benchmark MSL.
- [ ] **Zero Offset Verification**: Rain gauge tipping bucket clean; zero-offset recorded in `calibration_records`.
- [ ] **Heartbeat Check**: Device successfully transmits ping to `POST /api/v1/telemetry`.
- [ ] **Database Registration**: Station, device, and sensors registered via Admin API.

---

## 2. Shift Handover Checklist (EOC Operations)

Complete at 08:00 and 20:00 daily during active monsoon watch:

- [ ] **Service Status**: `GET /api/v1/system/status` indicates `OPERATIONAL`.
- [ ] **Active Warnings**: Review all open incidents and active flood/landslide risk zones on GIS layer.
- [ ] **Data Sources Active**:
  - [ ] IMD Radar (Patiala / Shimla Doppler)
  - [ ] GPM Satellite IMERG Precipitation
  - [ ] CWC Hydrological Streamflow
  - [ ] Sentinel-1 SAR Flooding & InSAR Landslide Ground Deformation
  - [ ] Upper Beas IoT Ground Stations (5/5 online)
- [ ] **Audit Trail**: `GET /api/v1/audit/verify-chain` returns `chain_intact: true`.
- [ ] **Pending Alerts**: Verify zero orphaned or unreviewed alerts in `PENDING_APPROVAL` status.
- [ ] **Incident Commander on Duty**: Identify and record designated Senior Incident Commander name and contact.

---

## 3. Monsoon Storm Pre-Flight & Cloudburst Readiness Checklist

Execute when IMD issues Yellow or Orange alerts for Kullu/Mandi:

- [ ] **Telemetry Ingestion Frequency**: Increase station sampling rate to 30-second intervals.
- [ ] **Dam Coordination**: Verify direct communication link with Larji and Pandoh Dam control rooms.
- [ ] **Evacuation Route Clearance**: Run `GET /api/v1/gis/routes` to verify NH-3 corridors are clear of predicted landslides.
- [ ] **Safe Zone Capacity**: Confirm emergency shelters at Kullu, Manali, and Bhuntar are staffed.
- [ ] **Notification Gateway Readiness**: Verify SMS gateway credits and CAP broadcast endpoint connections.
- [ ] **Database Backup**: Run manual on-demand backup: `python scripts/backup_db.py`.

---

## 4. Post-Event Debrief & Model Verification Checklist

Execute within 24 hours following any significant hydrometeorological event:

- [ ] **Data Preservation**: Export all high-frequency sensor records and freeze incident dataset.
- [ ] **Forecast Accuracy Assessment**:
  - [ ] Compare M1 nowcast vs observed rain gauge accumulations.
  - [ ] Compare M2 flood probability vs actual overtopping locations.
  - [ ] Compare M7 landslide triggers vs reported debris flows.
  - [ ] Compare M11 inundation depth vs high-water mud marks.
- [ ] **Timeline Verification**: Reconstruct event timeline using `tools.telemetry_simulator.replay`.
- [ ] **Audit Review**: Inspect all Commander authorization actions in `audit_logs`.
- [ ] **Calibration Check**: Inspect field sensors for physical debris damage or zero drift.
