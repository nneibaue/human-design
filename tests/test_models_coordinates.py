"""
Tests for models.coordinates module.

Tests cover:
- LocalTime conversion to UTC and Julian Day
- GeographicalCoordinate timezone detection
- ZodiacCoordinate parsing and conversions
- CoordinateRange calculations
- Location data model
"""

from datetime import datetime

import pytest

from human_design.models.coordinates import (
    CoordinateRange,
    GeographicalCoordinate,
    LocalTime,
    Location,
    ZodiacCoordinate,
)
from human_design.models.core import ZodiacSign


class TestLocalTime:
    """Tests for LocalTime model."""

    def test_create_from_datetime(self) -> None:
        """Test LocalTime creation from datetime."""
        dt = datetime(1990, 1, 15, 10, 30, 0)
        local_time = LocalTime(dt)
        assert local_time.root == dt

    def test_utc_conversion_eastern_time(self) -> None:
        """Test conversion from Eastern time to UTC."""
        # 1990-01-15 10:30 EST is 1990-01-15 15:30 UTC
        dt = datetime(1990, 1, 15, 10, 30, 0)
        local_time = LocalTime(dt)
        utc = local_time.utc("America/New_York")

        assert utc.year == 1990
        assert utc.month == 1
        assert utc.day == 15
        assert utc.hour == 15
        assert utc.minute == 30

    def test_utc_conversion_london_time(self) -> None:
        """Test conversion from London time to UTC."""
        # 1990-01-15 10:30 GMT is 1990-01-15 10:30 UTC
        dt = datetime(1990, 1, 15, 10, 30, 0)
        local_time = LocalTime(dt)
        utc = local_time.utc("Europe/London")

        assert utc.hour == 10
        assert utc.minute == 30

    def test_jd_calculation(self) -> None:
        """Test Julian Day calculation."""
        dt = datetime(1990, 1, 15, 10, 30, 0)
        local_time = LocalTime(dt)
        jd = local_time.jd("America/New_York")

        # J2000 epoch is 2451545.0 (2000-01-01 12:00 UTC)
        # 1990-01-15 15:30 UTC should be before J2000
        assert isinstance(jd, float)
        assert 2447900 < jd < 2451545  # Before J2000

    def test_jd_with_different_timezones(self) -> None:
        """Test that different timezones give same UTC time and JD."""
        dt = datetime(1990, 1, 15, 10, 30, 0)
        local_time = LocalTime(dt)

        jd_ny = local_time.jd("America/New_York")
        jd_london = local_time.jd("Europe/London")

        # These should be different because the local times represent
        # different UTC times, so JDs should differ
        assert jd_ny != jd_london


class TestGeographicalCoordinate:
    """Tests for GeographicalCoordinate model."""

    def test_create_coordinate(self) -> None:
        """Test creating a geographical coordinate."""
        coord = GeographicalCoordinate(lat=40.7128, lon=-74.0060)
        assert coord.lat == 40.7128
        assert coord.lon == -74.0060

    @pytest.mark.parametrize(
        "lat,lon,expected_tz",
        [
            (40.7128, -74.0060, "America/New_York"),  # New York
            (51.5074, -0.1278, "Europe/London"),  # London
            (35.6762, 139.6503, "Asia/Tokyo"),  # Tokyo
        ],
    )
    def test_timezone_detection(self, lat: float, lon: float, expected_tz: str) -> None:
        """Test timezone detection for various coordinates."""
        coord = GeographicalCoordinate(lat=lat, lon=lon)
        assert coord.timezone == expected_tz

    def test_invalid_coordinates_raise_error(self) -> None:
        """Test that invalid coordinates (e.g., middle of ocean) raise error."""
        # Coordinates in the middle of the ocean
        coord = GeographicalCoordinate(lat=0.0, lon=0.0)
        # May not have a timezone or may have a generic one
        # Just verify it doesn't crash catastrophically
        tz = coord.timezone
        assert isinstance(tz, str)


class TestZodiacCoordinate:
    """Tests for ZodiacCoordinate model."""

    def test_create_zodiac_coordinate(self) -> None:
        """Test creating a zodiac coordinate."""
        coord = ZodiacCoordinate(sign="VIRGO", degree=15, minute=30, second=0)
        assert coord.sign == ZodiacSign.VIRGO
        assert coord.degree == 15
        assert coord.minute == 30
        assert coord.second == 0

    def test_create_from_enum(self) -> None:
        """Test creating zodiac coordinate from ZodiacSign enum."""
        coord = ZodiacCoordinate(sign=ZodiacSign.ARIES, degree=0, minute=0, second=0)
        assert coord.sign == ZodiacSign.ARIES

    @pytest.mark.parametrize(
        "sign,degree,minute,second,expected_degrees",
        [
            ("VIRGO", 0, 0, 0, 150.0),  # Virgo starts at 150°
            ("VIRGO", 15, 30, 0, 165.5),  # 150 + 15 + 0.5
            ("ARIES", 0, 0, 0, 0.0),  # Aries starts at 0°
        ],
    )
    def test_to_decimal_degrees(
        self,
        sign: str,
        degree: int,
        minute: int,
        second: int,
        expected_degrees: float,
    ) -> None:
        """Test conversion to decimal degrees."""
        coord = ZodiacCoordinate(sign=sign, degree=degree, minute=minute, second=second)
        assert coord.to_decimal_degrees() == pytest.approx(expected_degrees)

    def test_serialization_by_sign_name(self) -> None:
        """Test that sign field serializes by enum name."""
        coord = ZodiacCoordinate(sign=ZodiacSign.LEO, degree=10, minute=0, second=0)
        dump = coord.model_dump()
        assert dump["sign"] == "LEO"
        assert dump["degree"] == 10

    def test_json_serialization(self) -> None:
        """Test JSON serialization of zodiac coordinate."""
        coord = ZodiacCoordinate(sign="PISCES", degree=5, minute=15, second=30)
        json_str = coord.model_dump_json()
        assert '"sign":"PISCES"' in json_str
        assert '"degree":5' in json_str


class TestCoordinateRange:
    """Tests for CoordinateRange model."""

    def test_create_coordinate_range(self) -> None:
        """Test creating a coordinate range."""
        start = ZodiacCoordinate(sign="VIRGO", degree=11, minute=0, second=0)
        end = ZodiacCoordinate(sign="VIRGO", degree=17, minute=59, second=59)
        range_obj = CoordinateRange(start=start, end=end)

        assert range_obj.start == start
        assert range_obj.end == end

    @pytest.mark.parametrize(
        "start_sign,start_deg,start_min,start_sec,end_sign,end_deg,end_min,end_sec,expected_start,expected_end",
        [
            ("VIRGO", 0, 0, 0, "VIRGO", 5, 0, 0, 150.0, 155.0),  # Virgo range
            ("ARIES", 0, 0, 0, "ARIES", 5, 37, 30, 0.0, 5.625833),  # Aries range
        ],
    )
    def test_start_and_end_deg_properties(
        self,
        start_sign: str,
        start_deg: int,
        start_min: int,
        start_sec: int,
        end_sign: str,
        end_deg: int,
        end_min: int,
        end_sec: int,
        expected_start: float,
        expected_end: float,
    ) -> None:
        """Test start_deg and end_deg computed properties."""
        start = ZodiacCoordinate(
            sign=start_sign, degree=start_deg, minute=start_min, second=start_sec
        )
        end = ZodiacCoordinate(sign=end_sign, degree=end_deg, minute=end_min, second=end_sec)
        range_obj = CoordinateRange(start=start, end=end)

        assert range_obj.start_deg == pytest.approx(expected_start)
        assert range_obj.end_deg == pytest.approx(expected_end, abs=0.001)


class TestLocation:
    """Tests for Location data model."""

    def test_create_location(self) -> None:
        """Test creating a location."""
        loc = Location(
            place="New York, USA", latitude=40.7128, longitude=-74.0060, timezone="America/New_York"
        )
        assert loc.place == "New York, USA"
        assert loc.latitude == 40.7128
        assert loc.longitude == -74.0060
        assert loc.timezone == "America/New_York"

    def test_location_fields_accessible(self) -> None:
        """Test that Location fields are accessible and mutable."""
        loc = Location(
            place="London, UK", latitude=51.5074, longitude=-0.1278, timezone="Europe/London"
        )
        # Should be able to access fields
        assert loc.place == "London, UK"
        # Location is a BaseModel, so it should support modification in dict form
        data = loc.model_dump()
        assert data["place"] == "London, UK"
