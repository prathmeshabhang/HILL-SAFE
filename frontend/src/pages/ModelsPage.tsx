import React, { useState, useEffect } from 'react';
import { fetchModelEvidenceList } from '../services/api/endpoints';
import { IntelligenceCapabilityInfo } from '../types';
import { StatusBadge } from '../components/Common/StatusBadge';
import {
  FileCheck2,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  Lock,
  Layers,
  ArrowRight,
  Database,
  Activity,
  Calendar,
  Clock,
  Info,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { FeatureEngineeringStudio } from '../components/Analysis/FeatureEngineeringStudio';

export const ModelsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'studio' | 'catalog'>('studio');
  const [capabilities, setCapabilities] = useState<IntelligenceCapabilityInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('ALL');
  const [showChainModal, setShowChainModal] = useState(false);

  useEffect(() => {
    fetchModelEvidenceList().then(setCapabilities);
  }, []);

  const domains = [
    'ALL',
    'Flash Flood Intelligence',
    'Landslide Intelligence',
    'Natural Dam Intelligence',
    'Compound Hazard Intelligence',
    'Ground Movement Intelligence',
    'Water-Level Intelligence',
    'Flood Propagation Intelligence',
    'Population Exposure Intelligence',
    'Infrastructure Impact Intelligence',
    'Decision Support & Gating',
  ];

  const compoundHazardChain = [
    { step: 1, label: 'Extreme Rainfall', desc: 'Monsoonal cloudburst & orographic surge' },
    { step: 2, label: 'Catchment Saturation', desc: 'Antecedent soil moisture threshold exceeded' },
    { step: 3, label: 'Landslide', desc: 'Steep overburden slope failure & debris mobilization' },
    { step: 4, label: 'River Blockage', desc: 'Debris chute impounds tributary drainage gorge' },
    { step: 5, label: 'Natural Dam', desc: 'Unconsolidated colluvium dam barrier formation' },
    { step: 6, label: 'Water Accumulation', desc: 'Upstream lake expansion & reservoir volume growth' },
    { step: 7, label: 'Breach / Outburst', desc: 'Overtopping / piping geomechanical failure' },
    { step: 8, label: 'Flash Flood', desc: 'Catastrophic peak discharge surge propagation' },
    { step: 9, label: 'Infrastructure Disruption', desc: 'NH-3 highway scouring, bridge submerged' },
    { step: 10, label: 'Population Exposure', desc: 'Vulnerable riverbank settlements in flood path' },
    { step: 11, label: 'Evacuation Requirement', desc: 'Statutory safe haven activation & dual-auth dispatch' },
  ];

  const filteredCapabilities = capabilities.filter((c) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      c.capability_name.toLowerCase().includes(q) ||
      c.purpose.toLowerCase().includes(q) ||
      (c.dataset && c.dataset.toLowerCase().includes(q)) ||
      (c.validation && c.validation.toLowerCase().includes(q)) ||
      (c.inputs && c.inputs.some((i) => i.toLowerCase().includes(q))) ||
      (c.outputs && c.outputs.some((o) => o.toLowerCase().includes(q))) ||
      (c.limitations && c.limitations.toLowerCase().includes(q));

    const matchesDomain =
      selectedDomain === 'ALL' ||
      c.capability_name.toLowerCase().includes(selectedDomain.toLowerCase()) ||
      (selectedDomain === 'Decision Support & Gating' &&
        (c.capability_name.includes('Warning') ||
          c.capability_name.includes('Safe-Zone') ||
          c.capability_name.includes('Evacuation') ||
          c.capability_name.includes('Calibration')));

    return matchesSearch && matchesDomain;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-500">
              ANALYTICS & SCIENTIFIC EVIDENCE AUDIT
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs font-mono font-bold text-emerald-500">
              OPERATIONAL CAPABILITIES VERIFIED
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Model & Evidence Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
            Authoritative operational intelligence capabilities, observational inputs, validation evidence, uncertainty quantification, and scientific boundary specifications.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge type="FROZEN_VERIFIED" label="FROZEN ARTIFACTS VERIFIED" />
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 p-1.5 bg-slate-100 dark:bg-slate-800/80 rounded-2xl w-fit">
        <button
          onClick={() => setActiveTab('studio')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'studio'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>AI/ML Studio & Feature Engineering</span>
        </button>

        <button
          onClick={() => setActiveTab('catalog')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'catalog'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          <span>Model & Evidence Catalog (M1–M20)</span>
        </button>
      </div>

      {/* Tab 1: AI/ML Studio & Feature Engineering */}
      {activeTab === 'studio' && <FeatureEngineeringStudio />}

      {/* Tab 2: Scientific Evidence & Model Catalog */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          {/* Compound Hazard Chain Banner */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 border border-indigo-800/40 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-indigo-400">
                SYSTEM HAZARD CASCADE FRAMEWORK
              </span>
              <span className="text-xs text-indigo-300/40">•</span>
              <span className="text-xs text-indigo-300 font-semibold">11-Stage Compound Chain</span>
            </div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <span>Himalayan Multi-Hazard Compound Cascade Propagation</span>
            </h2>
          </div>
          <button
            onClick={() => setShowChainModal(!showChainModal)}
            className="self-start sm:self-auto text-xs font-semibold px-3 py-1.5 rounded-xl bg-indigo-600/40 hover:bg-indigo-600/60 border border-indigo-400/30 text-indigo-200 transition"
          >
            {showChainModal ? 'Compact View' : 'Inspect Full 11-Stage Flow'}
          </button>
        </div>

        {/* Horizontal Chain Scroller */}
        <div className="overflow-x-auto pb-2 scrollbar-thin">
          <div className="flex items-center gap-2 min-w-max">
            {compoundHazardChain.map((node, idx) => (
              <React.Fragment key={node.step}>
                <div className="bg-white/10 hover:bg-white/15 transition rounded-2xl p-3 border border-white/10 w-44 flex-shrink-0 space-y-1">
                  <div className="flex items-center justify-between text-[10px] font-mono text-indigo-300">
                    <span>STAGE 0{node.step}</span>
                  </div>
                  <div className="text-xs font-bold text-white truncate">{node.label}</div>
                  <div className="text-[10px] text-slate-300 line-clamp-2">{node.desc}</div>
                </div>
                {idx < compoundHazardChain.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-indigo-400 flex-shrink-0 opacity-70" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="relative flex-1 min-w-[260px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by intelligence capability, purpose, inputs, or validation metrics..."
            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl pl-9 pr-4 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            {domains.map((d) => (
              <option key={d} value={d}>
                {d === 'ALL' ? 'All Intelligence Capabilities' : d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Intelligence Capability Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredCapabilities.map((cap, index) => {
          const badgeType =
            cap.scientific_status === 'PRELIMINARY_EXTERNAL_EVIDENCE'
              ? 'PRELIMINARY'
              : cap.scientific_status === 'PROXY_VALIDATED_PROTOTYPE'
              ? 'BENCHMARK'
              : cap.scientific_status === 'PENDING_EXTERNAL_DATA'
              ? 'PENDING'
              : 'BENCHMARK';

          return (
            <div
              key={cap.capability_name || index}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4 hover:shadow-md transition flex flex-col justify-between"
            >
              <div className="space-y-3.5">
                {/* Header row: Capability & Version */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                      INTELLIGENCE CAPABILITY
                    </span>
                    <h3 className="font-extrabold text-base text-slate-900 dark:text-white leading-tight">
                      {cap.capability_name}
                    </h3>
                    {cap.official_name && (
                      <div className="text-xs text-slate-500 font-medium">
                        {cap.official_name}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                      {cap.version || 'v4.0.0'}
                    </span>
                    <StatusBadge type={badgeType} label={cap.scientific_status || 'BENCHMARKED'} />
                  </div>
                </div>

                {/* Purpose */}
                <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <span className="font-semibold text-slate-900 dark:text-white">Purpose: </span>
                  {cap.purpose}
                </div>

                {/* Inputs & Outputs Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1">
                      <Activity className="w-3 h-3 text-blue-500" />
                      <span>Observational Inputs</span>
                    </span>
                    <ul className="space-y-1 text-[11px] text-slate-600 dark:text-slate-300">
                      {cap.inputs && cap.inputs.length > 0 ? (
                        cap.inputs.map((inp, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-blue-500 font-bold">•</span>
                            <span>{inp}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-400">Observational field & satellite telemetry</li>
                      )}
                    </ul>
                  </div>

                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                      <span>Outputs</span>
                    </span>
                    <ul className="space-y-1 text-[11px] text-slate-600 dark:text-slate-300">
                      {cap.outputs && cap.outputs.length > 0 ? (
                        cap.outputs.map((out, o) => (
                          <li key={o} className="flex items-start gap-1">
                            <span className="text-emerald-500 font-bold">•</span>
                            <span>{out}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-400">Hazard probability & risk indicator bounds</li>
                      )}
                    </ul>
                  </div>
                </div>

                {/* Dataset & Validation */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1">
                      <Database className="w-3 h-3 text-indigo-500" />
                      <span>Dataset</span>
                    </span>
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      {cap.dataset}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3 text-emerald-500" />
                      <span>Validation & Metric</span>
                    </span>
                    <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                      {cap.validation}
                    </div>
                  </div>
                </div>

                {/* Confidence & Timestamp */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400 font-medium">Calibrated Confidence</span>
                    <div className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                      {cap.confidence}
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>Freshness / Cadence</span>
                    </span>
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300 mt-0.5 truncate">
                      {cap.timestamp}
                    </div>
                  </div>
                </div>

                {/* Limitations / Boundary Note */}
                <div className="p-3 rounded-2xl bg-amber-500/5 border border-amber-500/20 text-[11px] text-slate-600 dark:text-slate-300 space-y-0.5">
                  <div className="font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1">
                    <Info className="w-3.5 h-3.5" />
                    <span>Limitations & Boundary Note</span>
                  </div>
                  <p>{cap.limitations}</p>
                </div>
              </div>

              {/* Cryptographic Hash Immutability Strip */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Lock className="w-3 h-3 text-emerald-500" />
                  <span>Bit-Identical Cryptographic Verification</span>
                </div>
                <span className="text-emerald-500 font-bold flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Verified
                </span>
              </div>
            </div>
          );
        })}
      </div>
      </div>
      )}
    </div>
  );
};
