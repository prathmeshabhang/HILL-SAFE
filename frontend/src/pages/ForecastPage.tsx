/**
 * frontend/src/pages/ForecastPage.tsx
 * ===================================
 * Forecasts & Prediction Operational View (Phase 06).
 * Recreates the exact layout and data density from Reference Image 4:
 * 1. 4 Summary Metric Cards (Peak Risk Window, Max River Level, Rainfall Forecast, High Risk Wards)
 * 2. 6-Hour Rolling Multi-Chart Panel:
 *    - 6h Rainfall bar chart (mm/hr)
 *    - 6h River Stage area chart with dashed danger line (3.5m) and 3.6m peak marker
 *    - 6h Flood Risk Index
 * 3. Geotechnical & Compound Intelligence:
 *    - 6h Landslide Trigger Probability area chart
 *    - Compound Multi-Hazard score
 *    - Key Contributing Factors breakdown bars
 * 4. 6-Hour Forecast Timeline Tabular View (with +3h peak row highlighted)
 * 5. Spatial Forecast Mini Map & AI Insights Cards
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer } from '../components/Map/MapContainer';
import {
  CloudRain,
  Waves,
  Clock,
  AlertTriangle,
  TrendingUp,
  MapPin,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  Download,
  Play,
  CheckCircle2,
  Calendar,
  Layers,
} from 'lucide-react';

export const ForecastPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedLeadHour, setSelectedLeadHour] = useState<number>(3);

  // 6-hour timeline tabular data
  const timelineData = [
    {
      hour: '+1h (15:00 IST)',
      rainfall: '24.2 mm/h',
      stage: '2.95 m',
      floodRisk: 'Moderate (0.58)',
      landslideRisk: 'Moderate (0.52)',
      dominant: 'FLASH_FLOOD',
      action: 'Issue Yellow Advisory to low-lying wards',
      isPeak: false,
    },
    {
      hour: '+2h (16:00 IST)',
      rainfall: '38.5 mm/h',
      stage: '3.42 m',
      floodRisk: 'High (0.81)',
      landslideRisk: 'High (0.69)',
      dominant: 'COMPOUND_SURGE',
      action: 'Prepare Riverbank Evacuation Corridors',
      isPeak: false,
    },
    {
      hour: '+3h (17:00 IST)',
      rainfall: '45.0 mm/h',
      stage: '3.62 m',
      floodRisk: 'Critical (0.92)',
      landslideRisk: 'High (0.74)',
      dominant: 'NATURAL_DAM_BREACH_RISK',
      action: 'CRITICAL: Evacuate Ward 3 Naggar & Bahang reach',
      isPeak: true, // HIGHLIGHTED IN RED/PINK
    },
    {
      hour: '+4h (18:00 IST)',
      rainfall: '28.0 mm/h',
      stage: '3.38 m',
      floodRisk: 'High (0.76)',
      landslideRisk: 'High (0.71)',
      dominant: 'FLASH_FLOOD',
      action: 'Maintain flood wall barrier alerts',
      isPeak: false,
    },
    {
      hour: '+5h (19:00 IST)',
      rainfall: '14.5 mm/h',
      stage: '2.85 m',
      floodRisk: 'Moderate (0.54)',
      landslideRisk: 'Moderate (0.62)',
      dominant: 'LANDSLIDE_DELAYED',
      action: 'Monitor waterlogged slopes behind schools',
      isPeak: false,
    },
    {
      hour: '+6h (20:00 IST)',
      rainfall: '6.2 mm/h',
      stage: '2.40 m',
      floodRisk: 'Low (0.35)',
      landslideRisk: 'Moderate (0.55)',
      dominant: 'DEBRIS_CLEARANCE',
      action: 'Begin initial structural damage survey',
      isPeak: false,
    },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 sm:p-6 rounded-3xl shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              HYDROLOGICAL & GEOTECHNICAL ML PREDICTIONS
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs font-mono text-emerald-500 font-semibold">M1–M12 Active</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white">
            Forecasts & Prediction
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Catchment-wide 6-Hour Rolling ML Projections & Multi-Hazard Timeline for Upper Beas Basin.
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start md:self-auto">
          <button
            onClick={() => navigate('/dam-analysis')}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-700 transition flex items-center gap-1.5"
          >
            <Play className="w-3.5 h-3.5 text-blue-500" />
            <span>Simulate Breach</span>
          </button>

          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Forecast PDF</span>
          </button>
        </div>
      </div>

      {/* 2. Top 4 Summary Metric Cards (Matching Image 4) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Peak Risk Window */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
              Critical Timeline
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
              URGENT
            </span>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white font-mono">
              Next 2–4 Hours
            </div>
            <div className="text-xs font-bold text-rose-500 mt-1">
              16:00 – 18:00 IST • Peak Surge
            </div>
          </div>
          <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
            Convective cloudburst cell aligns with tributary time of concentration.
          </p>
        </div>

        {/* Card 2: Max River Level */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
              Max Projected River Level
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
              DANGER MARK
            </span>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white font-mono flex items-baseline gap-2">
              <span>3.62 m</span>
              <span className="text-xs text-rose-500 font-bold font-sans">+0.82 m</span>
            </div>
            <div className="text-xs font-bold text-amber-500 mt-1">
              Surpasses Danger Mark (3.5 m)
            </div>
          </div>
          <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
            Highest projected stage at Bhuntar & Aleo Bridge gauge stations.
          </p>
        </div>

        {/* Card 3: Rainfall Forecast */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
              6h Rainfall Accumulation
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              HEAVY
            </span>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white font-mono">
              65.4 mm
            </div>
            <div className="text-xs font-bold text-blue-500 mt-1">
              Solang & Upper Beas Catchment
            </div>
          </div>
          <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
            M1 ConvLSTM Radar Nowcast predicts intense localized cloudburst banding.
          </p>
        </div>

        {/* Card 4: High Risk Wards */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
              High Risk Jurisdictions
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
              12 / 42 WARDS
            </span>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white font-mono">
              12 Wards
            </div>
            <div className="text-xs font-bold text-purple-500 mt-1">
              Compound Flood & Landslide Exposure
            </div>
          </div>
          <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
            Naggar 3, Bahang GP, Vashisht 1 & Old Manali facing severe surge threat.
          </p>
        </div>
      </div>

      {/* 3. Primary Multi-Chart Projections (Two Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 6h Rainfall, River Stage & Flood Risk (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base flex items-center gap-2">
                  <Waves className="w-4 h-4 text-blue-500" />
                  <span>6-Hour Hydrological Surge & Rainfall Nowcast</span>
                </h3>
                <p className="text-xs text-slate-500">
                  Hydrodynamic modeling (M10/M11) synchronized with CWC rating curves
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 font-bold">
                Cadence: 15 min
              </span>
            </div>

            {/* Chart 1: Rainfall (mm/hr) Bars */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-600 dark:text-slate-400 font-semibold flex items-center gap-1.5">
                  <CloudRain className="w-3.5 h-3.5 text-blue-500" />
                  <span>Rainfall Rate Forecast (mm/hr)</span>
                </span>
                <span className="text-blue-500 font-bold">Peak: 45.0 mm/h @ +3h</span>
              </div>

              {/* Bar Chart */}
              <div className="h-24 w-full flex items-end justify-between gap-3 pt-2">
                {[
                  { time: '14:00', val: 18.5 },
                  { time: '15:00', val: 24.2 },
                  { time: '16:00', val: 38.5 },
                  { time: '17:00 (Peak)', val: 45.0, peak: true },
                  { time: '18:00', val: 28.0 },
                  { time: '19:00', val: 14.5 },
                  { time: '20:00', val: 6.2 },
                ].map((item, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] font-mono text-slate-500">{item.val}</span>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-t-lg h-16 flex items-end">
                      <div
                        className={`w-full rounded-t-lg transition-all ${
                          item.peak
                            ? 'bg-blue-600 shadow-md shadow-blue-500/30'
                            : 'bg-blue-400/80 hover:bg-blue-500'
                        }`}
                        style={{ height: `${(item.val / 45) * 100}%` }}
                      />
                    </div>
                    <span className="text-[9px] font-mono text-slate-400 truncate w-full text-center">
                      {item.time.split(' ')[0]}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Chart 2: River Stage (m) Hydrograph with Danger Line */}
            <div className="space-y-2 pt-4 border-t border-slate-100 dark:border-slate-800">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-600 dark:text-slate-400 font-semibold flex items-center gap-1.5">
                  <Waves className="w-3.5 h-3.5 text-cyan-500" />
                  <span>River Stage Hydrograph vs 3.5 m Danger Mark</span>
                </span>
                <span className="text-rose-500 font-bold">Max: 3.62 m (Breach Warning)</span>
              </div>

              {/* Hydrograph Area with Danger Line */}
              <div className="h-36 w-full relative pt-2">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 500 120" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="stageGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
                      <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.2" />
                      <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>

                  {/* Red Dashed Danger Level Line at 3.5m (approx Y=30) */}
                  <line x1="0" y1="30" x2="500" y2="30" stroke="#ef4444" strokeWidth="2" strokeDasharray="4 4" />
                  <text x="10" y="24" fill="#ef4444" fontSize="10" fontFamily="monospace" fontWeight="bold">
                    DANGER LEVEL 3.50 m
                  </text>

                  {/* Warning Level Line at 2.8m (approx Y=65) */}
                  <line x1="0" y1="65" x2="500" y2="65" stroke="#f59e0b" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                  <text x="10" y="60" fill="#f59e0b" fontSize="9" fontFamily="monospace">
                    WARNING LEVEL 2.80 m
                  </text>

                  {/* Stage Area */}
                  <path
                    d="M 0,90 Q 100,75 200,45 T 320,18 T 420,55 T 500,85 L 500,120 L 0,120 Z"
                    fill="url(#stageGrad)"
                  />
                  {/* Stage Line */}
                  <path
                    d="M 0,90 Q 100,75 200,45 T 320,18 T 420,55 T 500,85"
                    fill="none"
                    stroke="#06b6d4"
                    strokeWidth="3"
                  />

                  {/* Peak Marker Badge */}
                  <circle cx="320" cy="18" r="5" fill="#ef4444" stroke="#ffffff" strokeWidth="2" />
                </svg>

                {/* Peak Callout Badge */}
                <div className="absolute top-2 right-1/3 bg-rose-600 text-white text-[10px] font-mono px-2 py-0.5 rounded shadow font-bold">
                  Peak 3.62 m @ 17:00
                </div>

                <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-2">
                  <span>14:00 (2.4m)</span>
                  <span>15:00 (2.9m)</span>
                  <span>16:00 (3.4m)</span>
                  <span className="text-rose-500 font-bold">17:00 (3.62m)</span>
                  <span>18:00 (3.3m)</span>
                  <span>20:00 (2.4m)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Landslide Probability, Compound Hazard & Key Factors (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">
                  Geotechnical & Multi-Hazard Scores
                </h3>
                <p className="text-xs text-slate-500">
                  Coupled landslide triggering (M4) & cascade indexing (M12)
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 font-bold">
                74% Trigger Peak
              </span>
            </div>

            {/* Landslide Probability Area SVG */}
            <div className="space-y-1">
              <span className="text-xs font-mono text-slate-600 dark:text-slate-400 font-semibold">
                6h Landslide Probability (%)
              </span>
              <div className="h-28 w-full relative pt-2">
                <svg className="w-full h-full" viewBox="0 0 400 90" preserveAspectRatio="none">
                  <path
                    d="M 0,70 Q 100,60 200,30 T 280,20 T 400,65 L 400,90 L 0,90 Z"
                    fill="rgba(244, 63, 94, 0.2)"
                  />
                  <path
                    d="M 0,70 Q 100,60 200,30 T 280,20 T 400,65"
                    fill="none"
                    stroke="#f43f5e"
                    strokeWidth="2.5"
                  />
                  <circle cx="280" cy="20" r="4" fill="#f43f5e" stroke="#fff" strokeWidth="1.5" />
                </svg>
                <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
                  <span>+1h (45%)</span>
                  <span>+2h (62%)</span>
                  <span className="text-rose-500 font-bold">+3h (74% Max)</span>
                  <span>+4h (68%)</span>
                  <span>+6h (42%)</span>
                </div>
              </div>
            </div>

            {/* Key Contributing Risk Factors Bars */}
            <div className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold block">
                Primary Hazard Drivers (M13 Vulnerability)
              </span>

              <div className="space-y-1">
                <div className="flex justify-between font-mono">
                  <span>Rainfall Intensity Surge</span>
                  <span className="font-bold text-blue-500">38%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full rounded-full" style={{ width: '38%' }} />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between font-mono">
                  <span>Antecedent Soil Saturation</span>
                  <span className="font-bold text-emerald-500">28%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: '28%' }} />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between font-mono">
                  <span>Terrain Steepness (30°+ Slope)</span>
                  <span className="font-bold text-orange-500">20%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-orange-500 h-full rounded-full" style={{ width: '20%' }} />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between font-mono">
                  <span>River Proximity & Choke Bottleneck</span>
                  <span className="font-bold text-rose-500">14%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-rose-500 h-full rounded-full" style={{ width: '14%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. 6-Hour Forecast Timeline Tabular View (with Peak Row Highlighted) */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-500" />
              <span>6-Hour Multi-Hazard Forecast Progression Matrix</span>
            </h3>
            <p className="text-xs text-slate-500">
              Discrete hourly operational lead time intervals with pre-scripted emergency directives
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 font-bold self-start sm:self-auto">
            ● +3h Peak Inundation Alert Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] font-mono uppercase text-slate-400">
                <th className="py-2.5 px-3">Lead Time</th>
                <th className="py-2.5 px-3">Precipitation</th>
                <th className="py-2.5 px-3">River Stage</th>
                <th className="py-2.5 px-3">Flood Risk</th>
                <th className="py-2.5 px-3">Landslide Risk</th>
                <th className="py-2.5 px-3">Dominant Threat</th>
                <th className="py-2.5 px-3">Operational Directive</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {timelineData.map((row, idx) => (
                <tr
                  key={idx}
                  className={`transition ${
                    row.isPeak
                      ? 'bg-rose-500/15 dark:bg-rose-950/40 font-bold border-l-4 border-rose-500'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <td className="py-3 px-3 font-mono text-slate-900 dark:text-white flex items-center gap-2">
                    {row.isPeak && (
                      <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                    )}
                    <span>{row.hour}</span>
                  </td>
                  <td className="py-3 px-3 font-mono text-blue-600 dark:text-blue-400 font-bold">
                    {row.rainfall}
                  </td>
                  <td className="py-3 px-3 font-mono">
                    <span
                      className={
                        parseFloat(row.stage) >= 3.5
                          ? 'text-rose-600 dark:text-rose-400 font-black'
                          : 'text-slate-700 dark:text-slate-300'
                      }
                    >
                      {row.stage}
                    </span>
                  </td>
                  <td className="py-3 px-3">{row.floodRisk}</td>
                  <td className="py-3 px-3">{row.landslideRisk}</td>
                  <td className="py-3 px-3">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      {row.dominant}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`text-[11px] ${
                        row.isPeak
                          ? 'text-rose-700 dark:text-rose-300 font-extrabold'
                          : 'text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {row.action}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Spatial Forecast Mini Map & AI Insights Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Spatial Mini Map (5 Cols) */}
        <div className="lg:col-span-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                +3h Projected Inundation Footprint
              </h3>
              <p className="text-[11px] text-slate-400">
                Spatial hydrodynamic flood extent at 17:00 IST peak surge
              </p>
            </div>
            <button
              onClick={() => navigate('/map')}
              className="text-xs text-blue-500 font-semibold hover:underline flex items-center gap-1"
            >
              <span>Expand Map</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-64 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 relative">
            <MapContainer className="w-full h-full" />
          </div>
        </div>

        {/* AI Forecast Insights Cards (7 Cols) */}
        <div className="lg:col-span-7 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <h3 className="font-bold text-slate-900 dark:text-white text-base">
              Automated AI Decision Intelligence Insights
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-2xl text-blue-900 dark:text-blue-300">
              <strong className="block text-sm font-bold mb-1">
                1. Hydrological Flash Flood Surges (Solang & Manalsu Reach)
              </strong>
              <p className="leading-relaxed">
                A localized convective cloudburst band will deliver up to 45 mm/hr rainfall into high-elevation tributaries. Because antecedent soil moisture is already at 78%, runoff coefficient exceeds 0.72, generating a sharp peak hydrograph in under 90 minutes.
              </p>
            </div>

            <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-900 dark:text-rose-300">
              <strong className="block text-sm font-bold mb-1">
                2. Landslide & Natural Dam Impoundment Threat
              </strong>
              <p className="leading-relaxed">
                Steep colluvium slopes in Naggar and Bahang sectors face a 74% failure trigger probability. Overtopping of natural debris dams along Chhaki Nullah could release sudden secondary flood surges into downstream residential clusters.
              </p>
            </div>

            <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-900 dark:text-emerald-300">
              <strong className="block text-sm font-bold mb-1">
                3. Incident Commander Recommended Actions
              </strong>
              <p className="leading-relaxed">
                Activate pre-evacuation alert for 12 identified high-risk wards. Station earthmoving machinery at vulnerable culverts and keep the Kullu Left Bank highway open as the primary emergency corridor.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
