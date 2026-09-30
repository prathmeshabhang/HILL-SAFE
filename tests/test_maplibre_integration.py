"""
tests/test_maplibre_integration.py
===================================
End-to-End Verification Test Suite for FLOODY SHIELD Phase 05A:
MapLibre GL JS Geospatial Rebuild & Layer Manager Integration.

Validates:
1. All authoritative backend GIS endpoints consumed by MapLibreLayerManager return valid RFC 7946 GeoJSON.
2. Evacuation corridors are de-duplicated down to distinct non-repeating pairs.
3. MapLibre frontend components and layer manager exports exist and adhere to architecture rules.
4. Zero hardcoded production secrets or private tokens in frontend map code.
5. Upper Beas Basin bounding envelope correctly brackets the target catchment.
"""

import os
import re
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_01_backend_gis_endpoints_availability():
    """Verify all backend GIS layers consumed by MapLibre respond with valid GeoJSON."""
    # 1. Rivers
    res_rivers = client.get("/api/v1/gis/rivers")
    assert res_rivers.status_code == 200
    rivers_data = res_rivers.json()
    assert rivers_data.get("type") == "FeatureCollection"
    assert len(rivers_data.get("features", [])) >= 3
    for f in rivers_data["features"]:
        assert f.get("geometry", {}).get("type") in ["LineString", "MultiLineString"]

    # 2. Administrative Wards & Gram Panchayats
    res_admin = client.get("/api/v1/gis/hyperlocal/admin")
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data.get("type") == "FeatureCollection"
    assert len(admin_data.get("features", [])) >= 5
    for f in admin_data["features"]:
        assert f.get("geometry", {}).get("type") in ["Polygon", "MultiPolygon"]

    # 3. Hazards / Risk Grid
    res_hazards = client.get("/api/v1/gis/hazards")
    assert res_hazards.status_code == 200
    assert res_hazards.json().get("type") == "FeatureCollection"

    # 4. Safe Zones / High Ground Shelters
    res_safe = client.get("/api/v1/gis/safe-zones")
    assert res_safe.status_code == 200
    assert res_safe.json().get("type") == "FeatureCollection"
    assert len(res_safe.json().get("features", [])) >= 3

    # 5. Evacuation Routes
    res_routes = client.get("/api/v1/gis/routes")
    assert res_routes.status_code == 200
    assert res_routes.json().get("type") == "FeatureCollection"

    # 6. IoT Stations
    res_stations = client.get("/api/v1/stations")
    assert res_stations.status_code == 200
    assert "stations" in res_stations.json()

    # 7. Natural Dam Candidates
    res_dams = client.get("/api/v1/natural-dams")
    assert res_dams.status_code == 200
    assert res_dams.json().get("type") == "FeatureCollection"


def test_02_evacuation_routes_deduplication():
    """Verify evacuation corridors are strictly de-duplicated without repeating corridor pairs."""
    res = client.get("/api/v1/gis/routes")
    assert res.status_code == 200
    features = res.json().get("features", [])
    assert len(features) > 0

    seen_pairs = set()
    for f in features:
        props = f.get("properties", {})
        origin = props.get("origin_name", "").strip().lower()
        dest = props.get("destination_safe_zone", "").strip().lower()
        pair_key = (origin, dest)
        assert pair_key not in seen_pairs, f"Duplicate evacuation corridor detected: {pair_key}"
        seen_pairs.add(pair_key)


def test_03_maplibre_frontend_files_and_exports():
    """Verify MapLibreContainer, MapLibreLayerManager, and HazardSurfaceGenerator exist with clean exports."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")

    maplibre_container = os.path.join(frontend_dir, "components", "Map", "MapLibreContainer.tsx")
    assert os.path.isfile(maplibre_container), "MapLibreContainer.tsx missing"

    with open(maplibre_container, "r", encoding="utf-8") as f:
        content = f.read()
        assert "export const MapLibreContainer" in content
        assert "MapLibreLayerManager" in content
        assert "isWebGL2Available" in content
        assert "MAP GRAPHICS UNSUPPORTED" in content

    layer_manager = os.path.join(frontend_dir, "services", "maps", "mapLibreLayerManager.ts")
    assert os.path.isfile(layer_manager), "mapLibreLayerManager.ts missing"

    with open(layer_manager, "r", encoding="utf-8") as f:
        content = f.read()
        assert "export class MapLibreLayerManager" in content
        assert "basemap-satellite-layer" in content
        assert "hazard-surface-raster-layer" in content
        assert "rivers-glow-layer" in content
        assert "admin-units-line-layer" in content

    generator = os.path.join(frontend_dir, "services", "maps", "hazardSurfaceGenerator.ts")
    assert os.path.isfile(generator), "hazardSurfaceGenerator.ts missing"

    with open(generator, "r", encoding="utf-8") as f:
        content = f.read()
        assert "generateHazardSurfaceDataUrl" in content
        assert "UPPER_BEAS_IMAGE_COORDINATES" in content

    # Check MapContainer defaults to maplibre
    map_container = os.path.join(frontend_dir, "components", "Map", "MapContainer.tsx")
    with open(map_container, "r", encoding="utf-8") as f:
        content = f.read()
        assert "preferredEngine = 'maplibre'" in content


def test_04_no_hardcoded_secrets_in_new_map_code():
    """Verify zero hardcoded API keys or secrets in new MapLibre source files."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")
    target_files = [
        os.path.join(frontend_dir, "components", "Map", "MapLibreContainer.tsx"),
        os.path.join(frontend_dir, "services", "maps", "mapLibreLayerManager.ts"),
        os.path.join(frontend_dir, "services", "maps", "hazardSurfaceGenerator.ts"),
    ]

    api_key_pattern = re.compile(r"AIzaSy[A-Za-z0-9_-]{33}")

    for file_path in target_files:
        assert os.path.isfile(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = api_key_pattern.findall(content)
            assert not matches, f"Hardcoded API key detected in {file_path}"


def test_05_beas_basin_bounds_consistency():
    """Verify Upper Beas catchment coordinates bracket the actual river valley."""
    generator_file = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "src", "services", "maps", "hazardSurfaceGenerator.ts"
    )
    with open(generator_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "north: 32.40" in content
        assert "south: 31.62" in content
        assert "west: 76.90" in content
        assert "east: 77.40" in content
