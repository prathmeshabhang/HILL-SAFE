/**
 * frontend/src/pages/DevelopmentZonesPage.tsx
 * =============================================
 * High-Risk Development & Construction Prohibition Zones (Phase 06).
 *
 * Implements authoritative geospatial planning boundaries under:
 * - Himachal Pradesh Town & Country Planning (TCP) Act 1977
 * - NDMA National Guidelines on Management of Landslides & Floods
 * - Central Water Commission (CWC) Floodplain Zoning Regulations
 *
 * Grounded in verified geomorphic sectors of the Upper Beas Basin (Kullu-Manali):
 * - Active Riverbed & 100m Floodway (Prohibited Red Zone)
 * - Old Manali / Manalsu Flash Flood Debris Cone (Restricted Amber Zone)
 * - Bahang Riparian NH-3 Corridor (Prohibited Red Zone)
 * - Akhara Bazar Riverfront Embankment (Prohibited Red Zone)
 * - Bhuntar Parvati-Beas Confluence Basin (Restricted Amber Zone)
 * - Marhi-Kothi Active Landslide Slope (Prohibited Red Zone)
 * - Naggar Castle & Jagatsukh Ancient Terraces (Safe Development Green Zones)
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchDevelopmentZones } from '../services/api/endpoints';
import { DevelopmentZone, DevelopmentZonesResponse } from '../types';
import { useMapStore } from '../store/useMapStore';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Building2,
  HardHat,
  FileText,
  Download,
  Printer,
  Compass,
  MapPin,
  ExternalLink,
  Filter,
  CheckCircle2,
  XCircle,
  TrendingDown,
  Info,
  Maximize2,
} from 'lucide-react';

export const DevelopmentZonesPage: React.FC = () => {
  const navigate = useNavigate();
  const { flyToLocation, setSelectedFeature } = useMapStore();

  const [data, setData] = useState<DevelopmentZonesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedZone, setSelectedZone] = useState<DevelopmentZone | null>(null);

  useEffect(() => {
    fetchDevelopmentZones().then((res) => {
      setData(res);
      if (res?.zones && res.zones.length > 0) {
        setSelectedZone(res.zones[0]);
      }
      setLoading(false);
    });
  }, []);

  const zones: DevelopmentZone[] = data?.zones || [];

  const filteredZones = zones.filter((z) => {
    const matchesCat = filterCategory === 'ALL' || z.category === filterCategory;
    const matchesSearch =
      z.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      z.hazard_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      z.policy.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const handleExportCSV = () => {
    if (!zones.length) return;
    const headers = ['Zone_ID', 'Zone_Name', 'Category', 'Policy', 'Hazard_Type', 'Buffer_Meters', 'Vulnerability', 'Non_Compliant_Structures', 'Action'];
    const rows = zones.map((z) => [
      z.zone_id,
      `"${z.name}"`,
      z.category,
      `"${z.policy}"`,
      `"${z.hazard_type}"`,
      z.buffer_m,
      z.vulnerability_score,
      z.non_compliant_structures_count,
      `"${z.recommended_action}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `FloodyShield_Development_Zoning_Report_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    if (!data) return;
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `FloodyShield_Development_Zoning_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleViewOnMap = (zone: DevelopmentZone) => {
    if (zone.coordinates && zone.coordinates.length > 0) {
      const mid = zone.coordinates[0];
      setSelectedFeature({
        type: 'HAZARD_ZONE',
        id: zone.zone_id,
        name: zone.name,
        riskTier: zone.category === 'SAFE_DEVELOPMENT_ZONE' ? 'SAFE' : 'HIGH',
        dataMode: 'TCP_MUNICIPAL_ZONING',
        coordinates: mid,
        properties: zone as any,
      });
      flyToLocation(mid[0], mid[1], 14.0);
      navigate('/map');
    }
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'PROHIBITED_RED_ZONE':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/10 text-rose-500 border border-rose-500/30 flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5" />
            <span>PROHIBITED RED ZONE</span>
          </span>
        );
      case 'HIGH_RISK_RESTRICTED_ZONE':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/10 text-amber-500 border border-amber-500/30 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>RESTRICTED AMBER ZONE</span>
          </span>
        );
      case 'SAFE_DEVELOPMENT_ZONE':
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>SAFE GREEN HAVEN</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Context */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center gap-1.5">
                <HardHat className="w-3.5 h-3.5" />
                TCP &amp; NDMA Mandated Zoning Regulation
              </span>
              <span className="text-xs text-slate-400 font-mono">Upper Beas River Basin</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              High-Risk Development &amp; Construction Prohibition Zones
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl leading-relaxed">
              Regulatory land-use boundaries enforcing strict construction bans along active Himalayan river channels,
              debris-flow cones, and unstable landslide slopes — balanced with designated safe bedrock terraces.
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={handleExportCSV}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold transition flex items-center gap-1.5 border border-slate-200 dark:border-slate-700"
            >
              <Download className="w-3.5 h-3.5 text-blue-500" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={handleExportJSON}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold transition flex items-center gap-1.5 border border-slate-200 dark:border-slate-700"
            >
              <FileText className="w-3.5 h-3.5 text-blue-500" />
              <span>JSON</span>
            </button>
            <button
              onClick={() => window.print()}
              className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print Audit</span>
            </button>
          </div>
        </div>

        {/* KPI Summary Tiles */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
          <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-slate-200 dark:border-slate-700/60">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Total Monitored Zones</div>
            <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">{data?.zones_count || 8}</div>
            <div className="text-[11px] text-slate-500">Upper Beas Catchment</div>
          </div>

          <div className="bg-rose-50 dark:bg-rose-950/20 p-4 rounded-2xl border border-rose-200 dark:border-rose-900/40">
            <div className="text-[10px] font-mono uppercase tracking-wider text-rose-500 font-bold">Prohibited Red Zones</div>
            <div className="text-2xl font-black text-rose-600 dark:text-rose-400 mt-1">{data?.red_zones_count || 4}</div>
            <div className="text-[11px] text-rose-500/80">Strict zero-construction ban</div>
          </div>

          <div className="bg-amber-50 dark:bg-amber-950/20 p-4 rounded-2xl border border-amber-200 dark:border-amber-900/40">
            <div className="text-[10px] font-mono uppercase tracking-wider text-amber-500 font-bold">Restricted Amber Zones</div>
            <div className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">{data?.restricted_zones_count || 2}</div>
            <div className="text-[11px] text-amber-500/80">Regulated timber permits only</div>
          </div>

          <div className="bg-emerald-50 dark:bg-emerald-950/20 p-4 rounded-2xl border border-emerald-200 dark:border-emerald-900/40">
            <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-500 font-bold">Safe Green Havens</div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{data?.safe_zones_count || 2}</div>
            <div className="text-[11px] text-emerald-500/80">Approved high bedrock terraces</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3 rounded-2xl shadow-sm">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
          {[
            { id: 'ALL', label: 'All Zones (8)' },
            { id: 'PROHIBITED_RED_ZONE', label: 'Red Zones (4)' },
            { id: 'HIGH_RISK_RESTRICTED_ZONE', label: 'Amber Restricted (2)' },
            { id: 'SAFE_DEVELOPMENT_ZONE', label: 'Safe Havens (2)' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterCategory(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition shrink-0 ${
                filterCategory === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="w-full sm:w-72">
          <input
            type="text"
            placeholder="Search by zone name or hazard type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Main Content Grid: Zone Cards + Detailed Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Zone Cards */}
        <div className="lg:col-span-2 space-y-4">
          {filteredZones.map((z) => {
            const isSelected = selectedZone?.zone_id === z.zone_id;
            return (
              <div
                key={z.zone_id}
                onClick={() => setSelectedZone(z)}
                className={`bg-white dark:bg-slate-900 rounded-3xl p-5 border transition-all duration-200 cursor-pointer space-y-3 hover:shadow-md ${
                  isSelected
                    ? 'border-blue-500 ring-2 ring-blue-500/20 shadow-sm'
                    : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
                        {z.zone_id}
                      </span>
                      <span className="text-xs text-slate-300 dark:text-slate-700">•</span>
                      <span className="text-xs text-slate-500 font-medium">
                        Buffer: <b>{z.buffer_m > 0 ? `${z.buffer_m}m Mandate` : 'N/A (Elevated Bench)'}</b>
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      {z.name}
                    </h3>
                  </div>

                  {getCategoryBadge(z.category)}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 dark:bg-slate-800/40 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-400 block">Primary Hazard Threat</span>
                    <span className="font-semibold text-slate-700 dark:text-slate-200">{z.hazard_type}</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-400 block">Enforcement Status</span>
                    <span className="font-semibold text-slate-700 dark:text-slate-200">{z.status.replace(/_/g, ' ')}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  <b className="text-slate-900 dark:text-white">Policy Mandate:</b> {z.policy}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                  <div className="flex items-center gap-3 text-[11px] font-mono">
                    <span className="text-slate-500">
                      Vulnerability: <b className={z.vulnerability_score >= 0.8 ? 'text-rose-500 font-bold' : 'text-emerald-500 font-bold'}>{z.vulnerability_score.toFixed(2)}</b>
                    </span>
                    <span className="text-slate-500">
                      Non-Compliant Structures: <b className="text-slate-900 dark:text-white font-bold">{z.non_compliant_structures_count}</b>
                    </span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewOnMap(z);
                    }}
                    className="px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-600 hover:text-white text-xs font-semibold transition flex items-center gap-1.5"
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>View on Map</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Col: Selected Zone Regulatory Dossier */}
        <div className="space-y-4">
          {selectedZone ? (
            <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5 sticky top-20">
              <div className="space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                    Regulatory Planning Dossier
                  </span>
                  {getCategoryBadge(selectedZone.category)}
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {selectedZone.name}
                </h3>
                <span className="text-xs text-slate-500 font-mono block">
                  Jurisdiction ID: {selectedZone.zone_id}
                </span>
              </div>

              {/* Policy Mandate */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                  Statutory Building Code Mandate
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                  {selectedZone.policy}
                </div>
              </div>

              {/* Recommended Enforcement Action */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                  Recommended Planning Authority Action
                </div>
                <div className="p-3.5 rounded-2xl bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 text-xs text-blue-800 dark:text-blue-300 leading-relaxed">
                  {selectedZone.recommended_action}
                </div>
              </div>

              {/* Metrics Breakdown */}
              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Hazard Category</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedZone.hazard_type}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">River Riparian Buffer</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedZone.buffer_m} meters</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Vulnerability Rating</span>
                  <span className="font-semibold text-rose-500">{selectedZone.vulnerability_score} / 1.00</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Identified Encroachments</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{selectedZone.non_compliant_structures_count} buildings</span>
                </div>
              </div>

              {/* Map Button */}
              <button
                onClick={() => handleViewOnMap(selectedZone)}
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition flex items-center justify-center gap-1.5"
              >
                <Compass className="w-4 h-4" />
                <span>Fly to Zone on Catchment Map</span>
              </button>
            </div>
          ) : (
            <div className="bg-slate-50 dark:bg-slate-800/40 p-8 rounded-3xl border border-dashed border-slate-300 dark:border-slate-700 text-center text-slate-400 text-xs">
              Select a development zone from the list to view statutory zoning regulations and building restrictions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
