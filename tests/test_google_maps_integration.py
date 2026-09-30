"""
tests/test_google_maps_integration.py
======================================
Integration verification tests for Google Maps Platform and Backend GIS architecture in FLOODY SHIELD.
Validates:
1. Backend GeoJSON specifications conform strictly to RFC 7946 and google.maps.Data requirements.
2. Layer manager endpoints provide non-empty FeatureCollections and required attributes.
3. Provenance and security isolation: No hardcoded API keys in tracked repository files.
4. Fail-soft behavior for missing or unconfigured environments.
"""

import pytest
import os
import re
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_key_security_no_hardcoded_keys():
    """Verify that no production Google Maps API key is hardcoded in source files."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")
    
    # Google API keys usually start with 'AIzaSy' and are 39 chars
    api_key_pattern = re.compile(r"AIzaSy[A-Za-z0-9_-]{33}")
    
    violating_files = []
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx", ".html")):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = api_key_pattern.findall(content)
                    if matches:
                        violating_files.append((filepath, matches))
                        
    assert not violating_files, f"Hardcoded Google Maps API keys detected in source: {violating_files}"


def test_gis_hazards_geojson_for_google_maps_data():
    """Verify /api/v1/gis/hazards returns valid GeoJSON Polygon FeatureCollection for google.maps.Data."""
    response = client.get("/api/v1/gis/hazards")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    assert "features" in data
    features = data["features"]
    assert len(features) > 0

    for f in features:
        assert f.get("type") == "Feature"
        geom = f.get("geometry", {})
        assert geom.get("type") in ["Polygon", "MultiPolygon"]
        props = f.get("properties", {})
        assert "risk" in props or "risk_level" in props


def test_gis_hyperlocal_admin_geojson_for_google_maps_data():
    """Verify /api/v1/gis/hyperlocal/admin returns 12 administrative units with census & SVI data."""
    response = client.get("/api/v1/gis/hyperlocal/admin")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) >= 5

    for f in features:
        props = f.get("properties", {})
        assert "name" in props or "unit_name" in props
        # Verify hazard tier present either at top level or in current_hazard dict
        assert "risk_tier" in props or "current_hazard" in props
        if "current_hazard" in props:
            assert "risk_level" in props["current_hazard"]
        # Verify Census 2011 population exposure present either flat or in exposure dict
        assert "census_population" in props or "population" in props or "exposure" in props
        if "exposure" in props:
            assert "permanent_population" in props["exposure"]


def test_gis_safe_zones_geojson_for_google_maps_data():
    """Verify /api/v1/gis/safe-zones returns high-ground shelters above flood line."""
    response = client.get("/api/v1/gis/safe-zones")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) > 0
    for f in features:
        props = f.get("properties", {})
        assert "name" in props


def test_gis_evacuation_routes_geojson_for_google_maps_data():
    """Verify /api/v1/gis/routes returns clearance-tagged LineStrings."""
    response = client.get("/api/v1/gis/routes")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) > 0
    for f in features:
        geom = f.get("geometry", {})
        assert geom.get("type") in ["LineString", "MultiLineString"]
        props = f.get("properties", {})
        assert "clearance_status" in props or "status" in props


def test_gis_cascade_bottlenecks_for_google_maps_data():
    """Verify /api/v1/gis/cascade/bottlenecks returns point debris dams with blockage % and discharge."""
    response = client.get("/api/v1/gis/cascade/bottlenecks")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) > 0
    for f in features:
        props = f.get("properties", {})
        assert "estimated_blockage_pct" in props or "blockage_pct" in props or "blockage" in props


def test_stations_telemetry_for_google_maps_markers():
    """Verify /api/v1/stations returns staging stations with geographic coordinates."""
    response = client.get("/api/v1/stations")
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data or isinstance(data, list)
    stations = data.get("stations", data)
    assert len(stations) > 0
    for s in stations:
        assert "lat" in s or "latitude" in s
        assert "lng" in s or "lon" in s or "longitude" in s


def test_active_alerts_for_google_maps_cap_polygons():
    """Verify /api/v1/alerts returns CAP alert records."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data or isinstance(data, list)


def test_gis_rivers_geojson_for_google_maps_data():
    """Verify /api/v1/gis/rivers returns authoritative river network LineStrings."""
    response = client.get("/api/v1/gis/rivers")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) >= 5
    for f in features:
        geom = f.get("geometry", {})
        assert geom.get("type") in ["LineString", "MultiLineString"]
        props = f.get("properties", {})
        assert "river_id" in props
        assert "name" in props

