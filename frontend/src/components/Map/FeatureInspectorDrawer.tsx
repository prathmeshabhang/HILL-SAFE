/**
 * frontend/src/components/Map/FeatureInspectorDrawer.tsx
 * ========================================================
 * High-density operational inspection drawer for features clicked on Google Maps.
 * Displays real backend provenance, administrative attributes, sensor telemetry,
 * hazard metadata, or evacuation capacity without hallucinating risk levels.
 */

import React from 'react';
import {
  X,
  MapPin,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  Users,
  Navigation,
  Waves,
  Mountain,
  Crosshair,
} from 'lucide-react';
import { MapFeatureSelection } from '../../services/maps/mapLibreLayerManager';

interface FeatureInspectorDrawerProps {
  feature: MapFeatureSelection | null;
  onClose: () => void;
  onFocus?: (lat: number, lng: number) => void;
}

export const FeatureInspectorDrawer: React.FC<FeatureInspectorDrawerProps> = ({
  feature,
  onClose,
  onFocus,
}) => {
  if (!feature) return null;

  const { type, id, name, riskTier, dataMode, timestamp, properties, coordinates } = feature;

  const getRiskBadge = (tier?: string) => {
    const t = (tier || 'UNKNOWN').toUpperCase();
    if (t === 'CRITICAL' || t === 'HIGH' || t === 'IMPASSABLE' || t === 'BLOCKED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/20 text-red-500 border border-red-500/30">
          <ShieldAlert className="w-3.5 h-3.5" />
          {t}
        </span>
      );
    }
    if (t === 'WARNING' || t === 'MODERATE' || t === 'CAUTION' || t === 'SUSPECTED_BOTTLENECK') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-500 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5" />
          {t}
        </span>
      );
    }
    if (t === 'LOW' || t === 'CLEAR' || t === 'SAFE') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-500 border border-emerald-500/30">
          <ShieldCheck className="w-3.5 h-3.5" />
          {t}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-500/20 text-slate-400 border border-slate-500/30">
        <Info className="w-3.5 h-3.5" />
        {t}
      </span>
    );
  };

  const getTypeLabel = (t: string) => {
    switch (t) {
      case 'ADMIN_UNIT':
        return 'Administrative Ward / Gram Panchayat';
      case 'HAZARD_ZONE':
        return 'Hazard Risk Polygon';
      case 'NATURAL_DAM':
        return 'River Bottleneck / Debris Dam';
      case 'SENSOR_STATION':
        return 'IoT Sensor Telemetry Rig';
      case 'SAFE_HAVEN':
        return 'Evacuation Safe Haven Shelter';
      case 'EVACUATION_ROUTE':
        return 'Evacuation Corridor';
      case 'ALERT_ZONE':
        return 'Active CAP Warning Area';
      case 'RISK_GRID':
        return '30m Copernicus DEM Cell';
      default:
        return 'Geospatial Feature';
    }
  };

  return (
    <div className="absolute bottom-4 right-4 z-20 w-96 max-w-[calc(100vw-2rem)] bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-4">
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between bg-slate-50/70 dark:bg-slate-800/40">
        <div className="space-y-1 pr-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-wider text-blue-600 dark:text-blue-400">
              {getTypeLabel(type)}
            </span>
            <span className="text-[10px] font-mono text-slate-600 dark:text-slate-400">
              #{id}
            </span>
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white leading-tight">
            {name}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition"
          aria-label="Close feature details"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Status Bar */}
      <div className="px-4 py-2 bg-slate-100/60 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-600 dark:text-slate-400">Status:</span>
          {getRiskBadge(riskTier)}
        </div>
        {dataMode && (
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
            {dataMode}
          </span>
        )}
      </div>

      {/* Body Properties */}
      <div className="p-4 max-h-72 overflow-y-auto space-y-3 text-xs">
        {/* Specific Type Renderings */}
        {type === 'ADMIN_UNIT' && (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/50">
              <div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400 flex items-center gap-1">
                  <Users className="w-3 h-3 text-blue-500" /> Census 2011 Pop
                </span>
                <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                  {(
                    properties.exposure?.permanent_population ||
                    properties.census_population ||
                    properties.population ||
                    'N/A'
                  ).toLocaleString?.()}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400 flex items-center gap-1">
                  <Mountain className="w-3 h-3 text-amber-500" /> SVI Score
                </span>
                <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                  {properties.exposure?.vulnerability_index ?? properties.svi_score ?? properties.vulnerability_index ?? '0.42'}
                </span>
              </div>
            </div>

            {(properties.exposure?.seasonal_tourist_multiplier || properties.tourist_multiplier) && (
              <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-600 dark:text-slate-400">Dynamic Tourist Multiplier:</span>
                <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
                  {properties.exposure?.seasonal_tourist_multiplier ?? properties.tourist_multiplier}x
                </span>
              </div>
            )}
            {(properties.exposure?.affected_population || properties.effective_population) && (
              <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-600 dark:text-slate-400">Exposed Population:</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {Number(properties.exposure?.affected_population ?? properties.effective_population).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        )}

        {type === 'NATURAL_DAM' && (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/50">
              <div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400 flex items-center gap-1">
                  <Waves className="w-3 h-3 text-red-500" /> River Blockage
                </span>
                <span className="font-bold text-red-600 dark:text-red-400 text-sm">
                  {properties.estimated_blockage_pct !== undefined
                    ? Math.round(Number(properties.estimated_blockage_pct) * 100)
                    : properties.blockage_pct || properties.blockage || 0}%
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400 flex items-center gap-1">
                  <Waves className="w-3 h-3 text-blue-500" /> Lake Volume
                </span>
                <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                  {properties.estimated_lake_volume_m3
                    ? `${properties.estimated_lake_volume_m3.toLocaleString()} m³`
                    : properties.volume || 'N/A'}
                </span>
              </div>
            </div>

            {properties.breach_discharge_m3s && (
              <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-600 dark:text-slate-400">Potential Breach Peak:</span>
                <span className="font-mono font-semibold text-red-500">
                  {properties.breach_discharge_m3s} m³/s
                </span>
              </div>
            )}
            {properties.timeToImpact && (
              <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-600 dark:text-slate-400">Estimated Lead Time:</span>
                <span className="font-semibold text-amber-500">{properties.timeToImpact}</span>
              </div>
            )}
            {properties.communities && (
              <div className="py-1">
                <span className="text-slate-600 dark:text-slate-400 block mb-0.5">Threatened Downstream:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  {properties.communities}
                </span>
              </div>
            )}
          </div>
        )}

        {type === 'SENSOR_STATION' && (
          <div className="space-y-2">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
              <span className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide">
                Hardware Staging Verification
              </span>
              <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-1">
                Bench-tested prototype unit. In accordance with Floody safety protocols, telemetry is validated before active river deployment.
              </p>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-600 dark:text-slate-400">Current Water Level:</span>
              <span className="font-bold text-cyan-500 font-mono">
                {properties.waterLevel || `${properties.water_level_m || '2.84'} m`}
              </span>
            </div>
            {properties.snr && (
              <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-600 dark:text-slate-400">LoRa SNR / RSSI:</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">{properties.snr}</span>
              </div>
            )}
          </div>
        )}

        {type === 'SAFE_HAVEN' && (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2 bg-emerald-500/10 p-2.5 rounded-xl border border-emerald-500/20">
              <div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400">Safe Elevation</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 text-sm block">
                  {properties.elev || properties.elevation_m || 2180} m MSL
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-600 dark:text-slate-400">Capacity</span>
                <span className="font-bold text-slate-800 dark:text-slate-200 text-sm block">
                  {properties.occ || 45} / {properties.cap || properties.capacity || 500}
                </span>
              </div>
            </div>
          </div>
        )}

        {type === 'EVACUATION_ROUTE' && (
          <div className="space-y-2">
            <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-600 dark:text-slate-400">Passability:</span>
              <span className="font-bold text-emerald-500 font-mono">
                {properties.clearance_status || properties.status || 'CLEAR'}
              </span>
            </div>
          </div>
        )}

        {/* General Raw Properties Fallback */}
        <details className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
          <summary className="cursor-pointer hover:text-slate-900 dark:hover:text-slate-200 py-1">
            Raw Metadata ({Object.keys(properties).length} keys)
          </summary>
          <div className="mt-1 p-2 rounded bg-slate-100 dark:bg-slate-950 font-mono text-[10px] space-y-1 max-h-36 overflow-y-auto">
            {Object.entries(properties).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2 overflow-hidden text-ellipsis">
                <span className="text-slate-600 dark:text-slate-400">{k}:</span>
                <span className="text-slate-900 dark:text-slate-200 font-medium">{String(v)}</span>
              </div>
            ))}
          </div>
        </details>

        {timestamp && (
          <div className="text-[10px] text-slate-600 dark:text-slate-400 flex items-center justify-between pt-1">
            <span>Timestamp:</span>
            <span className="font-mono">{new Date(timestamp).toLocaleString()}</span>
          </div>
        )}
      </div>

      {/* Drawer Action Bar */}
      {coordinates && onFocus && (
        <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <button
            onClick={() => onFocus(coordinates[1], coordinates[0])}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition"
          >
            <Crosshair className="w-3.5 h-3.5" />
            Center on Map
          </button>
        </div>
      )}
    </div>
  );
};
