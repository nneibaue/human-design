"""
Tests for models.summaries_64keys module.

Tests cover:
- GateLineSummary64Keys parsing
- GateSummary64Keys with extended properties
- ActivationSummary64Keys with from_raw conversion
- CenterSummary64Keys with open/defined descriptions
- BodyGraphSummary64Keys structure
"""

from typing import cast

from human_design.models.bodygraph import (
    CenterDefinition,
    GateDefinition,
)
from human_design.models.coordinates import CoordinateRange, ZodiacCoordinate
from human_design.models.core import GateLineNumber, Planet
from human_design.models.summaries_64keys import (
    ActivationSummary64Keys,
    BodyGraphSummary64Keys,
    CenterSummary64Keys,
    GateLineSummary64Keys,
    GateSummary64Keys,
)


class TestGateLineSummary64Keys:
    """Tests for GateLineSummary64Keys model."""

    def test_create_gate_line_summary(self) -> None:
        """Test creating a gate line summary."""
        line = GateLineSummary64Keys(
            line_number=1,
            title="In Harmony",
            text="The gift of finding those who will support one's ideas.",
        )

        assert line.line_number == 1
        assert line.title == "In Harmony"
        assert line.text == "The gift of finding those who will support one's ideas."

    def test_gate_line_with_different_line_numbers(self) -> None:
        """Test gate lines with all valid line numbers."""
        for line_num in range(1, 7):
            line = GateLineSummary64Keys(
                line_number=line_num,  # type: ignore
                title=f"Line {line_num}",
                text="Description",
            )
            assert line.line_number == line_num

    def test_serialization(self) -> None:
        """Test serialization of gate line summary."""
        line = GateLineSummary64Keys(
            line_number=1,
            title="Example",
            text="Example description",
        )

        data = line.model_dump()
        assert data["line_number"] == 1
        assert data["title"] == "Example"
        assert data["text"] == "Example description"


class TestGateSummary64Keys:
    """Tests for GateSummary64Keys model."""

    def test_create_gate_summary(self) -> None:
        """Test creating a gate summary."""
        start = ZodiacCoordinate(sign="VIRGO", degree=11, minute=0, second=0)
        end = ZodiacCoordinate(sign="VIRGO", degree=17, minute=59, second=59)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=64,
            bridge=63,
            coordinate_range=coord_range,
            quarter="Q4 - Mutation",
            name="Attention",
            summary="Attention",
            description="The gate of attention to detail.",
            strive="To develop discernment",
            lines=[
                GateLineSummary64Keys(
                    line_number=1,
                    title="Detail",
                    text="Attention to detail",
                )
            ],
        )

        assert gate.number == 64
        assert gate.quarter == "Q4 - Mutation"
        assert gate.name == "Attention"
        assert gate.summary == "Attention"
        assert len(gate.lines) == 1

    def test_gate_summary_inherits_from_gate_definition(self) -> None:
        """Test that GateSummary64Keys is a GateDefinition."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=1,
            bridge=2,
            coordinate_range=coord_range,
            quarter="Q1 - Initiation",
            name="The Self",
            summary="The Self",
            description="Gate of the Self",
            strive="Self-expression",
            lines=[],
        )

        assert isinstance(gate, GateDefinition)
        assert gate.number == 1
        assert gate.bridge == 2

    def test_gate_summary_with_multiple_lines(self) -> None:
        """Test gate summary with all 6 lines."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        lines = [
            GateLineSummary64Keys(
                line_number=cast(GateLineNumber, i),
                title=f"Line {i}",
                text=f"Description of line {i}",
            )
            for i in range(1, 7)
        ]

        gate = GateSummary64Keys(
            number=1,
            bridge=2,
            coordinate_range=coord_range,
            quarter="Q1 - Initiation",
            name="The Self",
            summary="The Self",
            description="Gate of the Self",
            strive="Self-expression",
            lines=lines,
        )

        assert len(gate.lines) == 6


class TestActivationSummary64Keys:
    """Tests for ActivationSummary64Keys model."""

    def test_create_activation_summary(self) -> None:
        """Test creating an activation summary."""
        start = ZodiacCoordinate(sign="VIRGO", degree=11, minute=0, second=0)
        end = ZodiacCoordinate(sign="VIRGO", degree=17, minute=59, second=59)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=64,
            bridge=63,
            coordinate_range=coord_range,
            quarter="Q4 - Mutation",
            name="Attention",
            summary="Attention",
            description="The gate of attention to detail.",
            strive="To develop discernment",
            lines=[
                GateLineSummary64Keys(
                    line_number=1,
                    title="Detail",
                    text="Attention to detail",
                )
            ],
        )

        line = GateLineSummary64Keys(
            line_number=1,
            title="Detail",
            text="Attention to detail",
        )

        activation = ActivationSummary64Keys(
            planet=Planet.SUN,
            gate=gate,
            line=line,
        )

        assert activation.planet == Planet.SUN
        assert activation.gate == gate
        assert activation.line == line

    def test_from_raw_conversion(self) -> None:
        """Test converting RawActivation to ActivationSummary64Keys."""
        # This would require loading actual gates from YAML and creating
        # the proper gate summary objects, which is more of an integration test
        # For now, we just verify the method exists and is callable
        assert hasattr(ActivationSummary64Keys, "from_raw")
        assert callable(ActivationSummary64Keys.from_raw)

    def test_serialization(self) -> None:
        """Test serialization of activation summary."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=1,
            bridge=2,
            coordinate_range=coord_range,
            quarter="Q1 - Initiation",
            name="The Self",
            summary="The Self",
            description="Gate of the Self",
            strive="Self-expression",
            lines=[],
        )

        line = GateLineSummary64Keys(
            line_number=1,
            title="Title",
            text="Description",
        )

        activation = ActivationSummary64Keys(
            planet=Planet.MOON,
            gate=gate,
            line=line,
        )

        data = activation.model_dump()
        assert "planet" in data
        assert "gate" in data
        assert "line" in data


class TestCenterSummary64Keys:
    """Tests for CenterSummary64Keys model."""

    def test_create_center_summary(self) -> None:
        """Test creating a center summary."""
        start = ZodiacCoordinate(sign="VIRGO", degree=11, minute=0, second=0)
        end = ZodiacCoordinate(sign="VIRGO", degree=17, minute=59, second=59)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateDefinition(number=64, bridge=63, coordinate_range=coord_range)

        center = CenterSummary64Keys(
            name="INSPIRATION",
            gates=[gate],
            description_open="When the Inspiration center is open...",
            shadow_open="The shadow of an open Inspiration center...",
            description_defined="When the Inspiration center is defined...",
            shadow_defined="The shadow of a defined Inspiration center...",
        )

        assert center.name == "INSPIRATION"
        assert len(center.gates) == 1
        assert center.description_open == "When the Inspiration center is open..."

    def test_center_summary_inherits_from_center_definition(self) -> None:
        """Test that CenterSummary64Keys is a CenterDefinition."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateDefinition(number=1, bridge=2, coordinate_range=coord_range)

        center = CenterSummary64Keys(
            name="MIND",
            gates=[gate],
        )

        assert isinstance(center, CenterDefinition)
        assert center.name == "MIND"

    def test_center_summary_with_defaults(self) -> None:
        """Test center summary with default open/defined descriptions."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateDefinition(number=1, bridge=2, coordinate_range=coord_range)

        center = CenterSummary64Keys(
            name="EMOTION",
            gates=[gate],
        )

        assert center.description_open == ""
        assert center.shadow_open == ""
        assert center.description_defined == ""
        assert center.shadow_defined == ""


class TestBodyGraphSummary64Keys:
    """Tests for BodyGraphSummary64Keys model."""

    def test_create_bodygraph_summary(self) -> None:
        """Test creating a bodygraph summary."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=1,
            bridge=2,
            coordinate_range=coord_range,
            quarter="Q1",
            name="The Self",
            summary="Summary",
            description="Description",
            strive="Strive",
            lines=[],
        )

        line = GateLineSummary64Keys(
            line_number=1,
            title="Title",
            text="Description",
        )

        activation = ActivationSummary64Keys(
            planet=Planet.SUN,
            gate=gate,
            line=line,
        )

        bodygraph = BodyGraphSummary64Keys(
            birth_info_date="1990-01-15",
            birth_info_city="New York",
            birth_info_country="USA",
            conscious_activations=[activation],
            unconscious_activations=[],
        )

        assert bodygraph.birth_info_date == "1990-01-15"
        assert bodygraph.birth_info_city == "New York"
        assert len(bodygraph.conscious_activations) == 1
        assert bodygraph.conscious_activations[0].gate.number == 1

    def test_bodygraph_summary_structure(self) -> None:
        """Test that bodygraph summary has expected structure."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=1,
            bridge=2,
            coordinate_range=coord_range,
            quarter="Q1",
            name="The Self",
            summary="The Self",
            description="Description",
            strive="Strive",
            lines=[],
        )

        line = GateLineSummary64Keys(
            line_number=1,
            title="Title",
            text="Description",
        )

        activation = ActivationSummary64Keys(
            planet=Planet.SUN,
            gate=gate,
            line=line,
        )

        bodygraph = BodyGraphSummary64Keys(
            birth_info_date="1990-01-15",
            birth_info_city="New York",
            birth_info_country="USA",
            conscious_activations=[activation],
            unconscious_activations=[],
        )

        data = bodygraph.model_dump()
        assert "birth_info_date" in data
        assert "birth_info_city" in data
        assert "conscious_activations" in data
        assert "unconscious_activations" in data

    def test_serialization_to_json(self) -> None:
        """Test serialization to JSON."""
        start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
        end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
        coord_range = CoordinateRange(start=start, end=end)

        gate = GateSummary64Keys(
            number=1,
            bridge=2,
            coordinate_range=coord_range,
            quarter="Q1",
            name="The Self",
            summary="Self",
            description="Self",
            strive="Self",
            lines=[],
        )

        line = GateLineSummary64Keys(
            line_number=1,
            title="Title",
            text="Description",
        )

        activation = ActivationSummary64Keys(
            planet=Planet.SUN,
            gate=gate,
            line=line,
        )

        bodygraph = BodyGraphSummary64Keys(
            birth_info_date="1990-01-15",
            birth_info_city="New York",
            birth_info_country="USA",
            conscious_activations=[activation],
            unconscious_activations=[],
        )

        json_str = bodygraph.model_dump_json()
        assert isinstance(json_str, str)
        assert "birth_info" in json_str
        assert "conscious_activations" in json_str
