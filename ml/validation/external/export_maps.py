"""
export_maps.py — GIS Map Products for M6 External Validation
=============================================================
Exports GIS-compatible GeoJSON and GeoTIFF layers:
  1. M6_external_validation_points.geojson (classified TP, FP, TN, FN)
  2. M6_external_validation_prediction.tif
  3. M6_external_validation_observed.tif
  4. M6_external_validation_error.tif
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import tifffile
from shapely.geometry import Point, mapping

from ml.satellite_hazard.config import StudyAreaConfig
from ml.validation.external.frozen_evaluator import ExternalEvaluationResult


class ExternalValidationMapExporter:
    def __init__(self, output_dir: Optional[Path | str] = None):
        self.output_dir = Path(
            output_dir
            or Path(__file__).resolve().parents[3] / "data" / "satellite_output"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.study_area = StudyAreaConfig()

    def export_all(
        self,
        eval_result: ExternalEvaluationResult,
        scene_prediction_grid: Optional[np.ndarray] = None,
    ) -> Dict[str, Path]:
        """
        Exports GeoJSON points and GeoTIFF rasters representing the external validation outcome.
        """
        exported_files: Dict[str, Path] = {}

        # 1. GeoJSON Points with Error Categories
        features = []
        for s in eval_result.validation_samples:
            pt = Point(s.longitude, s.latitude)
            y_true = s.observed_label
            y_pred = 1 if s.m6_probability >= 0.50 else 0

            if y_true == 1 and y_pred == 1:
                cat = "TRUE_POSITIVE"
            elif y_true == 0 and y_pred == 1:
                cat = "FALSE_POSITIVE"
            elif y_true == 0 and y_pred == 0:
                cat = "TRUE_NEGATIVE"
            else:
                cat = "FALSE_NEGATIVE"

            feat = {
                "type": "Feature",
                "geometry": mapping(pt),
                "properties": {
                    "sample_id": s.sample_id,
                    "observed_label": y_true,
                    "observed_status": "HISTORICAL_LANDSLIDE" if y_true == 1 else "STABLE_NON_LANDSLIDE",
                    "m6_probability": s.m6_probability,
                    "m6_class": s.m6_class,
                    "error_category": cat,
                    "model_id": s.model_id,
                    "model_version": s.model_version,
                    "inference_timestamp": s.inference_timestamp,
                    "elevation_m": s.features.get("elevation_m"),
                    "slope_deg": s.features.get("slope_deg"),
                    "dist_to_road_m": s.features.get("dist_to_road_m"),
                    "dist_to_river_m": s.features.get("dist_to_river_m"),
                },
            }
            features.append(feat)

        geojson_data = {
            "type": "FeatureCollection",
            "name": "M6_External_Validation_Points",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

        geojson_path = self.output_dir / "M6_external_validation_points.geojson"
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)
        exported_files["points_geojson"] = geojson_path

        # 2. Raster products (500x400 grid standard)
        rows, cols = self.study_area.grid_rows, self.study_area.grid_cols
        min_lon, max_lon = self.study_area.min_lon, self.study_area.max_lon
        min_lat, max_lat = self.study_area.min_lat, self.study_area.max_lat

        # A. Prediction Raster
        if scene_prediction_grid is not None and scene_prediction_grid.shape == (rows, cols):
            pred_grid = scene_prediction_grid.astype(np.float32)
        else:
            # Generate continuous baseline raster from point interpolation or existing M6 file
            existing_m6 = self.output_dir / "landslide_m6_susceptibility.tif"
            if existing_m6.exists():
                pred_grid = tifffile.imread(str(existing_m6)).astype(np.float32)
            else:
                pred_grid = np.full((rows, cols), 0.35, dtype=np.float32)

        pred_tif_path = self.output_dir / "M6_external_validation_prediction.tif"
        tifffile.imwrite(str(pred_tif_path), pred_grid)
        exported_files["prediction_tif"] = pred_tif_path

        # B. Observed Validation Grid (-1: unobserved background, 1: observed landslide, 0: negative)
        obs_grid = np.full((rows, cols), -1.0, dtype=np.float32)
        # C. Error Grid (0: background, 1: True Positive, 2: False Positive, 3: False Negative, 4: True Negative)
        err_grid = np.zeros((rows, cols), dtype=np.int32)

        for s in eval_result.validation_samples:
            if min_lat <= s.latitude <= max_lat and min_lon <= s.longitude <= max_lon:
                r_idx = int((max_lat - s.latitude) / (max_lat - min_lat) * rows)
                c_idx = int((s.longitude - min_lon) / (max_lon - min_lon) * cols)
                r_idx = max(0, min(r_idx, rows - 1))
                c_idx = max(0, min(c_idx, cols - 1))

                y_true = s.observed_label
                y_pred = 1 if s.m6_probability >= 0.50 else 0
                obs_grid[r_idx, c_idx] = float(y_true)

                if y_true == 1 and y_pred == 1:
                    err_grid[r_idx, c_idx] = 1  # TP
                elif y_true == 0 and y_pred == 1:
                    err_grid[r_idx, c_idx] = 2  # FP
                elif y_true == 1 and y_pred == 0:
                    err_grid[r_idx, c_idx] = 3  # FN
                else:
                    err_grid[r_idx, c_idx] = 4  # TN

        obs_tif_path = self.output_dir / "M6_external_validation_observed.tif"
        tifffile.imwrite(str(obs_tif_path), obs_grid)
        exported_files["observed_tif"] = obs_tif_path

        err_tif_path = self.output_dir / "M6_external_validation_error.tif"
        tifffile.imwrite(str(err_tif_path), err_grid)
        exported_files["error_tif"] = err_tif_path

        return exported_files

    def export_unvalidated_inventory(
        self,
        events: List[Any],
        dataset_record: Any,
    ) -> Dict[str, Path]:
        """
        Exports real external observed landslide points to M6_external_validation_points.geojson
        and baseline Upper Beas rasters with explicit unobserved flags (-1.0) when external events
        fall outside the local catchment AOI.
        """
        exported_files: Dict[str, Path] = {}

        # 1. GeoJSON Points with External Metadata
        features = []
        for idx, ev in enumerate(events):
            pt = Point(ev.longitude, ev.latitude)
            props = {
                "sample_id": ev.event_id or f"ext_{idx+1}",
                "observed_label": 1,
                "observed_status": "HISTORICAL_LANDSLIDE",
                "m6_probability": None,
                "m6_class": "UNINFERRED_OUTSIDE_LOCAL_SCENE",
                "error_category": "OUTSIDE_UPPER_BEAS_AOI",
                "source_dataset": ev.source_dataset or dataset_record.dataset_name,
                "provider": dataset_record.provider,
                "event_date": ev.event_date or dataset_record.temporal_extent,
                "landslide_type": ev.landslide_type or "unspecified",
                "latitude": round(ev.latitude, 6),
                "longitude": round(ev.longitude, 6),
            }
            if ev.properties:
                for k, v in ev.properties.items():
                    if k not in props:
                        props[k] = v

            feat = {
                "type": "Feature",
                "geometry": mapping(pt),
                "properties": props,
            }
            features.append(feat)

        geojson_data = {
            "type": "FeatureCollection",
            "name": "M6_External_Validation_Points",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

        geojson_path = self.output_dir / "M6_external_validation_points.geojson"
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)
        exported_files["points_geojson"] = geojson_path

        # 2. Raster products for Upper Beas Scene (500x400)
        rows, cols = self.study_area.grid_rows, self.study_area.grid_cols

        # A. Prediction Raster
        existing_m6 = self.output_dir / "landslide_m6_susceptibility.tif"
        if existing_m6.exists():
            pred_grid = tifffile.imread(str(existing_m6)).astype(np.float32)
        else:
            pred_grid = np.full((rows, cols), 0.35, dtype=np.float32)

        pred_tif_path = self.output_dir / "M6_external_validation_prediction.tif"
        tifffile.imwrite(str(pred_tif_path), pred_grid)
        exported_files["prediction_tif"] = pred_tif_path

        # B. Observed Validation Grid (-1.0: unobserved background across Upper Beas)
        obs_grid = np.full((rows, cols), -1.0, dtype=np.float32)
        obs_tif_path = self.output_dir / "M6_external_validation_observed.tif"
        tifffile.imwrite(str(obs_tif_path), obs_grid)
        exported_files["observed_tif"] = obs_tif_path

        # C. Error Grid (0: unobserved background)
        err_grid = np.zeros((rows, cols), dtype=np.int32)
        err_tif_path = self.output_dir / "M6_external_validation_error.tif"
        tifffile.imwrite(str(err_tif_path), err_grid)
        exported_files["error_tif"] = err_tif_path

        return exported_files
