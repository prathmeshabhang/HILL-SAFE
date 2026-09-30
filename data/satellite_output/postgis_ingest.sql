-- =============================================================================
-- postgis_ingest.sql — Automated Pipeline Ingestion for PostGIS
-- FLOODY SHIELD — Predict • Protect • Preserve
-- =============================================================================
BEGIN;
INSERT INTO natural_dam_candidates (id, river_name, geometry, elevation_m, probability, confidence, candidate_tier, status, data_quality, last_detected_at) VALUES ('ND_BEAS_001', 'Beas_Sainj_Confluence', ST_SetSRID(ST_MakePoint(77.218, 31.725), 4326), 885.0, 0.862, 0.880, 'HIGH_CONFIDENCE_CANDIDATE', 'AUTHORITY_VALIDATION_REQUIRED', 'EXCELLENT', NOW()) ON CONFLICT (id) DO UPDATE SET probability = EXCLUDED.probability, confidence = EXCLUDED.confidence, status = EXCLUDED.status, last_detected_at = NOW();
INSERT INTO natural_dam_candidates (id, river_name, geometry, elevation_m, probability, confidence, candidate_tier, status, data_quality, last_detected_at) VALUES ('ND_CONTROL_PANDOH', 'Beas_Pandoh_Reservoir', ST_SetSRID(ST_MakePoint(77.0583, 31.6708), 4326), 850.0, 0.000, 0.950, 'NO_EVIDENCE', 'FALSE_POSITIVE', 'EXCELLENT', NOW()) ON CONFLICT (id) DO UPDATE SET probability = EXCLUDED.probability, confidence = EXCLUDED.confidence, status = EXCLUDED.status, last_detected_at = NOW();
INSERT INTO natural_dam_impoundments (dam_id, geometry, surface_area_m2, estimated_volume_m3, computed_at) VALUES ('ND_BEAS_001', ST_SetSRID(ST_GeomFromGeoJSON('{"type": "Polygon", "coordinates": [[[77.21300000000001, 31.720000000000002], [77.223, 31.720000000000002], [77.223, 31.73], [77.21300000000001, 31.73], [77.21300000000001, 31.720000000000002]]]}'), 4326), 138000.0, 1610000.0, NOW());
COMMIT;
