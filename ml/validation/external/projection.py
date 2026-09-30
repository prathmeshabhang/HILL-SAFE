"""
projection.py — CRS Validation & Metric Spatial Projections
============================================================
Provides rigorous coordinate system verification, coordinate order auditing,
and WGS84 (EPSG:4326) <-> UTM Zone 43N (EPSG:32643) projection.
Ensures that all buffer, distance, and area calculations occur strictly in meters.
"""

from __future__ import annotations

import math
from typing import Tuple


# WGS84 Ellipsoid constants
WGS84_A = 6378137.0                # Semi-major axis (meters)
WGS84_F = 1.0 / 298.257223563      # Flattening
WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2  # First eccentricity squared
UTM_K0 = 0.9996                    # UTM central scale factor
UTM_ZONE_43N_CENTRAL_MERIDIAN = 75.0  # Degrees East
FALSE_EASTING = 500000.0           # Meters
FALSE_NORTHING = 0.0              # Meters (Northern hemisphere)


def validate_coordinates(lat: float, lon: float) -> None:
    """
    Validates geographic coordinate bounds and checks for latitude/longitude swap.
    Himachal Pradesh lies in lat [30.0, 34.0], lon [75.0, 79.5].
    """
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of valid range [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of valid range [-180, 180]: {lon}")

    # Detect coordinate order transposition for Himalayan region
    if 75.0 <= lat <= 79.5 and 30.0 <= lon <= 34.0:
        raise ValueError(
            f"Coordinate transposition detected! Latitude={lat}, Longitude={lon}. "
            f"In Himachal Pradesh, latitude should be ~31-33 and longitude ~76-78."
        )


def wgs84_to_utm43n(lat: float, lon: float) -> Tuple[float, float]:
    """
    Projects WGS84 (lat, lon) in degrees to UTM Zone 43N (easting, northing) in meters.
    Standard Transverse Mercator projection implementation.
    """
    validate_coordinates(lat, lon)

    phi = math.radians(lat)
    lam = math.radians(lon)
    lam0 = math.radians(UTM_ZONE_43N_CENTRAL_MERIDIAN)

    a = WGS84_A
    e2 = WGS84_E2
    e_prime_sq = e2 / (1.0 - e2)

    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
    tan_phi = math.tan(phi)

    # Radius of curvature in the prime vertical
    N = a / math.sqrt(1.0 - e2 * sin_phi ** 2)
    T = tan_phi ** 2
    C = e_prime_sq * cos_phi ** 2
    A = (lam - lam0) * cos_phi

    # Meridian distance M
    M = a * (
        (1.0 - e2 / 4.0 - 3.0 * e2 ** 2 / 64.0 - 5.0 * e2 ** 3 / 256.0) * phi
        - (3.0 * e2 / 8.0 + 3.0 * e2 ** 2 / 32.0 + 45.0 * e2 ** 3 / 1024.0) * math.sin(2.0 * phi)
        + (15.0 * e2 ** 2 / 256.0 + 45.0 * e2 ** 3 / 1024.0) * math.sin(4.0 * phi)
        - (35.0 * e2 ** 3 / 3072.0) * math.sin(6.0 * phi)
    )

    # Easting
    easting = FALSE_EASTING + UTM_K0 * N * (
        A
        + (1.0 - T + C) * (A ** 3) / 6.0
        + (5.0 - 18.0 * T + T ** 2 + 72.0 * C - 58.0 * e_prime_sq) * (A ** 5) / 120.0
    )

    # Northing
    northing = FALSE_NORTHING + UTM_K0 * (
        M
        + N * tan_phi * (
            (A ** 2) / 2.0
            + (5.0 - T + 9.0 * C + 4.0 * C ** 2) * (A ** 4) / 24.0
            + (61.0 - 58.0 * T + T ** 2 + 600.0 * C - 330.0 * e_prime_sq) * (A ** 6) / 720.0
        )
    )

    return easting, northing


def utm43n_to_wgs84(easting: float, northing: float) -> Tuple[float, float]:
    """
    Inverse projection from UTM Zone 43N (easting, northing) in meters to WGS84 (lat, lon) in degrees.
    """
    a = WGS84_A
    e2 = WGS84_E2
    e_prime_sq = e2 / (1.0 - e2)
    e1 = (1.0 - math.sqrt(1.0 - e2)) / (1.0 + math.sqrt(1.0 - e2))

    x = easting - FALSE_EASTING
    y = northing - FALSE_NORTHING

    M = y / UTM_K0
    mu = M / (a * (1.0 - e2 / 4.0 - 3.0 * e2 ** 2 / 64.0 - 5.0 * e2 ** 3 / 256.0))

    phi1 = mu + (3.0 * e1 / 2.0 - 27.0 * e1 ** 3 / 32.0) * math.sin(2.0 * mu) \
              + (21.0 * e1 ** 2 / 16.0 - 55.0 * e1 ** 4 / 32.0) * math.sin(4.0 * mu) \
              + (151.0 * e1 ** 3 / 96.0) * math.sin(6.0 * mu) \
              + (1097.0 * e1 ** 4 / 512.0) * math.sin(8.0 * mu)

    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    tan_phi1 = math.tan(phi1)

    N1 = a / math.sqrt(1.0 - e2 * sin_phi1 ** 2)
    R1 = a * (1.0 - e2) / ((1.0 - e2 * sin_phi1 ** 2) ** 1.5)
    D = x / (N1 * UTM_K0)

    T1 = tan_phi1 ** 2
    C1 = e_prime_sq * cos_phi1 ** 2

    lat_rad = phi1 - (N1 * tan_phi1 / R1) * (
        D ** 2 / 2.0
        - (5.0 + 3.0 * T1 + 10.0 * C1 - 4.0 * C1 ** 2 - 9.0 * e_prime_sq) * D ** 4 / 24.0
        + (61.0 + 90.0 * T1 + 298.0 * C1 + 45.0 * T1 ** 2 - 252.0 * e_prime_sq - 3.0 * C1 ** 2) * D ** 6 / 720.0
    )

    lon_rad = math.radians(UTM_ZONE_43N_CENTRAL_MERIDIAN) + (
        D
        - (1.0 + 2.0 * T1 + C1) * D ** 3 / 6.0
        + (5.0 - 2.0 * C1 + 28.0 * T1 - 3.0 * C1 ** 2 + 8.0 * e_prime_sq + 24.0 * T1 ** 2) * D ** 5 / 120.0
    ) / cos_phi1

    return math.degrees(lat_rad), math.degrees(lon_rad)


def metric_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes Euclidean distance in true meters by projecting both points to UTM Zone 43N.
    Avoids distorted degree calculations.
    """
    x1, y1 = wgs84_to_utm43n(lat1, lon1)
    x2, y2 = wgs84_to_utm43n(lat2, lon2)
    return math.hypot(x2 - x1, y2 - y1)
