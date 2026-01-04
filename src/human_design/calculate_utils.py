"""
Utility functions for Human Design chart calculations.

This module contains low-level utilities that are used by the models:
- calc_lon_ut: Calculate planetary longitude and speed at a Julian Day
- geocode_place: Convert place names to coordinates with caching
"""

import json
import os
import time
from typing import Any

import swisseph as swe  # type: ignore


def calc_lon_ut(jd_ut: float, body: int) -> tuple[float, float]:
    """
    Calculate the ecliptic longitude and speed of a celestial body.

    Args:
        jd_ut: Julian Day in Universal Time
        body: Swiss Ephemeris body constant (e.g., swe.SUN, swe.MOON)

    Returns:
        Tuple of (longitude in degrees [0, 360), speed in degrees/day)
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    (xx, _retflag) = swe.calc_ut(jd_ut, body, flags)
    lon = float(xx[0]) % 360.0
    speed = float(xx[3])
    return lon, speed


def geocode_place(place: str, cache_path: str = ".geocode_cache.json") -> tuple[float, float]:
    """
    Geocode a human-readable place string to (lat, lon).

    Uses a simple JSON cache to avoid repeated API calls. Falls back to ArcGIS
    geocoder (free, no API key required) if not cached.

    Args:
        place: Location string (e.g., "New York, USA" or "Albuquerque, United States")
        cache_path: Path to JSON cache file for storing geocoded locations.

    Returns:
        Tuple of (latitude, longitude) as floats.

    Raises:
        RuntimeError: If geocoding fails.
    """
    from geopy.geocoders import ArcGIS  # type: ignore

    cache: dict[str, Any] = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    if place in cache:
        return float(cache[place]["lat"]), float(cache[place]["lon"])

    # Use ArcGIS (free, no API key required)
    geolocator = ArcGIS()
    try:
        loc = geolocator.geocode(place)
    except Exception:
        loc = None
    if loc is None:
        raise RuntimeError(f"Could not geocode place: {place!r}")

    lat, lon = float(loc.latitude), float(loc.longitude) # type: ignore
    cache[place] = {"lat": lat, "lon": lon, "ts": time.time()}
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)
    return lat, lon
