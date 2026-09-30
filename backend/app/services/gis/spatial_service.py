"""
backend/app/services/gis/spatial_service.py
===========================================
Geospatial Query & PostGIS Analysis Service for Upper Beas River Basin.
Supports spatial bounding-box queries, hazard intersections, safe-zone buffers,
and evacuation corridor clearance analysis.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from shapely.geometry import Point, Polygon, box, shape, mapping
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.models.spatial import InfrastructureAssetModel, PopulationZoneModel, SafeZoneModel
from backend.app.database.models.risk import RiskZoneModel
from backend.app.database.models.evacuation import EvacuationRouteModel


class SpatialGISService:
    def __init__(self):
        self.aoi_bbox = [settings.MIN_LONGITUDE, settings.MIN_LATITUDE, settings.MAX_LONGITUDE, settings.MAX_LATITUDE]

    def get_hazard_zones_geojson(
        self,
        db: Session,
        bbox: Optional[List[float]] = None,
        zone_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns GeoJSON FeatureCollection of active hazard zones within AOI/bounding box."""
        query = db.query(RiskZoneModel)
        if zone_type:
            query = query.filter_by(zone_type=zone_type)

        records = query.all()
        features = []

        bbox_geom = None
        if bbox and len(bbox) == 4:
            try:
                bbox_geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
            except Exception:
                bbox_geom = None

        # If no custom zones exist in DB, supply default Upper Beas key corridor zones
        if not records:
            default_zones = [
                {
                    "name": "NH-3 Aut-Larji Riverbed Ribbon",
                    "zone_type": "INUNDATION_AND_DEBRIS_FLOW",
                    "risk_level": "CRITICAL",
                    "coordinates": [
                        [77.145, 31.715],
                        [77.170, 31.760],
                        [77.195, 31.750],
                        [77.145, 31.715],
                    ],
                },
                {
                    "name": "Bhuntar Airport Floodplain Reach",
                    "zone_type": "FLASH_FLOOD_LOW_LYING",
                    "risk_level": "HIGH",
                    "coordinates": [
                        [77.140, 31.870],
                        [77.165, 31.890],
                        [77.155, 31.910],
                        [77.140, 31.870],
                    ],
                },
                {
                    "name": "Palchan-Solang Debris Flow Cone",
                    "zone_type": "LANDSLIDE_RUNOUT",
                    "risk_level": "HIGH",
                    "coordinates": [
                        [77.150, 32.280],
                        [77.180, 32.310],
                        [77.190, 32.290],
                        [77.150, 32.280],
                    ],
                },
            ]
            for dz in default_zones:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [dz["coordinates"]],
                    },
                    "properties": {
                        "name": dz["name"],
                        "zone_type": dz["zone_type"],
                        "risk_level": dz["risk_level"],
                    },
                })
        else:
            for r in records:
                try:
                    geom = json.loads(r.geometry_geojson)
                except Exception:
                    geom = None
                features.append({
                    "type": "Feature",
                    "id": r.id,
                    "geometry": geom,
                    "properties": {
                        "name": r.name,
                        "zone_type": r.zone_type,
                        "risk_level": r.risk_level,
                    },
                })

        if bbox_geom:
            filtered = []
            for f in features:
                if f.get("geometry"):
                    try:
                        s_geom = shape(f["geometry"])
                        if bbox_geom.intersects(s_geom):
                            filtered.append(f)
                    except Exception:
                        filtered.append(f)
                else:
                    filtered.append(f)
            features = filtered

        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
            "count": len(features),
        }

    def get_safe_zones_geojson(
        self,
        db: Session,
        min_elevation_m: float = 1000.0,
        min_capacity: int = 100,
        bbox: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Returns designated safe zones and emergency shelters meeting criteria."""
        records = (
            db.query(SafeZoneModel)
            .filter(SafeZoneModel.elevation_m >= min_elevation_m)
            .filter(SafeZoneModel.capacity_headcount >= min_capacity)
            .all()
        )

        bbox_geom = None
        if bbox and len(bbox) == 4:
            try:
                bbox_geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
            except Exception:
                bbox_geom = None

        features = []
        # Default Upper Beas shelters if empty
        if not records:
            default_shelters = [
                {"name": "Kullu Degree College Ground", "lat": 31.960, "lon": 77.112, "elev": 1280.0, "cap": 1500, "score": 0.95},
                {"name": "Bhuntar Forest Rest House", "lat": 31.885, "lon": 77.160, "elev": 1150.0, "cap": 450, "score": 0.88},
                {"name": "Manali Club House High Terrace", "lat": 32.255, "lon": 77.185, "elev": 2080.0, "cap": 800, "score": 0.92},
                {"name": "Banjar Tehsil Relief Camp", "lat": 31.640, "lon": 77.340, "elev": 1350.0, "cap": 600, "score": 0.90},
            ]
            for s in default_shelters:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
                    "properties": {
                        "name": s["name"],
                        "elevation_m": s["elev"],
                        "capacity_headcount": s["cap"],
                        "suitability_score": s["score"],
                        "status": "DESIGNATED_ACTIVE",
                    },
                })
        else:
            for r in records:
                features.append({
                    "type": "Feature",
                    "id": r.id,
                    "geometry": {"type": "Point", "coordinates": [r.longitude, r.latitude]},
                    "properties": {
                        "name": r.name,
                        "safe_zone_type": r.safe_zone_type,
                        "elevation_m": r.elevation_m,
                        "capacity_headcount": r.capacity_headcount,
                        "suitability_score": r.suitability_score,
                    },
                })

        if bbox_geom:
            filtered = []
            for f in features:
                if f.get("geometry"):
                    try:
                        s_geom = shape(f["geometry"])
                        if bbox_geom.intersects(s_geom):
                            filtered.append(f)
                    except Exception:
                        filtered.append(f)
                else:
                    filtered.append(f)
            features = filtered

        return {
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
        }

    def get_infrastructure_geojson(
        self,
        db: Session,
        bbox: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Returns critical infrastructure assets (NH-3 segments, tunnels, bridges)."""
        records = db.query(InfrastructureAssetModel).all()

        bbox_geom = None
        if bbox and len(bbox) == 4:
            try:
                bbox_geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
            except Exception:
                bbox_geom = None

        features = []

        if not records:
            default_assets = [
                {"name": "NH-3 Aut-Larji River Highway Segment", "type": "NATIONAL_HIGHWAY", "lat": 31.73, "lon": 77.16, "tier": "TIER_1"},
                {"name": "Aut Tunnel North Portal", "type": "TUNNEL", "lat": 31.745, "lon": 77.18, "tier": "TIER_1"},
                {"name": "Bhuntar Suspension Bridge", "type": "BRIDGE", "lat": 31.88, "lon": 77.15, "tier": "TIER_1"},
                {"name": "Pandoh Dam Intake Works", "type": "HYDROPOWER_DAM", "lat": 31.67, "lon": 77.06, "tier": "TIER_1"},
            ]
            for a in default_assets:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
                    "properties": {
                        "name": a["name"],
                        "asset_type": a["type"],
                        "criticality_tier": a["tier"],
                    },
                })
        else:
            for r in records:
                features.append({
                    "type": "Feature",
                    "id": r.id,
                    "geometry": {"type": "Point", "coordinates": [r.longitude or 77.15, r.latitude or 31.8]},
                    "properties": {
                        "name": r.name,
                        "asset_type": r.asset_type,
                        "criticality_tier": r.criticality_tier,
                        "replacement_cost_inr": r.replacement_cost_inr,
                    },
                })

        if bbox_geom:
            filtered = []
            for f in features:
                if f.get("geometry"):
                    try:
                        s_geom = shape(f["geometry"])
                        if bbox_geom.intersects(s_geom):
                            filtered.append(f)
                    except Exception:
                        filtered.append(f)
                else:
                    filtered.append(f)
            features = filtered

        return {
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
        }

    def get_evacuation_routes_geojson(self, db: Session, incident_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns calculated evacuation routes from M16, strictly de-duplicated without repetitive corridors."""
        query = db.query(EvacuationRouteModel)
        if incident_id:
            query = query.filter_by(incident_id=incident_id)

        records = query.all()

        # Canonical corridor geometry mapping for distinct Upper Beas routes
        ROUTE_GEOMETRIES = {
            "Bhuntar Settlement": [[77.152, 31.878], [77.140, 31.910], [77.112, 31.960]],
            "Manali Mall Road": [[77.189, 32.242], [77.185, 32.246], [77.181, 32.251]],
            "Old Manali Riverbank": [[77.178, 32.255], [77.175, 32.258], [77.172, 32.262]],
            "Naggar Valley Reach": [[77.168, 32.145], [77.165, 32.148], [77.162, 32.152]],
            "Palchan Lowland": [[77.164, 32.308], [77.160, 32.312], [77.158, 32.315]],
        }

        features = []
        seen_corridors = set()

        for r in records:
            orig = (r.origin_name or "Valley Reach").strip()
            dest = (r.destination_safe_zone or "Safe Zone").strip()
            key = (orig.lower(), dest.lower())
            if key in seen_corridors:
                continue
            seen_corridors.add(key)

            coords = ROUTE_GEOMETRIES.get(
                orig,
                [[77.152, 31.878], [77.135, 31.920], [77.112, 31.960]]
            )

            features.append({
                "type": "Feature",
                "id": r.id,
                "properties": {
                    "incident_id": r.incident_id,
                    "name": f"{orig} to {dest}",
                    "origin_name": orig,
                    "destination_safe_zone": dest,
                    "distance_km": r.distance_km,
                    "estimated_duration_min": r.estimated_duration_min,
                    "clearance_status": r.clearance_status or "CLEAR",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
            })

        # Ensure complementary unique corridors exist across Upper Beas reach
        default_unique_corridors = [
            {
                "id": "RTE-MANALI-HADIMBA",
                "origin_name": "Manali Mall Road",
                "destination_safe_zone": "Hadimba Temple Safe Ridge",
                "distance_km": 1.8,
                "estimated_duration_min": 24,
                "clearance_status": "CLEAR",
                "coordinates": [[77.189, 32.242], [77.185, 32.246], [77.181, 32.251]],
            },
            {
                "id": "RTE-OLDMANALI-SCHOOL",
                "origin_name": "Old Manali Riverbank",
                "destination_safe_zone": "Govt Senior Secondary School Safe Zone",
                "distance_km": 1.2,
                "estimated_duration_min": 18,
                "clearance_status": "CAUTION",
                "coordinates": [[77.178, 32.255], [77.175, 32.258], [77.172, 32.262]],
            },
            {
                "id": "RTE-NAGGAR-CASTLE",
                "origin_name": "Naggar Valley Reach",
                "destination_safe_zone": "Naggar Castle Upper Terrace",
                "distance_km": 2.1,
                "estimated_duration_min": 28,
                "clearance_status": "CLEAR",
                "coordinates": [[77.168, 32.145], [77.165, 32.148], [77.162, 32.152]],
            },
            {
                "id": "RTE-PALCHAN-SOLANG",
                "origin_name": "Palchan Lowland",
                "destination_safe_zone": "Solang Upper Terminal Safe Ground",
                "distance_km": 3.4,
                "estimated_duration_min": 45,
                "clearance_status": "CAUTION",
                "coordinates": [[77.164, 32.308], [77.160, 32.312], [77.158, 32.315]],
            },
        ]

        for def_c in default_unique_corridors:
            key = (def_c["origin_name"].lower(), def_c["destination_safe_zone"].lower())
            if key not in seen_corridors:
                seen_corridors.add(key)
                features.append({
                    "type": "Feature",
                    "id": def_c["id"],
                    "properties": {
                        "incident_id": "STANDBY_CORRIDOR",
                        "name": f"{def_c['origin_name']} to {def_c['destination_safe_zone']}",
                        "origin_name": def_c["origin_name"],
                        "destination_safe_zone": def_c["destination_safe_zone"],
                        "distance_km": def_c["distance_km"],
                        "estimated_duration_min": def_c["estimated_duration_min"],
                        "clearance_status": def_c["clearance_status"],
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": def_c["coordinates"],
                    },
                })

        return {
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
        }

    def get_rivers_geojson(self) -> Dict[str, Any]:
        """Returns authoritative Upper Beas river network and key tributaries as GeoJSON LineStrings."""
        features = [
            {
                "type": "Feature",
                "id": "RIV-BEAS-MAIN",
                "properties": {
                    "river_id": "BEAS_MAIN_STEM",
                    "name": "Beas River (Main Stem)",
                    "category": "MAIN_RIVER",
                    "stream_order": 5,
                    "length_km": 68.5,
                    "gradient_mps": 17.5,
                    "conveyance_status": "HIGH_SURGE",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        # Rohtang Crest & Upper Gorge
                        [77.085, 32.365],
                        [77.098, 32.358],
                        [77.112, 32.348],
                        [77.125, 32.340],
                        [77.135, 32.332],
                        [77.145, 32.325],
                        [77.152, 32.320],
                        [77.158, 32.316],
                        # Kothi Gorge to Palchan Confluence
                        [77.162, 32.312],
                        [77.165, 32.310],
                        [77.168, 32.308],
                        [77.170, 32.302],
                        [77.172, 32.296],
                        # Burwa & Bahang
                        [77.174, 32.290],
                        [77.176, 32.285],
                        [77.179, 32.278],
                        [77.182, 32.270],
                        [77.185, 32.265],
                        # Vashisht Reach & Old Manali Confluence
                        [77.188, 32.258],
                        [77.191, 32.252],
                        [77.189, 32.246],
                        # Manali Town & Aleo Bridge
                        [77.188, 32.240],
                        [77.190, 32.238],
                        [77.192, 32.235],
                        [77.194, 32.230],
                        [77.195, 32.224],
                        # Simsa, Rangri & Prini Bends
                        [77.197, 32.218],
                        [77.198, 32.210],
                        [77.200, 32.204],
                        # Jagatsukh & Haripur S-Curves
                        [77.202, 32.198],
                        [77.200, 32.190],
                        [77.196, 32.182],
                        [77.192, 32.175],
                        [77.188, 32.168],
                        [77.184, 32.160],
                        [77.180, 32.152],
                        # Naggar Heritage & Patlikuhal Meanders
                        [77.175, 32.145],
                        [77.168, 32.138],
                        [77.158, 32.132],
                        [77.148, 32.128],
                        [77.142, 32.122],
                        [77.139, 32.115],
                        # Katrain, 15-Mile & Raison Valley
                        [77.138, 32.105],
                        [77.136, 32.095],
                        [77.134, 32.085],
                        [77.132, 32.072],
                        [77.130, 32.060],
                        [77.128, 32.048],
                        [77.126, 32.038],
                        # Babeli Nature Park & Pirdi Rafting Bends
                        [77.124, 32.025],
                        [77.121, 32.012],
                        [77.118, 31.998],
                        [77.116, 31.985],
                        [77.114, 31.975],
                        # Kullu Urban Corridor (Akhara Bazar, Sarvari Confluence, Dhalpur)
                        [77.113, 31.965],
                        [77.110, 31.958],
                        [77.112, 31.950],
                        [77.116, 31.942],
                        [77.122, 31.932],
                        [77.128, 31.922],
                        [77.135, 31.912],
                        # Shamshi & Bhuntar Airport Reach
                        [77.142, 31.902],
                        [77.148, 31.892],
                        [77.152, 31.885],
                        # Parvati River Confluence at Bhuntar
                        [77.155, 31.879],
                        [77.158, 31.872],
                        [77.162, 31.862],
                        [77.166, 31.852],
                        # Bajoura & Takoli Gorge Entry
                        [77.172, 31.840],
                        [77.178, 31.828],
                        [77.185, 31.818],
                        [77.190, 31.810],
                        [77.195, 31.800],
                        [77.200, 31.788],
                        # Panarsa & Aut Gorge / Tunnel
                        [77.204, 31.775],
                        [77.206, 31.762],
                        [77.208, 31.750],
                        [77.212, 31.740],
                        [77.215, 31.732],
                        # Larji Confluence (Beas, Sainj, Tirthan)
                        [77.218, 31.725],
                        [77.216, 31.716],
                        # Pandoh Gorge (Thalout, Hanogi Mata, Jhalogi)
                        [77.208, 31.710],
                        [77.198, 31.705],
                        [77.185, 31.702],
                        [77.172, 31.698],
                        [77.158, 31.695],
                        [77.142, 31.690],
                        [77.125, 31.686],
                        [77.108, 31.682],
                        [77.085, 31.678],
                        [77.070, 31.674],
                        # Pandoh Dam Spillway
                        [77.058, 31.671],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "RIV-SOLANG",
                "properties": {
                    "river_id": "SOLANG_NULLAH",
                    "name": "Solang Nullah Tributary",
                    "category": "TRIBUTARY",
                    "stream_order": 3,
                    "length_km": 8.4,
                    "conveyance_status": "DEBRIS_WATCH",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.135, 32.342],
                        [77.140, 32.335],
                        [77.145, 32.330],
                        [77.149, 32.325],
                        [77.152, 32.320],
                        [77.156, 32.316],
                        [77.160, 32.312],
                        [77.164, 32.308],
                        [77.168, 32.308],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "RIV-MANALSU",
                "properties": {
                    "river_id": "MANALSU_NULLAH",
                    "name": "Manalsu Nullah (Old Manali)",
                    "category": "TRIBUTARY",
                    "stream_order": 3,
                    "length_km": 6.2,
                    "conveyance_status": "NORMAL",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.148, 32.270],
                        [77.154, 32.266],
                        [77.158, 32.262],
                        [77.165, 32.258],
                        [77.172, 32.255],
                        [77.175, 32.253],
                        [77.181, 32.247],
                        [77.185, 32.244],
                        [77.188, 32.240],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "RIV-PARVATI",
                "properties": {
                    "river_id": "PARVATI_RIVER",
                    "name": "Parvati River (Kasol - Bhuntar)",
                    "category": "MAJOR_TRIBUTARY",
                    "stream_order": 4,
                    "length_km": 34.0,
                    "conveyance_status": "ELEVATED",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.350, 32.025],
                        [77.340, 32.010],
                        [77.328, 32.000],
                        [77.315, 31.992],
                        [77.300, 31.985],
                        [77.285, 31.975],
                        [77.268, 31.962],
                        [77.250, 31.950],
                        [77.235, 31.940],
                        [77.218, 31.928],
                        [77.205, 31.918],
                        [77.195, 31.910],
                        [77.182, 31.900],
                        [77.170, 31.890],
                        [77.162, 31.884],
                        [77.155, 31.879],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "RIV-SAINJ",
                "properties": {
                    "river_id": "SAINJ_RIVER",
                    "name": "Sainj River (Valley Reach)",
                    "category": "MAJOR_TRIBUTARY",
                    "stream_order": 4,
                    "length_km": 28.0,
                    "conveyance_status": "NORMAL",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.400, 31.795],
                        [77.380, 31.790],
                        [77.360, 31.788],
                        [77.340, 31.785],
                        [77.322, 31.784],
                        [77.306, 31.782],
                        [77.288, 31.770],
                        [77.272, 31.760],
                        [77.260, 31.750],
                        [77.245, 31.740],
                        [77.230, 31.732],
                        [77.218, 31.725],
                    ],
                },
            },
            {
                "type": "Feature",
                "id": "RIV-TIRTHAN",
                "properties": {
                    "river_id": "TIRTHAN_RIVER",
                    "name": "Tirthan River (Banjar - Larji)",
                    "category": "MAJOR_TRIBUTARY",
                    "stream_order": 4,
                    "length_km": 26.5,
                    "conveyance_status": "NORMAL",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.420, 31.605],
                        [77.400, 31.620],
                        [77.382, 31.628],
                        [77.365, 31.635],
                        [77.350, 31.640],
                        [77.330, 31.652],
                        [77.308, 31.668],
                        [77.280, 31.680],
                        [77.260, 31.692],
                        [77.242, 31.702],
                        [77.225, 31.710],
                        [77.216, 31.716],
                    ],
                },
            },
        ]
        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": features,
            "count": len(features),
        }


spatial_service = SpatialGISService()
