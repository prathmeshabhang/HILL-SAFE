import React from 'react';
import { NavLink } from 'react-router-dom';
import { useUiStore } from '../../store/useUiStore';
import { useUserStore } from '../../store/useUserStore';
import {
  ShieldAlert,
  Map,
  Waves,
  Navigation,
  BookOpen,
  LayoutDashboard,
  Radio,
  FileCheck2,
  X,
  Pin,
  PinOff,
  Home,
  CloudRain,
  Mountain,
  ChevronLeft,
  HardHat,
  KeyRound,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const {
    sidebarOpen,
    setSidebarOpen,
    sidebarPinned,
    toggleSidebarPinned,
  } = useUiStore();
  const { role } = useUserStore();

  const mainNav = [
    { to: '/', label: 'Command Dashboard', icon: LayoutDashboard, badge: 'Live' },
    { to: '/ward-view', label: 'Village / Ward View', icon: Home, badge: 'Hyper-local' },
    { to: '/map', label: 'Catchment Risk Map', icon: Map, badge: 'MapLibre 3D' },
    { to: '/development-zones', label: 'Development Zones', icon: HardHat, badge: 'TCP Bans' },
    { to: '/forecasts', label: 'Forecasts & Prediction', icon: CloudRain, badge: '6h Rolling' },
    { to: '/sensors', label: 'Sensor & Data Sources', icon: Radio, badge: 'Multi-Source' },
    { to: '/natural-dams', label: 'Natural Dam AI Model', icon: Mountain, badge: 'Optical/SAR' },
    { to: '/dam-analysis', label: 'Dam Breach Simulation', icon: Waves, badge: 'Froehlich' },
    { to: '/command', label: 'Alerts & Advisories', icon: ShieldAlert, badge: 'CAP v1.2' },
    { to: '/evacuation', label: 'Evacuation Corridors', icon: Navigation, badge: '5 Routes' },
    { to: '/login', label: 'Login & Personas', icon: KeyRound, badge: 'Open/EOC' },
    { to: '/models', label: 'AI Models Studio', icon: FileCheck2, badge: 'M1–M20' },
    { to: '/preparedness', label: 'Settings & SOP Guide', icon: BookOpen },
  ];

  // The sidebar is visible if pinned or opened
  const isVisible = sidebarPinned || sidebarOpen;

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden transition-opacity duration-300"
        />
      )}

      {/* Main Sidebar Aside */}
      <aside
        className={`fixed top-16 bottom-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] will-change-transform flex flex-col justify-between overflow-y-auto ${
          isVisible ? 'translate-x-0 shadow-2xl' : '-translate-x-full shadow-none pointer-events-none'
        }`}
      >
        <div className="p-4 space-y-4">
          {/* Top Pin / Hide bar */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Navigation
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-semibold">
                {sidebarPinned ? 'Docked' : 'Overlay'}
              </span>
            </div>

            <div className="flex items-center gap-1">
              {/* Pin Toggle Button */}
              <button
                onClick={toggleSidebarPinned}
                title={
                  sidebarPinned
                    ? 'Unpin sidebar (hide menu to maximize map canvas)'
                    : 'Pin sidebar (keep permanently docked)'
                }
                className={`p-1.5 rounded-lg text-xs transition-colors flex items-center gap-1 cursor-pointer ${
                  sidebarPinned
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                    : 'text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {sidebarPinned ? (
                  <Pin className="w-3.5 h-3.5 text-blue-500 rotate-45" />
                ) : (
                  <PinOff className="w-3.5 h-3.5" />
                )}
              </button>

              {/* Close / Hide Button (visible to all screen sizes) */}
              <button
                onClick={() => setSidebarOpen(false)}
                title="Hide Menu Bar"
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Section: Main Command Navigation */}
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2 px-2">
              Command Modules
            </div>
            <div className="space-y-1">
              {mainNav.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => {
                      // Automatically hide menu upon selection when in unpinned mode
                      if (!sidebarPinned) setSidebarOpen(false);
                    }}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 ${
                        isActive
                          ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400 font-semibold shadow-sm'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 shrink-0">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer info in sidebar with explicit Hide Menu button */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 text-[11px] space-y-2.5 text-slate-500 dark:text-slate-400">
          <button
            onClick={() => setSidebarOpen(false)}
            className="w-full py-1.5 px-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Hide Menu Bar</span>
          </button>

          <div className="flex items-center justify-between pt-1">
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              Upper Beas Basin
            </span>
            <span className="text-[10px] text-emerald-500 font-bold font-mono">● LIVE</span>
          </div>
          <div className="font-mono text-[10px]">
            31.40°N–32.45°N | 76.80°E–77.45°E
          </div>
        </div>
      </aside>
    </>
  );
};
