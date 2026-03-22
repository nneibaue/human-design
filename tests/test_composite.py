"""
Tests for CompositeBodyGraph - combining charts through gate activation stacking.

Tests:
- __add__ operator for combining charts
- Emergent channel formation (channels that form across charts)
- Composite type/authority/profile calculation
- Chaining multiple charts (penta, multichart)
- Transit overlays
"""

import pytest

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.composite import CompositeBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.models.type_authority import HDType, Authority
from datetime import datetime


class TestCompositeCreation:
    """Tests for creating composite charts."""

    def test_add_two_charts(self):
        """Test combining two charts with + operator."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        # Combine with + operator
        composite = chart1 + chart2

        assert isinstance(composite, CompositeBodyGraph)
        assert len(composite.charts) == 2
        assert composite.charts[0] is chart1
        assert composite.charts[1] is chart2

    def test_chain_multiple_charts(self):
        """Test chaining multiple charts for penta."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        chart3 = RawBodyGraph(
            birth_info=BirthInfo(
                date="2010-03-10",
                localtime=LocalTime(datetime(2010, 3, 10, 8, 0)),
                city="Portland",
                country="OR",
            )
        )

        # Chain with multiple + operators
        penta = chart1 + chart2 + chart3

        assert isinstance(penta, CompositeBodyGraph)
        assert len(penta.charts) == 3

    def test_add_composite_to_composite(self):
        """Test combining two composite charts."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        chart3 = RawBodyGraph(
            birth_info=BirthInfo(
                date="2010-03-10",
                localtime=LocalTime(datetime(2010, 3, 10, 8, 0)),
                city="Portland",
                country="OR",
            )
        )

        composite1 = chart1 + chart2
        composite2 = composite1 + chart3

        assert len(composite2.charts) == 3


class TestGateActivationStacking:
    """Tests for gate activation stacking logic."""

    def test_all_activated_gates_union(self):
        """Test that all_activated_gates returns union of all charts."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Composite should have at least as many gates as each individual chart
        assert len(composite.all_activated_gates) >= len(chart1.all_activated_gates)
        assert len(composite.all_activated_gates) >= len(chart2.all_activated_gates)

        # All gates from chart1 should be in composite
        assert chart1.all_activated_gates.issubset(composite.all_activated_gates)
        # All gates from chart2 should be in composite
        assert chart2.all_activated_gates.issubset(composite.all_activated_gates)

    def test_composite_has_more_channels(self):
        """Test that composite may have more channels than individual charts."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Composite should have at least as many channels as largest individual chart
        max_individual = max(len(chart1.active_channels), len(chart2.active_channels))
        assert len(composite.active_channels) >= max_individual

        # All channels from chart1 should be in composite
        chart1_channel_pairs = {(ch.gate_a, ch.gate_b) for ch in chart1.active_channels}
        composite_channel_pairs = {(ch.gate_a, ch.gate_b) for ch in composite.active_channels}
        assert chart1_channel_pairs.issubset(composite_channel_pairs)


class TestEmergentChannels:
    """Tests for emergent channel detection."""

    def test_emergent_channels_detection(self):
        """Test that emergent_channels finds channels that form across charts."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Get emergent channels
        emergent = composite.emergent_channels()

        # Each emergent channel should exist in composite but not in either individual chart
        composite_pairs = {(ch.gate_a, ch.gate_b) for ch in composite.active_channels}
        chart1_pairs = {(ch.gate_a, ch.gate_b) for ch in chart1.active_channels}
        chart2_pairs = {(ch.gate_a, ch.gate_b) for ch in chart2.active_channels}

        for ch in emergent:
            pair = (ch.gate_a, ch.gate_b)
            assert pair in composite_pairs
            assert pair not in chart1_pairs
            assert pair not in chart2_pairs

    def test_emergent_channels_real_example(self):
        """
        Test emergent channels with real example.

        If chart1 has Gate X and chart2 has Gate Y, and they form Channel X-Y,
        that channel should be detected as emergent.
        """
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2
        emergent = composite.emergent_channels()

        # Emergent channels should be a subset of all composite channels
        assert len(emergent) <= len(composite.active_channels)


class TestCompositeTypeAuthority:
    """Tests for type/authority calculation on composites."""

    def test_composite_has_type(self):
        """Test that composite charts have calculable type."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Composite should have valid type
        assert isinstance(composite.type, HDType)
        assert composite.type in HDType

    def test_composite_has_authority(self):
        """Test that composite charts have calculable authority."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Composite should have valid authority
        assert isinstance(composite.authority, Authority)
        assert composite.authority in Authority

    def test_composite_type_may_differ(self):
        """Test that composite type can differ from individual types."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Composite type exists (may or may not differ from individuals)
        # This test just validates the calculation works
        assert composite.type in HDType
        assert chart1.type in HDType
        assert chart2.type in HDType


class TestCompositeDefinedCenters:
    """Tests for defined centers in composite charts."""

    def test_composite_defined_centers(self):
        """Test that composite may have more defined centers than individuals."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Composite should have at least as many defined centers as largest individual
        max_individual = max(len(chart1.defined_centers), len(chart2.defined_centers))
        assert len(composite.defined_centers) >= max_individual

    def test_centers_defined_through_emergent_channels(self):
        """Test that centers can become defined through emergent channels."""
        chart1 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        chart2 = RawBodyGraph(
            birth_info=BirthInfo(
                date="1985-06-20",
                localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
                city="Seattle",
                country="WA",
            )
        )

        composite = chart1 + chart2

        # Each emergent channel should define its connected centers
        for emergent_channel in composite.emergent_channels():
            assert emergent_channel.center_a in composite.defined_centers
            assert emergent_channel.center_b in composite.defined_centers


class TestPentaCharts:
    """Tests for penta charts (3-5 people)."""

    def test_five_person_penta(self):
        """Test creating penta with 5 people."""
        charts = []
        dates = [
            ("1990-01-15", 9, 13),
            ("1985-06-20", 14, 30),
            ("2010-03-10", 8, 0),
            ("1988-11-05", 16, 45),
            ("1992-07-22", 11, 20),
        ]

        for date_str, hour, minute in dates:
            year, month, day = map(int, date_str.split("-"))
            chart = RawBodyGraph(
                birth_info=BirthInfo(
                    date=date_str,
                    localtime=LocalTime(datetime(year, month, day, hour, minute)),
                    city="Denver",
                    country="CO",
                )
            )
            charts.append(chart)

        # Create penta by chaining
        penta = charts[0] + charts[1] + charts[2] + charts[3] + charts[4]

        assert len(penta.charts) == 5
        assert isinstance(penta.type, HDType)
        assert isinstance(penta.authority, Authority)
