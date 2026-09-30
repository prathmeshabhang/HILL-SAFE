"""
geojson_generator.py — OGC Standard GeoJSON Exporter for Natural Dam Spatial Layers
==================================================================================
Converts pipeline results into interactive GeoJSON layers for Leaflet GIS,
PostGIS ingestion, and mobile disaster responder applications.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ml.natural_dam.inference.pipeline_runner import CompleteNaturalDamRecord


class NaturalDamGeoJSONExporter:
    """Exports standardized GeoJSON FeatureCollections from pipeline outputs."""

    @staticmethod
    def export_candidates_geojson(records: List[CompleteNaturalDamRecord]) -> Dict[str, Any]:
        features = []
        for r in records:
            c = r.candidate
            props = {
                "dam_id": c.dam_id,
                "river_name": c.river_name,
                "candidate_tier": c.candidate_tier,
                "status": c.status,
                "probability": c.probability,
                "confidence": c.confidence,
                "data_quality": c.data_quality,
                "observation_freshness": c.observation_freshness,
                "indicators_passed": f"{c.indicators_passed_count}/{c.total_indicators_count}",
                "upstream_water_growth_pct": r.impoundment.expansion_pct,
                "river_width_reduction_pct": r.obstruction.width_reduction_pct,
                "outburst_risk": r.outburst_risk.outburst_risk_level,
                "population_at_risk": r.exposure.population_exposed,
                "false_positive_rejected": c.false_positive_rejected,
                "rejection_reason": c.rejection_reason,
                "headline": r.explanation["headline"],
                "statutory_notice": r.explanation.get("disclaimer", ""),
            }

            feature = {
                "type": "Feature",
                "id": c.dam_id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [c.lon, c.lat],
                },
                "properties": props,
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "name": "natural_dam_candidates",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

    @staticmethod
    def export_impoundment_geojson(records: List[CompleteNaturalDamRecord]) -> Dict[str, Any]:
        features = []
        for r in records:
            if r.candidate.false_positive_rejected or not r.impoundment.has_impoundment:
                continue

            poly_coords = [[lon, lat] for lat, lon in r.impoundment.impoundment_polygon_coords]
            # Ensure closed polygon
            if poly_coords[0] != poly_coords[-1]:
                poly_coords.append(poly_coords[0])

            props = {
                "dam_id": r.candidate.dam_id,
                "river_name": r.candidate.river_name,
                "impounded_area_m2": r.impoundment.impounded_water_area_m2,
                "impounded_area_km2": r.impoundment.impounded_water_area_km2,
                "estimated_dam_height_m": r.impoundment.estimated_dam_height_m,
                "estimated_volume_m3": r.impoundment.estimated_impounded_volume_m3,
                "volume_method": r.impoundment.volume_estimation_method,
                "expansion_rate_m2_hr": r.impoundment.expansion_rate_m2_hr,
            }

            feature = {
                "type": "Feature",
                "id": f"IMP_{r.candidate.dam_id}",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [poly_coords],
                },
                "properties": props,
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "name": "potential_impounded_water",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }
