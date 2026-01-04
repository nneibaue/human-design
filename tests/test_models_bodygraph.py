"""
Tests for models.bodygraph module.

Tests cover:
- GateDefinition parsing and validation
- CenterDefinition with gates
- BodyGraphDefinition YAML loading and gate lookup
- RawActivation creation
- BirthInfo validation and computed fields
- RawBodyGraph calculation of activations
"""

from datetime import datetime

import pytest

from human_design.models.bodygraph import (
    BirthInfo,
    BodyGraphDefinition,
    CenterDefinition,
    GateDefinition,
    RawActivation,
    RawBodyGraph,
)
from human_design.models.coordinates import LocalTime, ZodiacCoordinate
from human_design.models.core import Planet


class TestGateDefinition:
    """Tests for GateDefinition model."""

    def test_create_gate_definition(self) -> None:
        """Test creating a gate definition."""
        start = ZodiacCoordinate(sign="VIRGO", degree=11, minute=0, second=0)
        end = ZodiacCoordinate(sign="VIRGO", degree=17, minute=59, second=59)
        from human_design.models.coordinates import CoordinateRange

        coord_range = CoordinateRange(start=start, end=end)
        gate = GateDefinition(number=64, bridge=63, coordinate_range=coord_range)

        assert gate.number == 64
        assert gate.bridge == 63
        assert gate.coordinate_range == coord_range

    def test_gate_with_list_bridge(self) -> None:
        """Test gate with multiple bridge values."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        from human_design.models.coordinates import CoordinateRange

        coord_range = CoordinateRange(start=start, end=end)
        gate = GateDefinition(number=1, bridge=[2, 3], coordinate_range=coord_range)

        assert gate.number == 1
        assert gate.bridge == [2, 3]


class TestCenterDefinition:
    """Tests for CenterDefinition model."""

    def test_create_center_definition(self) -> None:
        """Test creating a center definition."""
        start = ZodiacCoordinate(sign="VIRGO", degree=11, minute=0, second=0)
        end = ZodiacCoordinate(sign="VIRGO", degree=17, minute=59, second=59)
        from human_design.models.coordinates import CoordinateRange

        coord_range = CoordinateRange(start=start, end=end)
        gate = GateDefinition(number=64, bridge=63, coordinate_range=coord_range)
        center = CenterDefinition(name="INSPIRATION", gates=[gate])

        assert center.name == "INSPIRATION"
        assert len(center.gates) == 1
        assert center.gates[0].number == 64


class TestBodyGraphDefinition:
    """Tests for BodyGraphDefinition model."""

    def test_load_bodygraph_from_yaml(self) -> None:
        """Test loading bodygraph definition from YAML file."""
        bg_def = BodyGraphDefinition.load()

        assert isinstance(bg_def, BodyGraphDefinition)
        assert len(bg_def.centers) == 9
        assert all(isinstance(c, CenterDefinition) for c in bg_def.centers)

    def test_bodygraph_has_all_gates(self) -> None:
        """Test that bodygraph contains all 64 gates."""
        bg_def = BodyGraphDefinition.load()

        all_gates = list(bg_def.all_gates)
        assert len(all_gates) == 64

        # Check all gate numbers 1-64 are present
        gate_numbers = sorted([g.number for g in all_gates])
        assert gate_numbers == list(range(1, 65))

    def test_get_gate_by_number(self) -> None:
        """Test retrieving gate by number."""
        bg_def = BodyGraphDefinition.load()

        gate = bg_def.get_gate(1)
        assert gate is not None
        assert gate.number == 1

        gate = bg_def.get_gate(64)
        assert gate is not None
        assert gate.number == 64

    def test_get_nonexistent_gate(self) -> None:
        """Test that getting nonexistent gate returns None."""
        bg_def = BodyGraphDefinition.load()

        gate = bg_def.get_gate(999)
        assert gate is None

    def test_gate_and_line_from_longitude_gate_64(self) -> None:
        """Test gate and line mapping from longitude for gate 64."""
        bg_def = BodyGraphDefinition.load()

        # Gate 64 spans approximately Virgo 11° to 17°59'
        # Which is roughly 161° to 168° in absolute degrees
        lon = 164.0  # Should fall in gate 64
        gate_num, line_num = bg_def.gate_and_line_from_longitude(lon)

        assert gate_num == 64
        assert 1 <= line_num <= 6

    def test_gate_and_line_from_longitude_gate_1(self) -> None:
        """Test gate and line mapping from longitude for gate 1."""
        bg_def = BodyGraphDefinition.load()

        # Gate 1 starts around 0 degrees
        lon = 2.0  # Very early Aries
        gate_num, line_num = bg_def.gate_and_line_from_longitude(lon)

        # Just verify it returns valid gate and line numbers
        assert 1 <= gate_num <= 64
        assert 1 <= line_num <= 6

    def test_longitude_maps_to_valid_gate_and_line(self) -> None:
        """Test that any longitude maps to a valid gate and line."""
        bg_def = BodyGraphDefinition.load()

        test_longitudes = [0, 45, 90, 135, 180, 225, 270, 315, 359.9]
        for lon in test_longitudes:
            gate_num, line_num = bg_def.gate_and_line_from_longitude(lon)
            assert 1 <= gate_num <= 64
            assert 1 <= line_num <= 6


class TestRawActivation:
    """Tests for RawActivation model."""

    def test_create_raw_activation(self) -> None:
        """Test creating a raw activation."""
        activation = RawActivation(planet=Planet.SUN, gate=61, line=5)

        assert activation.planet == Planet.SUN
        assert activation.gate == 61
        assert activation.line == 5

    def test_activation_with_different_planets(self) -> None:
        """Test creating activations with different planets."""
        for planet in [Planet.SUN, Planet.MOON, Planet.MERCURY]:
            activation = RawActivation(planet=planet, gate=1, line=1)
            assert activation.planet == planet


class TestBirthInfo:
    """Tests for BirthInfo model."""

    def test_create_birth_info(self) -> None:
        """Test creating birth info."""
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )

        assert birth_info.date == "1990-01-15"
        assert birth_info.city == "New York"
        assert birth_info.country == "USA"

    def test_place_computed_field(self) -> None:
        """Test place computed field combines city and country."""
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="Paris",
            country="France",
        )

        assert birth_info.place == "Paris, France"

    def test_coordinates_computed_field(self) -> None:
        """Test coordinates computed field geocodes the place."""
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )

        lat, lon = birth_info.coordinates
        # Should be near New York coordinates
        assert 40.0 < lat < 41.0
        assert -75.0 < lon < -73.0

    def test_timezone_computed_field(self) -> None:
        """Test timezone computed field from coordinates."""
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )

        assert birth_info.timezone == "America/New_York"

    def test_birth_jd_ut_computed_field(self) -> None:
        """Test birth_jd_ut computed field calculates Julian Day."""
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )

        jd = birth_info.birth_jd_ut
        assert isinstance(jd, float)
        # Should be before J2000 epoch (2451545.0)
        assert 2447900 < jd < 2451545

    def test_design_jd_ut_computed_field(self) -> None:
        """Test design_jd_ut computed field (88 degrees earlier)."""
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )

        design_jd = birth_info.design_jd_ut
        birth_jd = birth_info.birth_jd_ut

        # Design should be before birth (negative offset in JD)
        assert design_jd < birth_jd
        # Roughly 88 days difference (but can vary slightly depending on Sun's speed)
        # Allow 80-95 day range
        jd_diff = birth_jd - design_jd
        assert 80 < jd_diff < 95

    def test_invalid_date_format_raises_error(self) -> None:
        """Test that invalid date format raises validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BirthInfo(
                date="15/01/1990",  # Wrong format
                localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
                city="New York",
                country="USA",
            )

    def test_plus_minus_options_validation(self) -> None:
        """Test that BirthInfo validates date and localtime consistency."""
        from pydantic import ValidationError

        # Valid case - date matches localtime
        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )
        assert birth_info.date == "1990-01-15"

        # Invalid case - date doesn't match localtime date
        with pytest.raises(ValidationError, match="must match localtime date"):
            BirthInfo(
                date="1990-01-14",  # Different date
                localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),  # Different date
                city="New York",
                country="USA",
            )


class TestRawBodyGraph:
    """Tests for RawBodyGraph model."""

    @pytest.fixture
    def birth_info(self) -> BirthInfo:
        """Create a standard birth info for testing."""
        return BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )

    def test_create_raw_bodygraph(self, birth_info: BirthInfo) -> None:
        """Test creating a raw bodygraph."""
        raw_bg = RawBodyGraph(birth_info=birth_info)

        assert raw_bg.birth_info == birth_info
        assert isinstance(raw_bg.conscious_activations, list)
        assert isinstance(raw_bg.unconscious_activations, list)

    def test_conscious_activations_count(self, birth_info: BirthInfo) -> None:
        """Test that conscious activations has 13 bodies (Sun, Earth, 8 planets, nodes)."""
        raw_bg = RawBodyGraph(birth_info=birth_info)

        assert len(raw_bg.conscious_activations) == 13
        assert all(isinstance(a, RawActivation) for a in raw_bg.conscious_activations)

    def test_unconscious_activations_count(self, birth_info: BirthInfo) -> None:
        """Test that unconscious activations has 13 bodies (Sun, Earth, 8 planets, nodes)."""
        raw_bg = RawBodyGraph(birth_info=birth_info)

        assert len(raw_bg.unconscious_activations) == 13
        assert all(isinstance(a, RawActivation) for a in raw_bg.unconscious_activations)

    def test_activations_have_valid_gates(self, birth_info: BirthInfo) -> None:
        """Test that all activations have valid gate and line numbers."""
        raw_bg = RawBodyGraph(birth_info=birth_info)

        for activation in raw_bg.conscious_activations:
            assert 1 <= activation.gate <= 64
            assert 1 <= activation.line <= 6

        for activation in raw_bg.unconscious_activations:
            assert 1 <= activation.gate <= 64
            assert 1 <= activation.line <= 6

    def test_different_birth_dates_produce_different_activations(self) -> None:
        """Test that different birth dates produce different activations."""
        birth_info_1 = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )
        birth_info_2 = BirthInfo(
            date="2000-06-21",
            localtime=LocalTime(datetime(2000, 6, 21, 10, 30)),
            city="New York",
            country="USA",
        )

        raw_bg_1 = RawBodyGraph(birth_info=birth_info_1)
        raw_bg_2 = RawBodyGraph(birth_info=birth_info_2)

        # At least some activations should differ
        gates_1 = [a.gate for a in raw_bg_1.conscious_activations]
        gates_2 = [a.gate for a in raw_bg_2.conscious_activations]

        assert gates_1 != gates_2

    def test_serialization(self, birth_info: BirthInfo) -> None:
        """Test that raw bodygraph can be serialized to JSON.

        Note: Serialization can be slow due to expensive astronomical calculations
        in the computed fields (conscious_activations and unconscious_activations).
        We only test JSON serialization to keep the test fast.
        """
        raw_bg = RawBodyGraph(birth_info=birth_info)

        # Test JSON serialization - should not raise
        json_str = raw_bg.model_dump_json(exclude={"birth_info": {"coordinates", "timezone"}})
        assert isinstance(json_str, str)
        assert "conscious_activations" in json_str
        assert "unconscious_activations" in json_str
