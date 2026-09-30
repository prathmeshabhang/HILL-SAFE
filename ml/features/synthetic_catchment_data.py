"""
synthetic_catchment_data.py — FLOODY SHIELD Data Generator
============================================================
Generates physically grounded synthetic catchment observations and historical event
logs for the prototype study area in Himachal Pradesh (Beas/Sutlej basin).

SCIENTIFIC PRINCIPLES:
-----------------------
1. Terrain Realism:
   - Elevation: 600m (valley floor) to 2800m (ridge).
   - Slope: 5° (alluvial plains) to 48° (steep gorge slopes).
   - Flow accumulation: High in stream channels, low on ridges.
2. Hydrological Coupling:
   - Flood probability increases with high flow accumulation, low slope, high antecedent
     rainfall, rising river level, and soil saturation.
3. Geotechnical Coupling:
   - Landslide susceptibility increases with high slope (25°-45°), steep curvature,
     and weak lithology.
   - Landslide trigger occurs when susceptible slopes encounter extreme short-term
     rainfall (>30 mm/h) or high 3-day antecedent rainfall (>100 mm) + high soil moisture.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd


def generate_study_area_dataset(
    n_samples: int = 5000,
    random_seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates tabular datasets for:
      1. Flood Model M2 training (hydrological & terrain features).
      2. Landslide Models M6 & M7 training (geotechnical & trigger features).
    """
    np.random.seed(random_seed)

    # Base coordinates: Himachal Pradesh prototype area
    lats = np.random.uniform(30.55, 31.95, n_samples)
    lons = np.random.uniform(76.55, 78.45, n_samples)

    # 1. Terrain Features
    elevation = np.random.uniform(600.0, 2800.0, n_samples)
    slope = np.random.exponential(scale=18.0, size=n_samples)
    slope = np.clip(slope, 2.0, 60.0)  # degrees
    aspect = np.random.uniform(0.0, 360.0, n_samples)
    curvature = np.random.normal(loc=0.0, scale=1.2, size=n_samples)
    
    # Distance to stream (meters)
    dist_to_stream = np.random.exponential(scale=350.0, size=n_samples) + 10.0
    # Flow accumulation (log-scale drainage area in cells)
    flow_accumulation = np.random.exponential(scale=1500.0, size=n_samples) + 1.0

    # Land cover code (1: Forest, 2: Agriculture, 3: Bare Rock / Steep, 4: Built-up / Settlement)
    land_cover = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.45, 0.30, 0.15, 0.10])
    
    # Lithology/Soil code (1: Hard Gneiss/Granite, 2: Schist/Phyllite, 3: Alluvial/Colluvial soil)
    lithology = np.random.choice([1, 2, 3], size=n_samples, p=[0.35, 0.40, 0.25])

    # 2. Meteorological & Hydrological Variables (Simulating monsoon weather regimes)
    # Rainfall rates (mm/hr)
    rainfall_1h = np.random.exponential(scale=6.0, size=n_samples)
    rainfall_3h = rainfall_1h * np.random.uniform(1.8, 2.8, size=n_samples)
    rainfall_6h = rainfall_3h * np.random.uniform(1.4, 2.0, size=n_samples)
    rainfall_24h = rainfall_6h * np.random.uniform(1.5, 3.0, size=n_samples)
    antecedent_rain_3d = np.random.exponential(scale=45.0, size=n_samples)  # 3-day antecedent mm

    # Soil moisture (% saturation, 10% to 95%)
    soil_moisture = np.clip(20.0 + (antecedent_rain_3d * 0.4) + np.random.normal(0, 5, n_samples), 10.0, 95.0)

    # River hydrometry
    river_level = np.random.uniform(1.5, 9.0, n_samples)  # meters
    river_level_change_1h = np.random.normal(loc=0.05, scale=0.4, size=n_samples)  # m/hr

    # -------------------------------------------------------------
    # Physically Grounded Flood Target (M2)
    # -------------------------------------------------------------
    # Flood is likely in valley bottoms (low slope, low elevation, high flow accumulation, close to stream)
    # under intense precipitation, high antecedent wetness, and high river stage.
    flood_score = (
        (rainfall_1h * 0.25)
        + (rainfall_6h * 0.10)
        + (antecedent_rain_3d * 0.05)
        + (soil_moisture * 0.08)
        + (river_level * 1.5)
        + (river_level_change_1h * 2.5)
        - (slope * 0.35)                     # Water runs off steep slopes
        - (dist_to_stream * 0.008)           # Flood danger drops away from channel
        + (np.log1p(flow_accumulation) * 0.8) # Basins accumulate water
        - (elevation * 0.002)
    )
    # Normalize with sigmoid to probability
    p_flood = 1.0 / (1.0 + np.exp(-(flood_score - 18.0) / 4.0))
    flood_occurrence = (np.random.rand(n_samples) < p_flood).astype(int)

    df_flood = pd.DataFrame({
        "lat": lats,
        "lon": lons,
        "elevation": elevation,
        "slope": slope,
        "flow_accumulation": flow_accumulation,
        "dist_to_stream": dist_to_stream,
        "land_cover": land_cover,
        "rainfall_1h": rainfall_1h,
        "rainfall_3h": rainfall_3h,
        "rainfall_6h": rainfall_6h,
        "rainfall_24h": rainfall_24h,
        "antecedent_rain_3d": antecedent_rain_3d,
        "soil_moisture": soil_moisture,
        "river_level": river_level,
        "river_level_change_1h": river_level_change_1h,
        "flood_occurred": flood_occurrence,
        "true_p_flood": p_flood,
    })

    # -------------------------------------------------------------
    # Physically Grounded Landslide Targets (M6 Susceptibility & M7 Trigger)
    # -------------------------------------------------------------
    # M6 Static Susceptibility depends purely on slope, lithology, aspect, curvature, distance to stream
    # Peak susceptibility occurs on steep slopes between 28° and 48°, weak lithology (code 2 or 3)
    optimal_slope_factor = np.exp(-((slope - 36.0) ** 2) / (2 * 12.0**2))
    lithology_factor = np.where(lithology == 1, 0.2, np.where(lithology == 2, 0.7, 1.0))
    susceptibility_score = (
        (optimal_slope_factor * 5.0)
        + (lithology_factor * 3.0)
        + (np.abs(curvature) * 0.8)
        + np.where(dist_to_stream < 150.0, 1.5, 0.0)
    )
    p_susceptible = 1.0 / (1.0 + np.exp(-(susceptibility_score - 4.5) / 1.2))
    susceptible_class = np.where(p_susceptible > 0.7, 2, np.where(p_susceptible > 0.35, 1, 0)) # 0: Low, 1: Medium, 2: High

    # M7 Dynamic Trigger: Susceptible slope + Intense short-term rain OR extreme soil saturation
    trigger_score = (
        (susceptibility_score * 0.8)
        + (rainfall_1h * 0.18)
        + (antecedent_rain_3d * 0.04)
        + (soil_moisture * 0.06)
        - 8.5
    )
    p_trigger = 1.0 / (1.0 + np.exp(-trigger_score / 2.0))
    landslide_triggered = (np.random.rand(n_samples) < p_trigger).astype(int)

    df_landslide = pd.DataFrame({
        "lat": lats,
        "lon": lons,
        "elevation": elevation,
        "slope": slope,
        "aspect": aspect,
        "curvature": curvature,
        "lithology": lithology,
        "dist_to_stream": dist_to_stream,
        "land_cover": land_cover,
        "susceptibility_class": susceptible_class,
        "rainfall_1h": rainfall_1h,
        "antecedent_rain_3d": antecedent_rain_3d,
        "soil_moisture": soil_moisture,
        "landslide_triggered": landslide_triggered,
        "true_p_trigger": p_trigger,
    })

    return df_flood, df_landslide


if __name__ == "__main__":
    out_dir = Path("data/samples")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Generating physically grounded synthetic catchment datasets...")
    df_flood, df_landslide = generate_study_area_dataset(n_samples=6000)

    flood_path = out_dir / "catchment_flood_training.csv"
    landslide_path = out_dir / "catchment_landslide_training.csv"

    df_flood.to_csv(flood_path, index=False)
    df_landslide.to_csv(landslide_path, index=False)

    print(f"Saved Flood Dataset ({len(df_flood)} rows): {flood_path}")
    print(f"  Flood incidence rate: {df_flood['flood_occurred'].mean() * 100:.1f}%")
    print(f"Saved Landslide Dataset ({len(df_landslide)} rows): {landslide_path}")
    print(f"  High susceptibility rate: {(df_landslide['susceptibility_class'] == 2).mean() * 100:.1f}%")
    print(f"  Landslide trigger rate:   {df_landslide['landslide_triggered'].mean() * 100:.1f}%")
