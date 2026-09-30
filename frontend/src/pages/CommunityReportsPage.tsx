import React, { useState, useEffect } from 'react';
import { fetchCommunityReports, submitCommunityReport } from '../services/api/endpoints';
import { CommunityReport } from '../types';
import { useUserStore } from '../store/useUserStore';
import {
  MessageSquare,
  Camera,
  MapPin,
  Send,
  CheckCircle,
  AlertCircle,
  Clock,
  Waves,
} from 'lucide-react';

export const CommunityReportsPage: React.FC = () => {
  const { location } = useUserStore();
  const [reports, setReports] = useState<CommunityReport[]>([]);
  const [hazardType, setHazardType] = useState('Stream Overflow');
  const [waterDepth, setWaterDepth] = useState('30');
  const [description, setDescription] = useState('');
  const [reporterName, setReporterName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    fetchCommunityReports().then(setReports);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitSuccess(false);

    try {
      const newReport = await submitCommunityReport({
        reporter_name: reporterName || 'Local Citizen',
        latitude: location.lat,
        longitude: location.lng,
        location_name: location.name,
        hazard_type: hazardType,
        water_depth_cm: parseInt(waterDepth, 10) || 0,
        description,
      });

      setReports([newReport, ...reports]);
      setDescription('');
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 4000);
    } catch {
      // Handled
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-500">
          CROWDSOURCED VALLEY INTELLIGENCE (CWC / SDMA FEED)
        </span>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
          Community Ground Reports & Hazard Spotting
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
          Citizens and local responders contribute ground-level eyewitness observations to cross-validate satellite and hydrological models.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Submission Form */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Send className="w-5 h-5 text-blue-500" />
            <span>Submit Ground Observation</span>
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Reporter Name (Optional)
              </label>
              <input
                type="text"
                value={reporterName}
                onChange={(e) => setReporterName(e.target.value)}
                placeholder="e.g. Ramesh Sharma"
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Observed Hazard Type
              </label>
              <select
                value={hazardType}
                onChange={(e) => setHazardType(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option>Stream Overflow / Bank Breach</option>
                <option>Debris / Boulder Jam in Nullah</option>
                <option>Road Crack / Landslide Slump</option>
                <option>Culvert or Bailey Bridge Choking</option>
                <option>River Scour Near Building Foundation</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Estimated Water Depth on Road / Ground (cm)
              </label>
              <input
                type="number"
                value={waterDepth}
                onChange={(e) => setWaterDepth(e.target.value)}
                min="0"
                max="500"
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Observation Location
              </label>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs">
                <MapPin className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <span className="truncate text-slate-700 dark:text-slate-300 font-medium">
                  {location.name}
                </span>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Description & Impact Notes
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                required
                placeholder="Describe current water flow velocity, debris size, road traffic status..."
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            {submitSuccess && (
              <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2 font-medium">
                <CheckCircle className="w-4 h-4" />
                <span>Report logged and routed to EOC dispatch queue!</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting || !description}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 text-xs transition disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{isSubmitting ? 'Transmitting Report...' : 'Transmit Ground Report'}</span>
            </button>
          </form>
        </div>

        {/* Right Column: Verified Ground Reports Feed */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500 px-1">
            <span>Recent Community Feed ({reports.length})</span>
            <span>Live Ground Telemetry</span>
          </div>

          <div className="space-y-3">
            {reports.map((rep) => (
              <div
                key={rep.id}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-400">
                        {rep.id}
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                        {rep.hazard_type}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                      <MapPin className="w-3.5 h-3.5 text-blue-500" />
                      <span>{rep.location_name}</span>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      rep.verified
                        ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-500 border border-amber-500/30'
                    }`}
                  >
                    {rep.verified ? 'VERIFIED BY EOC' : 'PENDING FIELD CHECK'}
                  </span>
                </div>

                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                  "{rep.description}"
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-3">
                    {rep.water_depth_cm !== undefined && (
                      <span className="font-mono text-blue-500 font-bold">
                        Depth: {rep.water_depth_cm} cm
                      </span>
                    )}
                    <span>By: {rep.reporter_name}</span>
                  </div>
                  <div className="flex items-center gap-1 font-mono text-[10px]">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(rep.created_at).toLocaleTimeString('en-IN')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
