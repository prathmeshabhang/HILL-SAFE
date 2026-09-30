/**
 * frontend/src/pages/SensorsPage.tsx
 * ==================================
 * Sensor & Data Sources Operational Telemetry View (Phase 06).
 * Recreates the exact layout and architecture from Reference Image 5:
 * 1. 5 Top Summary Metric Cards (Online Sensors, Offline Alert, Satellite Feeds, IMD Radar, Telemetry Latency)
 * 2. Left Column:
 *    - Data Sources Status Table (INSAT-3DS, SMAP, IMD, IoT Grid, CWC)
 *    - Interactive Sensor Locations Map with status markers
 * 3. Right Column:
 *    - Real-Time Data Streams tabbed chart (Water Level, Rainfall, Soil Moisture, Velocity)
 *    - Multi-Source Data Fusion & Redundancy Pipeline Flowchart
 *    - Sensor Hardware Health & Trends Table with Sparklines
 */

import React, { useState, useEffect } from 'react';
import { fetchStations, fetchSourcesHealth, fetchSourcesSnapshot, createStation, deleteStation } from '../services/api/endpoints';
import { StationTelemetry, MultiSourceHealthSummary, MultiSourceSnapshot } from '../types';
import { MapContainer } from '../components/Map/MapContainer';
import {
  Radio,
  Satellite,
  Waves,
  CloudRain,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Cpu,
  Layers,
  ShieldCheck,
  RefreshCw,
  Sun,
  BatteryCharging,
  Wifi,
  ArrowRight,
  TrendingUp,
  Download,
  Plus,
  Trash2,
  X,
  MapPin,
  Check,
  Info,
} from 'lucide-react';

export const SensorsPage: React.FC = () => {
  const [stations, setStations] = useState<StationTelemetry[]>([]);
  const [sourcesHealth, setSourcesHealth] = useState<MultiSourceHealthSummary | null>(null);
  const [sourcesSnapshot, setSourcesSnapshot] = useState<MultiSourceSnapshot | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeStreamTab, setActiveStreamTab] = useState<'water' | 'rain' | 'soil' | 'velocity'>('water');

  // Station Management State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<StationTelemetry | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    station_id: '',
    station_type: 'MET_HYDRO_IOT',
    latitude: 32.2450,
    longitude: 77.1890,
    elevation_m: 2050,
    river_basin: 'Upper Beas Basin (Manali Reach)',
    status: 'ACTIVE',
  });

  const loadData = () => {
    setLoading(true);
    Promise.all([
      fetchStations().then(setStations),
      fetchSourcesHealth().then(setSourcesHealth),
      fetchSourcesSnapshot().then(setSourcesSnapshot),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateStation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    setIsSubmitting(true);
    try {
      await createStation({
        name: formData.name.trim(),
        station_id: formData.station_id.trim() || undefined,
        station_type: formData.station_type,
        latitude: Number(formData.latitude),
        longitude: Number(formData.longitude),
        elevation_m: Number(formData.elevation_m),
        river_basin: formData.river_basin,
        status: formData.status,
      });
      setNotification({ type: 'success', message: `Station "${formData.name}" registered successfully.` });
      setIsAddModalOpen(false);
      setFormData({
        name: '',
        station_id: '',
        station_type: 'MET_HYDRO_IOT',
        latitude: 32.2450,
        longitude: 77.1890,
        elevation_m: 2050,
        river_basin: 'Upper Beas Basin (Manali Reach)',
        status: 'ACTIVE',
      });
      loadData();
    } catch (err: any) {
      setNotification({ type: 'error', message: err?.response?.data?.detail || 'Failed to add station' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteStation = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteStation(deleteTarget.station_id);
      setNotification({ type: 'success', message: `Station "${deleteTarget.station_name}" deleted.` });
      setDeleteTarget(null);
      loadData();
    } catch (err: any) {
      setNotification({ type: 'error', message: err?.response?.data?.detail || 'Failed to delete station' });
    } finally {
      setIsDeleting(false);
    }
  };

  const sourcesList = [
    {
      name: 'INSAT-3DS Hydro-Estimator',
      category: 'Meteorological Satellite',
      status: 'ONLINE',
      cadence: '15 min scan',
      latency: '2.4 min',
      provenance: 'ISRO / MOSDAC',
    },
    {
      name: 'NASA SMAP Radiometer',
      category: 'Soil Moisture Satellite',
      status: 'ONLINE',
      cadence: '12 hr revisit',
      latency: '45 min',
      provenance: 'NASA / NSIDC',
    },
    {
      name: 'IMD AWS Surface Gauges',
      category: 'In-Situ Weather Stations',
      status: 'ONLINE',
      cadence: '15 min cycle',
      latency: '1.2 min',
      provenance: 'IMD New Delhi',
    },
    {
      name: 'IoT Ultrasonic & Radar Grid',
      category: 'Catchment River Rigs',
      status: 'DEGRADED',
      cadence: '30 sec LoRaWAN',
      latency: '42 sec',
      provenance: 'Physical Staging Rigs',
    },
    {
      name: 'CWC Hydrometric Stations',
      category: 'River Stage & Discharge',
      status: 'ONLINE',
      cadence: 'Hourly sync',
      latency: '8 min',
      provenance: 'Central Water Comm.',
    },
  ];

  const handleExportTelemetryCsv = () => {
    if (!stations || stations.length === 0) return;
    const csvRows = [
      ['HILL-SAFE - IOT & HYDROMETRIC TELEMETRY REPORT', ''],
      ['Exported At (UTC)', new Date().toISOString()],
      ['Authority', 'Himachal Pradesh State Disaster Management Authority'],
      ['Total Active Stations', stations.length.toString()],
      [''],
      ['Station ID', 'Station Name', 'Elevation (m)', 'Latitude', 'Longitude', 'Deployment Status', 'Water Level (m)', '1h Rainfall (mm)', 'Battery (%)', 'Last Signal'],
      ...stations.map(st => [
        st.station_id,
        st.station_name,
        st.elevation_m.toString(),
        st.latitude.toFixed(4),
        st.longitude.toFixed(4),
        st.deployment_status,
        st.water_level_m.toString(),
        st.rainfall_1h_mm.toString(),
        `${st.battery_pct}%`,
        `${st.last_heard_seconds_ago}s ago`,
      ]),
    ];
    const csvContent = csvRows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `HILL_SAFE_TELEMETRY_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`flex items-center justify-between p-4 rounded-2xl text-xs font-bold border transition shadow-sm ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30'
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? (
              <Check className="w-4 h-4 text-emerald-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-500" />
            )}
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 1. Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 sm:p-6 rounded-3xl shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              TELEMETRY & MULTI-SOURCE INGESTION
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs font-mono text-emerald-500 font-semibold">● FAIL-SOFT ACTIVE</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white">
            Sensor & Data Sources
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Real-time status of IoT river gauges, meteorological satellite downlinks, and redundant data fusion pipeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Station</span>
          </button>

          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-700 transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-500' : 'text-slate-400'}`} />
            <span>Sync Feeds</span>
          </button>

          <button
            onClick={handleExportTelemetryCsv}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* 2. Top 5 Summary Metric Cards (Matching Image 5) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Card 1: 8/10 Online */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">IoT Sensors</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
            8 / 10 Online
          </div>
          <span className="text-[10px] text-emerald-500 font-medium block">80% Catchment Coverage</span>
        </div>

        {/* Card 2: 1 Offline */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Offline Alert</span>
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          </div>
          <div className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono">
            1 Offline
          </div>
          <span className="text-[10px] text-rose-500 font-medium truncate block">Aleo Bridge (Battery low)</span>
        </div>

        {/* Card 3: INSAT-3DS */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Satellite</span>
            <Satellite className="w-3.5 h-3.5 text-blue-500" />
          </div>
          <div className="text-xl font-black text-slate-900 dark:text-white font-mono truncate">
            INSAT-3DS
          </div>
          <span className="text-[10px] text-blue-500 font-medium block">Active 15-min HEM pass</span>
        </div>

        {/* Card 4: IMD Radar */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Doppler Radar</span>
            <Activity className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="text-xl font-black text-slate-900 dark:text-white font-mono truncate">
            IMD Radar
          </div>
          <span className="text-[10px] text-cyan-500 font-medium block">Palampur DWR Online</span>
        </div>

        {/* Card 5: Data Latency */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-1.5 col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Telemetry Latency</span>
            <Clock className="w-3.5 h-3.5 text-purple-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
            42s Latency
          </div>
          <span className="text-[10px] text-purple-500 font-medium block">Real-time MQTT Gateway</span>
        </div>
      </div>

      {/* 3. Main Two-Column Telemetry Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Data Sources Table + Sensor Locations Map (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">
          {/* Data Sources Status Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base flex items-center gap-2">
                  <Satellite className="w-4 h-4 text-blue-500" />
                  <span>Integrated Observation Feeds</span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Heterogeneous satellite, in-situ meteorological, and hydrometric providers
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 font-bold">
                5 Feeds Active
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] font-mono uppercase text-slate-400">
                    <th className="py-2 px-2.5">Data Feed</th>
                    <th className="py-2 px-2.5">Status</th>
                    <th className="py-2 px-2.5">Cadence</th>
                    <th className="py-2 px-2.5">Latency</th>
                    <th className="py-2 px-2.5">Provenance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {sourcesList.map((src, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-2.5">
                        <span className="font-bold text-slate-900 dark:text-white block">
                          {src.name}
                        </span>
                        <span className="text-[10px] text-slate-400">{src.category}</span>
                      </td>
                      <td className="py-2.5 px-2.5">
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                            src.status === 'ONLINE'
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {src.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-2.5 font-mono text-[11px] text-slate-500">
                        {src.cadence}
                      </td>
                      <td className="py-2.5 px-2.5 font-mono text-[11px] text-slate-500">
                        {src.latency}
                      </td>
                      <td className="py-2.5 px-2.5 font-mono text-[10px] text-slate-400">
                        {src.provenance}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sensor Locations Map */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-2">
                  <Radio className="w-4 h-4 text-blue-500" />
                  <span>Catchment Telemetry Rig Deployment Map</span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Locations of ultrasonic bridge sensors, river stage gauges & IMD stations
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 font-bold">
                Upper Beas Corridor
              </span>
            </div>

            <div className="h-64 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 relative">
              <MapContainer className="w-full h-full" />
            </div>
          </div>
        </div>

        {/* Right Column: Real-Time Data Streams Chart, Fusion Diagram & Sensor Health Table (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">
          {/* Real-Time Data Streams Chart (Tabbed) */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-500" />
                  <span>Real-Time Ingested Telemetry Streams</span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Live synchronized measurements across Beas River gauge network
                </p>
              </div>

              {/* Stream Selector Tabs */}
              <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
                {[
                  { id: 'water', label: 'Water (m)' },
                  { id: 'rain', label: 'Rain (mm/h)' },
                  { id: 'soil', label: 'Soil (%)' },
                  { id: 'velocity', label: 'Speed (m/s)' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveStreamTab(tab.id as any)}
                    className={`px-2.5 py-1 rounded-lg transition ${
                      activeStreamTab === tab.id
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* SVG Live Stream Display with 3.5m Danger Line */}
            <div className="h-44 w-full relative pt-2">
              <svg className="w-full h-full" viewBox="0 0 500 130" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="streamGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Danger Level Line (3.5m) */}
                <line x1="0" y1="30" x2="500" y2="30" stroke="#ef4444" strokeWidth="2" strokeDasharray="3 3" />
                <text x="10" y="24" fill="#ef4444" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  DANGER THRESHOLD 3.50 m
                </text>

                {/* Warning Level Line (2.8m) */}
                <line x1="0" y1="65" x2="500" y2="65" stroke="#f59e0b" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />

                {/* Telemetry Stream Area */}
                <path
                  d="M 0,95 Q 80,85 160,70 T 320,40 T 420,25 T 500,45 L 500,130 L 0,130 Z"
                  fill="url(#streamGrad)"
                />
                <path
                  d="M 0,95 Q 80,85 160,70 T 320,40 T 420,25 T 500,45"
                  fill="none"
                  stroke="#06b6d4"
                  strokeWidth="2.5"
                />

                <circle cx="420" cy="25" r="4.5" fill="#ef4444" stroke="#ffffff" strokeWidth="1.5" />
              </svg>

              <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-2">
                <span>10 min ago (2.1m)</span>
                <span>5 min ago (2.7m)</span>
                <span>2 min ago (3.2m)</span>
                <span className="text-rose-500 font-bold">Now: 3.55m (Over Danger)</span>
              </div>
            </div>
          </div>

          {/* Data Fusion & Redundancy Pipeline Architecture Flow Diagram */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4">
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-500" />
                <span>Multi-Source Redundancy & Data Fusion Pipeline</span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Automated ingestion gateway resolving sensor dropouts and discrepancies
              </p>
            </div>

            {/* Architecture Steps Flow */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-1">
                <span className="w-5 h-5 rounded-full bg-blue-500/10 text-blue-500 font-mono font-bold flex items-center justify-center mx-auto text-[10px]">
                  1
                </span>
                <div className="font-bold text-slate-900 dark:text-white text-[11px]">Raw Streams</div>
                <p className="text-[9px] text-slate-400">IoT, AWS, INSAT, SMAP, CWC</p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-1">
                <span className="w-5 h-5 rounded-full bg-cyan-500/10 text-cyan-500 font-mono font-bold flex items-center justify-center mx-auto text-[10px]">
                  2
                </span>
                <div className="font-bold text-slate-900 dark:text-white text-[11px]">Ingest & QA/QC</div>
                <p className="text-[9px] text-slate-400">CRC validation & spike filter</p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-1">
                <span className="w-5 h-5 rounded-full bg-purple-500/10 text-purple-500 font-mono font-bold flex items-center justify-center mx-auto text-[10px]">
                  3
                </span>
                <div className="font-bold text-slate-900 dark:text-white text-[11px]">Fusion Engine</div>
                <p className="text-[9px] text-slate-400">Kalman & spatial interpolation</p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-1">
                <span className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-500 font-mono font-bold flex items-center justify-center mx-auto text-[10px]">
                  4
                </span>
                <div className="font-bold text-slate-900 dark:text-white text-[11px]">Hazard Matrix</div>
                <p className="text-[9px] text-slate-400">M1–M20 ML models feeding</p>
              </div>
            </div>
          </div>

          {/* Sensor Hardware Health & Fleet Management Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-500" />
                  <span>IoT Station Fleet & Hardware Health</span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Telemetry stations active in Upper Beas Basin with live operational controls
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 font-bold">
                  {stations.length} Registered
                </span>
                <button
                  onClick={() => setIsAddModalOpen(true)}
                  className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-sm"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Station</span>
                </button>
              </div>
            </div>

            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-white dark:bg-slate-900 z-10">
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] font-mono uppercase text-slate-400">
                    <th className="py-2 px-2.5">Station ID</th>
                    <th className="py-2 px-2.5">Location</th>
                    <th className="py-2 px-2.5">Elevation</th>
                    <th className="py-2 px-2.5">Battery</th>
                    <th className="py-2 px-2.5">Status</th>
                    <th className="py-2 px-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {(stations.length > 0 ? stations : [
                    { station_id: 'STN-BEAS-01', station_name: 'Solang Gorge Bridge', elevation_m: 2480, battery_pct: 94, deployment_status: 'ACTIVE' },
                    { station_id: 'STN-BEAS-02', station_name: 'Palchan Confluence', elevation_m: 2310, battery_pct: 88, deployment_status: 'ACTIVE' },
                    { station_id: 'STN-BEAS-03', station_name: 'Old Manali Manalsu', elevation_m: 2090, battery_pct: 91, deployment_status: 'ACTIVE' },
                    { station_id: 'STN-BEAS-04', station_name: 'Aleo Bridge Main Stem', elevation_m: 1980, battery_pct: 35, deployment_status: 'OFFLINE' },
                    { station_id: 'STN-BEAS-05', station_name: 'Naggar Chhaki Reach', elevation_m: 1750, battery_pct: 96, deployment_status: 'ACTIVE' },
                  ] as any[]).map((row, idx) => {
                    const isOffline = (row.deployment_status || '').toUpperCase() === 'OFFLINE' || (row.battery_pct && row.battery_pct < 40);
                    return (
                      <tr key={row.station_id || idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-2.5 font-mono font-bold text-slate-900 dark:text-white truncate max-w-[120px]">
                          {row.station_id}
                        </td>
                        <td className="py-2.5 px-2.5 text-slate-700 dark:text-slate-300">
                          <span className="font-semibold block truncate max-w-[160px]">{row.station_name || row.name}</span>
                          {row.latitude && row.longitude && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              {row.latitude.toFixed(3)}°N, {row.longitude.toFixed(3)}°E
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-2.5 font-mono text-[11px] text-slate-500">
                          {row.elevation_m ? `${row.elevation_m}m` : '—'}
                        </td>
                        <td className="py-2.5 px-2.5 font-mono text-[11px]">
                          <span className={isOffline ? 'text-rose-500 font-bold' : 'text-slate-600 dark:text-slate-400'}>
                            {row.battery_pct !== undefined ? `${row.battery_pct}%` : '12.4V'}
                          </span>
                        </td>
                        <td className="py-2.5 px-2.5">
                          <span
                            className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                              !isOffline
                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {!isOffline ? 'ONLINE' : 'OFFLINE'}
                          </span>
                        </td>
                        <td className="py-2.5 px-2.5 text-right">
                          <button
                            onClick={() => setDeleteTarget(row)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-500/10 rounded-lg transition"
                            title="Delete Station"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Add Station Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-emerald-500/10 text-emerald-500 rounded-xl">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900 dark:text-white">Register Sensor Station</h3>
                  <p className="text-xs text-slate-400">Add physical gauging rig or weather station to HILL-SAFE</p>
                </div>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateStation} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-slate-700 dark:text-slate-300">Station Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Vashisht Hot Springs Gauge Rig"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-slate-700 dark:text-slate-300">Station ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="Auto-generated if empty"
                    value={formData.station_id}
                    onChange={(e) => setFormData({ ...formData, station_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-[11px]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-700 dark:text-slate-300">Station Type</label>
                  <select
                    value={formData.station_type}
                    onChange={(e) => setFormData({ ...formData, station_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="MET_HYDRO_IOT">MET_HYDRO_IOT (Ultrasonic + Rain)</option>
                    <option value="HYDROLOGICAL_PRIMARY">HYDROLOGICAL_PRIMARY (Radar Stage)</option>
                    <option value="WEATHER_AUTOMATIC">WEATHER_AUTOMATIC (AWS Barometric)</option>
                    <option value="SEISMIC_TILT">SEISMIC_TILT (Pore Pressure / Incline)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-slate-700 dark:text-slate-300">Latitude *</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="32.2450"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-[11px]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-700 dark:text-slate-300">Longitude *</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="77.1890"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-[11px]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-700 dark:text-slate-300">Altitude (m)</label>
                  <input
                    type="number"
                    placeholder="2050"
                    value={formData.elevation_m}
                    onChange={(e) => setFormData({ ...formData, elevation_m: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-[11px]"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-slate-700 dark:text-slate-300">River Reach / Basin</label>
                <input
                  type="text"
                  placeholder="e.g. Upper Beas Basin - Vashisht Reach"
                  value={formData.river_basin}
                  onChange={(e) => setFormData({ ...formData, river_basin: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-sm transition flex items-center gap-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Registering...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      <span>Register Station</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-rose-500/10 text-rose-500 rounded-2xl">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-black text-slate-900 dark:text-white">Delete Sensor Station</h3>
                <p className="text-xs text-slate-400">Confirm decommissioning of physical sensor rig</p>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700/60 text-xs space-y-1">
              <div className="font-bold text-slate-900 dark:text-white">
                {deleteTarget.station_name || deleteTarget.station_id}
              </div>
              <div className="text-slate-500 font-mono text-[11px]">
                ID: {deleteTarget.station_id}
              </div>
              <div className="text-[11px] text-slate-400">
                {deleteTarget.elevation_m}m elevation • {deleteTarget.latitude?.toFixed(4)}°N, {deleteTarget.longitude?.toFixed(4)}°E
              </div>
            </div>

            <p className="text-xs text-rose-600 dark:text-rose-400">
              Warning: Deleting this station removes all live observational streams and associated device telemetry from HILL-SAFE.
            </p>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                disabled={isDeleting}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-bold transition text-xs"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteStation}
                disabled={isDeleting}
                className="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold shadow-sm transition flex items-center gap-1.5 text-xs"
              >
                {isDeleting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Confirm Delete</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
