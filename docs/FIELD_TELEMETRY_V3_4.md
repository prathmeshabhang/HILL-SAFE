# FLOODY SHIELD v3.4 — Field Telemetry & Sensor Registry Specification

**System**: FLOODY SHIELD (Predict • Protect • Preserve)  
**Basin**: Upper Beas River Basin (Kullu–Manali, Himachal Pradesh, India)  
**Scope**: Hardware Hierarchy, Ingestion Protocols, Temporal State Machine, Idempotency & Aggregation  

---

## 1. Physical Hardware Hierarchy

To accurately represent physical disaster monitoring infrastructure in mountainous terrain, FLOODY SHIELD v3.4 models hardware as a three-tier hierarchy:

```
[ Sensor Station ] (e.g., STN_LARJI_01 - Confluence of Beas and Sainj)
       |
       +---> [ Telemetry Device ] (e.g., DEV_LARJI_LORA_01 - Solar/Cellular/LoRa Node)
       |            |
       |            +---> [ Sensor ] (SNS_LARJI_RADAR_01 - River Level, 0-25m)
       |            +---> [ Sensor ] (SNS_LARJI_RAIN_01 - Rain Gauge, 0-250 mm/h)
       |            +---> [ Sensor ] (SNS_LARJI_BATT_01 - Battery Voltage, 0-15V)
       |
       +---> [ Telemetry Device ] (e.g., DEV_LARJI_SLOPE_01 - Geotechnical Array)
                    |
                    +---> [ Sensor ] (SNS_LARJI_PWP_01 - Piezometer, 0-500 kPa)
                    +---> [ Sensor ] (SNS_LARJI_TILT_01 - Inclinometer, 0-90 deg)
```

### Database Entities
1. **`SensorStationModel` (`sensor_stations`)**:
   - `id`: Unique alphanumeric station code.
   - `name`: Descriptive name (e.g., "Larji Dam Hydro-Meteorological Station").
   - `station_type`: Station classification (`MET_HYDRO_IOT`, `WEATHER_RADAR`, `SEISMIC_ACOUSTIC`).
   - `latitude`, `longitude`, `elevation_m`: Geographical coordinates (WGS-84).
   - `river_basin`: River catchment identifier.
   - `is_active`: Operational state toggle.
   - `last_heartbeat`: Timestamp of latest transmission from any child device.

2. **`DeviceModel` (`devices`)**:
   - `device_id`: Unique identifier (e.g., `DEV_AUT_PWP_01`).
   - `station_id`: Foreign key referencing parent station.
   - `device_type`: Classification (`LORA_NODE`, `CELLULAR_GATEWAY`, `SATELLITE_UPLINK`).
   - `serial_number`: Manufacturer serial number or IMEI.
   - `hardware_version`, `firmware_version`: Hardware and firmware tracking.
   - `battery_level`: Battery charge percentage (0–100%).
   - `solar_voltage`: Input solar panel voltage in Volts.
   - `signal_strength`: RSSI in dBm.
   - `status`: Lifecycle state (`PLANNED`, `INSTALLED`, `ACTIVE`, `DEGRADED`, `OFFLINE`, `RETIRED`).

3. **`SensorModel` (`sensors`)**:
   - `sensor_id`: Unique sensor code (e.g., `SNS_AUT_RAIN_01`).
   - `device_id`: Foreign key referencing parent device.
   - `sensor_type`: Measurement type (`RAIN_GAUGE`, `WATER_LEVEL`, `PORE_WATER_PRESSURE`, `TILT`, `ACOUSTIC_GEOPHONE`).
   - `unit`: Engineering unit (`mm/h`, `m`, `kPa`, `deg`, `mm/s2`, `V`).
   - `measurement_range_min`, `measurement_range_max`: Physical plausibility limits.
   - `sampling_interval_sec`: Configured observation interval in seconds.
   - `calibration_status`: Calibration validity (`VALID`, `DUE_SOON`, `EXPIRED`, `UNSUPPORTED`).
   - `next_calibration_at`: Scheduled expiration of current calibration.

4. **`CalibrationRecordModel` (`calibration_records`)**:
   - Stores zero offset, scale multiplier, calibration authority name, reference instrument, and technician notes.

5. **`DeviceHeartbeatModel` (`device_heartbeats`)**:
   - High-frequency diagnostic telemetry logging battery voltage, percentage, RSSI, SNR, and hardware error flags.

---

## 2. Ingestion Protocols & Validation Pipeline

Field nodes transmit observations via HTTP REST (`POST /api/v1/telemetry`) or MQTT bridging gateways.

### Step 1: UTC Normalization
Incoming timestamps in `observed_at` are validated and converted to UTC timezone-aware datetimes. ISO-8601 strings with offsets (`+05:30`) or `Z` are parsed strictly. If no timezone is provided, UTC is assumed and stamped.

### Step 2: Temporal State Machine
The gateway compares `observed_at` against current gateway time (`now_utc`):

$$\text{latency\_seconds} = \text{now\_utc} - \text{observed\_at}$$
$$\text{skew\_seconds} = \text{observed\_at} - \text{now\_utc}$$

```
                          [ Incoming Packet ]
                                   |
                     +-------------+-------------+
                     |                           |
             skew > 7200s?               skew <= 7200s
                     |                           |
                     v                           v
              HTTP 422 Error           latency > 86400s (24h)?
       (TELEMETRY_FUTURE_TIMESTAMP)              |
                                          +------+------+
                                          |             |
                                         Yes            No
                                          |             |
                                          v             v
                                      [EXPIRED]   latency > 21600s (6h)?
                                                        |
                                                 +------+------+
                                                 |             |
                                                Yes            No
                                                 |             |
                                                 v             v
                                             [STALE]    latency > 3600s (1h)?
                                                               |
                                                        +------+------+
                                                        |             |
                                                       Yes            No
                                                        |             |
                                                        v             v
                                                      [LATE]       [VALID]
```

### Step 3: Deterministic Idempotency & Tampering Detection
To guarantee exactly-once persistence and prevent replay manipulation:
1. Every packet is hashed using SHA-256 over its immutable identity attributes:
   $$\text{Payload} = \text{source} \parallel \text{station\_id} \parallel \text{device\_id} \parallel \text{sensor\_id} \parallel \text{measurement\_type} \parallel \text{seq} \parallel \text{observed\_at}$$
   $$\text{source\_event\_id} = \text{SHA-256}(\text{Payload})$$
2. If `source_event_id` already exists in `sensor_observations`:
   - If $|\text{existing.value} - \text{incoming.value}| \le 10^{-5}$:
     Packet is classified as a benign network retransmission. Returns HTTP 200 with `status="DUPLICATE"` and the existing observation ID.
   - If $|\text{existing.value} - \text{incoming.value}| > 10^{-5}$:
     Replay tampering detected! The packet claims the exact same event sequence and timestamp but with a different observed value. Rejection code HTTP 409 (`TELEMETRY_INTEGRITY_VIOLATION`) is raised and an audit alert is triggered.

---

## 3. High-Throughput Batch Ingestion

Field gateways aggregating packets from remote sub-catchments submit batches via:
`POST /api/v1/telemetry/batch`

```json
{
  "packets": [
    {
      "source": "FIELD_GATEWAY_AUT",
      "station_id": "ST_AUT_01",
      "device_id": "DEV_AUT_01",
      "sensor_id": "SNS_AUT_RAIN_01",
      "measurement_type": "RAINFALL",
      "value": 14.5,
      "unit": "mm/h",
      "sequence_number": 4012,
      "observed_at": "2026-09-21T11:45:00Z"
    }
  ]
}
```

Response summarizes batch counts:
```json
{
  "total": 1,
  "total_packets": 1,
  "accepted": 1,
  "ingested": 1,
  "duplicates": 0,
  "rejected": 0,
  "results": [...]
}
```

---

## 4. Timeseries Aggregations

Operational dashboards and ML model adapters query aggregated timeseries telemetry via:
`GET /api/v1/observations/timeseries`

Supported aggregation functions:
- `raw`: Full pagination of individual observations.
- `latest`: Most recent recorded observation.
- `mean`: Arithmetic mean of observed values over query window.
- `min`: Minimum observed value.
- `max`: Maximum peak observation (e.g. peak flood stage, peak rainfall intensity).
- `sum`: Cumulative sum (e.g. total 24-hour rainfall accumulation).
- `count`: Total observation count within interval.
