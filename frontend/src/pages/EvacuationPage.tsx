import React, { useState, useEffect } from 'react';
import { fetchEvacuationRoutes, fetchSafeHavens } from '../services/api/endpoints';
import { EvacuationRoute, SafeHaven } from '../types';
import { MapContainer } from '../components/Map/MapContainer';
import { useMapStore } from '../store/useMapStore';
import {
  Navigation,
  ShieldCheck,
  AlertTriangle,
  MapPin,
  Compass,
  Building,
  Phone,
  Radio,
  Zap,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  XCircle,
  Volume2,
} from 'lucide-react';

export const EvacuationPage: React.FC = () => {
  const [routes, setRoutes] = useState<EvacuationRoute[]>([]);
  const [havens, setHavens] = useState<SafeHaven[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<EvacuationRoute | null>(null);
  const [isNavigating, setIsNavigating] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);

  const { selectedRouteId, setSelectedRouteId } = useMapStore();

  useEffect(() => {
    fetchEvacuationRoutes().then((res) => {
      setRoutes(res);
      if (res.length > 0) {
        // If store already has a selectedRouteId (e.g. from map click on HomePage), match it
        const currentId = useMapStore.getState().selectedRouteId;
        const matchingRoute = currentId ? res.find(r => r.id === currentId || r.name.toLowerCase().includes(currentId.toLowerCase())) : null;
        const active = matchingRoute || res[0];
        setSelectedRoute(active);
        setSelectedRouteId(active.id);
      }
    });
    fetchSafeHavens().then(setHavens);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-500">
              EVACUATION INTELLIGENCE & SAFE PASSAGE ROUTING
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              HIGH GROUND PRIORITIZATION
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Evacuation Guidance & Verified Safe Havens
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
            Real-time elevation-routed escape corridors directing citizens safely above active flood inundation zones.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Routes & Havens List */}
        <div className="space-y-4">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1">
            Dynamic Evacuation Routes
          </div>

          <div className="space-y-2.5">
            {routes.map((rte) => {
              const isSelected = selectedRoute?.id === rte.id;
              const isClear = rte.status === 'CLEAR';
              const isCaution = rte.status === 'CAUTION';

              return (
                <div
                  key={rte.id}
                  onClick={() => {
                    setSelectedRoute(rte);
                    setSelectedRouteId(rte.id);
                    setCurrentStepIndex(0);
                  }}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-500/10 border-blue-500 shadow-md ring-1 ring-blue-500'
                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] font-bold text-slate-400">
                      {rte.id}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        isClear
                          ? 'bg-emerald-500/20 text-emerald-500'
                          : isCaution
                          ? 'bg-amber-500/20 text-amber-500'
                          : 'bg-red-500/20 text-red-500'
                      }`}
                    >
                      {rte.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-slate-900 dark:text-white mt-1">
                    {rte.name}
                  </h3>

                  <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-blue-500" />
                    <span className="truncate">To: {rte.destination_haven_name}</span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px]">
                    <div>
                      <span className="text-slate-400 text-[10px]">Distance</span>
                      <div className="font-bold text-slate-800 dark:text-slate-200">
                        {rte.total_distance_km} km
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Transit</span>
                      <div className="font-bold text-slate-800 dark:text-slate-200">
                        {rte.estimated_transit_minutes} min
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Elev Gain</span>
                      <div className="font-bold text-emerald-500">
                        +{rte.elevation_gain_m} m
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Safe Havens List */}
          <div className="pt-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1 mb-2">
              Verified High Ground Havens ({havens.length})
            </div>

            <div className="space-y-2">
              {havens.map((sh) => (
                <div
                  key={sh.id}
                  className="bg-white dark:bg-slate-900 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 text-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <Building className="w-3.5 h-3.5 text-emerald-500" />
                      {sh.name}
                    </span>
                    <span className="font-mono text-[10px] text-emerald-500 font-bold">
                      {sh.elevation_m}m ELEV
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-500 text-[11px]">
                    <span>Occupancy: <b>{sh.current_occupancy} / {sh.capacity_people}</b></span>
                    <div className="flex items-center gap-2">
                      {sh.has_emergency_power && <span title="Emergency Generator"><Zap className="w-3.5 h-3.5 text-amber-500" /></span>}
                      {sh.has_satellite_comms && <span title="Satellite Phone"><Radio className="w-3.5 h-3.5 text-cyan-500" /></span>}
                      {sh.has_medical_supplies && <span title="First Aid Supplies"><CheckCircle className="w-3.5 h-3.5 text-emerald-500" /></span>}
                    </div>
                  </div>

                  {sh.contact_phone && (
                    <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                      <Phone className="w-3 h-3 text-slate-400" />
                      <span>{sh.contact_phone}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Evacuation Map & Turn Guidance */}
        <div className="lg:col-span-2 space-y-4">
          <div className="h-[440px] rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm relative">
            <MapContainer className="w-full h-full" />
          </div>

          {selectedRoute && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
              {isNavigating ? (
                /* Active Live Step Navigation Cockpit */
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div className="flex items-center gap-2.5">
                      <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                      </span>
                      <span className="text-xs font-mono font-bold tracking-wider text-emerald-600 dark:text-emerald-400 uppercase">
                        LIVE STEP GUIDANCE ACTIVE
                      </span>
                    </div>
                    <button
                      onClick={() => setIsNavigating(false)}
                      className="text-xs font-medium text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 flex items-center gap-1 transition"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Exit Guidance</span>
                    </button>
                  </div>

                  {(() => {
                    const steps = [
                      {
                        title: 'Ridge Departure Point',
                        detail: `Depart immediately from ${selectedRoute.origin}. Follow the green evacuation corridor markers away from river cutting.`,
                        distance: '0.2 km',
                        elevation: '+25 m',
                        status: 'SAFE',
                      },
                      {
                        title: 'Elevation Ascent Corridor',
                        detail: `Ascend along the marked high-ground pathway (+${selectedRoute.elevation_gain_m}m total gradient). Maintain steady uphill movement.`,
                        distance: `${(selectedRoute.total_distance_km * 0.5).toFixed(1)} km`,
                        elevation: `+${Math.round(selectedRoute.elevation_gain_m * 0.65)} m`,
                        status: 'SAFE',
                      },
                      ...(selectedRoute.chokepoints || []).map((cp) => ({
                        title: `Caution at ${cp.name}`,
                        detail: `Proceed with caution (${cp.risk}). Stick strictly to elevated path shoulders and avoid natural gullies.`,
                        distance: `${(selectedRoute.total_distance_km * 0.75).toFixed(1)} km`,
                        elevation: `+${selectedRoute.elevation_gain_m} m`,
                        status: 'CAUTION',
                      })),
                      {
                        title: `Safe Haven Arrival: ${selectedRoute.destination_haven_name}`,
                        detail: `Arrive at verified high-ground shelter. Present at check-in station for emergency registration and medical triage.`,
                        distance: `${selectedRoute.total_distance_km} km`,
                        elevation: `+${selectedRoute.elevation_gain_m} m`,
                        status: 'DESTINATION',
                      },
                    ];

                    const step = steps[currentStepIndex] || steps[0];
                    const isLastStep = currentStepIndex === steps.length - 1;

                    return (
                      <div className="space-y-4">
                        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-400 uppercase">
                              Step {currentStepIndex + 1} of {steps.length}
                            </span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold">
                              {step.status}
                            </span>
                          </div>
                          <h4 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <Navigation className="w-4 h-4 text-emerald-500 animate-pulse" />
                            {step.title}
                          </h4>
                          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                            {step.detail}
                          </p>
                          <div className="flex items-center gap-4 pt-1 text-[11px] text-slate-500 font-mono">
                            <span>Waypoint Dist: <b>{step.distance}</b></span>
                            <span>•</span>
                            <span>Elev: <b className="text-emerald-500">{step.elevation}</b></span>
                          </div>
                        </div>

                        {/* Navigation Step Actions */}
                        <div className="flex items-center justify-between pt-1">
                          <button
                            disabled={currentStepIndex === 0}
                            onClick={() => setCurrentStepIndex((prev) => Math.max(0, prev - 1))}
                            className="px-4 py-2 border border-slate-200 dark:border-slate-700 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1.5 transition"
                          >
                            <ChevronLeft className="w-4 h-4" />
                            <span>Previous Step</span>
                          </button>

                          <div className="flex items-center gap-2">
                            <a
                              href="tel:112"
                              className="px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30 rounded-xl text-xs font-bold flex items-center gap-1.5 transition"
                            >
                              <Phone className="w-3.5 h-3.5" />
                              <span>SOS 112</span>
                            </a>

                            {isLastStep ? (
                              <button
                                onClick={() => {
                                  setIsNavigating(false);
                                  setCurrentStepIndex(0);
                                }}
                                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
                              >
                                <CheckCircle className="w-4 h-4" />
                                <span>Reached Safe Haven</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => setCurrentStepIndex((prev) => Math.min(steps.length - 1, prev + 1))}
                                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-500/20 transition flex items-center gap-1.5"
                              >
                                <span>Next Turn</span>
                                <ChevronRight className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              ) : (
                /* Overview Mode Before Navigation Starts */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-base text-slate-900 dark:text-white">
                        Route Corridor: {selectedRoute.name}
                      </h3>
                      <p className="text-xs text-slate-500">
                        Passes through elevated ridge pathways away from active river cutting.
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-xs font-bold font-mono">
                      CLEAR PATH
                    </span>
                  </div>

                  {selectedRoute.chokepoints && selectedRoute.chokepoints.length > 0 && (
                    <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-1 text-xs">
                      <div className="font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Hazard Chokepoints Noted on Route:</span>
                      </div>
                      {selectedRoute.chokepoints.map((cp, idx) => (
                        <div key={idx} className="text-slate-600 dark:text-slate-300 pl-5">
                          • <b>{cp.name}</b> ({cp.lat}°N, {cp.lng}°E): {cp.risk}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2">
                    <div className="text-xs text-slate-500">
                      Elevation Gain: <b className="text-slate-800 dark:text-slate-200">+{selectedRoute.elevation_gain_m} meters</b> | Est. Speed: <b className="text-slate-800 dark:text-slate-200">4.5 km/h</b>
                    </div>

                    <button
                      onClick={() => {
                        setIsNavigating(true);
                        setCurrentStepIndex(0);
                        setSelectedRouteId(selectedRoute.id);
                      }}
                      className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-500/25 transition flex items-center gap-2"
                    >
                      <Navigation className="w-4 h-4" />
                      <span>Start Step Guidance</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
