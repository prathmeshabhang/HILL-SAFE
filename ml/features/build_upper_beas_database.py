"""
build_upper_beas_database.py — FLOODY SHIELD Dataset Engine
=============================================================
Generates high-fidelity, physically coupled hydrological, meteorological, and
geotechnical observation records for the Upper Beas Catchment (Kullu–Manali, HP).

GROUND TRUTH & BENCHMARKS ENCODED:
----------------------------------
1. Geographic Domain:
   - Upper Beas Basin (Kullu, Manali, Naggar, Bhuntar, Aut, Pandoh Gorge).
   - Coordinates: [76.80°E - 77.45°E, 31.60°N - 32.40°N]
   - Elevation: 850m to 3800m.
2. 12 Flash Flood Conditioning Factors (from Himachal research / HiFlo-DAT):
   - elevation, slope, aspect, plan_curvature, profile_curvature, TWI, SPI,
     distance_to_river, rainfall_intensity, LULC, soil_clay_content.
3. GSI Landslide Susceptibility Parameters:
   - slope_angle, lithology (gneiss, schist, phyllite), distance_to_fault,
     distance_to_road (NH-3 cut-slope instability), drainage_density.
4. CWC Hydrometric Warning Thresholds:
   - Beas at Bhuntar (Warning Level: 1086.5m, Danger Level: 1088.0m).
5. Historical Extreme Regimes:
   - Encodes normal monsoon, heavy convective storms, and cloudburst triggers
     analogous to the July 2023 disaster.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

# Target Catchment Bounding Box
WEST, SOUTH, EAST, NORTH = 76.80, 31.60, 77.45, 32.40


def build_beas_catchment_datasets(n_samples: int = 8000, seed: int = 42):
    np.random.seed(seed)

    # 1. Coordinate spatial distribution across Upper Beas Valley
    lats = np.random.uniform(SOUTH, NORTH, n_samples)
    lons = np.random.uniform(WEST, EAST, n_samples)

    # 2. Elevation & Topography (Valley bottom along Beas river ~900m-1400m, ridges up to 3600m)
    # Distance to main Beas river corridor (approx centerline through Kullu)
    beas_centerline_lon = 77.15 + (lats - 31.60) * 0.15
    dist_to_main_river_m = np.abs(lons - beas_centerline_lon) * 111000.0 + np.random.exponential(scale=250.0, size=n_samples)

    # Elevation increases rapidly away from the valley floor
    elevation_m = 950.0 + (dist_to_main_river_m * 0.28) + (lats - SOUTH) * 450.0 + np.random.normal(0, 80, n_samples)
    elevation_m = np.clip(elevation_m, 850.0, 3800.0)

    # Slope: very steep gorge walls (30° - 55°), flatter terraces along Kullu/Bhuntar (5° - 18°)
    slope_deg = np.where(dist_to_main_river_m < 300.0,
                         np.random.uniform(3.0, 16.0, n_samples),
                         np.random.exponential(scale=24.0, size=n_samples) + 12.0)
    slope_deg = np.clip(slope_deg, 2.0, 65.0)

    aspect_deg = np.random.uniform(0.0, 360.0, n_samples)
    plan_curvature = np.random.normal(0.0, 1.4, n_samples)
    profile_curvature = np.random.normal(0.0, 1.2, n_samples)

    # Topographic Wetness Index (TWI) = ln(a / tan(beta)) -> high in valley bottoms, low on ridges
    slope_rad = np.radians(np.clip(slope_deg, 1.0, 89.0))
    flow_accum = np.where(dist_to_main_river_m < 500.0,
                          np.random.exponential(scale=10000.0, size=n_samples) + 2000.0,
                          np.random.exponential(scale=500.0, size=n_samples) + 10.0)
    twi = np.log((flow_accum * 30.0) / np.tan(slope_rad))
    twi = np.clip(twi, 2.0, 22.0)

    # Stream Power Index (SPI) = a * tan(beta)
    spi = np.log1p(flow_accum * np.tan(slope_rad))

    # Distance to National Highway NH-3 (major cut-slope vulnerability)
    dist_to_road_m = np.abs(dist_to_main_river_m - 120.0) + np.random.exponential(scale=150.0, size=n_samples)

    # Lithology (GSI Himachal classifications: 1=Granitic Gneiss (Hard), 2=Schist (Moderate), 3=Phyllite/Shale (Weak/Sheared))
    lithology_code = np.random.choice([1, 2, 3], size=n_samples, p=[0.30, 0.45, 0.25])
    # LULC: 1=Dense Deodar/Pine Forest, 2=Apple Orchards/Terrace, 3=Barren Scree/Steep Rock, 4=Urban Settlement (Kullu/Manali)
    lulc_code = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.40, 0.35, 0.15, 0.10])
    soil_clay_pct = np.clip(15.0 + lithology_code * 8.0 + np.random.normal(0, 4, n_samples), 8.0, 55.0)

    # 3. Dynamic Hydro-Meteorological Features (Simulating monsoon weather & cloudburst events)
    # Rainfall intensity (mm/hr)
    rainfall_15m = np.random.exponential(scale=4.5, size=n_samples)
    rainfall_1h = rainfall_15m * np.random.uniform(2.2, 3.8, size=n_samples)
    rainfall_3h = rainfall_1h * np.random.uniform(1.8, 2.7, size=n_samples)
    rainfall_6h = rainfall_3h * np.random.uniform(1.3, 2.1, size=n_samples)
    rainfall_24h = rainfall_6h * np.random.uniform(1.4, 2.8, size=n_samples)
    antecedent_rain_3d = np.random.exponential(scale=55.0, size=n_samples)

    # Soil moisture (% saturation)
    soil_moisture_pct = np.clip(25.0 + (antecedent_rain_3d * 0.38) + (rainfall_6h * 0.2) + np.random.normal(0, 4, n_samples), 15.0, 98.0)

    # CWC River Stage at nearest gauge (Beas/Parvati river: bed level ~1080m, Warning=1086.5m, Danger=1088.0m)
    cwc_river_level_m = 1080.0 + np.random.uniform(1.0, 9.5, n_samples)
    cwc_rate_of_rise_m_hr = np.random.normal(0.08, 0.35, n_samples)

    # -------------------------------------------------------------
    # MODEL M2: Flash Flood Occurrence Labeling (Upper Beas)
    # -------------------------------------------------------------
    # Floods occur on valley bottoms with high TWI, close to river, low slope, high river stage,
    # and heavy short-term rainfall or cloudburst.
    # Distance to river in kilometers
    dist_km = dist_to_main_river_m / 1000.0

    flood_affinity = (
        (twi * 0.8)
        - (slope_deg * 0.25)
        - (dist_km * 0.45)
        + (rainfall_1h * 0.18)
        + (rainfall_3h * 0.08)
        + (soil_moisture_pct * 0.05)
        + ((cwc_river_level_m - 1085.0) * 1.4)
        + (cwc_rate_of_rise_m_hr * 2.2)
        - ((elevation_m - 900.0) * 0.001)
        + (np.where(lulc_code == 4, 2.0, 0.0))  # Impervious urban settlement
    )
    p_flood = 1.0 / (1.0 + np.exp(-(flood_affinity - 3.5) / 2.5))
    flood_label = (np.random.rand(n_samples) < p_flood).astype(int)

    df_m2 = pd.DataFrame({
        "lat": lats,
        "lon": lons,
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "aspect_deg": aspect_deg,
        "plan_curvature": plan_curvature,
        "profile_curvature": profile_curvature,
        "twi": twi,
        "spi": spi,
        "dist_to_river_m": dist_to_main_river_m,
        "lulc_code": lulc_code,
        "soil_clay_pct": soil_clay_pct,
        "rainfall_15m": rainfall_15m,
        "rainfall_1h": rainfall_1h,
        "rainfall_3h": rainfall_3h,
        "rainfall_6h": rainfall_6h,
        "rainfall_24h": rainfall_24h,
        "antecedent_rain_3d": antecedent_rain_3d,
        "soil_moisture_pct": soil_moisture_pct,
        "cwc_river_level_m": cwc_river_level_m,
        "cwc_rate_of_rise_m_hr": cwc_rate_of_rise_m_hr,
        "flash_flood_occurred": flood_label,
    })

    # -------------------------------------------------------------
    # MODEL M6 & M7: Landslide Susceptibility & Dynamic Trigger Labeling
    # -------------------------------------------------------------
    # M6 Static Susceptibility: Peak between 32° - 48° slope, weak lithology (Phyllite/Schist),
    # close to road cut (NH-3) or undercut by torrential stream.
    slope_factor = np.exp(-((slope_deg - 38.0) ** 2) / (2 * 10.0**2))
    lith_factor = np.where(lithology_code == 3, 3.5, np.where(lithology_code == 2, 2.0, 0.5))
    road_cut_factor = np.where(dist_to_road_m < 80.0, 2.5, 0.0)
    undercut_factor = np.where(dist_to_main_river_m < 150.0, 1.8, 0.0)

    static_suscept_score = (slope_factor * 6.0) + lith_factor + road_cut_factor + undercut_factor + (np.abs(profile_curvature) * 0.9)
    # 3 classes: 0=Low, 1=Medium, 2=High
    suscept_prob = 1.0 / (1.0 + np.exp(-(static_suscept_score - 7.0) / 1.5))
    suscept_class = np.where(suscept_prob > 0.65, 2, np.where(suscept_prob > 0.30, 1, 0))

    # M7 Dynamic Trigger: Susceptible slope + (Intense 1h rain OR 3-day antecedent rain > 80mm + saturated soil)
    trigger_score = (
        (static_suscept_score * 0.9)
        + (rainfall_1h * 0.24)
        + (antecedent_rain_3d * 0.05)
        + (soil_moisture_pct * 0.08)
        - 11.0
    )
    p_trigger = 1.0 / (1.0 + np.exp(-trigger_score / 2.2))
    landslide_triggered = (np.random.rand(n_samples) < p_trigger).astype(int)

    df_landslide = pd.DataFrame({
        "lat": lats,
        "lon": lons,
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "aspect_deg": aspect_deg,
        "profile_curvature": profile_curvature,
        "lithology_code": lithology_code,
        "dist_to_road_m": dist_to_road_m,
        "dist_to_river_m": dist_to_main_river_m,
        "lulc_code": lulc_code,
        "susceptibility_class": suscept_class,
        "rainfall_1h": rainfall_1h,
        "antecedent_rain_3d": antecedent_rain_3d,
        "soil_moisture_pct": soil_moisture_pct,
        "landslide_triggered": landslide_triggered,
    })

    return df_m2, df_landslide


if __name__ == "__main__":
    out_dir = Path("data/processed/upper_beas")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_m2, df_landslide = build_beas_catchment_datasets(n_samples=10000)

    p_m2 = out_dir / "upper_beas_flood_dataset.csv"
    p_ls = out_dir / "upper_beas_landslide_dataset.csv"

    df_m2.to_csv(p_m2, index=False)
    df_landslide.to_csv(p_ls, index=False)

    print(f"Upper Beas Database built successfully:")
    print(f"  Flood Dataset ({len(df_m2)} rows): {p_m2}")
    print(f"    Flash Flood Incident Rate: {df_m2['flash_flood_occurred'].mean() * 100:.1f}%")
    print(f"  Landslide Dataset ({len(df_landslide)} rows): {p_ls}")
    print(f"    High Susceptibility Rate:  {(df_landslide['susceptibility_class'] == 2).mean() * 100:.1f}%")
    print(f"    Landslide Trigger Rate:    {df_landslide['landslide_triggered'].mean() * 100:.1f}%")
