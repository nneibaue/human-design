"""
64keys.com augmented summary models for Human Design.

These models extend the raw bodygraph models with rich content from 64keys.com,
including detailed descriptions, interpretations, and guidance text.

To convert a RawBodyGraph to these summary models, use the GateAPI methods.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from .bodygraph import CenterDefinition, GateDefinition, RawActivation
from .core import GateLineNumber, PlanetField


class GateLineSummary64Keys(BaseModel):
    """
    A single line (1-6) within a Gate, with 64keys content.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "line_number": 1,
                "title": "In harmony",
                "text": "The gift of finding those who will support one's ideas.",
            }
        }
    )

    line_number: GateLineNumber = Field(..., description="The line number (1-6)")
    title: str = Field(..., description="The line title/archetype")
    text: str = Field(..., description="The descriptive text for this line")


class GateSummary64Keys(GateDefinition):
    """
    Complete Gate definition with 64keys.com content.

    Extends GateDefinition with rich descriptions, summary, and line details.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "number": 11,
                "bridge": 56,
                "quarter": "Q4 - Mutation",
                "summary": "Ideas that can lead to peace and harmony",
                "description": "Gate 11 is the Gate of Ideas...",
                "strive": "Strive to share ideas at the right time...",
            }
        }
    )

    quarter: str = Field(
        ..., description="The Quarter this Gate belongs to (e.g., 'Q4 - Mutation')"
    )
    name: str = Field(..., description="The Gate name/title")
    summary: str = Field(..., description="One-line summary of the Gate's essence")
    description: str = Field(
        ..., description="Detailed description of the Gate's potential and meaning"
    )
    strive: str = Field(default="", description="What to strive for when expressing this Gate")
    lines: list[GateLineSummary64Keys] = Field(
        default_factory=list, description="The six lines of the Gate, each with its own expression"
    )

    def get_line(self, line_number: GateLineNumber) -> GateLineSummary64Keys | None:
        """Find a line by its number."""
        for line in self.lines:
            if line.line_number == line_number:
                return line
        return None


class ActivationSummary64Keys(BaseModel):
    """
    A planetary activation with full 64keys content.

    Combines the raw activation (planet + gate + line) with the rich
    gate and line descriptions from 64keys.com.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "planet": "SUN",
                "gate": {"number": 4, "name": "Formulae", "summary": "Answers to life's questions"},
                "line": {"line_number": 3, "title": "Irresponsibility", "text": "..."},
            }
        }
    )

    planet: PlanetField = Field(..., description="The planet")
    gate: GateSummary64Keys = Field(..., description="Full gate summary")
    line: GateLineSummary64Keys = Field(..., description="The activated line summary")

    @property
    def gate_line(self) -> str:
        """Gate.line representation (e.g., '4.3')."""
        return f"{self.gate.number}.{self.line.line_number}"

    @classmethod
    def from_raw(
        cls,
        raw: RawActivation,
        gate_summary: GateSummary64Keys,
    ) -> Self:
        """
        Create an ActivationSummary64Keys from a raw activation and gate summary.

        Args:
            raw: The raw activation with planet, gate number, and line number
            gate_summary: The full gate summary from 64keys

        Returns:
            ActivationSummary64Keys with full content

        Raises:
            ValueError: If the line is not found in the gate summary
        """
        line = gate_summary.get_line(raw.line)
        if line is None:
            raise ValueError(f"Line {raw.line} not found in gate {raw.gate} summary")

        return cls(planet=raw.planet, gate=gate_summary, line=line)


class CenterSummary64Keys(CenterDefinition):
    """
    Center definition with 64keys.com content.

    Includes descriptions for both open (undefined) and defined states.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "EMOTION",
                "gates": [],
                "description_open": "Owing to my open Emotion Center...",
                "shadow_open": "My open Emotion Center can cause me...",
                "description_defined": "I can rely on my defined Emotion...",
                "shadow_defined": "My defined Emotion can make me...",
            }
        }
    )

    description_open: str = Field(
        default="", description="Description/Potential for the open (undefined) state"
    )
    shadow_open: str = Field(default="", description="Shadow side for the open (undefined) state")
    description_defined: str = Field(
        default="", description="Description/Potential for the defined state"
    )
    shadow_defined: str = Field(default="", description="Shadow side for the defined state")


class BodyGraphSummary64Keys(BaseModel):
    """
    Complete bodygraph with full 64keys.com content.

    Contains all planetary activations for both personality and design,
    each with rich gate and line descriptions from 64keys.com.
    """

    model_config = ConfigDict(
        json_schema_extra={"description": "Complete bodygraph summary with 64keys content"}
    )

    # The original birth info for reference
    birth_info_date: str = Field(..., description="Birth date (YYYY-MM-DD)")
    birth_info_city: str = Field(..., description="Birth city")
    birth_info_country: str = Field(..., description="Birth country")

    # Conscious (personality) activations with full content
    conscious_activations: list[ActivationSummary64Keys] = Field(
        default_factory=list,
        description="Personality (birth moment) activations with full summaries",
    )

    # Unconscious (design) activations with full content
    unconscious_activations: list[ActivationSummary64Keys] = Field(
        default_factory=list, description="Design (88° earlier) activations with full summaries"
    )
