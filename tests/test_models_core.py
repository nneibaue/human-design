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

    @pytest.mark.parametrize(
        "sign,expected_value",
        [
            (ZodiacSign.ARIES, ("Aries", 0, 30)),
            (ZodiacSign.VIRGO, ("Virgo", 150, 180)),
            (ZodiacSign.PISCES, ("Pisces", 330, 360)),
        ],
    )
    def test_zodiac_sign_values(
        self, sign: ZodiacSign, expected_value: tuple[str, int, int]
    ) -> None:
        """Test that ZodiacSign values are tuples with name and degrees."""
        assert sign.value == expected_value

    @pytest.mark.parametrize(
        "sign,expected_name",
        [
            (ZodiacSign.ARIES, "Aries"),
            (ZodiacSign.CAPRICORN, "Capricorn"),
            (ZodiacSign.LIBRA, "Libra"),
        ],
    )
    def test_full_name_property(self, sign: ZodiacSign, expected_name: str) -> None:
        """Test full_name property returns correct human-readable names."""
        assert sign.full_name == expected_name

    @pytest.mark.parametrize(
        "sign,expected_start",
        [
            (ZodiacSign.ARIES, 0),
            (ZodiacSign.TAURUS, 30),
            (ZodiacSign.GEMINI, 60),
            (ZodiacSign.PISCES, 330),
        ],
    )
    def test_start_deg_property(self, sign: ZodiacSign, expected_start: int) -> None:
        """Test start_deg property returns correct starting degrees."""
        assert sign.start_deg == expected_start

    @pytest.mark.parametrize(
        "sign,expected_end",
        [
            (ZodiacSign.ARIES, 30),
            (ZodiacSign.TAURUS, 60),
            (ZodiacSign.PISCES, 360),
        ],
    )
    def test_end_deg_property(self, sign: ZodiacSign, expected_end: int) -> None:
        """Test end_deg property returns correct ending degrees."""
        assert sign.end_deg == expected_end

    @pytest.mark.parametrize(
        "sign,degrees,minutes,seconds,expected",
        [
            (ZodiacSign.ARIES, 15, 30, 0, 15.5),
            (ZodiacSign.VIRGO, 0, 0, 0, 150.0),
            (ZodiacSign.VIRGO, 15, 30, 36, 165.51),
        ],
    )
    def test_to_decimal_degrees(
        self,
        sign: ZodiacSign,
        degrees: float,
        minutes: float,
        seconds: float,
        expected: float,
    ) -> None:
        """Test conversion of degrees/minutes/seconds to decimal degrees."""
        result = sign.to_decimal_degrees(degrees, minutes, seconds)
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize(
        "sign_name,expected_sign",
        [
            ("ARIES", ZodiacSign.ARIES),
            ("VIRGO", ZodiacSign.VIRGO),
            ("PISCES", ZodiacSign.PISCES),
        ],
    )
    def test_zodiac_sign_by_name(self, sign_name: str, expected_sign: ZodiacSign) -> None:
        """Test accessing ZodiacSign enum members by name."""
        assert ZodiacSign[sign_name] == expected_sign


class TestZodiacSignParsing:
    """Tests for _parse_zodiac_sign validation function."""

    @pytest.mark.parametrize(
        "input_str,expected_sign",
        [
            ("ARIES", ZodiacSign.ARIES),
            ("virgo", ZodiacSign.VIRGO),
            ("Capricorn", ZodiacSign.CAPRICORN),
        ],
    )
    def test_parse_zodiac_sign_from_string(self, input_str: str, expected_sign: ZodiacSign) -> None:
        """Test parsing ZodiacSign from string name."""
        result = _parse_zodiac_sign(input_str)
        assert result == expected_sign

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

    @pytest.mark.parametrize(
        "input_value,expected_sign",
        [
            ("ARIES", ZodiacSign.ARIES),
            ("virgo", ZodiacSign.VIRGO),
            (ZodiacSign.LEO, ZodiacSign.LEO),
        ],
    )
    def test_parse_string_and_enum(
        self, input_value: str | ZodiacSign, expected_sign: ZodiacSign
    ) -> None:
        """Test ZodiacSignField parses strings (case-insensitive) and enum values."""
        model = self.SampleModel(sign=input_value)  # type: ignore
        assert model.sign == expected_sign

    @pytest.mark.parametrize(
        "sign,expected_serialized",
        [
            (ZodiacSign.VIRGO, "VIRGO"),
            (ZodiacSign.PISCES, "PISCES"),
            (ZodiacSign.ARIES, "ARIES"),
        ],
    )
    def test_serialize_by_name(self, sign: ZodiacSign, expected_serialized: str) -> None:
        """Test ZodiacSignField serializes enum by name."""
        model = self.SampleModel(sign=sign)
        assert model.model_dump()["sign"] == expected_serialized

    def test_serialize_to_json(self) -> None:
        """Test ZodiacSignField serializes to JSON string."""
        model = self.SampleModel(sign=ZodiacSign.PISCES)
        json_str = model.model_dump_json()
        assert '"sign":"PISCES"' in json_str

    def test_invalid_string_raises_error(self) -> None:
        """Test invalid string raises validation error."""
        with pytest.raises(ValidationError):
            self.SampleModel(sign="INVALID")  # type: ignore
