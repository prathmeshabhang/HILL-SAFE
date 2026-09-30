-- =============================================================================
-- schema.sql — Production PostGIS Spatial Schema for Natural River Dam Engine
-- =============================================================================
-- FLOODY SHIELD — Early Warning System for Hilly Regions (SIH PS-26192)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Natural Dam Candidates Table
CREATE TABLE IF NOT EXISTS natural_dam_candidates (
    id VARCHAR(64) PRIMARY KEY,
    river_name VARCHAR(128) NOT NULL,
    geometry GEOMETRY(Point, 4326) NOT NULL,
    elevation_m NUMERIC(7, 2),
    probability NUMERIC(4, 3) NOT NULL CHECK (probability >= 0.0 AND probability <= 1.0),
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    candidate_tier VARCHAR(32) NOT NULL, -- 'HIGH_CONFIDENCE_CANDIDATE', 'LIKELY', 'POSSIBLE', 'NO_EVIDENCE'
    status VARCHAR(64) NOT NULL DEFAULT 'AUTHORITY_VALIDATION_REQUIRED',
    data_quality VARCHAR(32) DEFAULT 'GOOD',
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_version VARCHAR(32) NOT NULL DEFAULT 'v2.1.0'
);

CREATE INDEX IF NOT EXISTS idx_natural_dam_geom ON natural_dam_candidates USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_natural_dam_status ON natural_dam_candidates (status);
CREATE INDEX IF NOT EXISTS idx_natural_dam_tier ON natural_dam_candidates (candidate_tier);

-- 2. Multi-Temporal Remote Sensing Observations
CREATE TABLE IF NOT EXISTS natural_dam_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dam_id VARCHAR(64) REFERENCES natural_dam_candidates(id) ON DELETE CASCADE,
    observation_time TIMESTAMPTZ NOT NULL,
    sensor_source VARCHAR(64) NOT NULL, -- 'Sentinel-1 SAR', 'Sentinel-2 MSI', 'Copernicus GLO-30'
    channel_width_m NUMERIC(6, 2),
    upstream_water_area_m2 NUMERIC(12, 2),
    sar_backscatter_vv_db NUMERIC(5, 2),
    optical_ndvi_loss NUMERIC(4, 3),
    antecedent_rainfall_mm NUMERIC(6, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dam_obs_dam_id ON natural_dam_observations (dam_id);

-- 3. Upstream Impoundments (Polygons of Flooded Reservoirs)
CREATE TABLE IF NOT EXISTS natural_dam_impoundments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dam_id VARCHAR(64) REFERENCES natural_dam_candidates(id) ON DELETE CASCADE,
    geometry GEOMETRY(Polygon, 4326) NOT NULL,
    surface_area_m2 NUMERIC(12, 2) NOT NULL,
    estimated_dam_height_m NUMERIC(6, 2),
    estimated_volume_m3 NUMERIC(14, 2),
    volume_estimation_method VARCHAR(64) DEFAULT 'V_SHAPED_VALLEY_PYRAMID',
    expansion_rate_m2_hr NUMERIC(10, 2),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_impoundment_geom ON natural_dam_impoundments USING GIST (geometry);

-- 4. Authority Field Validations & Responder Sign-offs
CREATE TABLE IF NOT EXISTS natural_dam_validations (
    id VARCHAR(64) PRIMARY KEY,
    dam_id VARCHAR(64) REFERENCES natural_dam_candidates(id) ON DELETE CASCADE,
    validator_role VARCHAR(128) NOT NULL,
    status VARCHAR(64) NOT NULL, -- 'Confirmed', 'Not a Natural Dam', 'False Detection', 'Needs Investigation'
    evidence_type VARCHAR(64) NOT NULL, -- 'DRONE_AERIAL_SURVEY', 'GROUND_INSPECTION', 'SATELLITE_REANALYSIS'
    notes TEXT NOT NULL,
    photo_url TEXT,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_val_dam_id ON natural_dam_validations (dam_id);

-- 5. Downstream Infrastructure & Demographic Exposure
CREATE TABLE IF NOT EXISTS natural_dam_downstream_exposure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dam_id VARCHAR(64) REFERENCES natural_dam_candidates(id) ON DELETE CASCADE,
    corridor_geometry GEOMETRY(LineString, 4326),
    exposure_tier VARCHAR(32) NOT NULL, -- 'EXTREME', 'HIGH', 'MODERATE', 'LOW'
    villages_count INT DEFAULT 0,
    population_exposed INT DEFAULT 0,
    roads_compromised_km NUMERIC(6, 2) DEFAULT 0.0,
    bridges_compromised INT DEFAULT 0,
    schools_at_risk INT DEFAULT 0,
    hospitals_at_risk INT DEFAULT 0,
    assessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Natural Dam Alert Log
CREATE TABLE IF NOT EXISTS natural_dam_alerts (
    id VARCHAR(64) PRIMARY KEY,
    dam_id VARCHAR(64) REFERENCES natural_dam_candidates(id) ON DELETE CASCADE,
    alert_type VARCHAR(64) NOT NULL, -- 'AUTHORITY_INVESTIGATION_REQUIRED', 'OUTBURST_BREACH_WARNING'
    target_jurisdiction VARCHAR(128) NOT NULL, -- 'HPSDMA_Mandi_Kullu'
    cap_identifier VARCHAR(128),
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
