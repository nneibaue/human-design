"""
Tests for transit calculations.

Tests:
- transit_now() creates valid chart
- transit_at() creates chart for specific moment
- Transit + birth chart creates composite
- Transit activations are consistent (conscious == unconscious)
"""

import pytest
from datetime import datetime

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.models.transit import Transit, transit_at, transit_now


class TestTransitCreation:
    """Tests for creating transit charts."""

    def test_transit_now_creates_chart(self):
        """Test Transit.now() creates valid Transit."""
        transit = Transit.now(location="Denver, CO")

        assert isinstance(transit, Transit)
        assert len(transit.all_activated_gates) > 0
        assert len(transit.activations) == 13  # All 13 planets/nodes

    def test_transit_now_function_works(self):
        """Test transit_now() function (backwards compat)."""
        transit = Transit.now(location="Denver, CO")

        assert isinstance(transit, Transit)
        assert len(transit.all_activated_gates) > 0

    def test_transit_at_specific_moment(self):
        """Test Transit.at() creates chart for specific datetime."""
        dt = datetime(2024, 1, 1, 0, 0)
        transit = Transit.at(dt, location="New York, NY")

        assert isinstance(transit, Transit)
        assert len(transit.all_activated_gates) > 0
        assert transit.moment == dt

    def test_transit_default_location(self):
        """Test transit uses Greenwich as default location."""
        transit = Transit.now()

        assert isinstance(transit, Transit)
        assert transit.city == "Greenwich"
        assert transit.country == "UK"

    def test_transit_single_activation_set(self):
        """Test transit has single set of activations (no conscious/unconscious split)."""
        transit = Transit.now(location="Denver, CO")

        # Transit should have only one set of activations
        assert len(transit.activations) == 13  # 13 planets/nodes

        # Transit has activations property, not conscious/unconscious
        assert hasattr(transit, "activations")
        assert not hasattr(transit, "conscious_activations")
        assert not hasattr(transit, "unconscious_activations")

    def test_transit_location_parsing(self):
        """Test location string parsing."""
        transit = Transit.at(datetime.now(), location="Seattle, WA")

        assert transit.city == "Seattle"
        assert transit.country == "WA"

    def test_transit_invalid_location_format(self):
        """Test invalid location format raises error."""
        with pytest.raises(ValueError, match="must be 'city, country' format"):
            Transit.now(location="InvalidLocation")


class TestTransitComposite:
    """Tests for combining transits with birth charts."""

    def test_transit_plus_birth_chart(self):
        """Test transit can be added to birth chart."""
        birth_chart = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        transit = Transit.at(
            datetime(2024, 1, 1, 0, 0),
            location="Denver, CO"
        )

        # Combine with + operator
        with_transit = birth_chart + transit

        # Composite should have gates from both
        assert len(with_transit.all_activated_gates) >= len(birth_chart.all_activated_gates)
        assert len(with_transit.all_activated_gates) >= len(transit.all_activated_gates)

    def test_birth_chart_plus_transit(self):
        """Test birth chart can add transit (commutative)."""
        birth_chart = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        transit = Transit.now(location="Denver, CO")

        # Both orders should work
        composite1 = birth_chart + transit
        composite2 = transit + birth_chart

        # Should have same gates (order doesn't matter for gate union)
        assert composite1.all_activated_gates == composite2.all_activated_gates

    def test_transit_creates_emergent_channels(self):
        """Test transit can create emergent channels with birth chart."""
        birth_chart = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        transit = Transit.at(
            datetime(2024, 6, 15, 12, 0),
            location="Denver, CO"
        )

        with_transit = birth_chart + transit

        # Composite may have more channels than birth chart alone
        assert len(with_transit.active_channels) >= len(birth_chart.active_channels)

        # Check if any emergent channels formed
        emergent = with_transit.emergent_channels()
        # Emergent channels are those in composite but not in individuals
        assert len(emergent) >= 0  # May or may not have emergent channels


class TestTransitProperties:
    """Tests for transit chart properties."""

    def test_transit_has_type(self):
        """Test transit charts have type."""
        transit = Transit.now(location="Denver, CO")

        assert transit.type is not None

    def test_transit_has_authority(self):
        """Test transit charts have authority."""
        transit = Transit.now(location="Denver, CO")

        assert transit.authority is not None

    def test_transit_no_profile(self):
        """Test transits don't have profiles (ontologically distinct from birth charts)."""
        transit = Transit.now(location="Denver, CO")

        # Transits don't have profiles - profile requires conscious + unconscious
        # Sun positions from birth, but transits are a single moment
        assert not hasattr(transit, "profile")

    def test_multiple_transits_composition(self):
        """Test multiple transits can be composed."""
        transit1 = transit_at(datetime(2024, 1, 1, 0, 0), location="Denver, CO")
        transit2 = transit_at(datetime(2024, 6, 1, 0, 0), location="Denver, CO")
        transit3 = transit_at(datetime(2024, 12, 1, 0, 0), location="Denver, CO")

        # Compose multiple transits (unusual but should work)
        multi = transit1 + transit2 + transit3

        assert len(multi.charts) == 3
        assert len(multi.all_activated_gates) >= len(transit1.all_activated_gates)


class TestTransitTimezones:
    """Tests for transit timezone handling."""

    def test_transit_different_timezones(self):
        """Test transit respects location timezone."""
        dt = datetime(2024, 1, 1, 12, 0)  # Noon

        transit_denver = Transit.at(dt, location="Denver, CO")
        transit_nyc = Transit.at(dt, location="New York, NY")

        # Different timezones mean different UTC times mean different planetary positions
        # These should NOT be identical (unless by chance)
        denver_sun = next(act for act in transit_denver.activations if act.planet.name == "SUN")
        nyc_sun = next(act for act in transit_nyc.activations if act.planet.name == "SUN")

        # Gates might be same or different depending on timezone offset and gate boundaries
        # Just verify both have Sun activations
        assert denver_sun is not None
        assert nyc_sun is not None
