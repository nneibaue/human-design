#!/usr/bin/env python3
"""
Compute Human Design-style planetary activations (Gate.Line) from birth datetime + birthplace.

Dependencies:
  pip install pyswisseph geopy timezonefinder

Usage:
  python hd_bodygraph.py \
    --date 1990-01-15 \
    --time 13:37 \
    --place "Portland, United States" \
    --out bodygraph.json

Notes:
- Geocoding uses Nominatim (OpenStreetMap) via geopy: free, rate-limited. Consider caching.
- Timezone is resolved offline from coordinates via timezonefinder.
- Planetary longitudes computed via Swiss Ephemeris (pyswisseph).
- Gate mapping uses a gate-by-degree table (tropical zodiac degrees).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe  # pyswisseph
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# -------------------------
# Gate-by-degree mapping
# -------------------------
# Source table format:
# Each entry is (gate, start_deg, end_deg) on the tropical zodiac circle,
# where degrees are absolute [0, 360) with 0 = 0° Aries.
#
# The Barney+flow "gates by degrees" page provides these ranges by sign
# in degrees+minutes+seconds. We encode them here in decimal degrees.
#
# IMPORTANT: This list must cover the full 360° without gaps/overlaps.
#            If you want, you can regenerate this list programmatically
#            from a scraped/structured source, but this keeps it simple
#            and offline once installed.
#
# Ranges are [start, end) going forward; wrap-around handled separately.
#
# Aries starts at 0°, Taurus 30°, Gemini 60°, ... Pisces 330°.
#
# NOTE: The Barney+flow page uses ranges like "28°15' Pisces – 03°52'30\" Aries".
#       That implies wrap-around across 360°. We encode those as two segments
#       (e.g., Pisces 28.25°..30°, Aries 0°..3.875°).
#
# For brevity, we include the full 64-gate coverage.
#
# If you spot a mismatch with your favorite calculator, the usual culprits are:
# - sidereal vs tropical (Human Design uses tropical)
# - different ephemeris settings / node type
# - rounding at exact boundaries
GATE_RANGES: list[tuple[int, float, float]] = []


def _d(sign_base: float, deg: int, minutes: int = 0, seconds: int = 0) -> float:
    return sign_base + deg + minutes / 60.0 + seconds / 3600.0


def _add(gate: int, start: float, end: float) -> None:
    GATE_RANGES.append((gate, start, end))


def _build_gate_ranges() -> None:
    # Sign bases:
    AR, TA, GE, CA, LE, VI, LI, SC, SG, CP, AQ, PI = (
        0.0,
        30.0,
        60.0,
        90.0,
        120.0,
        150.0,
        180.0,
        210.0,
        240.0,
        270.0,
        300.0,
        330.0,
    )

    # --- ARIES (0..30) ---
    # Gate 25: 28°15' Pisces -> 3°52'30 Aries (wrap)
    _add(25, _d(PI, 28, 15, 0), 360.0)
    _add(25, 0.0, _d(AR, 3, 52, 30))
    _add(17, _d(AR, 3, 52, 30), _d(AR, 9, 30, 0))
    _add(21, _d(AR, 9, 30, 0), _d(AR, 15, 7, 30))
    _add(51, _d(AR, 15, 7, 30), _d(AR, 20, 45, 0))
    _add(42, _d(AR, 20, 45, 0), _d(AR, 26, 22, 30))
    _add(3, _d(AR, 26, 22, 30), _d(TA, 2, 0, 0))  # extends into Taurus

    # --- TAURUS (30..60) ---
    _add(27, _d(TA, 2, 0, 0), _d(TA, 7, 37, 30))
    _add(24, _d(TA, 7, 37, 30), _d(TA, 13, 15, 0))
    _add(2, _d(TA, 13, 15, 0), _d(TA, 18, 52, 30))
    _add(23, _d(TA, 18, 52, 30), _d(TA, 24, 30, 0))
    _add(8, _d(TA, 24, 30, 0), _d(GE, 0, 7, 30))  # into Gemini

    # --- GEMINI (60..90) ---
    _add(20, _d(GE, 0, 7, 30), _d(GE, 5, 45, 0))
    _add(16, _d(GE, 5, 45, 0), _d(GE, 11, 22, 30))
    _add(35, _d(GE, 11, 22, 30), _d(GE, 17, 0, 0))
    _add(45, _d(GE, 17, 0, 0), _d(GE, 22, 27, 30))
    _add(12, _d(GE, 22, 27, 30), _d(GE, 28, 15, 0))
    _add(15, _d(GE, 28, 15, 0), _d(CA, 3, 52, 30))  # into Cancer

    # --- CANCER (90..120) ---
    _add(52, _d(CA, 3, 52, 30), _d(CA, 9, 30, 0))
    _add(39, _d(CA, 9, 30, 0), _d(CA, 15, 7, 30))
    _add(53, _d(CA, 15, 7, 30), _d(CA, 20, 45, 0))
    _add(62, _d(CA, 20, 45, 0), _d(CA, 26, 22, 30))
    _add(56, _d(CA, 26, 22, 30), _d(LE, 2, 0, 0))  # into Leo

    # --- LEO (120..150) ---
    _add(31, _d(LE, 2, 0, 0), _d(LE, 7, 37, 30))
    _add(33, _d(LE, 7, 37, 30), _d(LE, 13, 15, 0))
    _add(7, _d(LE, 13, 15, 0), _d(LE, 18, 52, 30))
    _add(4, _d(LE, 18, 52, 30), _d(LE, 24, 30, 0))
    _add(29, _d(LE, 24, 30, 0), _d(VI, 0, 7, 30))  # into Virgo

    # --- VIRGO (150..180) ---
    _add(59, _d(VI, 0, 7, 30), _d(VI, 5, 45, 0))
    _add(40, _d(VI, 5, 45, 0), _d(VI, 11, 22, 30))
    _add(64, _d(VI, 11, 22, 30), _d(VI, 17, 0, 0))
    _add(47, _d(VI, 17, 0, 0), _d(VI, 22, 27, 30))
    _add(6, _d(VI, 22, 27, 30), _d(VI, 28, 15, 0))
    _add(46, _d(VI, 28, 15, 0), _d(LI, 3, 52, 30))  # into Libra

    # --- LIBRA (180..210) ---
    _add(18, _d(LI, 3, 52, 30), _d(LI, 9, 30, 0))
    _add(48, _d(LI, 9, 30, 0), _d(LI, 15, 7, 30))
    _add(57, _d(LI, 15, 7, 30), _d(LI, 20, 45, 0))
    _add(32, _d(LI, 20, 45, 0), _d(LI, 26, 22, 30))
    _add(50, _d(LI, 26, 22, 30), _d(SC, 2, 0, 0))  # into Scorpio

    # --- SCORPIO (210..240) ---
    _add(28, _d(SC, 2, 0, 0), _d(SC, 7, 37, 30))
    _add(44, _d(SC, 7, 37, 30), _d(SC, 13, 15, 0))
    _add(1, _d(SC, 13, 15, 0), _d(SC, 18, 52, 30))
    _add(43, _d(SC, 18, 52, 30), _d(SC, 24, 30, 0))
    _add(14, _d(SC, 24, 30, 0), _d(SG, 0, 7, 30))  # into Sagittarius

    # --- SAGITTARIUS (240..270) ---
    _add(34, _d(SG, 0, 7, 30), _d(SG, 5, 45, 0))
    _add(9, _d(SG, 5, 45, 0), _d(SG, 11, 22, 30))
    _add(5, _d(SG, 11, 22, 30), _d(SG, 17, 0, 0))
    _add(26, _d(SG, 17, 0, 0), _d(SG, 22, 27, 30))
    _add(11, _d(SG, 22, 27, 30), _d(SG, 28, 15, 0))
    _add(10, _d(SG, 28, 15, 0), _d(CP, 3, 52, 30))  # into Capricorn

    # --- CAPRICORN (270..300) ---
    _add(58, _d(CP, 3, 52, 30), _d(CP, 9, 30, 0))
    _add(38, _d(CP, 9, 30, 0), _d(CP, 15, 7, 30))
    _add(54, _d(CP, 15, 7, 30), _d(CP, 20, 45, 0))
    _add(61, _d(CP, 20, 45, 0), _d(CP, 26, 22, 30))
    _add(60, _d(CP, 26, 22, 30), _d(AQ, 2, 0, 0))  # into Aquarius

    # --- AQUARIUS (300..330) ---
    _add(41, _d(AQ, 2, 0, 0), _d(AQ, 7, 37, 30))
    _add(19, _d(AQ, 7, 37, 30), _d(AQ, 13, 15, 0))
    _add(13, _d(AQ, 13, 15, 0), _d(AQ, 18, 52, 30))
    _add(49, _d(AQ, 18, 52, 30), _d(AQ, 24, 30, 0))
    _add(30, _d(AQ, 24, 30, 0), _d(PI, 0, 7, 30))  # into Pisces

    # --- PISCES (330..360) ---
    _add(55, _d(PI, 0, 7, 30), _d(PI, 5, 45, 0))
    _add(37, _d(PI, 5, 45, 0), _d(PI, 11, 22, 30))
    _add(63, _d(PI, 11, 22, 30), _d(PI, 17, 0, 0))
    _add(22, _d(PI, 17, 0, 0), _d(PI, 22, 27, 30))
    _add(36, _d(PI, 22, 27, 30), _d(PI, 28, 15, 0))
    # Remaining Pisces tail (28°15'..30°) is Gate 25 already added above.


_build_gate_ranges()


# -------------------------
# Core utilities
# -------------------------
@dataclass(frozen=True)
class Location:
    place: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True)
class Activation:
    planet: str
    longitude: float  # degrees [0, 360)
    gate: int
    line: int


def _norm360(x: float) -> float:
    return x % 360.0


def _angdiff_signed(a: float, b: float) -> float:
    """Smallest signed difference a - b in degrees in [-180, 180)."""
    d = (a - b + 180.0) % 360.0 - 180.0
    return d


def geocode_place(place: str, cache_path: str = ".geocode_cache.json") -> tuple[float, float]:
    """Geocode a human-readable place string to (lat, lon). Uses a simple JSON cache."""
    from geopy.geocoders import ArcGIS

    cache: dict[str, Any] = {}
    if os.path.exists(cache_path):
        try:
            cache = json.loads(open(cache_path, encoding="utf-8").read())
        except Exception:
            cache = {}

    if place in cache:
        return float(cache[place]["lat"]), float(cache[place]["lon"])

    # Use ArcGIS (free, no API key required)
    geolocator = ArcGIS(timeout=20)
    loc = geolocator.geocode(place, exactly_one=True)
    if loc is None:
        raise RuntimeError(f"Could not geocode place: {place!r}")

    lat, lon = float(loc.latitude), float(loc.longitude)
    cache[place] = {"lat": lat, "lon": lon, "ts": time.time()}
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)
    return lat, lon


def timezone_for_latlon(lat: float, lon: float) -> str:
    tf = TimezoneFinder()
    tz = tf.timezone_at(lat=lat, lng=lon)
    if not tz:
        raise RuntimeError(f"Could not resolve timezone for lat/lon: {lat}, {lon}")
    return tz


def local_to_utc(dt_local: datetime, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    aware = dt_local.replace(tzinfo=tz)
    return aware.astimezone(UTC)


def jd_from_utc(dt_utc: datetime) -> float:
    """Convert UTC datetime to Swiss Ephemeris Julian Day (JD) (UT).

    Julian Day (JD) is a continuous count of days since noon on January 1, 4713 BC.
    """
    y, m, d = dt_utc.year, dt_utc.month, dt_utc.day
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60.0
        + dt_utc.second / 3600.0
        + dt_utc.microsecond / 3_600_000_000.0
    )
    return float(swe.julday(y, m, d, hour, swe.GREG_CAL))


def calc_lon_ut(jd_ut: float, body: int) -> tuple[float, float]:
    """Return (longitude_deg, speed_deg_per_day).

    Args:
        jd_ut: Julian Day (JD) in Universal Time (UT).
        body: Swiss Ephemeris body constant.
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    (xx, _retflag) = swe.calc_ut(jd_ut, body, flags)
    lon = float(xx[0])
    speed = float(xx[3])  # deg/day (with FLG_SPEED)
    return _norm360(lon), speed


def find_design_jd(birth_jd: float, birth_sun_lon: float) -> float:
    """
    Design Julian Day (JD) defined by Sun being 88° earlier (zodiac longitude).
    Solve for jd: sun_lon(jd) == (birth_sun_lon - 88) mod 360.

    Args:
        birth_jd: Birth Julian Day (JD) in Universal Time (UT).
        birth_sun_lon: Birth Sun longitude in degrees.

    Returns:
        Design Julian Day (JD) representing approximately 88 solar degrees earlier.
    """
    target = _norm360(birth_sun_lon - 88.0)

    # Start near ~88 days earlier (close enough for Newton iteration).
    jd = birth_jd - 88.0

    # Newton-ish iteration using sun speed.
    for _ in range(20):
        lon, speed = calc_lon_ut(jd, swe.SUN)
        err = _angdiff_signed(lon, target)  # lon - target
        if abs(err) < 1e-6:
            break
        # Step in days. speed is ~1 deg/day, so this is stable.
        jd -= err / (speed if speed != 0 else 0.9856)

    return jd


def gate_line_from_longitude(lon: float) -> tuple[int, int]:
    """
    Map longitude to (gate, line) using:
      - gate-by-degree ranges
      - line subdivision: 6 lines per gate segment

    Line is computed as:
      offset_in_gate / (gate_span/6)
    """
    lon = _norm360(lon)

    # Find gate range that contains lon.
    for gate, start, end in GATE_RANGES:
        if start <= end:
            if start <= lon < end:
                span = end - start
                offset = lon - start
                line = int(math.floor(offset / (span / 6.0))) + 1
                return gate, min(max(line, 1), 6)
        else:
            # wrap range, should not occur in our built list (we split wraps),
            # but keep robust.
            if lon >= start or lon < end:
                span = (360.0 - start) + end
                offset = (lon - start) if lon >= start else ((360.0 - start) + lon)
                line = int(math.floor(offset / (span / 6.0))) + 1
                return gate, min(max(line, 1), 6)

    raise RuntimeError(f"No gate range found for longitude {lon}")


def activations_for_jd(jd_ut: float) -> list[Activation]:
    """Calculate planetary activations at a given Julian Day (JD).

    Args:
        jd_ut: Julian Day (JD) in Universal Time (UT).

    Returns:
        List of Activation objects for all relevant planets and nodes.
    """
    planets: list[tuple[str, int]] = [
        ("Sun", swe.SUN),
        ("Earth", swe.EARTH),
        ("Moon", swe.MOON),
        ("Mercury", swe.MERCURY),
        ("Venus", swe.VENUS),
        ("Mars", swe.MARS),
        ("Jupiter", swe.JUPITER),
        ("Saturn", swe.SATURN),
        ("Uranus", swe.URANUS),
        ("Neptune", swe.NEPTUNE),
        ("Pluto", swe.PLUTO),
        ("TrueNode", swe.TRUE_NODE),
    ]

    out: list[Activation] = []

    # Sun
    sun_lon, _ = calc_lon_ut(jd_ut, swe.SUN)
    sun_gate, sun_line = gate_line_from_longitude(sun_lon)
    out.append(Activation("Sun", sun_lon, sun_gate, sun_line))

    # Earth = opposite Sun
    earth_lon = _norm360(sun_lon + 180.0)
    earth_gate, earth_line = gate_line_from_longitude(earth_lon)
    out.append(Activation("Earth", earth_lon, earth_gate, earth_line))

    # Other planets
    for name, body in planets:
        if name == "Sun":
            continue
        lon, _ = calc_lon_ut(jd_ut, body)
        gate, line = gate_line_from_longitude(lon)
        out.append(Activation(name, lon, gate, line))

    # South node opposite TrueNode
    for act in out:
        if act.planet == "TrueNode":
            sn_lon = _norm360(act.longitude + 180.0)
            sn_gate, sn_line = gate_line_from_longitude(sn_lon)
            out.append(Activation("SouthNode", sn_lon, sn_gate, sn_line))
            break

    # Stable order
    order = {
        "Sun": 0,
        "Earth": 1,
        "Moon": 2,
        "TrueNode": 3,
        "SouthNode": 4,
        "Mercury": 5,
        "Venus": 6,
        "Mars": 7,
        "Jupiter": 8,
        "Saturn": 9,
        "Uranus": 10,
        "Neptune": 11,
        "Pluto": 12,
    }
    out.sort(key=lambda a: order.get(a.planet, 999))
    return out


def activation_dict(acts: list[Activation]) -> list[dict[str, Any]]:
    return [
        {
            "planet": a.planet,
            "longitude_deg": round(a.longitude, 6),
            "gate": a.gate,
            "line": a.line,
            "gate_line": f"{a.gate}.{a.line}",
        }
        for a in acts
    ]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="Birth date, e.g. 1990-01-15")
    p.add_argument("--time", required=True, help="Birth local time, e.g. 13:37 (24h)")
    p.add_argument(
        "--place", required=True, help='Birthplace string, e.g. "Portland, United States"'
    )
    p.add_argument(
        "--lat", type=float, default=None, help="Optional: latitude override (skip geocoding)"
    )
    p.add_argument(
        "--lon", type=float, default=None, help="Optional: longitude override (skip geocoding)"
    )
    p.add_argument(
        "--tz", default=None, help="Optional: IANA timezone override (skip timezone lookup)"
    )
    p.add_argument("--out", default=None, help="Write JSON output to this file (else print)")
    args = p.parse_args()

    # Parse inputs
    try:
        y, m, d = map(int, args.date.split("-"))
        hh, mm = map(int, args.time.split(":"))
    except Exception as e:
        raise SystemExit(f"Bad --date/--time format: {e}")

    dt_local = datetime(y, m, d, hh, mm, 0)

    # Resolve location
    if args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
    else:
        lat, lon = geocode_place(args.place)

    tz_name = args.tz or timezone_for_latlon(lat, lon)

    loc = Location(place=args.place, latitude=lat, longitude=lon, timezone=tz_name)

    # Local -> UTC -> Julian Day (JD)
    dt_utc = local_to_utc(dt_local, tz_name)
    birth_jd = jd_from_utc(dt_utc)

    # Birth Sun longitude
    birth_sun_lon, _ = calc_lon_ut(birth_jd, swe.SUN)

    # Design Julian Day (JD) by 88° solar longitude offset
    design_jd = find_design_jd(birth_jd, birth_sun_lon)

    # Activations
    personality = activations_for_jd(birth_jd)
    design = activations_for_jd(design_jd)

    out = {
        "input": {
            "date": args.date,
            "time_local": args.time,
            "place": args.place,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "timezone": loc.timezone,
            "datetime_utc": dt_utc.isoformat(),
            "julian_day_ut": round(birth_jd, 8),
        },
        "design_time": {
            "julian_day_ut": round(design_jd, 8),
            # Julian Day (JD) -> rough UTC datetime (for debugging only)
            # Swiss Ephemeris provides reverse conversions, but we keep minimal here.
        },
        "personality": activation_dict(personality),
        "design": activation_dict(design),
    }

    text = json.dumps(out, indent=2, sort_keys=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Wrote {args.out}")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
