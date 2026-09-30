# FLOODY SHIELD — Frontend Disaster Management Interface (v4.0.0)

Professional, production-grade Emergency Operations Center (EOC) and Citizen Safety interface for the **FLOODY SHIELD — Predict • Protect • Preserve** flash flood and natural dam early warning platform.

---

## Key Features

1. **Upper Beas Basin Focus**:
   - Geographic extent: $31.40^\circ\text{N} - 32.45^\circ\text{N}$, $76.80^\circ\text{E} - 77.45^\circ\text{E}$ (Kullu–Manali corridor, Himachal Pradesh, India).
   - Powered by **MapLibre GL JS** with 2.5D topographic perspective and raster tiles (CartoDB Dark Matter / Positron, no external API keys required).

2. **Dedicated Natural Dam Intelligence**:
   - Continuous tracking of tributary debris damming (Solang Debris Dam, Rohtang Escarpment Lake, Hampta Stream Colluvium Pond).
   - Metrics: Blockage %, impounded volume ($m^3$), lake growth rate ($m^3/\text{day}$), breach risk level, estimated time to peak downstream impact.
   - Dedicated **Natural Dam Image Upload & Remote Sensing Analysis** workflow with automated NDWI and debris crest calculation + Authority Sign-Off Gating.

3. **Hyperlocal Personal Safety & Evacuation**:
   - "Am I Safe?" personal safety status card based on device GPS or selected valley sector.
   - Dynamic elevation-profiled evacuation corridors prioritizing high-ground ridge paths above 2,150 m.
   - Verified safe havens directory with capacity tracking, emergency generator power, and satellite communications status.

4. **Life-Safety Alerting & Dual-Authorization Gating (M17 Protocol)**:
   - WebSockets can stream advisories, but public life-safety alarm sirens strictly require Senior Incident Commander dual-authorization hitting `POST /api/v1/alerts/{id}/authorize`.
   - Full-screen emergency warning screen (Page 7) with Web Audio API synthesized siren.

5. **Scientific Integrity & Hardware Qualification**:
   - Honest labeling of hardware as `PROTOTYPE_STAGING` (5 electronic staging units, zero active in-water river deployments).
   - M1–M20 scientific model cards with cryptographic frozen hashes, sample size disclosure, and validation disclaimers.

---

## Page Directory

| Route | Page | Purpose |
|---|---|---|
| `/welcome` | Page 0 | Welcome, location picker, GPS permission, and role setup |
| `/` | Page 1 | Personal Safety Dashboard ("Am I Safe?", distance to river, nearest haven) |
| `/map` | Page 2 | Full interactive 2.5D topographic GIS with hazard layers & river cross-section |
| `/natural-dams` | Page 3 | Natural Dam Monitoring, impoundment volumes & breach threat |
| `/dam-analysis` | Page 3b | Dedicated Natural Dam Image Upload & Remote Sensing AI Analysis |
| `/replay` | Page 4 | Historical Replay of July 2023 Beas Flood with time-series scrubber |
| `/evacuation` | Page 5 | Turn-by-turn safe passage routing and high-ground shelter directory |
| `/community` | Page 6 | Crowdsourced citizen ground observations and photo reports |
| `/emergency` | Page 7 | Full-screen critical red alarm with audible siren simulation |
| `/preparedness` | Page 8 | 72-Hour "Go-Bag" checklist and emergency helplines directory |
| `/command` | Page 9 | EOC Incident Commander Operations Desk with Dual-Auth Alert Gateway |
| `/sensors` | Page 10 | IoT Sensor Network & Hardware Staging Health (`PROTOTYPE_STAGING`) |
| `/models` | Page 11 | Scientific Models M1–M20 evidence cards and frozen hash verification |
| `/sitrep` | Page 12 | Standardized SDMA daily situation reports with PDF/JSON export |

---

## Running Locally

### Prerequisites
- Node.js `v18+` (Tested on Node `v22.18.0` and npm `10.9.3`).
- FLOODY SHIELD FastAPI backend running on `http://127.0.0.1:8000`.

### Development Server
```bash
cd frontend
npm install
npm run dev
```
The application will launch on `http://127.0.0.1:5173`. Vite automatically proxies API requests (`/api/*`, `/health`, `/ws/*`) to the backend at `http://127.0.0.1:8000`.

### Production Build
```bash
npm run build
npm run preview
```
Production assets are generated in `frontend/dist/`.
