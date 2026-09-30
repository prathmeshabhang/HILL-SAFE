import React, { useState, useEffect } from 'react';
import {
  fetchAnalysisScenarios,
  runFeatureEngineering,
  runModelsThroughFeatures,
  fetchSourcesHealth,
} from '../../services/api/endpoints';
import {
  CuratedScenario,
  FeatureEngineeringResult,
  ModelExecutionResult,
  MultiSourceHealthSummary,
} from '../../types';
import {
  Zap,
  Cpu,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Radio,
  Sliders,
  TrendingUp,
  ShieldAlert,
  Droplets,
  Mountain,
  Compass,
} from 'lucide-react';

export const FeatureEngineeringStudio: React.FC = () => {
  const [sourceMode, setSourceMode] = useState<'LIVE' | 'SCENARIO' | 'CUSTOM'>('SCENARIO');
  const [scenarios, setScenarios] = useState<CuratedScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('JULY_2023_BEAS_CLOUDBURST');
  const [sourcesHealth, setSourcesHealth] = useState<MultiSourceHealthSummary | null>(null);

  // Custom inputs state
  const [rainfall1h, setRainfall1h] = useState<number>(65.0);
  const [antecedentRain, setAntecedentRain] = useState<number>(185.0);
  const [soilMoisture, setSoilMoisture] = useState<number>(88.5);
  const [slopeDeg, setSlopeDeg] = useState<number>(38.2);
  const [suscClass, setSuscClass] = useState<number>(4);
  const [riverStage, setRiverStage] = useState<number>(4.85);
  const [riverDischarge, setRiverDischarge] = useState<number>(2850.0);

  // Results state
  const [featureResult, setFeatureResult] = useState<FeatureEngineeringResult | null>(null);
  const [modelResult, setModelResult] = useState<ModelExecutionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load scenarios and source health on mount
  useEffect(() => {
    fetchAnalysisScenarios().then((data) => {
      setScenarios(data);
      if (data.length > 0) {
        setSelectedScenarioId(data[0].scenario_id);
      }
    });
    fetchSourcesHealth().then(setSourcesHealth);
  }, []);

  // When scenario changes, update slider fields for visibility
  useEffect(() => {
    const sc = scenarios.find((s) => s.scenario_id === selectedScenarioId);
    if (sc) {
      setRainfall1h(sc.rainfall_intensity_mmh);
      setAntecedentRain(sc.antecedent_rain_3d_mm);
      setSoilMoisture(sc.soil_moisture_pct);
      setSlopeDeg(sc.slope_deg);
      setSuscClass(sc.susceptibility_class);
      setRiverStage(sc.river_water_level_m);
      setRiverDischarge(sc.river_discharge_m3s);
    }
  }, [selectedScenarioId, scenarios]);

  // Execute Feature Engineering & Model Run
  const handleExecutePipeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: Record<string, any> = {
        source_mode: sourceMode,
      };

      if (sourceMode === 'SCENARIO') {
        payload.scenario_id = selectedScenarioId;
      } else if (sourceMode === 'CUSTOM') {
        payload.rainfall_intensity_mmh = rainfall1h;
        payload.antecedent_rain_3d_mm = antecedentRain;
        payload.soil_moisture_pct = soilMoisture;
        payload.slope_deg = slopeDeg;
        payload.susceptibility_class = suscClass;
        payload.river_water_level_m = riverStage;
        payload.river_discharge_m3s = riverDischarge;
      }

      // Run Feature Engineering
      const feRes = await runFeatureEngineering(payload);
      setFeatureResult(feRes);

      // Run Models through features
      const mRes = await runModelsThroughFeatures({
        ...payload,
        run_flood_physics: true,
        run_landslide_ai: true,
        run_cascade_analysis: true,
        run_hyperlocal_mapping: true,
      });
      setModelResult(mRes);
    } catch (err: any) {
      setError(err?.message || 'Pipeline execution failed');
    } finally {
      setLoading(false);
    }
  };

  // Run on mount once scenarios are loaded
  useEffect(() => {
    if (scenarios.length > 0) {
      handleExecutePipeline();
    }
  }, [scenarios]);

  return (
    <div className="space-y-6">
      {/* Top Banner: Multi-Source Ingestion & Feature Engineering Header */}
      <div className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 border border-blue-800/40 rounded-3xl p-6 text-white shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                MULTI-SOURCE INGESTION & AI ORCHESTRATOR
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> {sourcesHealth ? `${sourcesHealth.healthy_sources_count} OF ${sourcesHealth.total_sources_monitored} FEEDS ACTIVE` : '6 FEEDS CONNECTED'}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight">
              AI/ML Feature Engineering & Physics Inference Studio
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
              Ingests heterogeneous observations from satellite (INSAT-3DS, SMAP, Sentinel), telemetry gauges (IMD AWS, CWC, IoT), and Copernicus 30m DEM terrain rasters. Normalizes raw telemetry, engineers USDA NRCS & geomechanical feature vectors, and executes decoupled gradient boosting and physical hydraulic solvers.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExecutePipeline}
              disabled={loading}
              className="px-5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-blue-500/25 transition disabled:opacity-50"
            >
              <Zap className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Running AI Models...' : 'Run ML/AI Models'}</span>
            </button>
          </div>
        </div>

        {/* Live Agency Feed Connectivity Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-2 border-t border-slate-800/80">
          {[
            { id: 'INSAT_3DS', name: 'INSAT-3DS Satellite', metric: 'HEM Rain Rate', type: 'SATELLITE' },
            { id: 'SMAP', name: 'NASA/ISRO SMAP', metric: 'L-Band Soil Moisture', type: 'SATELLITE' },
            { id: 'IMD_AWS', name: 'IMD Automatic AWS', metric: '1h Rain Intensity', type: 'AGENCY' },
            { id: 'CWC_RIVER', name: 'CWC Thalout Gauge', metric: 'River Water Stage', type: 'AGENCY' },
            { id: 'UPPER_BEAS_IOT', name: 'Upper Beas IoT Rigs', metric: 'Ultrasonic / Tilt', type: 'IOT' },
            { id: 'SENTINEL_COPERNICUS', name: 'Sentinel-1/2 SAR', metric: 'SAR Coherence Mask', type: 'SATELLITE' },
          ].map((feed) => (
            <div
              key={feed.id}
              className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-[10px]">
                <span className="font-mono font-bold text-slate-300">{feed.id}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              </div>
              <div className="text-xs font-bold text-white mt-1 truncate">{feed.name}</div>
              <div className="text-[10px] text-blue-400 font-mono mt-0.5">{feed.metric}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Input Mode Selector Bar */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Observation Source & Simulation Controller
            </span>
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-2xl">
            {(['SCENARIO', 'LIVE', 'CUSTOM'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setSourceMode(mode)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                  sourceMode === mode
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {mode === 'SCENARIO' ? 'Storm Scenarios' : mode === 'LIVE' ? 'Live Basin Snapshot' : 'Custom Sensor Overrides'}
              </button>
            ))}
          </div>
        </div>

        {/* Mode 1: Curated Scenarios Selector */}
        {sourceMode === 'SCENARIO' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
            {scenarios.map((sc) => (
              <div
                key={sc.scenario_id}
                onClick={() => setSelectedScenarioId(sc.scenario_id)}
                className={`p-3.5 rounded-2xl border cursor-pointer transition flex flex-col justify-between ${
                  selectedScenarioId === sc.scenario_id
                    ? 'bg-blue-500/10 border-blue-500 dark:bg-blue-500/15 text-blue-600 dark:text-blue-400 ring-2 ring-blue-500/20'
                    : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    {sc.scenario_id.replace(/_/g, ' ')}
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white mt-0.5">
                    {sc.title}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                    {sc.description}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-mono">
                  <span>Rain: <b>{sc.rainfall_intensity_mmh} mm/h</b></span>
                  <span>SM: <b>{sc.soil_moisture_pct}%</b></span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Mode 2: Live Agency Snapshot Notice */}
        {sourceMode === 'LIVE' && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Radio className="w-5 h-5 text-emerald-500 flex-shrink-0 animate-pulse" />
              <div>
                <span className="font-bold">Live Multi-Source Feeds Active:</span> Ingesting real-time observations from CWC Thalout, IMD Manali AWS, INSAT-3DS infrared brightness, and SMAP surface moisture.
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-mono text-[10px] font-bold">
              FAIL-SOFT ENGAGED
            </span>
          </div>
        )}

        {/* Mode 3: Custom Sliders */}
        {sourceMode === 'CUSTOM' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>1h Rainfall Intensity:</span>
                <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{rainfall1h} mm/h</span>
              </div>
              <input
                type="range"
                min="0"
                max="120"
                step="1"
                value={rainfall1h}
                onChange={(e) => setRainfall1h(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>3-Day Antecedent Rain:</span>
                <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{antecedentRain} mm</span>
              </div>
              <input
                type="range"
                min="0"
                max="300"
                step="5"
                value={antecedentRain}
                onChange={(e) => setAntecedentRain(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Soil Moisture Saturation:</span>
                <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{soilMoisture}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="1"
                value={soilMoisture}
                onChange={(e) => setSoilMoisture(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Slope Gradient (DEM):</span>
                <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{slopeDeg}°</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                step="0.5"
                value={slopeDeg}
                onChange={(e) => setSlopeDeg(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Feature Engineering Pipeline Inspection Panel */}
      {featureResult && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-500" />
              <h3 className="font-extrabold text-base text-slate-900 dark:text-white">
                Engineered Feature Matrix (Extracted from Observations)
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Pipeline Stage: Ready for Inference
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Landslide AI Feature Vector */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Mountain className="w-3.5 h-3.5 text-amber-500" />
                  Landslide AI Vector (M7)
                </span>
                <span className="text-[10px] font-mono text-blue-500 font-bold">5-D DENSE</span>
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Susceptibility Class:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.landslide_ai_vector.susceptibility_class} (Tier 1-4)</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Slope Gradient:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.landslide_ai_vector.slope_deg}°</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">1h Rain Intensity:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.landslide_ai_vector.rainfall_1h} mm/h</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">3d Antecedent Rain:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.landslide_ai_vector.antecedent_rain_3d} mm</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Soil Saturation:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.landslide_ai_vector.soil_moisture_pct}%</span>
                </div>
              </div>
            </div>

            {/* SCS-CN Hydrologic Runoff Vector */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Droplets className="w-3.5 h-3.5 text-blue-500" />
                  SCS-CN Runoff Parameters
                </span>
                <span className="text-[10px] font-mono text-emerald-500 font-bold">USDA NRCS</span>
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Moisture Condition:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">{featureResult.engineered_features.scs_cn_hydrologic_vector.amc_condition}</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Effective Curve Number:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">CN = {featureResult.engineered_features.scs_cn_hydrologic_vector.effective_curve_number}</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Max Retention (S):</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.scs_cn_hydrologic_vector.potential_retention_s_mm} mm</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Initial Abstraction (Ia):</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.scs_cn_hydrologic_vector.initial_abstraction_ia_mm} mm</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Direct Runoff Depth (Q):</span>
                  <span className="font-bold text-blue-600 dark:text-blue-400">{featureResult.engineered_features.scs_cn_hydrologic_vector.direct_runoff_depth_mm} mm</span>
                </div>
              </div>
            </div>

            {/* Topographic 30m DEM Terrain Vector */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-purple-500" />
                  Topographic DEM Metrics
                </span>
                <span className="text-[10px] font-mono text-purple-500 font-bold">COP30 30m</span>
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Catchment Area:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.topographic_dem_vector.catchment_area_km2} km²</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Elevation Relief:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.topographic_dem_vector.elevation_relief_m} m</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Mean Slope:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.topographic_dem_vector.mean_slope_deg}°</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Channel Gradient:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{featureResult.engineered_features.topographic_dem_vector.channel_gradient_m_m} m/m</span>
                </div>
                <div className="flex justify-between p-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-400">Grid Resolution:</span>
                  <span className="font-bold text-purple-600 dark:text-purple-400">30 m Nominal</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Execution Results Dashboard */}
      {modelResult && modelResult.model_outputs && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-500" />
              <h3 className="font-extrabold text-lg text-slate-900 dark:text-white">
                AI/ML & Physics Model Execution Outputs
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-500 font-bold bg-emerald-500/10 px-3 py-1 rounded-xl border border-emerald-500/20">
              INFERENCE COMPLETED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1: Landslide AI Trigger Model */}
            {modelResult.model_outputs.landslide_ai && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-amber-500/10 text-amber-500">
                      <Mountain className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">MODEL M7</span>
                      <h4 className="font-extrabold text-base text-slate-900 dark:text-white">
                        Landslide AI Trigger Prediction
                      </h4>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-xl text-xs font-extrabold font-mono ${
                      modelResult.model_outputs.landslide_ai.payload.hazard_tier === 'CRITICAL'
                        ? 'bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30'
                        : modelResult.model_outputs.landslide_ai.payload.hazard_tier === 'HIGH'
                        ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                        : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    {modelResult.model_outputs.landslide_ai.payload.hazard_tier}
                  </span>
                </div>

                {/* Probability Gauge Bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-600 dark:text-slate-400">Trigger Activation Probability:</span>
                    <span className="font-mono text-sm font-black text-slate-900 dark:text-white">
                      {(modelResult.model_outputs.landslide_ai.payload.trigger_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        modelResult.model_outputs.landslide_ai.payload.trigger_probability > 0.65
                          ? 'bg-red-600'
                          : modelResult.model_outputs.landslide_ai.payload.trigger_probability > 0.35
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{
                        width: `${Math.min(100, modelResult.model_outputs.landslide_ai.payload.trigger_probability * 100)}%`,
                      }}
                    ></div>
                  </div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400">Decision Status</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">
                      {modelResult.model_outputs.landslide_ai.payload.trigger_predicted ? 'SLOPE MOBILIZATION EXPECTED' : 'QUIESCENT BOUND'}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400">Inference Engine</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">
                      {modelResult.model_outputs.landslide_ai.payload.model_type}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Card 2: Flood Physics & DEM Routing Engine */}
            {modelResult.model_outputs.flood_physics && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-blue-500/10 text-blue-500">
                      <Droplets className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">PHYSICS & 30m DEM</span>
                      <h4 className="font-extrabold text-base text-slate-900 dark:text-white">
                        SCS-CN Direct Runoff & Routing
                      </h4>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-xl text-xs font-extrabold font-mono bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
                    {modelResult.model_outputs.flood_physics.payload.derived_hazard_tier}
                  </span>
                </div>

                {/* Runoff and Peak Discharge Grid */}
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-2xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/40">
                    <span className="text-[10px] text-blue-500 font-bold uppercase">Direct Runoff Depth</span>
                    <div className="text-xl font-black text-blue-600 dark:text-blue-400 mt-0.5">
                      {modelResult.model_outputs.flood_physics.payload.scs_cn.direct_runoff_depth_mm} mm
                    </div>
                    <span className="text-[10px] text-slate-400">Coeff: {modelResult.model_outputs.flood_physics.payload.scs_cn.runoff_coefficient}</span>
                  </div>

                  <div className="p-3 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40">
                    <span className="text-[10px] text-indigo-500 font-bold uppercase">Peak Basin Discharge</span>
                    <div className="text-xl font-black text-indigo-600 dark:text-indigo-400 mt-0.5">
                      {modelResult.model_outputs.flood_physics.payload.routing.peak_discharge_m3s.toLocaleString()} m³/s
                    </div>
                    <span className="text-[10px] text-slate-400">Volume: {modelResult.model_outputs.flood_physics.payload.routing.runoff_volume_mcm} MCM</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                  <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400">Time to Peak</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">
                      {modelResult.model_outputs.flood_physics.payload.routing.time_to_peak_hours} hrs
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400">Flow Velocity</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">
                      {modelResult.model_outputs.flood_physics.payload.routing.flow_velocity_ms} m/s
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-[10px] text-slate-400">Concentration</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">
                      {modelResult.model_outputs.flood_physics.payload.routing.time_of_concentration_hours} hrs
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Card 3: Cascade & River Bottlenecks */}
            {modelResult.model_outputs.cascade_intelligence && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-red-500/10 text-red-500">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">CASCADE INTELLIGENCE</span>
                      <h4 className="font-extrabold text-base text-slate-900 dark:text-white">
                        River Bottleneck & Debris Dam Outburst
                      </h4>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-xl text-xs font-extrabold font-mono bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30">
                    {modelResult.model_outputs.cascade_intelligence.detected_bottlenecks_count} CANDIDATES
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  {modelResult.model_outputs.cascade_intelligence.bottlenecks.map((b: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-bold text-slate-900 dark:text-white">
                          {b.reach_name || `Bottleneck Reach #${idx + 1}`}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Channel Width: {b.channel_width_m}m • Obstruction: {b.obstruction_state}
                        </div>
                      </div>
                      <div className="text-right font-mono">
                        <span className="text-xs font-bold text-red-500">
                          {Math.round(b.bottleneck_probability * 100)}%
                        </span>
                        <div className="text-[10px] text-slate-400">Obstruction Prob</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Card 4: Hyperlocal Administrative Unit Impact */}
            {modelResult.model_outputs.hyperlocal_impact && (
              <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-purple-500/10 text-purple-500">
                      <ShieldAlert className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">ADMINISTRATIVE EXPOSURE</span>
                      <h4 className="font-extrabold text-base text-slate-900 dark:text-white">
                        Ward & Gram Panchayat Impact
                      </h4>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-xl text-xs font-extrabold font-mono bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30">
                    {modelResult.model_outputs.hyperlocal_impact.high_risk_units_count} CRITICAL UNITS
                  </span>
                </div>

                <div className="p-3 rounded-2xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-100 dark:border-purple-900/40 flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-purple-500 font-bold uppercase">Estimated Exposed Population</span>
                    <div className="text-xl font-black text-purple-600 dark:text-purple-400 mt-0.5">
                      {modelResult.model_outputs.hyperlocal_impact.total_exposed_population.toLocaleString()} Residents
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400">Census 2011 + Tourists</span>
                </div>

                <div className="space-y-2 text-xs">
                  {modelResult.model_outputs.hyperlocal_impact.administrative_units.slice(0, 3).map((u: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-bold text-slate-900 dark:text-white">
                          {u.unit_name} ({u.unit_type})
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Pop: {u.total_dynamic_population?.toLocaleString()} • SVI: {u.social_vulnerability_index}
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400">
                        {u.risk_tier}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
