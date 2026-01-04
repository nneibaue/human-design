"""
Tests for models.core module.

Tests cover:
- Planet enum and calculation methods
- ZodiacSign enum and properties
- ZodiacSignField validation and serialization
"""

import pytest
from pydantic import BaseModel, ValidationError

from human_design.models.core import (
    Planet,
    ZodiacSign,
    ZodiacSignField,
    _parse_zodiac_sign,
)


class TestPlanet:
    """Tests for Planet enum."""

    def test_planet_enum_values(self) -> None:
        """Test that all planets have valid Swiss Ephemeris values."""
        for planet in Planet:
            # Each planet should have a numeric value from swe constants
            assert isinstance(planet.value, int)
            assert planet.value >= 0

    def test_sun_calculations_at_epoch(self) -> None:
        """Test Sun longitude and speed at J2000 epoch."""
        jd = 2451545.0  # J2000 epoch
        lon = Planet.SUN.lon_ut(jd)
        speed = Planet.SUN.speed_ut(jd)

        # Sun is near Capricorn at J2000 (around 280-281°)
        assert 275.0 < lon < 285.0
        # Sun's speed is approximately 1 degree per day
        assert 0.9 < speed < 1.1

    def test_moon_calculations(self) -> None:
        """Test Moon has expected properties."""
        jd = 2451545.0
        lon = Planet.MOON.lon_ut(jd)
        speed = Planet.MOON.speed_ut(jd)

        # Longitude in valid range
        assert 0.0 <= lon < 360.0
        # Moon's speed varies but is typically 12-15 degrees per day
        assert 10.0 < speed < 16.0

    def test_longitude_always_in_range(self) -> None:
        """Test that all planets return longitude in [0, 360) range."""
        jd = 2451545.0
        for planet in Planet:
            if planet == Planet.SOUTH_NODE:
                # SOUTH_NODE is computed, not calculated directly
                continue
            lon = planet.lon_ut(jd)
            assert 0.0 <= lon < 360.0

    def test_earth_is_included(self) -> None:
        """Test that Earth is in the Planet enum."""
        assert Planet.EARTH in Planet


class TestZodiacSign:
    """Tests for ZodiacSign enum."""

    def test_all_signs_present(self) -> None:
        """Test all 12 zodiac signs are defined."""
        signs = list(ZodiacSign)
        assert len(signs) == 12

    def test_zodiac_sign_values(self) -> None:
        """Test that ZodiacSign values are tuples with name and degrees."""
        assert ZodiacSign.ARIES.value == ("Aries", 0, 30)
        assert ZodiacSign.VIRGO.value == ("Virgo", 150, 180)
        assert ZodiacSign.PISCES.value == ("Pisces", 330, 360)

    def test_full_name_property(self) -> None:
        """Test full_name property returns correct human-readable names."""
        assert ZodiacSign.ARIES.full_name == "Aries"
        assert ZodiacSign.CAPRICORN.full_name == "Capricorn"
        assert ZodiacSign.LIBRA.full_name == "Libra"

    def test_start_deg_property(self) -> None:
        """Test start_deg property returns correct starting degrees."""
        assert ZodiacSign.ARIES.start_deg == 0
        assert ZodiacSign.TAURUS.start_deg == 30
        assert ZodiacSign.GEMINI.start_deg == 60
        assert ZodiacSign.PISCES.start_deg == 330

    def test_end_deg_property(self) -> None:
        """Test end_deg property returns correct ending degrees."""
        assert ZodiacSign.ARIES.end_deg == 30
        assert ZodiacSign.TAURUS.end_deg == 60
        assert ZodiacSign.PISCES.end_deg == 360

    def test_to_decimal_degrees(self) -> None:
        """Test conversion of degrees/minutes/seconds to decimal degrees."""
        # Aries: 0-30 degrees
        result = ZodiacSign.ARIES.to_decimal_degrees(15, 30, 0)
        assert result == pytest.approx(15.5)

        # Virgo: 150-180 degrees
        result = ZodiacSign.VIRGO.to_decimal_degrees(0, 0, 0)
        assert result == pytest.approx(150.0)

        result = ZodiacSign.VIRGO.to_decimal_degrees(15, 30, 36)
        # 150 + 15 + (30/60) + (36/3600) = 150 + 15 + 0.5 + 0.01 = 165.51
        assert result == pytest.approx(165.51)

    def test_zodiac_sign_by_name(self) -> None:
        """Test accessing ZodiacSign enum members by name."""
        assert ZodiacSign["ARIES"] == ZodiacSign.ARIES
        assert ZodiacSign["VIRGO"] == ZodiacSign.VIRGO
        assert ZodiacSign["PISCES"] == ZodiacSign.PISCES


class TestZodiacSignParsing:
    """Tests for _parse_zodiac_sign validation function."""

    def test_parse_zodiac_sign_from_string(self) -> None:
        """Test parsing ZodiacSign from string name."""
        result = _parse_zodiac_sign("ARIES")
        assert result == ZodiacSign.ARIES

        result = _parse_zodiac_sign("virgo")
        assert result == ZodiacSign.VIRGO

        result = _parse_zodiac_sign("Capricorn")
        assert result == ZodiacSign.CAPRICORN

    def test_parse_zodiac_sign_from_enum(self) -> None:
        """Test parsing ZodiacSign from enum value returns as-is."""
        enum_val = ZodiacSign.LEO
        result = _parse_zodiac_sign(enum_val)
        assert result is enum_val

    def test_parse_zodiac_sign_invalid_string(self) -> None:
        """Test parsing invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ZodiacSign name"):
            _parse_zodiac_sign("INVALID_SIGN")

    def test_parse_zodiac_sign_invalid_type(self) -> None:
        """Test parsing invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse ZodiacSign"):
            _parse_zodiac_sign(123)


class TestZodiacSignField:
    """Tests for ZodiacSignField annotated type with Pydantic integration."""

    class SampleModel(BaseModel):
        sign: ZodiacSignField

    def test_parse_from_string(self) -> None:
        """Test ZodiacSignField parses string names."""
        model = self.SampleModel(sign="ARIES")
        assert model.sign == ZodiacSign.ARIES

    def test_parse_from_lowercase_string(self) -> None:
        """Test ZodiacSignField parses lowercase string names."""
        model = self.SampleModel(sign="virgo")
        assert model.sign == ZodiacSign.VIRGO

    def test_parse_from_enum(self) -> None:
        """Test ZodiacSignField accepts enum values."""
        model = self.SampleModel(sign=ZodiacSign.LEO)
        assert model.sign == ZodiacSign.LEO

    def test_serialize_by_name(self) -> None:
        """Test ZodiacSignField serializes enum by name."""
        model = self.SampleModel(sign=ZodiacSign.VIRGO)
        assert model.model_dump()["sign"] == "VIRGO"

    def test_serialize_to_json(self) -> None:
        """Test ZodiacSignField serializes to JSON string."""
        model = self.SampleModel(sign=ZodiacSign.PISCES)
        json_str = model.model_dump_json()
        assert '"sign":"PISCES"' in json_str

    def test_invalid_string_raises_error(self) -> None:
        """Test invalid string raises validation error."""
        with pytest.raises(ValidationError):
            self.SampleModel(sign="INVALID")
