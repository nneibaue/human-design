"""
Human Design Python Package

A toolkit for learning and working with Human Design using data from 64keys.com.

Core workflow:
1. Create a BirthInfo with date, time, city, country
2. Create a RawBodyGraph from the birth info (calculates all activations)
3. Convert to BodyGraphSummary64Keys via the API for full content
"""

from .api import GateAPI, bodygraph_to_summary, get_gate, get_gates, get_home_page
from .models import (
    ActivationSummary64Keys,
    # Raw calculation models
    BirthInfo,
    BodyGraphDefinition,
    BodyGraphSummary64Keys,
    CenterDefinition,
    CenterName,
    GateDefinition,
    GateLineNumber,
    GateLineSummary64Keys,
    GateNumber,
    # 64keys summary models
    GateSummary64Keys,
    # Core types
    Planet,
    RawActivation,
    RawBodyGraph,
    ZodiacSign,
)

__version__ = "0.1.0"

__all__ = [
    # Core types
    "Planet",
    "ZodiacSign",
    "GateNumber",
    "GateLineNumber",
    "CenterName",
    # Raw models
    "BirthInfo",
    "RawBodyGraph",
    "RawActivation",
    "GateDefinition",
    "CenterDefinition",
    "BodyGraphDefinition",
    # 64keys models
    "GateSummary64Keys",
    "GateLineSummary64Keys",
    "ActivationSummary64Keys",
    "BodyGraphSummary64Keys",
    # API
    "GateAPI",
    "get_gate",
    "get_gates",
    "bodygraph_to_summary",
    "get_home_page",
]
