/**
 * frontend/src/pages/FloodMapPage.tsx
 * ===================================
 * Catchment Risk Map Full Operational Geospatial View (Phase 06).
 * Recreates the exact layout and controls from Reference Image 3:
 * 1. Top Quick Filter Pills Bar (Flood, Landslide, Compound, Rainfall, River, Wards)
 * 2. Full-bleed Google Maps Canvas with in-map dynamic layers & controls
 * 3. Right Inspector Drawer:
 *    - Selected Ward Overview & Demographics
 *    - 87% Confidence Score Bar
 *    - Tabs (Overview, Risk Factors, Forecast, Assets)
 *    - Nearby Wards Risk Comparison Table
 * 4. Bottom River Hydrograph & Profile Drawer
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { MapContainer } from '../components/Map/MapContainer';
import { useHazardStore } from '../store/useHazardStore';
import { useMapStore } from '../store/useMapStore';
import { fetchHyperlocalAdminUnits, fetchStations } from '../services/api/endpoints';
import { HyperlocalAdminUnit, StationTelemetry } from '../types';
import {
  Layers,
  Activity,
  Waves,
  ShieldCheck,
  AlertTriangle,
  X,
  Navigation,
  Compass,
  MapPin,
  ExternalLink,
  Users,
  Home,
  CheckCircle2,
  TrendingUp,
  Maximize2,
  ChevronRight,
  Filter,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

export const FloodMapPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { resetToBeasCatchment, flyToLocation } = useMapStore();

  const [adminUnits, setAdminUnits] = useState<HyperlocalAdminUnit[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<HyperlocalAdminUnit | null>(null);
  const [stations, setStations] = useState<StationTelemetry[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'factors' | 'forecast' | 'assets'>('overview');
  const [showBottomProfile, setShowBottomProfile] = useState<boolean>(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);

  // Quick Filter Pills State
  const [activeFilters, setActiveFilters] = useState<Record<string, boolean>>({
    flood: true,
    landslide: true,
    compound: true,
    rainfall: true,
    river: true,
    wards: true,
  });

  const toggleFilter = (key: string) => {
    setActiveFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  useEffect(() => {
    Promise.all([fetchHyperlocalAdminUnits(), fetchStations()]).then(([units, stns]) => {
      setAdminUnits(units);
      setStations(stns);

      const targetId = searchParams.get('admin_id') || 'HP-KUL-NAG-03';
      const found = units.find((u) => u.admin_id === targetId) || units[0];
      if (found) {
        setSelectedUnit(found);
      }
    });
  }, [searchParams]);

  const nearbyWards = [
    { name: 'Naggar Ward 2 (Lower)', dist: '0.8 km', risk: 'HIGH', score: '0.78', status: 'Advisory Active' },
    { name: 'Naggar Ward 1 (Castle)', dist: '1.2 km', risk: 'MODERATE', score: '0.54', status: 'Monitoring' },
    { name: 'Jagatsukh GP Ward 4', dist: '2.8 km', risk: 'MODERATE', score: '0.61', status: 'Monitoring' },
    { name: 'Bahang GP Ward 1', dist: '5.2 km', risk: 'CRITICAL', score: '0.92', status: 'Evacuating' },
  ];

  return (
    <div className="space-y-3 h-[calc(100vh-125px)] flex flex-col min-w-0">
      {/* 1. Top Quick Filter Pills Bar (Matching Image 3) */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3 rounded-2xl shadow-sm">
        <div className="flex items-center gap-2 overflow-x-auto py-0.5 max-w-full">
          <div className="flex items-center gap-1.5 px-2 text-[11px] font-mono uppercase text-slate-400 font-bold shrink-0">
            <Filter className="w-3.5 h-3.5 text-blue-500" />
            <span>Map Layers:</span>
          </div>

          {[
            { id: 'flood', label: 'Flood Risk', activeColor: 'bg-cyan-500 text-white' },
            { id: 'landslide', label: 'Landslide Threat', activeColor: 'bg-rose-500 text-white' },
            { id: 'compound', label: 'Compound Multi-Hazard', activeColor: 'bg-purple-600 text-white' },
            { id: 'rainfall', label: 'Rainfall Nowcast', activeColor: 'bg-blue-600 text-white' },
            { id: 'river', label: 'River Network', activeColor: 'bg-sky-500 text-white' },
            { id: 'wards', label: 'Ward Boundaries', activeColor: 'bg-slate-700 text-white' },
          ].map((pill) => (
            <button
              key={pill.id}
              onClick={() => toggleFilter(pill.id)}
              className={`px-3 py-1 rounded-xl text-xs font-semibold transition shrink-0 flex items-center gap-1.5 ${
                activeFilters[pill.id]
                  ? `${pill.activeColor} shadow-sm`
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  activeFilters[pill.id] ? 'bg-white' : 'bg-slate-400'
                }`}
              />
              <span>{pill.label}</span>
            </button>
          ))}
        </div>

        {/* View Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition flex items-center gap-1.5 ${
              isDrawerOpen
                ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-blue-500" />
            <span>{isDrawerOpen ? 'Hide Inspector' : 'Inspect Details'}</span>
          </button>

          <button
            onClick={() => setShowBottomProfile(!showBottomProfile)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition flex items-center gap-1.5 ${
              showBottomProfile
                ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-blue-500" />
            <span>River Profile</span>
          </button>

          <button
            onClick={resetToBeasCatchment}
            className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Reset Basin</span>
          </button>
        </div>
      </div>

      {/* 2. Main Map Canvas + Right Inspector Drawer */}
      <div className="flex-1 relative rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm flex">
        {/* Dominant Map Canvas */}
        <div className="flex-1 h-full w-full relative">
          <MapContainer
            className="w-full h-full"
            onFeatureSelect={(type, data) => {
              if (data) {
                const found = adminUnits.find((u) => u.admin_id === (data.admin_id || data.id) || u.name === data.name);
                if (found) setSelectedUnit(found);
                setIsDrawerOpen(true);
              }
            }}
          />
        </div>

        {/* Right Location Details Drawer (Matching Image 3) */}
        {isDrawerOpen && (
          <div className="w-96 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-l border-slate-200 dark:border-slate-800 p-5 overflow-y-auto space-y-5 flex flex-col justify-between shrink-0 shadow-2xl z-20 transition-all duration-300">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-rose-500 font-bold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                      HIGH RISK JURISDICTION
                    </span>
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {selectedUnit?.admin_id || 'HP-KUL-NAG-03'}
                    </span>
                  </div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white mt-1">
                    {selectedUnit?.name || 'Naggar Ward 3'}
                  </h3>
                  <span className="text-xs text-slate-400 font-mono">
                    Upper Naggar Heritage Corridor (1,760m ASL)
                  </span>
                </div>

                <button
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* 87% Confidence Score Bar (Matching Image 3) */}
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200 dark:border-blue-800 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-blue-700 dark:text-blue-300 font-bold flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                    <span>87% AI Model Confidence</span>
                  </span>
                  <span className="text-[10px] text-blue-500 font-semibold">M1–M12 Ensemble</span>
                </div>
                <div className="w-full bg-blue-200 dark:bg-blue-950 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full rounded-full" style={{ width: '87%' }} />
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400">
                  Grounded in IMD AWS telemetry, Sentinel-1 InSAR & CWC rating curves
                </div>
              </div>

              {/* Inspector Tabs */}
              <div className="flex border-b border-slate-200 dark:border-slate-800 text-xs font-semibold">
                {[
                  { id: 'overview', label: 'Overview' },
                  { id: 'factors', label: 'Risk Factors' },
                  { id: 'forecast', label: 'Forecast' },
                  { id: 'assets', label: 'Assets' },
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setActiveTab(t.id as any)}
                    className={`flex-1 pb-2 border-b-2 transition text-center ${
                      activeTab === t.id
                        ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold'
                        : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Tab Contents: Overview */}
              {activeTab === 'overview' && (
                <div className="space-y-4 text-xs">
                  {/* Key Metrics Grid */}
                  <div className="grid grid-cols-2 gap-2.5">
                    <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800">
                      <span className="text-[10px] font-mono text-slate-400 uppercase">Population</span>
                      <div className="text-base font-black font-mono text-slate-900 dark:text-white mt-0.5">
                        {selectedUnit?.exposure.permanent_population || 420}
                      </div>
                      <span className="text-[10px] text-rose-500 font-medium">85 Vulnerable</span>
                    </div>

                    <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800">
                      <span className="text-[10px] font-mono text-slate-400 uppercase">Lead Time</span>
                      <div className="text-base font-black font-mono text-rose-600 dark:text-rose-400 mt-0.5">
                        35 min
                      </div>
                      <span className="text-[10px] text-slate-400 font-medium">To surge peak</span>
                    </div>
                  </div>

                  {/* Primary Threat Summary */}
                  <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-2xl space-y-1 text-rose-900 dark:text-rose-300">
                    <div className="font-bold flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-rose-500" />
                      <span>Compound Surge Vulnerability</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Saturated colluvium slope (78% soil moisture) coupled with Chhaki Nullah tributary rise (+0.35m/hr). Debris blockage threat at km 2.4.
                    </p>
                  </div>

                  {/* Link to Dedicated Village/Ward View */}
                  <button
                    onClick={() => navigate(`/ward-view?admin_id=${selectedUnit?.admin_id || 'HP-KUL-NAG-03'}`)}
                    className="w-full py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white rounded-xl font-bold shadow-md transition flex items-center justify-center gap-1.5"
                  >
                    <span>Inspect Full Village & Ward Intelligence</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}

              {activeTab === 'factors' && (
                <div className="space-y-3 text-xs">
                  <div className="space-y-1">
                    <div className="flex justify-between font-mono">
                      <span>Soil Moisture Saturation</span>
                      <span className="font-bold text-rose-500">84%</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-rose-500 h-full rounded-full" style={{ width: '84%' }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between font-mono">
                      <span>Terrain Slope (32° Gradient)</span>
                      <span className="font-bold text-orange-500">78%</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-orange-500 h-full rounded-full" style={{ width: '78%' }} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between font-mono">
                      <span>River Proximity (450m to Bank)</span>
                      <span className="font-bold text-amber-500">65%</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-amber-500 h-full rounded-full" style={{ width: '65%' }} />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'forecast' && (
                <div className="space-y-2 text-xs">
                  <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl flex justify-between font-mono">
                    <span>+1h (15:00)</span>
                    <span className="text-cyan-500 font-bold">24 mm/h • 2.95m Stage</span>
                  </div>
                  <div className="p-2.5 bg-rose-500/10 rounded-xl flex justify-between font-mono font-bold text-rose-600 dark:text-rose-400">
                    <span>+3h (17:00 Peak)</span>
                    <span>45 mm/h • 3.62m Stage</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl flex justify-between font-mono">
                    <span>+6h (20:00)</span>
                    <span className="text-slate-400">6 mm/h • 2.40m Stage</span>
                  </div>
                </div>
              )}

              {activeTab === 'assets' && (
                <div className="space-y-2 text-xs">
                  <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl flex justify-between">
                    <div>
                      <span className="font-bold block text-slate-800 dark:text-slate-200">
                        Government Primary School
                      </span>
                      <span className="text-[10px] text-slate-400">Identified Safe Haven (Cap: 250)</span>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-500 font-bold">CLEAR</span>
                  </div>

                  <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl flex justify-between">
                    <div>
                      <span className="font-bold block text-slate-800 dark:text-slate-200">
                        Chhaki Nullah Culvert Bridge
                      </span>
                      <span className="text-[10px] text-rose-500">Critical Access Chokepoint</span>
                    </div>
                    <span className="text-[10px] font-mono text-rose-500 font-bold">AT RISK</span>
                  </div>
                </div>
              )}

              {/* Nearby Wards Risk Comparison Table (Matching Image 3) */}
              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-wider text-slate-400 font-mono text-[10px]">
                    Adjacent Wards In Reach
                  </span>
                  <span className="text-[10px] font-mono text-blue-500">5 Monitored</span>
                </div>

                <div className="space-y-1.5 text-xs">
                  {nearbyWards.map((w, idx) => (
                    <div
                      key={idx}
                      className="p-2 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition flex items-center justify-between"
                    >
                      <div>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 block truncate max-w-[150px]">
                          {w.name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">{w.dist} away</span>
                      </div>
                      <div className="text-right">
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${
                            w.risk === 'CRITICAL'
                              ? 'bg-rose-500/20 text-rose-600 dark:text-rose-400'
                              : w.risk === 'HIGH'
                              ? 'bg-orange-500/20 text-orange-600 dark:text-orange-400'
                              : 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
                          }`}
                        >
                          {w.risk} ({w.score})
                        </span>
                        <span className="text-[9px] block text-slate-400">{w.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-400">
              <span>Upper Beas Basin Reach 04</span>
              <span className="text-emerald-500 font-bold">● Sensor Linked</span>
            </div>
          </div>
        )}

        {/* Drawer Re-open Tab if closed */}
        {!isDrawerOpen && (
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="absolute top-4 right-4 z-20 px-3 py-2 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg text-xs font-bold text-slate-700 dark:text-slate-300 hover:text-blue-500 flex items-center gap-1.5"
          >
            <MapPin className="w-3.5 h-3.5 text-blue-500" />
            <span>Show Location Details</span>
          </button>
        )}

        {/* Bottom Elevation / Hydrograph Sheet Drawer */}
        {showBottomProfile && (
          <div className="absolute bottom-4 left-4 right-4 z-20 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border border-slate-200 dark:border-slate-800 p-4 rounded-3xl shadow-2xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Waves className="w-4 h-4 text-blue-500" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  Beas River Hydrograph & Thalweg Profile (Solang → Bhuntar)
                </h4>
              </div>
              <button
                onClick={() => setShowBottomProfile(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="h-28 w-full flex items-end justify-between gap-1 pt-4 px-2">
              {[
                { station: 'Solang Gorge', elev: 2480, floodElev: 2483.8, danger: true },
                { station: 'Palchan', elev: 2310, floodElev: 2312.9, danger: true },
                { station: 'Old Manali', elev: 2090, floodElev: 2091.6, danger: false },
                { station: 'Aleo Bridge', elev: 1980, floodElev: 1984.1, danger: true },
                { station: 'Naggar Chhaki', elev: 1760, floodElev: 1763.5, danger: true },
                { station: '15 Mile', elev: 1650, floodElev: 1652.2, danger: false },
                { station: 'Kullu Sarvari', elev: 1290, floodElev: 1293.2, danger: false },
                { station: 'Bhuntar Confluence', elev: 1080, floodElev: 1083.8, danger: true },
              ].map((p, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
                    {p.elev}m
                  </span>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-t-md relative h-20 flex items-end">
                    <div
                      className={`w-full rounded-t-md transition-all ${
                        p.danger
                          ? 'bg-gradient-to-t from-red-600 to-rose-400 shadow-lg shadow-red-500/30'
                          : 'bg-gradient-to-t from-blue-600 to-cyan-400'
                      }`}
                      style={{ height: `${(p.elev / 2500) * 100}%` }}
                    />
                  </div>
                  <span className="text-[9px] font-medium text-slate-700 dark:text-slate-300 text-center truncate max-w-[80px]">
                    {p.station}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
