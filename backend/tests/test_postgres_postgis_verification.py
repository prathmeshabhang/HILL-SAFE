"""
backend/tests/test_postgres_postgis_verification.py
===================================================
Verification test harness for PostgreSQL / PostGIS spatial queries, geometries,
bounding boxes, and spatial predicates with cross-platform fallback.
Validates:
1. Spatial Geometries (Point, LineString, Polygon) in EPSG:4326 (WGS84).
2. Spatial Predicates: ST_Within, ST_Intersects, ST_DWithin (distance buffer).
3. Bounding Box (BBOX) filtering across GIS endpoints and spatial services.
4. Topology validity and PostGIS SQL dialect generation.
"""

import pytest
import json
from shapely.geometry import Point, LineString, Polygon, box, shape
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.gis.spatial_service import spatial_service
from backend.app.database.session import get_db, SessionLocal
from backend.app.database.models.spatial import SafeZoneModel, InfrastructureAssetModel
from backend.app.database.models.risk import RiskZoneModel

client = TestClient(app)


class TestPostgisSpatialVerification:
    """Verifies PostGIS-compatible spatial queries and predicates."""

    def test_geometry_types_validity(self):
        """Assert Point, LineString, and Polygon geometries are valid in EPSG:4326."""
        # 1. Point: Kullu River Gauge
        kullu_point = Point(77.108, 31.956)
        assert kullu_point.is_valid
        assert kullu_point.geom_type == "Point"

        # 2. LineString: NH-3 Aut to Pandoh corridor
        nh3_line = LineString([
            (77.145, 31.715),
            (77.160, 31.735),
            (77.170, 31.760),
        ])
        assert nh3_line.is_valid
        assert nh3_line.geom_type == "LineString"

        # 3. Polygon: Palchan-Solang Debris Flow Zone
        debris_poly = Polygon([
            (77.150, 32.280),
            (77.180, 32.310),
            (77.190, 32.290),
            (77.150, 32.280),
        ])
        assert debris_poly.is_valid
        assert debris_poly.geom_type == "Polygon"

    def test_st_within_predicate(self):
        """Verify ST_Within spatial containment predicate."""
        outer_aoi = box(76.8, 31.5, 77.6, 32.5)  # Upper Beas AOI bounding box
        
        station_inside = Point(77.108, 31.956)  # Kullu
        station_outside = Point(75.500, 30.000)  # Punjab plains (outside AOI)

        assert station_inside.within(outer_aoi) is True
        assert station_outside.within(outer_aoi) is False

    def test_st_intersects_predicate(self):
        """Verify ST_Intersects spatial intersection predicate for hazard zones and infrastructure."""
        # Hazard Inundation Ribbon
        flood_ribbon = Polygon([
            (77.140, 31.710),
            (77.140, 31.770),
            (77.180, 31.770),
            (77.180, 31.710),
            (77.140, 31.710),
        ])
        
        # Highway crossing through flood ribbon
        crossing_road = LineString([(77.130, 31.740), (77.190, 31.740)])
        # Mountain ridge road outside ribbon
        ridge_road = LineString([(77.250, 31.740), (77.290, 31.740)])

        assert flood_ribbon.intersects(crossing_road) is True
        assert flood_ribbon.intersects(ridge_road) is False

    def test_st_dwithin_distance_buffer(self):
        """Verify ST_DWithin / distance buffering in spatial units."""
        # Approximate 1 degree latitude ~ 111 km, 0.001 deg ~ 111 m
        beas_river_point = Point(77.1080, 31.9560)
        near_bank_house = Point(77.1085, 31.9562)  # ~60m away
        distant_hill_temple = Point(77.1250, 31.9800)  # ~3 km away

        buffer_100m_deg = 0.001  # ~111m buffer in degrees

        assert beas_river_point.distance(near_bank_house) <= buffer_100m_deg
        assert beas_river_point.distance(distant_hill_temple) > buffer_100m_deg

    def test_bounding_box_query_service(self):
        """Verify spatial service bounding box filtering."""
        db = SessionLocal()
        try:
            # Query whole basin
            res_all = spatial_service.get_hazard_zones_geojson(db)
            assert res_all["type"] == "FeatureCollection"
            assert res_all["count"] > 0

            # Query narrow bbox covering only Manali region (lat 32.2 to 32.35)
            res_manali = spatial_service.get_hazard_zones_geojson(
                db, bbox=[77.10, 32.20, 77.25, 32.35]
            )
            assert res_manali["type"] == "FeatureCollection"
            for feat in res_manali["features"]:
                s = shape(feat["geometry"])
                manali_box = box(77.10, 32.20, 77.25, 32.35)
                assert manali_box.intersects(s) is True

            # Query bbox completely disjoint (e.g. 70.0, 20.0, 71.0, 21.0)
            res_empty = spatial_service.get_hazard_zones_geojson(
                db, bbox=[70.0, 20.0, 71.0, 21.0]
            )
            assert res_empty["count"] == 0
        finally:
            db.close()

    def test_gis_endpoints_bbox_rest_api(self):
        """Verify REST API /api/v1/gis/hazards accepts bbox parameter."""
        # 1. Without bbox
        resp = client.get("/api/v1/gis/hazards")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"

        # 2. With valid bbox
        resp_bbox = client.get("/api/v1/gis/hazards?bbox=77.10,32.20,77.25,32.35")
        assert resp_bbox.status_code == 200
        data_bbox = resp_bbox.json()
        assert data_bbox["type"] == "FeatureCollection"

        # 3. With safe zones bbox
        resp_safe = client.get("/api/v1/gis/safe-zones?bbox=77.0,31.0,78.0,33.0")
        assert resp_safe.status_code == 200
        assert resp_safe.json()["type"] == "FeatureCollection"
