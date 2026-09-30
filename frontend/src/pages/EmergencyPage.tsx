import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useEmergencyStore } from '../store/useEmergencyStore';
import { useHazardStore } from '../store/useHazardStore';
import {
  ShieldAlert,
  Volume2,
  VolumeX,
  Navigation,
  ArrowRight,
  AlertTriangle,
  X,
  PhoneCall,
  CheckCircle,
} from 'lucide-react';

export const EmergencyPage: React.FC = () => {
  const navigate = useNavigate();
  const { isEmergencyActive, dismissEmergency, countdownSeconds, setCountdownSeconds } = useEmergencyStore();
  const { activeAlerts } = useHazardStore();
  const [soundPlaying, setSoundPlaying] = useState(false);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const oscRef = useRef<OscillatorNode | null>(null);

  const alert = activeAlerts.find((a) => a.severity === 'WARNING' || a.severity === 'CRITICAL') || {
    id: 'ALT-EMERGENCY-SURGE',
    code: 'FLASH_FLOOD_CRITICAL',
    headline: 'IMMEDIATE EVACUATION ORDER: UPPER BEAS VALLEY CORRIDOR',
    description: 'Catastrophic river surge detected following tributary debris breach. Water levels rising rapidly.',
    severity: 'CRITICAL',
    affected_zones: ['Palchan', 'Old Manali', 'Aleo', 'Kullu Floodplain'],
    recommended_actions: [
      'Move immediately to designated safe havens above 2,150 m elevation.',
      'Do not attempt to cross flooded roadways, underpasses, or bridges.',
      'Assist children, elderly, and mobility-impaired neighbors.',
    ],
  };

  // Synthesize audible siren tone using Web Audio API
  const startSiren = () => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      // Siren modulation
      osc.frequency.linearRampToValueAtTime(880, ctx.currentTime + 1.0);
      osc.frequency.linearRampToValueAtTime(440, ctx.currentTime + 2.0);

      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();

      audioCtxRef.current = ctx;
      oscRef.current = osc;
      setSoundPlaying(true);
    } catch (e) {
      console.warn('Web Audio API not supported or blocked:', e);
    }
  };

  const stopSiren = () => {
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
      oscRef.current = null;
      setSoundPlaying(false);
    }
  };

  useEffect(() => {
    return () => {
      stopSiren();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-[#7F1D1D] text-white flex flex-col justify-between p-6 sm:p-12 overflow-y-auto animate-pulse-danger">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-red-500/40 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white text-red-700 rounded-2xl animate-bounce">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <div className="font-mono text-xs uppercase tracking-widest text-red-200 font-bold">
              LIFE-SAFETY EMERGENCY BROADCAST • CAP PROTOCOL
            </div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              HILL-SAFE FLASH FLOOD ALARM
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={soundPlaying ? stopSiren : startSiren}
            className="px-4 py-2 rounded-xl bg-black/40 hover:bg-black/60 text-white font-mono text-xs font-bold flex items-center gap-2 border border-red-400/30 transition"
          >
            {soundPlaying ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            <span>{soundPlaying ? 'Silence Siren' : 'Test Audible Siren'}</span>
          </button>

          <button
            onClick={() => {
              stopSiren();
              dismissEmergency();
              navigate('/');
            }}
            className="p-2 rounded-xl bg-black/40 hover:bg-black/60 text-white transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Alert Card */}
      <div className="max-w-4xl mx-auto my-8 bg-black/50 backdrop-blur-xl border-2 border-red-400 rounded-3xl p-6 sm:p-10 shadow-2xl space-y-6">
        <div className="flex items-center gap-3 text-red-400 font-mono text-sm font-bold">
          <AlertTriangle className="w-5 h-5 animate-pulse" />
          <span>CODE: {alert.code}</span>
        </div>

        <h2 className="text-2xl sm:text-4xl font-black text-white leading-tight">
          {alert.headline}
        </h2>

        <p className="text-sm sm:text-base text-red-100 leading-relaxed">
          {alert.description}
        </p>

        {/* Affected Sectors */}
        <div className="space-y-2">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-red-300">
            Sectors Under Direct Impact:
          </div>
          <div className="flex flex-wrap gap-2">
            {alert.affected_zones.map((zone) => (
              <span
                key={zone}
                className="px-3 py-1 bg-red-600/80 rounded-xl text-xs font-bold border border-red-400 font-mono"
              >
                {zone}
              </span>
            ))}
          </div>
        </div>

        {/* Action Directives */}
        <div className="bg-red-950/70 border border-red-500/50 p-5 rounded-2xl space-y-3">
          <div className="text-xs font-bold uppercase tracking-wider text-red-200">
            Mandatory Action Checklist:
          </div>
          <ul className="space-y-2 text-xs sm:text-sm text-red-50">
            {alert.recommended_actions.map((act, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span>{act}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Navigation Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-red-500/40">
          <div className="flex items-center gap-2 text-xs font-mono text-red-200">
            <PhoneCall className="w-4 h-4 text-emerald-400" />
            <span>State Disaster Helpline: <b>1070</b> | Kullu Control Room: <b>1077</b></span>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={() => {
                stopSiren();
                dismissEmergency();
                navigate('/evacuation');
              }}
              className="w-full sm:w-auto px-6 py-3.5 bg-white hover:bg-red-50 text-red-900 font-extrabold rounded-2xl shadow-xl flex items-center justify-center gap-2 text-sm transition"
            >
              <Navigation className="w-4 h-4 text-red-700" />
              <span>Navigate to Safe Haven</span>
            </button>
          </div>
        </div>
      </div>

      {/* Footer Banner */}
      <div className="text-center font-mono text-xs text-red-300 border-t border-red-500/40 pt-4">
        HIMACHAL PRADESH STATE DISASTER MANAGEMENT AUTHORITY • HILL-SAFE EARLY WARNING NETWORK
      </div>
    </div>
  );
};
