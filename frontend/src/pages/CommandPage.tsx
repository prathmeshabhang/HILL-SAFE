import React, { useState, useEffect } from 'react';
import { fetchActiveAlerts, fetchActiveIncidents } from '../services/api/endpoints';
import { AlertItem, IncidentRecord } from '../types';
import { useUserStore } from '../store/useUserStore';
import { useHazardStore } from '../store/useHazardStore';
import { DualAuthModal } from '../components/Common/DualAuthModal';
import { StatusBadge } from '../components/Common/StatusBadge';
import {
  LayoutDashboard,
  ShieldAlert,
  Radio,
  Key,
  CheckCircle,
  AlertOctagon,
  Clock,
  Activity,
  Plus,
  Send,
  Zap,
} from 'lucide-react';

export const CommandPage: React.FC = () => {
  const { role, user } = useUserStore();
  const { activeAlerts, setActiveAlerts } = useHazardStore();
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [selectedAlertForAuth, setSelectedAlertForAuth] = useState<AlertItem | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Simulated live LoRa Gateway packets
  const [loraPackets, setLoraPackets] = useState<Array<{ id: string; time: string; station: string; rssi: number; snr: number; payload: string }>>([
    { id: 'PKT-9921', time: '14:42:10', station: 'STN-BEAS-01', rssi: -84, snr: 9.4, payload: 'WL=3.82m RT=0.42 RF=14.6' },
    { id: 'PKT-9922', time: '14:42:15', station: 'STN-BEAS-02', rssi: -91, snr: 8.1, payload: 'WL=2.95m RT=0.28 RF=11.2' },
    { id: 'PKT-9923', time: '14:42:22', station: 'STN-BEAS-03', rssi: -78, snr: 11.2, payload: 'WL=1.64m RT=0.15 RF=8.4' },
    { id: 'PKT-9924', time: '14:42:30', station: 'STN-BEAS-04', rssi: -95, snr: 7.6, payload: 'WL=4.12m RT=0.35 RF=9.0' },
  ]);

  useEffect(() => {
    fetchActiveAlerts().then(setActiveAlerts);
    fetchActiveIncidents().then(setIncidents);

    // Live packet feed tick
    const interval = window.setInterval(() => {
      const stations = ['STN-BEAS-01', 'STN-BEAS-02', 'STN-BEAS-03', 'STN-BEAS-04', 'STN-BEAS-05'];
      const stn = stations[Math.floor(Math.random() * stations.length)];
      const newPkt = {
        id: `PKT-${Math.floor(1000 + Math.random() * 9000)}`,
        time: new Date().toLocaleTimeString(),
        station: stn,
        rssi: -80 - Math.floor(Math.random() * 20),
        snr: parseFloat((6 + Math.random() * 6).toFixed(1)),
        payload: `WL=${(2 + Math.random() * 2).toFixed(2)}m QC=PASS`,
      };
      setLoraPackets((prev) => [newPkt, ...prev.slice(0, 6)]);
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const handleOpenAuth = (alert: AlertItem) => {
    setSelectedAlertForAuth(alert);
    setIsAuthModalOpen(true);
  };

  const handleAuthorizedSuccess = (authorizedAlert: AlertItem) => {
    setActiveAlerts(activeAlerts.map((a) => (a.id === authorizedAlert.id ? authorizedAlert : a)));
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-red-500">
              STATE EMERGENCY OPERATIONS CENTER (SEOC)
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs font-mono font-bold text-slate-500">
              STATION: COMMAND-KULLU-01
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            EOC Incident Commander Operations Desk
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
            Dual-authorization alert broadcast gating, incident escalation, and hardware LoRa stream monitor.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <StatusBadge type="PROTOTYPE_STAGING" />
        </div>
      </div>

      {/* Grid: Active Incidents + Alert Authorization Gateway */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Alert Gateway & Active Incidents */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section 1: Alert Broadcast Gateway (Warning & Evacuation Gating) */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-red-500" />
                  <span>Life-Safety Alert Broadcast Gateway</span>
                </h2>
                <p className="text-xs text-slate-500">
                  Warning & Evacuation Gating: Requires Senior Incident Commander cryptographic dual-authorization passkey to trigger public sirens.
                </p>
              </div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-red-500/10 text-red-500">
                {activeAlerts.length} Active
              </span>
            </div>

            <div className="space-y-3">
              {activeAlerts.map((alt) => {
                const isAuthorized = alt.status === 'AUTHORIZED';
                return (
                  <div
                    key={alt.id}
                    className={`p-4 rounded-2xl border transition space-y-3 ${
                      isAuthorized
                        ? 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700'
                        : 'bg-red-500/5 border-red-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-500">
                            {alt.id}
                          </span>
                          <span className="text-slate-300">•</span>
                          <span className="text-xs font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-600 dark:text-red-400">
                            {alt.severity}
                          </span>
                        </div>
                        <h3 className="font-bold text-slate-900 dark:text-white text-sm mt-1">
                          {alt.headline}
                        </h3>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                          {alt.description}
                        </p>
                      </div>

                      <span
                        className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-full ${
                          isAuthorized
                            ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-500 border border-amber-500/30'
                        }`}
                      >
                        {alt.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-700/60 text-xs">
                      <div className="text-[11px] text-slate-500 font-mono truncate max-w-sm">
                        {isAuthorized
                          ? `Signed by: ${alt.authorized_by || 'Senior Commander'}`
                          : 'Awaiting Commander Dual-Signature'}
                      </div>

                      {!isAuthorized && (
                        <button
                          onClick={() => handleOpenAuth(alt)}
                          className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl shadow transition flex items-center gap-1.5"
                        >
                          <Key className="w-3.5 h-3.5" />
                          <span>Authorize Broadcast</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 2: Active Incident Desk */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Active Valley Emergency Incidents ({incidents.length})
                </h3>
                <p className="text-xs text-slate-500">
                  Ground dispatch & responder reports in Upper Beas jurisdiction.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {incidents.map((inc) => (
                <div
                  key={inc.id}
                  className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-500">{inc.id}</span>
                      <span className="font-bold text-slate-900 dark:text-white text-sm">
                        {inc.title}
                      </span>
                    </div>
                    <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-500">
                      {inc.status}
                    </span>
                  </div>

                  <div className="text-slate-600 dark:text-slate-300">
                    Location: <b>{inc.location_name}</b> | Type: <b>{inc.incident_type}</b>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-200 dark:border-slate-700">
                    <span>Incident Commander: <b>{inc.commander_name || 'Assigned'}</b></span>
                    <span>Evacuation Ordered: <b className={inc.evacuation_ordered ? 'text-red-500' : 'text-emerald-500'}>{inc.evacuation_ordered ? 'YES' : 'NO'}</b></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: LoRa Gateway Stream & Rapid Drill Tools */}
        <div className="space-y-6">
          {/* LoRa Packet Sniffer */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Radio className="w-4 h-4 text-blue-500" />
                <span>LoRa Gateway Telemetry Packet Feed</span>
              </h3>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>

            <div className="space-y-2 font-mono text-[11px]">
              {loraPackets.map((pkt) => (
                <div
                  key={pkt.id}
                  className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1"
                >
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>{pkt.time}</span>
                    <span className="font-bold text-blue-500">{pkt.station}</span>
                    <span>SNR: {pkt.snr}dB</span>
                  </div>
                  <div className="text-slate-800 dark:text-slate-200 truncate">
                    {pkt.payload}
                  </div>
                </div>
              ))}
            </div>

            <div className="text-[10px] text-amber-500 font-mono pt-1">
              Note: Telemetry generated from 5 electronic bench prototype staging units.
            </div>
          </div>

          {/* Commander Emergency Drill Simulator */}
          <div className="bg-gradient-to-br from-red-600/10 via-slate-900/40 to-slate-900/60 border border-red-500/30 rounded-3xl p-6 shadow-sm space-y-3">
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-red-500" />
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                Emergency Siren Drill Broadcast
              </h3>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Test audible CAP civil defense siren overlay across all connected citizen dashboard sessions.
            </p>
            <button
              onClick={() => {
                window.location.href = '/emergency';
              }}
              className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-lg shadow-red-500/30 transition flex items-center justify-center gap-2"
            >
              <Zap className="w-4 h-4" />
              <span>Trigger Test Emergency Screen</span>
            </button>
          </div>
        </div>
      </div>

      {/* Dual Authorization Modal */}
      {selectedAlertForAuth && (
        <DualAuthModal
          alert={selectedAlertForAuth}
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onAuthorized={handleAuthorizedSuccess}
        />
      )}
    </div>
  );
};
