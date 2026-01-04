"""
Core types, enums, and type aliases for Human Design calculations.

This module contains foundational types used throughout the human_design package.
"""

from enum import Enum
from typing import Annotated, Any, Literal

import swisseph as swe  # type: ignore
from pydantic import BeforeValidator, PlainSerializer, validate_call

CenterName = Literal[
    "INSPIRATION",
    "MIND",
    "EXPRESSION",
    "IDENTITY",
    "WILLPOWER",
    "EMOTION",
    "DRIVE",
    "LIFEFORCE",
    "INTUITION",
]

GateNumber = Literal[
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
]

GateLineNumber = Literal[1, 2, 3, 4, 5, 6]


class Planet(Enum):
    """
    Planets used in Human Design calculations.

    Each planet has methods to compute its zodiac longitude and speed
    at a given Julian Day Universal Time.

    Note: TRUE_NODE and NORTH_NODE refer to the same astronomical point
    (the ascending lunar node). SOUTH_NODE is computed as the opposite
    (descending lunar node, NORTH_NODE + 180°).
    """

    SUN = swe.SUN
    EARTH = swe.EARTH
    MOON = swe.MOON
    MERCURY = swe.MERCURY
    VENUS = swe.VENUS
    MARS = swe.MARS
    JUPITER = swe.JUPITER
    SATURN = swe.SATURN
    URANUS = swe.URANUS
    NEPTUNE = swe.NEPTUNE
    PLUTO = swe.PLUTO
    TRUE_NODE = swe.TRUE_NODE
    NORTH_NODE = swe.TRUE_NODE  # Alias for TRUE_NODE
    SOUTH_NODE = 999  # Special marker for computed opposite of North Node

    def lon_ut(self, jd_ut: float) -> float:
        """Calculate the zodiac longitude for this planet at the given Julian Day UT."""
        if self == Planet.SOUTH_NODE:
            raise ValueError("SOUTH_NODE is computed from NORTH_NODE, not directly calculated")
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        (xx, _retflag) = swe.calc_ut(jd_ut, self.value, flags)
        lon = float(xx[0])
        return lon % 360.0

    def speed_ut(self, jd_ut: float) -> float:
        """Calculate the zodiac speed for this planet at the given Julian Day UT."""
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        (xx, _retflag) = swe.calc_ut(jd_ut, self.value, flags)
        speed = float(xx[3])  # deg/day (with FLG_SPEED)
        return speed


class ZodiacSign(Enum):
    """
    The 12 zodiac signs with their degree ranges.

    Each value is a tuple of (full_name, start_degree, end_degree).
    """

    ARIES = ("Aries", 0, 30)
    TAURUS = ("Taurus", 30, 60)
    GEMINI = ("Gemini", 60, 90)
    CANCER = ("Cancer", 90, 120)
    LEO = ("Leo", 120, 150)
    VIRGO = ("Virgo", 150, 180)
    LIBRA = ("Libra", 180, 210)
    SCORPIO = ("Scorpio", 210, 240)
    SAGITTARIUS = ("Sagittarius", 240, 270)
    CAPRICORN = ("Capricorn", 270, 300)
    AQUARIUS = ("Aquarius", 300, 330)
    PISCES = ("Pisces", 330, 360)

    def __init__(self, full_name: str, start_deg: int, end_deg: int):
        self._full_name = full_name
        self._start_deg = start_deg
        self._end_deg = end_deg

    @property
    def full_name(self) -> str:
        """Human-readable name."""
        return self._full_name

    @property
    def start_deg(self) -> int:
        """Starting degree of this sign (0-330)."""
        return self._start_deg

    @property
    def end_deg(self) -> int:
        """Ending degree of this sign (30-360)."""
        return self._end_deg

    @validate_call
    def to_decimal_degrees(self, degrees: float, minutes: float, seconds: float) -> float:
        """Convert degrees, minutes, seconds within this sign to absolute decimal degrees."""
        return self.start_deg + degrees + (minutes / 60) + (seconds / 3600)


def _parse_zodiac_sign(value: Any) -> ZodiacSign:
    """Parse ZodiacSign from string name or return as-is if already ZodiacSign."""
    if isinstance(value, ZodiacSign):
        return value
    if isinstance(value, str):
        try:
            return ZodiacSign[value.upper()]
        except KeyError as e:
            raise ValueError(f"Invalid ZodiacSign name: {value}") from e
    raise ValueError(f"Cannot parse ZodiacSign from {type(value)}: {value}")


# Annotated type that parses and serializes ZodiacSign by name for Pydantic models
ZodiacSignField = Annotated[
    ZodiacSign,
    BeforeValidator(_parse_zodiac_sign),
    PlainSerializer(lambda v: v.name, return_type=str),
]


def _parse_planet(value: Any) -> Planet:
    """Parse Planet from string name or return as-is if already Planet."""
    if isinstance(value, Planet):
        return value
    if isinstance(value, str):
        try:
            return Planet[value.upper()]
        except KeyError as e:
            raise ValueError(f"Invalid Planet name: {value}") from e
    raise ValueError(f"Cannot parse Planet from {type(value)}: {value}")


# Annotated type that parses and serializes Planet by name for Pydantic models
PlanetField = Annotated[
    Planet,
    BeforeValidator(_parse_planet),
    PlainSerializer(lambda v: v.name, return_type=str),
]
