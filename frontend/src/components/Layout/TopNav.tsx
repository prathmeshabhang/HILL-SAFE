/**
 * frontend/src/components/Layout/TopNav.tsx
 * ===========================================
 * Command Center Top Header for FLOODY SHIELD (Phase 06).
 * Features:
 * - Brand & Logo with operational system descriptor
 * - Global search bar with autocomplete for Upper Beas Wards, Panchayats & Sensor Rigs
 * - Active CAP Alert Indicator badge
 * - Monitored Basin Geographic Descriptor
 * - Real-time synchronized clock (IST & UTC)
 * - Incident role switcher & Dark/Light mode toggle
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUiStore } from '../../store/useUiStore';
import { useUserStore } from '../../store/useUserStore';
import { useHazardStore } from '../../store/useHazardStore';
import { useMapStore } from '../../store/useMapStore';
import { StatusBadge } from '../Common/StatusBadge';
import {
  Shield,
  Sun,
  Moon,
  MapPin,
  Menu,
  Volume2,
  VolumeX,
  Search,
  ShieldAlert,
  Clock,
  UserCheck,
  X,
  ChevronDown,
} from 'lucide-react';
import { UserRole } from '../../types';

// Pre-indexed geographic locations in Upper Beas Basin
const SEARCH_TARGETS = [
  { id: 'WARD_MANALI_01', name: 'Manali Ward 1 (Mall Road / Model Town)', type: 'Ward', lat: 32.242, lng: 77.189 },
  { id: 'WARD_MANALI_02', name: 'Manali Ward 2 (Old Manali / Manalsu)', type: 'Ward', lat: 32.253, lng: 77.181 },
  { id: 'WARD_KULLU_01', name: 'Kullu Ward 1 (Akhara Bazar / Sarvari)', type: 'Ward', lat: 31.958, lng: 77.109 },
  { id: 'WARD_BHUNTAR_01', name: 'Bhuntar Ward 1 (Airport Reach)', type: 'Ward', lat: 31.878, lng: 77.152 },
  { id: 'GP_VASHISHT', name: 'Vashisht Gram Panchayat', type: 'Panchayat', lat: 32.261, lng: 77.199 },
  { id: 'GP_BAHANG', name: 'Bahang Gram Panchayat', type: 'Panchayat', lat: 32.278, lng: 77.185 },
  { id: 'GP_PATLIKUHAL', name: 'Patlikuhal Gram Panchayat', type: 'Panchayat', lat: 32.128, lng: 77.145 },
  { id: 'GP_NAGGAR', name: 'Naggar Heritage Gram Panchayat', type: 'Panchayat', lat: 32.145, lng: 77.168 },
  { id: 'GP_SAINJ', name: 'Sainj Valley Gram Panchayat', type: 'Panchayat', lat: 31.785, lng: 77.312 },
  { id: 'GP_LARJI', name: 'Larji Confluence Gram Panchayat', type: 'Panchayat', lat: 31.715, lng: 77.218 },
  { id: 'GP_AUT', name: 'Aut Gorge Gram Panchayat', type: 'Panchayat', lat: 31.745, lng: 77.205 },
  { id: 'GP_BANJAR', name: 'Banjar Gateway Gram Panchayat', type: 'Panchayat', lat: 31.638, lng: 77.342 },
  { id: 'STN-BEAS-01', name: 'Solang Gorge Ultrasonic Bridge', type: 'Station', lat: 32.3142, lng: 77.1595 },
  { id: 'STN-BEAS-02', name: 'Palchan Confluence Radar Station', type: 'Station', lat: 32.3080, lng: 77.1640 },
  { id: 'STN-BEAS-04', name: 'Aleo Bridge Main Stem Rig', type: 'Station', lat: 32.2355, lng: 77.1920 },
];

export const TopNav: React.FC = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme, toggleSidebar } = useUiStore();
  const { role, setRole, location, setLocation } = useUserStore();
  const { backendOnline, activeAlerts } = useHazardStore();
  const { flyToLocation } = useMapStore();

  const [soundOn, setSoundOn] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const searchRef = useRef<HTMLDivElement>(null);

  // Live ticking clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-IN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Close search suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredTargets = SEARCH_TARGETS.filter((t) =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectTarget = (target: (typeof SEARCH_TARGETS)[0]) => {
    setLocation({
      lat: target.lat,
      lng: target.lng,
      name: target.name,
    });
    flyToLocation(target.lng, target.lat, 14.5);
    setSearchQuery('');
    setIsSearchOpen(false);
    navigate('/');
  };

  const roles: Array<{ id: UserRole; label: string }> = [
    { id: 'CITIZEN', label: 'Citizen View' },
    { id: 'FIELD_RESPONDER', label: 'Field Responder' },
    { id: 'INCIDENT_COMMANDER', label: 'Incident Commander' },
    { id: 'ADMIN', label: 'System Admin' },
  ];

  return (
    <header className="sticky top-0 z-30 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
        {/* Left: Brand & Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
            aria-label="Toggle Navigation Sidebar"
            title="Toggle Menu Bar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div
            onClick={() => navigate('/')}
            className="flex items-center gap-2.5 cursor-pointer group select-none"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-blue-500/25 group-hover:scale-105 transition-transform">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-base sm:text-lg tracking-tight bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                  HILL-SAFE
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold border border-blue-500/20">
                  COMMAND
                </span>
              </div>
              <p className="text-[10px] tracking-wide text-slate-500 font-medium hidden sm:block">
                Himalayan Flash Flood & Landslide Decision Support
              </p>
            </div>
          </div>
        </div>

        {/* Center: Global Location / Feature Search Bar */}
        <div ref={searchRef} className="relative hidden md:block flex-1 max-w-md mx-2">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              placeholder="Search Ward, Gram Panchayat, Station (e.g. Manali, Vashisht)..."
              value={searchQuery}
              onFocus={() => setIsSearchOpen(true)}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setIsSearchOpen(true);
              }}
              className="w-full pl-9 pr-8 py-1.5 bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-xl text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-slate-900 transition"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Autocomplete Dropdown */}
          {isSearchOpen && (
            <div className="absolute left-0 right-0 top-full mt-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl overflow-hidden z-50 max-h-72 overflow-y-auto">
              <div className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                <span>Hyperlocal Administrative Units</span>
                <span>{filteredTargets.length} Found</span>
              </div>
              {filteredTargets.length === 0 ? (
                <div className="p-3 text-center text-xs text-slate-400">
                  No location found matching "{searchQuery}"
                </div>
              ) : (
                filteredTargets.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleSelectTarget(item)}
                    className="w-full px-3 py-2 text-left hover:bg-slate-50 dark:hover:bg-slate-800/70 border-b border-slate-100 dark:border-slate-800/50 last:border-none flex items-center justify-between gap-2 transition"
                  >
                    <div className="flex items-center gap-2 overflow-hidden">
                      <MapPin className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                      <span className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate">
                        {item.name}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 shrink-0">
                      {item.type}
                    </span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right: Operational Status, Live Clock & User Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Active Warnings Indicator */}
          <div
            onClick={() => navigate('/command')}
            className="cursor-pointer hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/20 text-xs transition"
            title="Active Common Alerting Protocol Warnings"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
            </span>
            <span className="font-bold text-[11px]">
              {activeAlerts.length > 0 ? `${activeAlerts.length} Warnings Active` : 'Warnings: 2 Active'}
            </span>
          </div>

          {/* Monitored Region Badge */}
          <div className="hidden lg:flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs font-mono text-slate-600 dark:text-slate-300">
            <span className="text-blue-500 font-bold">REGION:</span>
            <span>Upper Beas Basin (HP)</span>
          </div>

          {/* Real-time Ticking Clock */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-800/80 text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{currentTime || '10:50:00'} IST</span>
          </div>

          {/* Development Zones Shortcut */}
          <button
            onClick={() => navigate('/development-zones')}
            className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold transition border border-slate-200 dark:border-slate-700"
            title="High-Risk Development & Building Ban Zones"
          >
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            <span className="hidden md:inline">Zoning</span>
          </button>

          {/* Login & Role Access Center Button */}
          <button
            onClick={() => navigate('/login')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition border ${
              role === 'CITIZEN'
                ? 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700'
                : 'bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
            }`}
            title="Login or Switch Operational Persona"
          >
            <UserCheck className="w-3.5 h-3.5 text-blue-500" />
            <span className="hidden md:inline">
              {role === 'CITIZEN' ? 'Citizen (Open)' : role.replace('_', ' ')}
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold border border-blue-500/20">
              {role === 'CITIZEN' ? 'Login' : 'Switch'}
            </span>
          </button>

          {/* Siren sound toggle */}
          <button
            onClick={() => setSoundOn(!soundOn)}
            title={soundOn ? 'Siren Audio On' : 'Siren Audio Muted'}
            className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            {soundOn ? (
              <Volume2 className="w-4 h-4 text-blue-500" />
            ) : (
              <VolumeX className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-slate-600" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
