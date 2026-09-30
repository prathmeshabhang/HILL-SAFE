/**
 * frontend/src/components/Map/LayerControl.tsx
 * =============================================
 * Floating Geospatial Layer & Basemap Control Panel for HILL-SAFE.
 * Inspired directly by professional disaster-management command interfaces:
 * - Collapsible translucent glassmorphism panel positioned inside the map canvas
 * - Multi-hazard layer toggles (Safe & Danger Wards, Hazard Surface, River Network, Sensors, Routes)
 * - Continuous Hazard Surface Opacity Slider
 * - Base Map Selector (Satellite, Hybrid, Terrain, Roadmap)
 */

import React, { useState } from 'react';
import { useMapStore, MapLayersState, BaseMapType } from '../../store/useMapStore';
import {
  Layers,
  Check,
  ChevronDown,
  ChevronUp,
  Sliders,
  Globe,
  Mountain,
  Map as MapIcon,
  Sun,
  Eye,
  EyeOff,
} from 'lucide-react';

interface LayerControlProps {
  onBaseMapChange?: (basemap: BaseMapType) => void;
  onOpacityChange?: (opacity: number) => void;
}

export const LayerControl: React.FC<LayerControlProps> = ({
  onBaseMapChange,
  onOpacityChange,
}) => {
  const {
    layers,
    toggleLayer,
    activeBasemap,
    setActiveBasemap,
    hazardOpacity,
    setHazardOpacity,
  } = useMapStore();

  const [isCollapsed, setIsCollapsed] = useState(true);

  const layerItems: Array<{
    key: keyof MapLayersState;
    label: string;
    badgeColor?: string;
    description?: string;
  }> = [
    { key: 'criticalZones', label: 'Safe & Danger Wards', badgeColor: 'bg-red-400' },
    { key: 'floodRisk', label: 'Hazard Risk Surface', badgeColor: 'bg-amber-500' },
    { key: 'riverNetwork', label: 'Beas River Network', badgeColor: 'bg-cyan-400' },
    { key: 'landslideRisk', label: 'Landslide Susceptibility', badgeColor: 'bg-orange-500' },
    { key: 'sensorStations', label: 'IoT Sensor Stations', badgeColor: 'bg-blue-500' },
    { key: 'safeHavens', label: 'Safe Haven Shelters', badgeColor: 'bg-emerald-500' },
    { key: 'evacuationRoutes', label: 'Evacuation Corridors', badgeColor: 'bg-emerald-400' },
    { key: 'naturalDams', label: 'River Bottlenecks (Danger)', badgeColor: 'bg-red-500' },
  ];

  const baseMaps: Array<{ id: BaseMapType; label: string; icon: React.ReactNode }> = [
    { id: 'hybrid', label: 'Hybrid', icon: <Globe className="w-3.5 h-3.5" /> },
    { id: 'satellite', label: 'Satellite', icon: <Globe className="w-3.5 h-3.5" /> },
    { id: 'terrain', label: 'Terrain', icon: <Mountain className="w-3.5 h-3.5" /> },
    { id: 'roadmap', label: 'Roadmap', icon: <MapIcon className="w-3.5 h-3.5" /> },
  ];

  const handleBaseMapSelect = (id: BaseMapType) => {
    setActiveBasemap(id);
    onBaseMapChange?.(id);
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setHazardOpacity(val);
    onOpacityChange?.(val);
  };

  if (isCollapsed) {
    return (
      <button
        onClick={() => setIsCollapsed(false)}
        className="bg-slate-900/90 hover:bg-slate-800 text-white backdrop-blur-md p-2.5 rounded-xl border border-slate-700/80 shadow-2xl flex items-center gap-2 text-xs font-semibold transition group"
        title="Open Layer Control"
      >
        <Layers className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
        <span className="hidden sm:inline">Layers &amp; Basemap</span>
      </button>
    );
  }

  return (
    <div className="bg-slate-950/90 text-white backdrop-blur-md p-3.5 rounded-2xl border border-slate-700/70 shadow-2xl text-xs w-[250px] sm:w-[260px] space-y-3 select-none transition-all">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2 font-bold tracking-wider uppercase text-[10px] text-slate-300">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>Layers &amp; Basemap</span>
        </div>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          title="Minimize Panel"
        >
          <ChevronUp className="w-4 h-4" />
        </button>
      </div>

      {/* Section 1: Base Map Selector */}
      <div className="space-y-1.5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Base Map</span>
          <span className="text-[9px] font-mono text-blue-400">{activeBasemap.toUpperCase()}</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {baseMaps.map((b) => {
            const isSelected = activeBasemap === b.id;
            return (
              <button
                key={b.id}
                onClick={() => handleBaseMapSelect(b.id)}
                className={`flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-lg text-[11px] font-medium transition ${
                  isSelected
                    ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-500/20'
                    : 'bg-slate-900/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800'
                }`}
              >
                {b.icon}
                <span>{b.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Section 2: Hazard Opacity Slider */}
      <div className="space-y-1 pt-1 border-t border-slate-800/80">
        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
          <span className="flex items-center gap-1">
            <Sliders className="w-3 h-3 text-amber-400" />
            <span>Hazard Opacity</span>
          </span>
          <span className="font-mono text-amber-400">{Math.round(hazardOpacity * 100)}%</span>
        </div>
        <input
          type="range"
          min="0.10"
          max="1.0"
          step="0.05"
          value={hazardOpacity}
          onChange={handleSliderChange}
          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
      </div>

      {/* Section 3: Multi-Hazard Operational Layers */}
      <div className="space-y-1 pt-1 border-t border-slate-800/80">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
          Operational Layers
        </div>
        <div className="space-y-1 max-h-[220px] overflow-y-auto pr-1 scrollbar-thin">
          {layerItems.map((item) => {
            const active = layers[item.key];
            return (
              <button
                key={item.key}
                onClick={() => toggleLayer(item.key)}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  active
                    ? 'bg-blue-500/15 text-blue-300 font-medium border border-blue-500/30'
                    : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2 text-[11px]">
                  <div
                    className={`w-3.5 h-3.5 rounded flex items-center justify-center border transition ${
                      active
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'border-slate-600 bg-slate-900'
                    }`}
                  >
                    {active && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                  </div>
                  <span>{item.label}</span>
                </div>
                {item.badgeColor && (
                  <span className={`w-2 h-2 rounded-full ${item.badgeColor} opacity-80`} />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
