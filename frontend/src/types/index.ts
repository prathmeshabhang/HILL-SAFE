/**
 * HILL-SAFE v4.0 - Core TypeScript Interface Definitions
 * Strictly aligned with docs/FRONTEND_API_INTEGRATION_CONTRACT.md
 */

export type AlertSeverity = 'INFO' | 'WATCH' | 'ADVISORY' | 'WARNING' | 'CRITICAL';
export type AlertStatus = 'DRAFT' | 'PENDING_AUTHORIZATION' | 'AUTHORIZED' | 'ISSUED' | 'CANCELLED' | 'EXPIRED';
export type UserRole = 'CITIZEN' | 'FIELD_RESPONDER' | 'INCIDENT_COMMANDER' | 'ADMIN';
export type HardwareDeploymentStatus = 'PROTOTYPE_STAGING' | 'BENCH_TEST' | 'FIELD_PILOT' | 'OPERATIONAL_RIVER';

export interface UserLocation {
  lat: number;
  lng: number;
  name: string;
  accuracyMeters?: number;
  altitudeMeters?: number;
}

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  agency?: string;
  phone?: string;
  isCommander: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  database: boolean;
  services: {
    ml_inference: boolean;
    gis_engine: boolean;
    lora_gateway: boolean;
    websocket: boolean;
  };
  disclaimer?: string;
}

export interface RiskSummary {
  basin: string;
  timestamp: string;
  aggregate_risk_score: number; // 0.0 to 1.0
  severity_level: AlertSeverity;
  active_warnings_count: number;
  monitored_stations_count: number;
  natural_dam_threat_level: 'NONE' | 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  landslide_susceptibility: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';
  rainfall_trend_mm_hr: number;
  primary_threat_description: string;
}

export interface StationTelemetry {
  station_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  battery_pct: number;
  solar_mv: number;
  signal_snr_db: number;
  water_level_m: number;
  water_level_rate_m_hr: number;
  water_temperature_c: number;
  rainfall_1h_mm: number;
  rainfall_24h_mm: number;
  soil_moisture_pct: number;
  turbidity_ntu: number;
  last_heard_seconds_ago: number;
  deployment_status: HardwareDeploymentStatus;
  quality_flags: {
    valid_range: boolean;
    stuck_value: boolean;
    spike_detected: boolean;
  };
}

export interface NaturalDamCandidate {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  valley_section: string;
  estimated_blockage_pct: number;
  lake_volume_m3: number;
  growth_rate_m3_day: number;
  stability_factor: number; // 0 to 1
  breach_risk: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  downstream_communities_at_risk: string[];
  estimated_time_to_peak_impact_hours: number;
  last_satellite_pass: string;
  optical_confidence: number;
  sar_coherence_drop: boolean;
}

export interface AlertItem {
  id: string;
  code: string;
  headline: string;
  description: string;
  severity: AlertSeverity;
  status: AlertStatus;
  affected_zones: string[];
  recommended_actions: string[];
  created_at: string;
  expires_at: string;
  authorized_by?: string;
  authorized_at?: string;
  source_model?: string;
  requires_dual_authorization: boolean;
}

export interface EvacuationRoute {
  id: string;
  name: string;
  origin: string;
  destination_haven_id: string;
  destination_haven_name: string;
  total_distance_km: number;
  estimated_transit_minutes: number;
  status: 'CLEAR' | 'CAUTION' | 'IMPASSABLE' | 'FLOODED';
  chokepoints: Array<{
    name: string;
    lat: number;
    lng: number;
    risk: string;
  }>;
  elevation_gain_m: number;
  geojson: any;
}

export interface SafeHaven {
  id: string;
  name: string;
  type: 'SCHOOL' | 'TEMPLE' | 'GOVT_BUILDING' | 'STADIUM' | 'HIGH_GROUND';
  latitude: number;
  longitude: number;
  elevation_m: number;
  capacity_people: number;
  current_occupancy: number;
  has_medical_supplies: boolean;
  has_emergency_power: boolean;
  has_satellite_comms: boolean;
  contact_phone?: string;
}

export interface ModelEvidenceInfo {
  capability_name: string;
  official_name?: string;
  version: string;
  purpose: string;
  inputs: string[];
  outputs: string[];
  dataset: string;
  evidence: string;
  validation: string;
  confidence: string;
  timestamp: string;
  limitations: string;
  
  // Backward compatibility fields
  model_id?: string;
  model_name?: string;
  subsystem?: string;
  scientific_status?: 'EMPIRICALLY_BENCHMARKED' | 'PRELIMINARY_EXTERNAL_EVIDENCE' | 'PROXY_VALIDATED_PROTOTYPE' | 'PENDING_EXTERNAL_DATA';
  validation_type?: 'SIMULATION_DEMONSTRATED' | 'SYNTHETIC_BENCHMARK' | 'HISTORICAL_REPLAY' | 'FIELD_TEST';
  frozen_hash?: string;
  hash_verified?: boolean;
  key_metric_label?: string;
  key_metric_value?: string;
  training_events_n?: number | string;
  disclaimer?: string;
}

export type IntelligenceCapabilityInfo = ModelEvidenceInfo;

export interface IncidentRecord {
  id: string;
  title: string;
  status: 'REPORTED' | 'CONFIRMED' | 'ESCALATED' | 'CONTAINED' | 'RESOLVED';
  severity: AlertSeverity;
  incident_type: 'FLASH_FLOOD' | 'LANDSLIDE' | 'DAM_BREACH' | 'RIVER_BANK_EROSION' | 'ROAD_BLOCK';
  location_name: string;
  latitude: number;
  longitude: number;
  commander_name?: string;
  casualties_reported: number;
  evacuation_ordered: boolean;
  created_at: string;
  updated_at: string;
}

export interface CommunityReport {
  id: string;
  reporter_name?: string;
  contact?: string;
  latitude: number;
  longitude: number;
  location_name: string;
  hazard_type: string;
  water_depth_cm?: number;
  description: string;
  photo_url?: string;
  verified: boolean;
  created_at: string;
}

export interface ReplayEvent {
  timestamp: string;
  hour_offset: number;
  title: string;
  rainfall_rate_mm_h: number;
  beas_river_discharge_cusecs: number;
  critical_events: string[];
  active_flood_polygon_count: number;
}

// ==========================================
// Phase 04 Multi-Source & Feature Engineering Types
// ==========================================
export interface SourceHealthEntry {
  source_id: string;
  source_type: string;
  status: 'ONLINE' | 'DEGRADED' | 'UNAVAILABLE' | 'NOT_CONFIGURED';
  is_configured: boolean;
  last_poll_at: string | null;
  last_success_at: string | null;
  last_observation_timestamp: string | null;
  freshness_age_seconds: number | null;
  freshness_threshold_seconds: number;
  success_count: number;
  error_count: number;
  consecutive_failures: number;
  last_error_message: string | null;
}

export interface MultiSourceHealthSummary {
  basin_id: string;
  evaluated_at: string;
  total_sources_monitored: number;
  configured_sources_count: number;
  healthy_sources_count: number;
  overall_connectivity_state: 'OPTIMAL' | 'DEGRADED' | 'CRITICAL' | 'UNAVAILABLE';
  sources: Record<string, SourceHealthEntry>;
  fail_soft_engaged: boolean;
  recommendations: string[];
}

export interface MultiSourceSnapshot {
  timestamp: string;
  fusion_state: string;
  confidence_score: number;
  active_sources_count: number;
  active_sources: string[];
  missing_or_stale_sources: string[];
  physical_indicators: {
    max_rainfall_rate_mmh: number | null;
    max_water_level_m: number | null;
    avg_soil_moisture_cm3cm3: number | null;
    max_slope_displacement_mm: number | null;
  };
  source_health: Record<string, SourceHealthEntry>;
  fail_soft_engaged: boolean;
  data_authenticity_notice: string;
}

export interface CuratedScenario {
  scenario_id: string;
  title: string;
  description: string;
  rainfall_intensity_mmh: number;
  antecedent_rain_3d_mm: number;
  soil_moisture_pct: number;
  slope_deg: number;
  susceptibility_class: number;
  river_water_level_m: number;
  river_discharge_m3s: number;
  location_name: string;
  dam_height_m: number;
  impounded_volume_m3: number;
}

export interface FeatureEngineeringResult {
  status: string;
  timestamp: string;
  source_mode: 'LIVE' | 'SCENARIO' | 'CUSTOM';
  scenario_id?: string;
  location_name: string;
  raw_inputs: Record<string, any>;
  engineered_features: {
    landslide_ai_vector: {
      susceptibility_class: number;
      slope_deg: number;
      rainfall_1h: number;
      antecedent_rain_3d: number;
      soil_moisture_pct: number;
    };
    scs_cn_hydrologic_vector: {
      amc_condition: string;
      effective_curve_number: number;
      potential_retention_s_mm: number;
      initial_abstraction_ia_mm: number;
      direct_runoff_depth_mm: number;
      runoff_coefficient: number;
    };
    topographic_dem_vector: {
      mean_slope_deg: number;
      elevation_relief_m: number;
      channel_gradient_m_m: number;
      catchment_area_km2: number;
      dem_resolution_m: number;
      dem_source: string;
    };
  };
  feature_metadata: Record<string, any>;
  data_sources_connected: Array<{
    source_id: string;
    measurement: string;
    value: string;
  }>;
}

export interface ModelExecutionResult {
  status: string;
  timestamp: string;
  source_mode: 'LIVE' | 'SCENARIO' | 'CUSTOM';
  scenario_id?: string;
  location_name: string;
  raw_inputs: Record<string, any>;
  feature_engineering: {
    landslide_features: Record<string, any>;
    feature_metadata: Record<string, any>;
  };
  model_outputs: {
    flood_physics?: {
      status: string;
      component_name: string;
      confidence_score: number;
      data_mode: string;
      payload: {
        rainfall_depth_evaluated_mm: number;
        scs_cn: {
          amc_condition: string;
          effective_curve_number: number;
          potential_retention_s_mm: number;
          initial_abstraction_ia_mm: number;
          direct_runoff_depth_mm: number;
          runoff_coefficient: number;
        };
        routing: {
          catchment_area_km2: number;
          flow_velocity_ms: number;
          time_of_concentration_hours: number;
          time_to_peak_hours: number;
          peak_discharge_m3s: number;
          runoff_volume_mcm: number;
          flow_accumulation_peak_cells: number;
        };
        terrain_metrics: {
          min_elev_m: number;
          max_elev_m: number;
          mean_elev_m: number;
          relief_m: number;
          mean_slope_deg: number;
          channel_gradient_m_m: number;
        };
        derived_hazard_tier: string;
      };
      duration_ms: number;
    };
    landslide_ai?: {
      status: string;
      component_name: string;
      confidence_score: number;
      data_mode: string;
      payload: {
        trigger_probability: number;
        trigger_predicted: boolean;
        hazard_tier: string;
        evaluated_features: Record<string, number>;
        feature_metadata: Record<string, any>;
        geotech_alert: boolean;
        model_type: string;
      };
      duration_ms: number;
    };
    cascade_intelligence?: {
      detected_bottlenecks_count: number;
      bottlenecks: any[];
      cascade_assessment: any;
    };
    hyperlocal_impact?: {
      total_administrative_units: number;
      high_risk_units_count: number;
      total_exposed_population: number;
      administrative_units: any[];
    };
  };
}

export interface HyperlocalExposure {
  permanent_population: number;
  seasonal_tourist_multiplier: number;
  tourist_population: number;
  total_estimated_population: number;
  affected_population: number;
  vulnerability_index: number;
  exposed_infrastructure_count: number;
  exposed_infrastructure: Array<{
    asset_id: string;
    name: string;
    category: string;
    criticality_tier: string;
  }>;
}

export interface HyperlocalHazardState {
  max_hazard_score: number;
  mean_hazard_score: number;
  dominant_hazard: string;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  exposed_area_pct: number;
}

export interface HyperlocalAdminUnit {
  admin_id: string;
  name: string;
  unit_type: 'WARD' | 'GRAM_PANCHAYAT';
  area_km2: number;
  centroid: [number, number];
  is_safe_terrace?: boolean;
  safe_haven_status?: string;
  current_hazard: HyperlocalHazardState;
  cascade_state: string;
  exposure: HyperlocalExposure;
  confidence: number;
  provenance: string;
  is_operational: boolean;
  timestamp: string;
}

export interface DevelopmentZone {
  zone_id: string;
  name: string;
  category: 'PROHIBITED_RED_ZONE' | 'HIGH_RISK_RESTRICTED_ZONE' | 'SAFE_DEVELOPMENT_ZONE';
  category_label: string;
  policy: string;
  hazard_type: string;
  buffer_m: number;
  status: string;
  vulnerability_score: number;
  non_compliant_structures_count: number;
  recommended_action: string;
  coordinates: Array<[number, number]>;
}

export interface DevelopmentZonesResponse {
  status: string;
  jurisdiction: string;
  zones_count: number;
  red_zones_count: number;
  restricted_zones_count: number;
  safe_zones_count: number;
  regulatory_framework: string;
  zones: DevelopmentZone[];
}


