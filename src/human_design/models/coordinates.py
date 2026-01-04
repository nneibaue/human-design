"""
Coordinate and location models for Human Design calculations.

This module contains models for geographical coordinates, zodiac coordinates,
and time-related conversions.
"""

from datetime import UTC, datetime
from typing import cast
from zoneinfo import ZoneInfo

import pytz  # type: ignore
import swisseph as swe  # type: ignore
from pydantic import BaseModel, RootModel, computed_field
from timezonefinder import TimezoneFinder

from .core import ZodiacSignField


class LocalTime(RootModel[datetime]):
    """
    A local time that can be converted to UTC given a timezone.
    """

    def utc(self, tz_name: str) -> datetime:
        """Convert local time to UTC based on timezone name."""
        tz = ZoneInfo(tz_name)
        return self.root.replace(tzinfo=tz).astimezone(UTC)

    def jd(self, tz_name: str) -> float:
        """Calculate Julian Day UT from local time and timezone."""
        utc = self.utc(tz_name)
        y, m, d = utc.year, utc.month, utc.day
        hour = (
            utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3_600_000_000.0
        )
        return float(swe.julday(y, m, d, hour, swe.GREG_CAL))


class GeographicalCoordinate(BaseModel):
    """
    A geographical coordinate with latitude and longitude.
    """

    lat: float
    lon: float

    @computed_field  # type: ignore
    @property
    def timezone(self) -> str:
        """Determine timezone from coordinates."""
        tz = TimezoneFinder().timezone_at(lat=self.lat, lng=self.lon)
        if tz is None:
            raise RuntimeError(
                f"Could not determine timezone for coordinates: {self.lat}, {self.lon}"
            )
        return tz


class ZodiacCoordinate(BaseModel):
    """
    A coordinate within the zodiac expressed as sign + degrees/minutes/seconds.
    """

    sign: ZodiacSignField | str
    degree: int
    minute: int
    second: int

    def to_decimal_degrees(self) -> float:
        """Convert to absolute decimal degrees (0-360)."""
        return (
            cast(ZodiacSignField, self.sign).start_deg
            + self.degree
            + (self.minute / 60.0)
            + (self.second / 3600.0)
        )


class CoordinateRange(BaseModel):
    """
    A range of zodiac coordinates (start to end).

    Used to define the zodiac span of each gate.
    """

    start: ZodiacCoordinate
    end: ZodiacCoordinate

    @computed_field  # type: ignore
    @property
    def start_deg(self) -> float:
        """Start of range in decimal degrees."""
        return self.start.to_decimal_degrees()

    @computed_field  # type: ignore
    @property
    def end_deg(self) -> float:
        """End of range in decimal degrees."""
        return self.end.to_decimal_degrees()


class Location(BaseModel):
    """
    A named location with coordinates and timezone.
    """

    place: str
    latitude: float
    longitude: float
    timezone: str

    @classmethod
    def from_place(cls, city: str, country: str) -> Location:
        """
        Create a Location from a city and country by geocoding.

        Args:
            city: City name
            country: Country name

        Returns:
            Location with resolved coordinates and timezone
        """
        from ..calculate_utils import geocode_place

        place = f"{city}, {country}"
        lat, lon = geocode_place(place)

        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if tz_name is None:
            raise RuntimeError(f"Could not determine timezone for coordinates: {lat}, {lon}")

        # Validate timezone
        try:
            pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError as e:
            raise RuntimeError(f"Unknown timezone found: {tz_name}") from e

        return cls(place=place, latitude=lat, longitude=lon, timezone=tz_name)
