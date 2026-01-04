"""
Human Design models.

This package contains Pydantic models for Human Design calculations:

- core: Enums and type aliases (Planet, ZodiacSign, GateNumber, etc.)
- coordinates: Location and coordinate models
- bodygraph: Raw calculated bodygraph models (no 64keys content)
- summaries_64keys: 64keys.com augmented models with descriptions

Usage:
    from human_design.models import (
        # Core types
        Planet, ZodiacSign, GateNumber, GateLineNumber, CenterName,

        # Raw calculation models
        BirthInfo, RawBodyGraph, RawActivation,
        GateDefinition, CenterDefinition, BodyGraphDefinition,

        # 64keys summary models
        GateSummary64Keys, GateLineSummary64Keys,
        ActivationSummary64Keys, BodyGraphSummary64Keys,
    )
"""

# Core types
# Raw bodygraph models
from .bodygraph import (
    BirthInfo,
    BodyGraphDefinition,
    CenterDefinition,
    GateDefinition,
    RawActivation,
    RawBodyGraph,
)

# Coordinate models
from .coordinates import (
    CoordinateRange,
    GeographicalCoordinate,
    LocalTime,
    Location,
    ZodiacCoordinate,
)
from .core import (
    CenterName,
    GateLineNumber,
    GateNumber,
    Planet,
    ZodiacSign,
    ZodiacSignField,
)

# 64keys summary models
from .summaries_64keys import (
    ActivationSummary64Keys,
    BodyGraphSummary64Keys,
    CenterSummary64Keys,
    GateLineSummary64Keys,
    GateSummary64Keys,
)

__all__ = [
    # Core
    "CenterName",
    "GateLineNumber",
    "GateNumber",
    "Planet",
    "ZodiacSign",
    "ZodiacSignField",
    # Coordinates
    "CoordinateRange",
    "GeographicalCoordinate",
    "LocalTime",
    "Location",
    "ZodiacCoordinate",
    # Raw bodygraph
    "BirthInfo",
    "BodyGraphDefinition",
    "CenterDefinition",
    "GateDefinition",
    "RawActivation",
    "RawBodyGraph",
    # 64keys summaries
    "ActivationSummary64Keys",
    "BodyGraphSummary64Keys",
    "CenterSummary64Keys",
    "GateLineSummary64Keys",
    "GateSummary64Keys",
]
