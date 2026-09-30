import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchNaturalDams } from '../services/api/endpoints';
import { NaturalDamCandidate } from '../types';
import { StatusBadge } from '../components/Common/StatusBadge';
import {
  Waves,
  UploadCloud,
  AlertOctagon,
  Eye,
  Layers,
  ArrowRight,
  TrendingUp,
  Clock,
  Radio,
  FileCheck,
} from 'lucide-react';

export const NaturalDamPage: React.FC = () => {
  const navigate = useNavigate();
  const [dams, setDams] = useState<NaturalDamCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDam, setSelectedDam] = useState<NaturalDamCandidate | null>(null);

  useEffect(() => {
    fetchNaturalDams().then((res) => {
      setDams(res);
      if (res.length > 0) setSelectedDam(res[0]);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-500">
              NATURAL DAM INTELLIGENCE & BREACH CASING
            </span>
            <span className="text-xs text-slate-400">•</span>
            <StatusBadge type="PRELIMINARY" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Natural Dam & Landslide Dammed Lake Monitoring
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
            Real-time tracking of tributary channel blockages, lake impoundment volume, and breach surge potential.
          </p>
        </div>

        <button
          onClick={() => navigate('/dam-analysis')}
          className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2 self-start sm:self-auto"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload New Dam Imagery</span>
        </button>
      </div>

      {/* Main Grid: Dam Cards List + Selected Deep Dive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Dam List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500 px-1">
            <span>Detected Candidates ({dams.length})</span>
            <span>Sentinel-1 SAR / Sentinel-2</span>
          </div>

          {dams.map((dam) => {
            const isSelected = selectedDam?.id === dam.id;
            const isHigh = dam.breach_risk === 'HIGH' || dam.breach_risk === 'VERY_HIGH';

            return (
              <div
                key={dam.id}
                onClick={() => setSelectedDam(dam)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-blue-500/10 border-blue-500 shadow-md ring-1 ring-blue-500'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-bold text-slate-400">
                    {dam.id}
                  </span>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      isHigh
                        ? 'bg-red-500/20 text-red-500'
                        : dam.breach_risk === 'MODERATE'
                        ? 'bg-amber-500/20 text-amber-500'
                        : 'bg-emerald-500/20 text-emerald-500'
                    }`}
                  >
                    {dam.breach_risk} RISK
                  </span>
                </div>

                <h3 className="font-bold text-sm text-slate-900 dark:text-white mt-1.5">
                  {dam.name}
                </h3>
                <div className="text-xs text-slate-500 mt-0.5">{dam.valley_section}</div>

                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400">Blockage</span>
                    <div className="font-bold text-slate-800 dark:text-slate-200">
                      {dam.estimated_blockage_pct}%
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400">Lake Volume</span>
                    <div className="font-bold text-slate-800 dark:text-slate-200">
                      {dam.lake_volume_m3.toLocaleString()} m³
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Detailed Candidate Inspector */}
        {selectedDam && (
          <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-blue-500">
                    ID: {selectedDam.id}
                  </span>
                  <span className="text-slate-400">•</span>
                  <span className="text-xs text-slate-500 font-mono">
                    Coords: {selectedDam.latitude}°N, {selectedDam.longitude}°E
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
                  {selectedDam.name}
                </h2>
              </div>

              <div className="flex items-center gap-2">
                <StatusBadge type="PRELIMINARY" />
              </div>
            </div>

            {/* Metrics Ribbon */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700/60">
                <div className="text-[10px] uppercase font-bold text-slate-400">Channel Blockage</div>
                <div className="text-xl font-extrabold text-red-500 mt-1">
                  {selectedDam.estimated_blockage_pct}%
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Estimated Debris Height ~14m</div>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700/60">
                <div className="text-[10px] uppercase font-bold text-slate-400">Impounded Lake</div>
                <div className="text-xl font-extrabold text-blue-500 mt-1">
                  {(selectedDam.lake_volume_m3 / 1000).toFixed(0)}k m³
                </div>
                <div className="text-[10px] text-emerald-500 mt-0.5">
                  +{selectedDam.growth_rate_m3_day.toLocaleString()} m³/day
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700/60">
                <div className="text-[10px] uppercase font-bold text-slate-400">Stability Index</div>
                <div className="text-xl font-extrabold text-amber-500 mt-1">
                  {selectedDam.stability_factor}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">&lt; 0.50 Unstable threshold</div>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700/60">
                <div className="text-[10px] uppercase font-bold text-slate-400">Time to Peak Impact</div>
                <div className="text-xl font-extrabold text-slate-800 dark:text-slate-100 mt-1">
                  {selectedDam.estimated_time_to_peak_impact_hours} hrs
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Palchan & Manali valley</div>
              </div>
            </div>

            {/* Satellite Pass & Optical Evidence */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Multi-Sensor Satellite Evidence
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                      <Radio className="w-3.5 h-3.5 text-blue-500" />
                      Sentinel-1 SAR Radar Backscatter
                    </span>
                    <span className="font-mono text-[10px] text-emerald-500 font-bold">COHERENCE LOSS</span>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Significant drop in interferometric coherence observed along Solang Nullah gorge flanks, indicating active slope displacement and gravel dam formation.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-cyan-500" />
                      Sentinel-2 NDWI Water Index
                    </span>
                    <span className="font-mono text-[10px] text-blue-500 font-bold">CONF: 88%</span>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Normalized Difference Water Index confirms standing pool upstream of blockage with growing surface area (48,500 m²).
                  </p>
                </div>
              </div>
            </div>

            {/* Downstream Vulnerable Communities */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Downstream Communities at Immediate Risk
              </h4>
              <div className="flex flex-wrap gap-2">
                {selectedDam.downstream_communities_at_risk.map((comm) => (
                  <span
                    key={comm}
                    className="px-3 py-1 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 text-xs font-semibold"
                  >
                    {comm}
                  </span>
                ))}
              </div>
            </div>

            {/* Scientific Transparency Disclaimer */}
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-400 space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4" />
                <span>Scientific Boundary & Evidence Qualification</span>
              </div>
              <p>
                Natural dam lake volumes are calculated via synthetic DEM filling and remote sensing proxy indices (Natural Dam Intelligence). Outburst flood breach routing is numerically simulated (Compound Hazard & Breach Routing Intelligence). Physical ground verification is conducted in coordination with Geological Survey of India and H.P. SDMA.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
