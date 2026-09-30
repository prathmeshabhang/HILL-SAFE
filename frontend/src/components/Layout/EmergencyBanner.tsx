import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useHazardStore } from '../../store/useHazardStore';
import { ShieldAlert, ArrowRight, AlertTriangle } from 'lucide-react';

export const EmergencyBanner: React.FC = () => {
  const navigate = useNavigate();
  const { activeAlerts } = useHazardStore();

  const criticalAlert = activeAlerts.find(
    (a) => a.severity === 'CRITICAL' || a.severity === 'WARNING'
  );

  if (!criticalAlert) return null;

  return (
    <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 text-white shadow-lg animate-pulse-danger relative z-40 border-b border-red-400/30">
      <div className="max-w-7xl mx-auto px-4 py-2.5 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-white/20 rounded-lg flex-shrink-0">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-black/30 tracking-wider font-bold">
                {criticalAlert.severity} ALERT
              </span>
              <span className="font-semibold text-sm sm:text-base">
                {criticalAlert.headline}
              </span>
            </div>
            <p className="text-xs text-red-100 hidden md:block">
              Immediate life-safety advisory: Move to designated high ground above 2,150 m.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/emergency')}
            className="flex items-center gap-1.5 px-3 py-1 bg-white text-red-700 hover:bg-red-50 text-xs sm:text-sm font-bold rounded-lg shadow transition"
          >
            <span>View Full Alarm</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
