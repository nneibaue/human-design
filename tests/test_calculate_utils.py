"""
Tests for calculate_utils module.

Tests cover:
- Planetary longitude calculations
- Geocoding with caching
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import swisseph as swe  # type: ignore

from human_design.calculate_utils import calc_lon_ut, geocode_place


class TestPlanetaryCalculations:
    """Tests for planetary longitude calculations."""

    @pytest.mark.parametrize(
        "body",
        [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS],
    )
    def test_calc_lon_ut_range(self, body: int) -> None:
        """Test that calculated longitude is in [0, 360) for all planets."""
        jd = 2451545.0  # J2000 epoch
        lon, speed = calc_lon_ut(jd, body)
        assert 0.0 <= lon < 360.0
        # Speed is in degrees/day, wider range to account for different planets
        assert -20.0 < speed < 20.0

    def test_calc_lon_ut_sun_at_epoch(self) -> None:
        """Test Sun's longitude at J2000 epoch."""
        jd = 2451545.0
        lon, speed = calc_lon_ut(jd, swe.SUN)
        # Sun is near Capricorn at J2000 (around 280-281°)
        assert 275.0 < lon < 285.0


class TestGeocoding:
    """Tests for geocoding functionality."""

    def test_geocode_caching(self) -> None:
        """Test that geocode results are cached to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cache_path = f.name

        try:
            # First call should hit the API
            with patch("geopy.geocoders.ArcGIS") as mock_arcgis:
                mock_loc = Mock()
                mock_loc.latitude = 40.7128
                mock_loc.longitude = -74.0060
                mock_arcgis.return_value.geocode.return_value = mock_loc

                lat, lon = geocode_place("New York, USA", cache_path=cache_path)
                assert lat == pytest.approx(40.7128)
                assert lon == pytest.approx(-74.0060)

                # Second call should use cache (not hit API again)
                mock_arcgis.return_value.geocode.reset_mock()
                lat2, lon2 = geocode_place("New York, USA", cache_path=cache_path)
                mock_arcgis.return_value.geocode.assert_not_called()
                assert lat2 == lat
                assert lon2 == lon

        finally:
            if os.path.exists(cache_path):
                os.unlink(cache_path)

    def test_geocode_failure(self) -> None:
        """Test geocoding failure raises RuntimeError."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cache_path = f.name

        try:
            with patch("geopy.geocoders.ArcGIS") as mock_arcgis:
                mock_arcgis.return_value.geocode.return_value = None

                with pytest.raises(RuntimeError, match="Could not geocode"):
                    geocode_place("Nonexistent Place XYZ123", cache_path=cache_path)
        finally:
            if os.path.exists(cache_path):
                os.unlink(cache_path)
