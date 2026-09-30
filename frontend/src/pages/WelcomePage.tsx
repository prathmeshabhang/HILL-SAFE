import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserStore } from '../store/useUserStore';
import { Shield, MapPin, Compass, ArrowRight, Lock, CheckCircle2 } from 'lucide-react';
import { UserRole } from '../types';

export const WelcomePage: React.FC = () => {
  const navigate = useNavigate();
  const { setLocation, setRole, detectGpsLocation } = useUserStore();

  const [selectedTown, setSelectedTown] = useState('Manali');
  const [selectedRole, setSelectedRole] = useState<UserRole>('CITIZEN');
  const [isDetecting, setIsDetecting] = useState(false);

  const predefinedLocations = [
    { name: 'Manali Town (Mall Road)', lat: 32.2396, lng: 77.1887, alt: 2050 },
    { name: 'Old Manali (Club House)', lat: 32.2530, lng: 77.1810, alt: 2180 },
    { name: 'Palchan Confluence (Solang)', lat: 32.3080, lng: 77.1640, alt: 2310 },
    { name: 'Kothi / Gulaba Foothill', lat: 32.3250, lng: 77.2050, alt: 2500 },
    { name: 'Aleo Bridge Sector', lat: 32.2355, lng: 77.1920, alt: 1980 },
    { name: 'Kullu Central Valley', lat: 31.9560, lng: 77.1080, alt: 1320 },
  ];

  const handleLocationSelect = (loc: typeof predefinedLocations[0]) => {
    setSelectedTown(loc.name);
    setLocation({
      name: loc.name,
      lat: loc.lat,
      lng: loc.lng,
      altitudeMeters: loc.alt,
    });
  };

  const handleGpsDetect = async () => {
    setIsDetecting(true);
    await detectGpsLocation();
    setIsDetecting(false);
  };

  const handleProceed = () => {
    setRole(selectedRole);
    if (selectedRole === 'INCIDENT_COMMANDER' || selectedRole === 'ADMIN') {
      navigate('/command');
    } else {
      navigate('/');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-500 mx-auto flex items-center justify-center text-white shadow-xl shadow-blue-500/25">
            <Shield className="w-9 h-9" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            HILL-SAFE <span className="text-blue-500 font-mono text-xl">v4.0</span>
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
            Upper Beas Catchment • Flash Flood & Natural Dam Early Warning
          </p>
        </div>

        {/* Step 1: Select or Detect Location */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-500" />
              <span>Step 1: Set Your Valley Location</span>
            </label>
            <button
              onClick={handleGpsDetect}
              disabled={isDetecting}
              className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <Compass className="w-3.5 h-3.5" />
              {isDetecting ? 'Detecting GPS...' : 'Detect Device GPS'}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {predefinedLocations.map((loc) => {
              const isSelected = selectedTown === loc.name;
              return (
                <button
                  key={loc.name}
                  onClick={() => handleLocationSelect(loc)}
                  className={`p-3 rounded-xl text-left border text-xs transition flex items-center justify-between ${
                    isSelected
                      ? 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400 font-semibold ring-1 ring-blue-500'
                      : 'border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <div>
                    <div className="font-medium">{loc.name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{loc.alt} m elevation</div>
                  </div>
                  {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-500" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 2: Access Role */}
        <div className="space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-500" />
            <span>Step 2: Choose Access Mode</span>
          </label>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { role: 'CITIZEN' as UserRole, title: 'Citizen / Tourist', desc: 'Personal safety, routes, community reports' },
              { role: 'FIELD_RESPONDER' as UserRole, title: 'Field Responder', desc: 'Incident dispatch & spot reports' },
              { role: 'INCIDENT_COMMANDER' as UserRole, title: 'EOC Commander', desc: 'Dual-auth warning gateway & full GIS' },
            ].map((r) => {
              const isSelected = selectedRole === r.role;
              return (
                <button
                  key={r.role}
                  onClick={() => setSelectedRole(r.role)}
                  className={`p-3.5 rounded-xl text-left border transition ${
                    isSelected
                      ? 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400 ring-1 ring-blue-500'
                      : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <div className="font-bold text-xs text-slate-800 dark:text-slate-200">{r.title}</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">{r.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action button */}
        <button
          onClick={handleProceed}
          className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2 text-sm transition"
        >
          <span>Enter HILL-SAFE Valley Platform</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
