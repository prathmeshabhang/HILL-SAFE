/**
 * frontend/src/pages/VillageWardPage.tsx
 * =====================================
 * Hyper-local Village & Ward Disaster Intelligence View (Phase 06).
 * Recreates the exact layout, structure, and widgets from Reference Image 2:
 * 1. Cascading Geographic Selectors (State -> District -> Block -> GP -> Ward) + Actions
 * 2. Overall Risk Header Banner with Flood/Landslide/Compound scores & Demographics
 * 3. Left Column:
 *    - Scenic Mountain Valley Banner + Live Environmental Conditions
 *    - 6-Hour Risk Trend Chart with Peak Risk Window Callout
 *    - Elevation & Terrain Cross-Section Profile (Ridge -> Settlement -> River)
 *    - "Why is this Ward at Risk?" AI Intelligence Explanations
 * 4. Right Column:
 *    - 72% Landslide Trigger Probability Radial Gauge & Contributing Factors
 *    - Local Ward Satellite Boundary Map
 *    - Recommended Immediate Actions Checklist
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { fetchHyperlocalAdminUnits, fetchBasinRiskSummary } from '../services/api/endpoints';
import { HyperlocalAdminUnit, RiskSummary } from '../types';
import { MapContainer } from '../components/Map/MapContainer';
import { useMapStore } from '../store/useMapStore';
import {
  MapPin,
  Mountain,
  Waves,
  AlertTriangle,
  Users,
  Home,
  CheckCircle2,
  CheckCircle,
  TrendingUp,
  Download,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Info,
  Droplets,
  Wind,
  Compass,
  ArrowRight,
  Shield,
  Clock,
  Sparkles,
  CheckSquare,
  Square,
  Printer,
  FileSpreadsheet,
  FileText,
  X,
} from 'lucide-react';

export const VillageWardPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { flyToLocation } = useMapStore();

  const [adminUnits, setAdminUnits] = useState<HyperlocalAdminUnit[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<HyperlocalAdminUnit | null>(null);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Selector state
  const [stateName] = useState('Himachal Pradesh');
  const [district] = useState('Kullu');
  const [block, setBlock] = useState('Naggar');
  const [gramPanchayat, setGramPanchayat] = useState('Naggar GP');
  const [selectedWardId, setSelectedWardId] = useState<string>('HP-KUL-NAG-03');

  // Checklist state
  const [checklist, setChecklist] = useState<Record<string, boolean>>({
    evacuate: false,
    sandbags: true,
    slope: false,
    volunteers: true,
    machinery: false,
  });

  const toggleChecklist = (id: string) => {
    setChecklist((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  useEffect(() => {
    Promise.all([fetchHyperlocalAdminUnits(), fetchBasinRiskSummary()])
      .then(([units, risk]) => {
        setAdminUnits(units);
        setRiskSummary(risk);

        // Check if query param specifies an admin_id
        const targetId = searchParams.get('admin_id') || 'HP-KUL-NAG-03';
        const found = units.find((u) => u.admin_id === targetId) || units[0];
        if (found) {
          setSelectedUnit(found);
          setSelectedWardId(found.admin_id);
        }
      })
      .finally(() => setLoading(false));
  }, [searchParams]);

  const handleWardChange = (wardId: string) => {
    setSelectedWardId(wardId);
    const unit = adminUnits.find((u) => u.admin_id === wardId);
    if (unit) {
      setSelectedUnit(unit);
      flyToLocation(unit.centroid[0], unit.centroid[1], 15);
    }
  };

  // Derive dynamic risk metrics
  const currentRiskLevel = selectedUnit?.current_hazard?.risk_level || 'MODERATE';
  const isSafeVillage = currentRiskLevel === 'LOW' || Boolean(selectedUnit?.is_safe_terrace);
  const isHighRisk = currentRiskLevel === 'HIGH' || currentRiskLevel === 'CRITICAL';
  const currentMaxScore = selectedUnit?.current_hazard?.max_hazard_score ?? (isSafeVillage ? 0.09 : 0.68);
  const floodScore = isSafeVillage ? 0.08 : (selectedUnit?.current_hazard?.dominant_hazard === 'FLOOD' ? 0.82 : 0.48);
  const landslideScore = isSafeVillage ? 0.09 : (selectedUnit?.current_hazard?.dominant_hazard === 'LANDSLIDE' ? 0.85 : 0.52);
  const compoundScore = isSafeVillage ? 0.04 : (selectedUnit?.current_hazard?.dominant_hazard === 'COMPOUND_CASCADE' ? 0.88 : currentMaxScore);

  const population = selectedUnit?.exposure?.permanent_population || 420;
  const households = Math.round(population / 4.5);
  const vulnerableCount = isSafeVillage ? 0 : Math.round(population * 0.2);

  // Export State
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);
  const [exportSuccessMsg, setExportSuccessMsg] = useState<string | null>(null);

  // CSV Report Generator
  const handleExportCsv = () => {
    if (!selectedUnit) return;
    const csvRows = [
      ['HILL-SAFE HYPER-LOCAL DISASTER SITUATION REPORT', ''],
      ['Reporting Authority', 'Himachal Pradesh State Disaster Management Authority (HP-SDMA)'],
      ['Report Generated At (UTC)', new Date().toISOString()],
      ['Catchment Basin', 'Upper Beas River Catchment (Kullu - Manali)'],
      [''],
      ['--- ADMINISTRATIVE JURISDICTION ---', ''],
      ['Administrative Unit ID', selectedUnit.admin_id],
      ['Ward / Village Name', selectedUnit.name],
      ['Administrative Unit Type', selectedUnit.unit_type],
      ['Gram Panchayat', gramPanchayat],
      ['Block / Tehsil', block],
      ['District', district],
      ['State', stateName],
      ['Jurisdiction Area (km²)', selectedUnit.area_km2.toString()],
      ['Centroid Latitude', selectedUnit.centroid[1].toFixed(5)],
      ['Centroid Longitude', selectedUnit.centroid[0].toFixed(5)],
      ['Terrain Profile', 'Upper Beas Mountain Gorge (1,760m ASL, Mean Slope 18.4°)'],
      ['Cascade Outburst State', selectedUnit.cascade_state || 'STABLE_MONITORED'],
      [''],
      ['--- MULTI-HAZARD RISK EVALUATION ---', ''],
      ['Composite Risk Tier', selectedUnit.current_hazard.risk_level],
      ['Primary Threat Classification', selectedUnit.current_hazard.dominant_hazard],
      ['Max Hazard Score', (selectedUnit.current_hazard.max_hazard_score * 100).toFixed(1) + '%'],
      ['Mean Hazard Score', (selectedUnit.current_hazard.mean_hazard_score * 100).toFixed(1) + '%'],
      ['Exposed Area Percentage', `${selectedUnit.current_hazard.exposed_area_pct}%`],
      ['Scientific Confidence', `${Math.round((selectedUnit.confidence || 0.88) * 100)}%`],
      ['Data Provenance', selectedUnit.provenance || 'Sentinel-1 SAR / Sentinel-2 MSI / IMD AWS'],
      [''],
      ['--- DEMOGRAPHICS & CRITICAL EXPOSURE ---', ''],
      ['Permanent Resident Population', (selectedUnit.exposure.permanent_population || population).toString()],
      ['Estimated Total Population (Peak)', (selectedUnit.exposure.total_estimated_population || Math.round(population * 1.35)).toString()],
      ['Seasonal Tourist Population', (selectedUnit.exposure.tourist_population || 180).toString()],
      ['Estimated Households', households.toString()],
      ['Identified Vulnerable Residents', vulnerableCount.toString()],
      ['Exposed Infrastructure Assets Count', (selectedUnit.exposure.exposed_infrastructure_count || 3).toString()],
      ['Exposed Critical Infrastructure Details', (selectedUnit.exposure.exposed_infrastructure || []).map(i => `${i.name} [${i.category}, ${i.criticality_tier}]`).join('; ') || 'Log Huts Bridge; HPSEB Substation; Govt Primary Health Centre'],
      [''],
      ['--- LOCAL EMERGENCY PROTOCOL STATUS ---', ''],
      ['Mandatory Lowland Evacuation Triggered', checklist.evacuate ? 'COMPLETED' : 'PENDING'],
      ['Pre-positioned Sandbags & Defenses', checklist.sandbags ? 'COMPLETED' : 'PENDING'],
      ['Active Slope & Scour Monitoring', checklist.slope ? 'COMPLETED' : 'PENDING'],
      ['Local Community Wardens Mobilized', checklist.volunteers ? 'COMPLETED' : 'PENDING'],
      ['Heavy Earthmoving Machinery on Standby', checklist.machinery ? 'COMPLETED' : 'PENDING'],
    ];

    const csvContent = csvRows.map(row => row.map(val => `"${String(val).replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `FLOODY_SHIELD_${selectedUnit.admin_id}_REPORT_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setExportSuccessMsg('CSV Report successfully downloaded!');
    setTimeout(() => setExportSuccessMsg(null), 3500);
  };

  // JSON Intelligence Generator
  const handleExportJson = () => {
    if (!selectedUnit) return;
    const reportPayload = {
      title: 'HILL-SAFE v4.0 - Hyper-Local Disaster Intelligence Report',
      authority: 'H.P. State Disaster Management Authority (HP-SDMA)',
      generated_at_utc: new Date().toISOString(),
      catchment: 'Upper Beas River Basin (Kullu - Manali)',
      jurisdiction: {
        admin_id: selectedUnit.admin_id,
        name: selectedUnit.name,
        unit_type: selectedUnit.unit_type,
        area_km2: selectedUnit.area_km2,
        gram_panchayat: gramPanchayat,
        block,
        district,
        state: stateName,
        centroid: {
          latitude: selectedUnit.centroid[1],
          longitude: selectedUnit.centroid[0],
        },
      },
      hazard_assessment: selectedUnit.current_hazard,
      exposure: selectedUnit.exposure,
      emergency_protocol_status: checklist,
      confidence: selectedUnit.confidence,
      provenance: selectedUnit.provenance,
      risk_summary_context: riskSummary,
    };

    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(reportPayload, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute('href', dataStr);
    dlAnchorElem.setAttribute('download', `FLOODY_SHIELD_${selectedUnit.admin_id}_INTELLIGENCE_${Date.now()}.json`);
    document.body.appendChild(dlAnchorElem);
    dlAnchorElem.click();
    document.body.removeChild(dlAnchorElem);
    setExportSuccessMsg('JSON Intelligence successfully exported!');
    setTimeout(() => setExportSuccessMsg(null), 3500);
  };

  // PDF Print Trigger
  const handlePrintPdf = () => {
    setIsExportModalOpen(false);
    setTimeout(() => {
      window.print();
    }, 150);
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Cascading Selectors */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                HYPER-LOCAL OPERATIONAL INTELLIGENCE
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-mono text-emerald-500 font-semibold">● REAL-TIME SYNC</span>
            </div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white mt-1">
              Village / Ward View
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Select an administrative jurisdiction to inspect micro-catchment hazard exposure, terrain cross-sections, and evacuation readiness.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 self-start md:self-auto">
            <button
              onClick={() => {
                if (selectedUnit) {
                  navigate(`/map?admin_id=${selectedUnit.admin_id}`);
                } else {
                  navigate('/map');
                }
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
            >
              <MapPin className="w-3.5 h-3.5" />
              <span>View on Map</span>
            </button>

            <button
              onClick={() => setIsExportModalOpen(true)}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-700 transition flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5 text-slate-400" />
              <span>Export Report</span>
            </button>
          </div>
        </div>

        {/* Cascading Filter Selectors Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
          {/* State */}
          <div className="space-y-1">
            <label className="text-[10px] font-mono uppercase text-slate-400 font-bold">State</label>
            <div className="p-2 bg-slate-50 dark:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium truncate">
              {stateName}
            </div>
          </div>

          {/* District */}
          <div className="space-y-1">
            <label className="text-[10px] font-mono uppercase text-slate-400 font-bold">District</label>
            <div className="p-2 bg-slate-50 dark:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium truncate">
              {district}
            </div>
          </div>

          {/* Block */}
          <div className="space-y-1">
            <label className="text-[10px] font-mono uppercase text-slate-400 font-bold">Tehsil / Block</label>
            <select
              value={block}
              onChange={(e) => setBlock(e.target.value)}
              className="w-full p-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="Naggar">Naggar Block</option>
              <option value="Manali">Manali Block</option>
              <option value="Kullu">Kullu Block</option>
              <option value="Banjar">Banjar Block</option>
            </select>
          </div>

          {/* Gram Panchayat */}
          <div className="space-y-1">
            <label className="text-[10px] font-mono uppercase text-slate-400 font-bold">Gram Panchayat</label>
            <select
              value={gramPanchayat}
              onChange={(e) => setGramPanchayat(e.target.value)}
              className="w-full p-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="Naggar GP">Naggar Gram Panchayat</option>
              <option value="Vashisht GP">Vashisht Gram Panchayat</option>
              <option value="Bahang GP">Bahang Gram Panchayat</option>
              <option value="Patlikuhal GP">Patlikuhal Gram Panchayat</option>
            </select>
          </div>

          {/* Ward Selector */}
          <div className="space-y-1 col-span-2 sm:col-span-1">
            <label className="text-[10px] font-mono uppercase text-blue-500 font-bold">Monitored Ward</label>
            <select
              value={selectedWardId}
              onChange={(e) => handleWardChange(e.target.value)}
              className="w-full p-2 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              {adminUnits.length > 0 ? (
                adminUnits.map((u) => (
                  <option key={u.admin_id} value={u.admin_id}>
                    {u.is_safe_terrace || u.current_hazard?.risk_level === 'LOW' ? `🟢 [SAFE] ${u.name}` : `⚠️ ${u.name}`}
                  </option>
                ))
              ) : (
                <option value="HP-KUL-NAG-03">Naggar Ward 3 (Upper)</option>
              )}
            </select>
          </div>
        </div>

        {/* Quick Link to High-Risk Development & Construction Prohibition Zones */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-xs border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2 text-slate-500">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Regulatory Land Use:</span>
            <span>Check statutory river setback &amp; building ban mandates across the basin.</span>
          </div>
          <button
            onClick={() => navigate('/development-zones')}
            className="px-3 py-1 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/30 text-rose-600 dark:text-rose-400 font-bold transition flex items-center gap-1.5 border border-rose-200 dark:border-rose-900/50"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
            <span>High-Risk Development &amp; Building Ban Zones</span>
            <ExternalLink className="w-3 h-3 ml-0.5" />
          </button>
        </div>
      </div>

      {/* 2. Top Overall Risk Banner Card */}
      <div className={`rounded-3xl p-6 text-white shadow-xl space-y-4 ${
        isSafeVillage
          ? 'bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 shadow-emerald-500/10'
          : currentRiskLevel === 'MODERATE'
          ? 'bg-gradient-to-r from-amber-600 via-yellow-600 to-orange-600 shadow-amber-500/10'
          : 'bg-gradient-to-r from-red-600 via-rose-600 to-orange-600 shadow-red-500/10'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-mono tracking-wider bg-black/25 px-2.5 py-0.5 rounded-full font-bold">
                {selectedUnit?.admin_id || 'HP-KUL-NAG-03'}
              </span>
              <span className="text-xs text-white/80">
                Centroid: {selectedUnit?.centroid ? `${selectedUnit.centroid[1].toFixed(3)}°N, ${selectedUnit.centroid[0].toFixed(3)}°E` : '32.145°N, 77.168°E'}
              </span>
              {isSafeVillage && (
                <span className="text-[10px] font-mono uppercase bg-white/20 px-2 py-0.5 rounded-full font-bold">
                  VERIFIED SAFE HAVEN
                </span>
              )}
            </div>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight">
              {selectedUnit?.name || 'Naggar Ward 3 (Upper Naggar Heritage Corridor)'}
            </h2>
            <p className="text-xs sm:text-sm text-white/90">
              {isSafeVillage
                ? 'Elevated crystalline bedrock terrace perched high above valley floor. Safe from floodwaters and catastrophic debris surges.'
                : 'Settlement located within monitored river corridor requiring active hydro-meteorological observation.'}
            </p>
          </div>

          {/* Prominent Risk Level Badge */}
          <div className="flex items-center gap-4 bg-black/25 backdrop-blur-md px-6 py-4 rounded-2xl border border-white/20 self-start md:self-auto">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-white/70 font-bold">
                Overall Risk Level
              </div>
              <div className="text-3xl font-black tracking-tight flex items-center gap-2">
                <span>{isSafeVillage ? 'SAFE' : currentRiskLevel}</span>
                <span className="text-sm font-mono px-2 py-0.5 rounded bg-white/20">
                  {currentMaxScore.toFixed(2)}
                </span>
              </div>
            </div>
            {isSafeVillage ? (
              <ShieldCheck className="w-10 h-10 text-white/90" />
            ) : (
              <ShieldAlert className="w-10 h-10 text-white/90" />
            )}
          </div>
        </div>

        {/* Breakdown Pills Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 pt-3 border-t border-white/15 text-xs">
          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10">
            <span className="text-[10px] text-white/70 block font-mono">Flood Risk</span>
            <span className="text-base font-black font-mono">High ({floodScore})</span>
          </div>

          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10">
            <span className="text-[10px] text-white/70 block font-mono">Landslide Risk</span>
            <span className="text-base font-black font-mono">Moderate ({landslideScore})</span>
          </div>

          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10">
            <span className="text-[10px] text-white/70 block font-mono">Compound Multi-Hazard</span>
            <span className="text-base font-black font-mono">High ({compoundScore})</span>
          </div>

          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10">
            <span className="text-[10px] text-white/70 block font-mono">Total Population</span>
            <span className="text-base font-black font-mono">{population} residents</span>
          </div>

          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10">
            <span className="text-[10px] text-white/70 block font-mono">Vulnerable Citizens</span>
            <span className="text-base font-black font-mono">{vulnerableCount} (Infants/Elderly)</span>
          </div>

          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10">
            <span className="text-[10px] text-white/70 block font-mono">Estimated Households</span>
            <span className="text-base font-black font-mono">{households} structures</span>
          </div>
        </div>
      </div>

      {/* 3. Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Conditions, 6h Risk Trend, Elevation Profile, AI Risk Reasons (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Card A: Scenic Valley Banner & Live Environmental Conditions */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-sm">
            {/* Visual Valley Graphic Banner */}
            <div className="h-44 relative bg-gradient-to-tr from-slate-900 via-blue-950 to-slate-800 p-5 flex flex-col justify-between text-white">
              {/* Background mountain silhouette overlay */}
              <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-cyan-400 via-blue-600 to-transparent" />
              
              <div className="relative z-10 flex items-center justify-between">
                <span className="text-xs font-mono font-bold bg-white/20 backdrop-blur px-2.5 py-1 rounded-full flex items-center gap-1.5">
                  <Mountain className="w-3.5 h-3.5 text-cyan-300" />
                  <span>Upper Naggar Gorge • 1,760 m ASL</span>
                </span>
                <span className="text-xs font-mono text-cyan-300">
                  Beas Sub-Catchment 04
                </span>
              </div>

              <div className="relative z-10 space-y-0.5">
                <div className="text-lg font-bold">Chhaki Nullah & Upper Colluvium Basin</div>
                <p className="text-xs text-slate-300">
                  Catchment slope: 32° • Colluvium overburden thickness: 3.8m • Drainage density: 4.2 km/km²
                </p>
              </div>
            </div>

            {/* Live Conditions Grid */}
            <div className="p-5 grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50/50 dark:bg-slate-800/40">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-blue-500" /> Current Rainfall
                </span>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white">
                  18.5 mm/hr
                </div>
                <span className="text-[10px] text-amber-500 font-medium">+4.2 mm/hr in last 30m</span>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                  <Waves className="w-3 h-3 text-cyan-500" /> River Distance
                </span>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white">
                  450 m
                </div>
                <span className="text-[10px] text-slate-400 font-medium">To Chhaki confluence</span>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                  <Mountain className="w-3 h-3 text-orange-500" /> Average Slope
                </span>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white">
                  32°
                </div>
                <span className="text-[10px] text-red-500 font-medium">High debris mobility</span>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-emerald-500" /> Soil Saturation
                </span>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white">
                  78%
                </div>
                <span className="text-[10px] text-amber-500 font-medium">Near liquefaction limit</span>
              </div>
            </div>
          </div>

          {/* Card B: 6-Hour Risk Trend Chart with Peak Risk Window */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-500" />
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base">
                    6-Hour Rolling Multi-Hazard Projection
                  </h3>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Hydrodynamic & geotechnical forecast for {selectedUnit?.name || 'Naggar Ward 3'}
                </p>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-3 text-xs font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-1 bg-cyan-500 rounded-full" />
                  <span className="text-slate-600 dark:text-slate-300">Flash Flood</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-1 bg-rose-500 rounded-full" />
                  <span className="text-slate-600 dark:text-slate-300">Landslide</span>
                </div>
              </div>
            </div>

            {/* Peak Risk Window Callout Banner (Matching Image 2) */}
            <div className="bg-rose-500/10 border border-rose-500/25 rounded-2xl p-3 flex items-center justify-between text-xs text-rose-700 dark:text-rose-300">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-rose-500 shrink-0" />
                <span className="font-bold">
                  Peak Risk Window: 16:00 – 18:00 IST (Next 2 to 4 Hours)
                </span>
              </div>
              <span className="font-mono text-[10px] bg-rose-500/20 text-rose-700 dark:text-rose-300 px-2 py-0.5 rounded font-bold">
                M12 Cascade Peak
              </span>
            </div>

            {/* Simulated 6-Hour SVG Forecast Chart */}
            <div className="h-44 w-full relative pt-2">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 500 140" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="floodGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
                  </linearGradient>
                  <linearGradient id="slideGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Shaded Peak Risk Zone in background */}
                <rect x="150" y="10" width="160" height="110" fill="rgba(244, 63, 94, 0.08)" rx="8" />

                {/* Gridlines */}
                <line x1="0" y1="30" x2="500" y2="30" stroke="#94a3b8" strokeOpacity="0.15" strokeDasharray="3 3" />
                <line x1="0" y1="70" x2="500" y2="70" stroke="#94a3b8" strokeOpacity="0.15" strokeDasharray="3 3" />
                <line x1="0" y1="110" x2="500" y2="110" stroke="#94a3b8" strokeOpacity="0.15" strokeDasharray="3 3" />

                {/* Area paths */}
                <path d="M 0,110 L 0,85 Q 120,70 230,25 T 350,45 T 500,90 L 500,120 L 0,120 Z" fill="url(#floodGrad)" />
                <path d="M 0,110 L 0,95 Q 130,85 230,35 T 350,55 T 500,100 L 500,120 L 0,120 Z" fill="url(#slideGrad)" />

                {/* Lines */}
                <path
                  d="M 0,85 Q 120,70 230,25 T 350,45 T 500,90"
                  fill="none"
                  stroke="#06b6d4"
                  strokeWidth="3"
                />
                <path
                  d="M 0,95 Q 130,85 230,35 T 350,55 T 500,100"
                  fill="none"
                  stroke="#f43f5e"
                  strokeWidth="3"
                />

                {/* Peak point marker */}
                <circle cx="230" cy="25" r="5" fill="#06b6d4" stroke="#ffffff" strokeWidth="2" />
                <circle cx="230" cy="35" r="5" fill="#f43f5e" stroke="#ffffff" strokeWidth="2" />
              </svg>

              {/* Time stamps below chart */}
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mt-2 px-1">
                <span>14:00 (Now)</span>
                <span>15:00 (+1h)</span>
                <span className="text-rose-500 font-bold">16:30 (Peak Surge)</span>
                <span>18:00 (+4h)</span>
                <span>20:00 (+6h)</span>
              </div>
            </div>
          </div>

          {/* Card C: Elevation & Terrain Profile Cross-Section */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base flex items-center gap-2">
                  <Compass className="w-4 h-4 text-blue-500" />
                  <span>Micro-Catchment Elevation & Cross-Section Profile</span>
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Transect from Eastern Ridge (2,100m) through Settlement Terrace (1,760m) to Beas River Thalweg (1,580m)
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                Transect: 1.8 km
              </span>
            </div>

            {/* Cross Section Graphic */}
            <div className="h-36 w-full relative pt-2">
              <svg className="w-full h-full" viewBox="0 0 500 120" preserveAspectRatio="none">
                {/* Terrain Polyline */}
                <path
                  d="M 0,20 L 100,35 L 200,65 L 320,70 L 420,105 L 500,110 L 500,120 L 0,120 Z"
                  fill="rgba(59, 130, 246, 0.08)"
                />
                <path
                  d="M 0,20 L 100,35 L 200,65 L 320,70 L 420,105 L 500,110"
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="2.5"
                />

                {/* High Risk Settlement Buffer */}
                <rect x="190" y="55" width="130" height="30" fill="rgba(239, 68, 68, 0.2)" stroke="#ef4444" strokeDasharray="3 3" rx="6" />

                {/* River water marker */}
                <path d="M 420,105 L 500,110 L 500,120 L 420,120 Z" fill="#06b6d4" fillOpacity="0.4" />

                {/* Labels & Markers */}
                <circle cx="50" cy="28" r="3" fill="#3b82f6" />
                <circle cx="250" cy="68" r="4" fill="#ef4444" />
                <circle cx="460" cy="108" r="3" fill="#06b6d4" />
              </svg>

              <div className="flex justify-between text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-1">
                <span>Upper Ridge (2,100 m)</span>
                <span className="text-red-500 font-bold">Settlement Terrace (1,760 m) [RISK ZONE]</span>
                <span className="text-cyan-500 font-bold">Beas River Bed (1,580 m)</span>
              </div>
            </div>
          </div>

          {/* Card D: "Why is this Ward at Risk?" AI Explanations */}
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Why is this Ward at Risk? — AI Diagnostic Summary
              </h3>
            </div>

            <div className="space-y-2.5 text-xs text-slate-700 dark:text-slate-300">
              <div className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                <p>
                  <strong className="text-slate-900 dark:text-white">Soil Saturation Threshold Exceeded:</strong> Overburden colluvial soil above Upper Naggar reached 78% volumetric saturation, reducing effective shear strength by 42%.
                </p>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                <p>
                  <strong className="text-slate-900 dark:text-white">Upstream Tributary Choke:</strong> Chhaki Nullah is experiencing rapid water stage rise (+0.35m/hr) caused by localized debris flow at upstream culvert km 2.4.
                </p>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                <p>
                  <strong className="text-slate-900 dark:text-white">Topographic Funneling:</strong> A 32° terrain gradient accelerates flash flood runoff into the settlement terrace in less than 35 minutes of travel time.
                </p>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                <p>
                  <strong className="text-slate-900 dark:text-white">Demographic Vulnerability:</strong> 85 vulnerable citizens (infants, elderly) reside in 24 houses directly in the predicted 50-year hydrodynamic flood corridor.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: 72% Radial Gauge, Mini Map, Actions Checklist (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Card 1: 72% Landslide Trigger Probability Radial Gauge */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                  GEOTECHNICAL HAZARD ENGINE (M4)
                </span>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">
                  Landslide Trigger Probability
                </h3>
              </div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                HIGH THREAT
              </span>
            </div>

            {/* Radial Gauge Display */}
            <div className="flex flex-col items-center justify-center py-2">
              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  {/* Track circle */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="currentColor"
                    strokeWidth="8"
                    className="text-slate-100 dark:text-slate-800"
                  />
                  {/* Progress circle */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="currentColor"
                    strokeWidth="8"
                    strokeDasharray="251.2"
                    strokeDashoffset={251.2 * (1 - 0.72)}
                    strokeLinecap="round"
                    className="text-rose-500 transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-4xl font-black text-slate-900 dark:text-white font-mono">
                    72%
                  </span>
                  <span className="text-[10px] font-bold text-rose-500 uppercase tracking-wider">
                    Probability
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-500 text-center mt-2">
                Confidence: <strong className="text-slate-700 dark:text-slate-300">89%</strong> (Based on Sentinel-1 InSAR & IMD AWS)
              </p>
            </div>

            {/* Contributing Factor Progress Bars */}
            <div className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
              <div className="space-y-1">
                <div className="flex justify-between text-slate-600 dark:text-slate-400 font-mono">
                  <span>Soil Moisture Saturation</span>
                  <span className="font-bold text-rose-500">84%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-rose-500 h-full rounded-full" style={{ width: '84%' }} />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-600 dark:text-slate-400 font-mono">
                  <span>Slope Angle Gradient (32°)</span>
                  <span className="font-bold text-orange-500">78%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-orange-500 h-full rounded-full" style={{ width: '78%' }} />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-600 dark:text-slate-400 font-mono">
                  <span>24h Rainfall Accumulation (62mm)</span>
                  <span className="font-bold text-amber-500">65%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-amber-500 h-full rounded-full" style={{ width: '65%' }} />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-600 dark:text-slate-400 font-mono">
                  <span>Geological Bedrock Instability</span>
                  <span className="font-bold text-blue-500">55%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full rounded-full" style={{ width: '55%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Local Ward Boundary Map */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                  Local Jurisdiction Boundary
                </h3>
                <span className="text-[10px] font-mono text-slate-400">
                  Naggar Ward 3 • 2.4 km² Area
                </span>
              </div>
              <button
                onClick={() => navigate('/map')}
                className="text-xs text-blue-500 hover:underline flex items-center gap-1 font-semibold"
              >
                <span>Full Map</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* Mini Map Container */}
            <div className="h-56 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 relative">
              <MapContainer className="w-full h-full" />
            </div>
          </div>

          {/* Card 3: Recommended Actions Checklist */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Recommended Response Actions</span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Pre-authorized SOP checklist for local Gram Panchayat & District Field Responders
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold">
                SOP Level 3
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              {[
                {
                  id: 'evacuate',
                  title: 'Evacuate Riverfront Households',
                  desc: 'Issue immediate evacuation orders for 14 homes within 50m of Chhaki Nullah bank.',
                  priority: 'HIGH',
                },
                {
                  id: 'sandbags',
                  title: 'Deploy Sandbags at Culvert km 2.4',
                  desc: 'Reinforce retaining wall to prevent tributary breach into the lower village road.',
                  priority: 'COMPLETED',
                },
                {
                  id: 'slope',
                  title: 'Monitor Slope Behind Primary School',
                  desc: 'Field team to inspect tension cracks along Naggar Castle upper ridge.',
                  priority: 'URGENT',
                },
                {
                  id: 'volunteers',
                  title: 'Alert GP Disaster Taskforce Volunteers',
                  desc: 'Assemble 12 local volunteers at Naggar Community Hall for rapid evacuation assistance.',
                  priority: 'ACTIVE',
                },
                {
                  id: 'machinery',
                  title: 'Pre-position JCB Excavators at Highway Fork',
                  desc: 'Ensure clearing equipment is on standby for debris clearance along connecting roads.',
                  priority: 'PENDING',
                },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => toggleChecklist(item.id)}
                  className={`p-3 rounded-2xl border transition cursor-pointer flex items-start gap-3 ${
                    checklist[item.id]
                      ? 'bg-emerald-500/5 border-emerald-500/30 text-slate-700 dark:text-slate-300'
                      : 'bg-slate-50 dark:bg-slate-800/50 border-slate-100 dark:border-slate-800 hover:border-blue-500/30'
                  }`}
                >
                  <div className="mt-0.5">
                    {checklist[item.id] ? (
                      <CheckSquare className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold ${checklist[item.id] ? 'line-through text-slate-400' : 'text-slate-900 dark:text-white'}`}>
                        {item.title}
                      </span>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold ${
                          item.priority === 'COMPLETED'
                            ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                            : item.priority === 'URGENT' || item.priority === 'HIGH'
                            ? 'bg-red-500/20 text-red-600 dark:text-red-400'
                            : 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                        }`}
                      >
                        {item.priority}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Export Report Dialog Modal */}
      {isExportModalOpen && selectedUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm no-print">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-xl w-full shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="bg-slate-50 dark:bg-slate-800/80 px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <Download className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-base text-slate-900 dark:text-white">
                    Export Situation Report
                  </h3>
                  <p className="text-xs text-slate-500">
                    Disaster intelligence export for {selectedUnit.name}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsExportModalOpen(false)}
                className="p-1.5 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Jurisdiction Badge */}
            <div className="p-6 space-y-4">
              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-xs font-mono font-bold text-slate-400 uppercase">
                    Jurisdiction Target
                  </div>
                  <div className="font-bold text-sm text-slate-900 dark:text-white mt-0.5">
                    {selectedUnit.name} ({selectedUnit.admin_id})
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    GP: {gramPanchayat} • Tehsil: {block} • District: {district}
                  </div>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold ${
                  isHighRisk ? 'bg-red-500/20 text-red-600 dark:text-red-400' : 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                }`}>
                  {selectedUnit.current_hazard.risk_level} RISK
                </span>
              </div>

              {/* Format Options */}
              <div className="space-y-3">
                <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                  Select Export Format
                </div>

                {/* Option 1: PDF Briefing */}
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-all flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400">
                      <Printer className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-1.5">
                        <span>Official PDF Report</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-500 font-bold">Print Ready</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Clean executive briefing layout for SDMA & District Magistrates with full risk profile.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handlePrintPdf}
                    className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition whitespace-nowrap"
                  >
                    Print / PDF
                  </button>
                </div>

                {/* Option 2: CSV Data */}
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      <FileSpreadsheet className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-sm text-slate-900 dark:text-white">
                        Tabular CSV Dataset (.csv)
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Complete demographic exposure, water depth, terrain slope, and checklist responses in Excel/Sheets format.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleExportCsv}
                    className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition whitespace-nowrap"
                  >
                    Download CSV
                  </button>
                </div>

                {/* Option 3: JSON Feed */}
                <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-purple-500/50 dark:hover:border-purple-500/50 transition-all flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-sm text-slate-900 dark:text-white">
                        Raw Intelligence Feed (.json)
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Structured machine-readable GeoJSON coordinates and multi-hazard model inference payload.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleExportJson}
                    className="px-3.5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-sm transition whitespace-nowrap"
                  >
                    Download JSON
                  </button>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
              <span className="font-mono text-[11px]">HP-SDMA Form: SITREP-W-2026</span>
              <button
                onClick={() => setIsExportModalOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Floating Toast Notification */}
      {exportSuccessMsg && (
        <div className="fixed bottom-6 right-6 z-50 p-4 bg-emerald-600 text-white rounded-2xl shadow-xl flex items-center gap-3 text-xs font-bold animate-slideUp">
          <CheckCircle className="w-4 h-4" />
          <span>{exportSuccessMsg}</span>
        </div>
      )}
    </div>
  );
};

