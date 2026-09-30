/**
 * frontend/src/components/Map/MapLegend.tsx
 * ==========================================
 * Floating Bottom Hazard & Feature Legend for HILL-SAFE.
 * Visually displays the continuous multi-color hazard gradient and explicit
 * teardrop map pointers for Safe Zones, Danger Zones, Evacuation Routes, and Sensors.
 */

import React from 'react';
import { useMapStore } from '../../store/useMapStore';
import { ShieldAlert, MapPin, Waves, Radio, ShieldCheck, Compass } from 'lucide-react';

export const MapLegend: React.FC = () => {
  const { layers } = useMapStore();

  const showHazardGradient = layers.floodRisk || layers.landslideRisk;

  return (
    <div className="bg-slate-950/92 text-white backdrop-blur-md p-3 sm:p-3.5 rounded-2xl border border-slate-700/70 shadow-2xl text-xs space-y-2.5 max-w-[360px] select-none">
      {/* Title */}
      <div className="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400">
        <span className="flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          <span>HILL-SAFE Hazard & Zone Map</span>
        </span>
        <span className="font-mono text-[9px] text-slate-500">M1–M20 SYNTHESIS</span>
      </div>

      {/* Continuous Hazard Color Gradient Bar */}
      {showHazardGradient && (
        <div className="space-y-1">
          <div className="h-2.5 w-full rounded-full bg-gradient-to-r from-emerald-500 via-yellow-400 via-orange-500 to-red-600 shadow-inner" />
          <div className="flex items-center justify-between text-[9px] font-mono text-slate-300 font-bold px-0.5">
            <span className="text-emerald-400 font-bold">SAFE (LOW)</span>
            <span className="text-yellow-400 font-bold">WATCH</span>
            <span className="text-orange-400 font-bold">WARNING</span>
            <span className="text-red-400 font-bold">DANGER</span>
          </div>
        </div>
      )}

      {/* Layer Feature Pointers & Symbols */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-2 pt-1 border-t border-slate-800/80 text-[11px]">
        {layers.criticalZones && (
          <>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-600 border border-white shadow-sm flex items-center justify-center text-[7px] font-black text-white">
                !
              </span>
              <span className="text-red-300 text-[10px] font-medium">Danger Zone Pin</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500 border border-white shadow-sm flex items-center justify-center text-[7px] font-black text-white">
                ✓
              </span>
              <span className="text-emerald-300 text-[10px] font-medium">Safe Zone Pin</span>
            </div>
          </>
        )}

        {layers.safeHavens && (
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-600 border border-white shadow-sm flex items-center justify-center text-[7px] font-black text-white">
              ★
            </span>
            <span className="text-emerald-300 text-[10px] font-medium">Safe Haven Pin</span>
          </div>
        )}

        {layers.naturalDams && (
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-600 border border-white shadow-sm flex items-center justify-center text-[7px] font-black text-white animate-pulse">
              ▲
            </span>
            <span className="text-red-300 text-[10px] font-medium">Bottleneck (Danger)</span>
          </div>
        )}

        {layers.sensorStations && (
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-500 border border-white shadow-sm flex items-center justify-center text-[7px] font-black text-white">
              S
            </span>
            <span className="text-sky-300 text-[10px] font-medium">IoT Sensor Pin</span>
          </div>
        )}

        {layers.evacuationRoutes && (
          <>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-blue-600 border border-white shadow-sm flex items-center justify-center text-[7px] font-black text-white">
                🏃
              </span>
              <span className="text-blue-300 text-[10px] font-medium">Evac Start Pin</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-1 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
              <span className="text-emerald-300 text-[10px] font-medium">Evac Route Path</span>
            </div>
          </>
        )}

        {layers.riverNetwork && (
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-1 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
            <span className="text-cyan-300 text-[10px] font-medium">Beas River Stream</span>
          </div>
        )}
      </div>
    </div>
  );
};
