"""Bodygraph rendering endpoint for production API."""

from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import HTTPException, Query
from pydantic import BaseModel

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.renderers.svg_generator_simple import generate_bodygraph_svg


class BodygraphResponse(BaseModel):
    """Response model for bodygraph endpoint."""

    svg: str
    type: str
    authority: str
    profile: str
    defined_centers: list[str]
    active_channels: list[tuple[int, int]]


def calculate_and_render_bodygraph(
    date: Annotated[str, Query(description="Birth date (YYYY-MM-DD)")],
    time: Annotated[str, Query(description="Birth time (HH:MM)")],
    city: Annotated[str, Query(description="City name")],
    country: Annotated[str, Query(description="Country or state code")],
) -> BodygraphResponse:
    """Calculate bodygraph and render as SVG.

    Args:
        date: Birth date in YYYY-MM-DD format
        time: Birth time in HH:MM format (24-hour)
        city: City of birth
        country: Country or state code (e.g., "NM", "CA", "TX")

    Returns:
        BodygraphResponse with SVG and metadata

    Raises:
        HTTPException: If calculation fails or invalid input
    """
    try:
        # Parse date and time
        date_parts = date.split("-")
        time_parts = time.split(":")

        if len(date_parts) != 3 or len(time_parts) != 2:
            raise ValueError("Invalid date or time format")

        year, month, day = map(int, date_parts)
        hour, minute = map(int, time_parts)

        # Create birth info
        birth_datetime = datetime(year, month, day, hour, minute)
        birth_info = BirthInfo(
            date=date,
            localtime=LocalTime(birth_datetime),
            city=city,
            country=country,
        )

        # Calculate bodygraph
        bodygraph = RawBodyGraph(birth_info=birth_info)

        # Extract data for SVG generator
        bodygraph_data = {
            "defined_centers": bodygraph.defined_centers,
            "active_channels": [(ch.gate_a, ch.gate_b) for ch in bodygraph.active_channels],
            "conscious_gates": [act.gate for act in bodygraph.conscious_activations],
            "unconscious_gates": [act.gate for act in bodygraph.unconscious_activations],
        }

        # Render SVG
        svg_content = generate_bodygraph_svg(bodygraph_data)

        # Build response
        return BodygraphResponse(
            svg=svg_content,
            type=bodygraph.type.value,
            authority=bodygraph.authority.value,
            profile=str(bodygraph.profile),
            defined_centers=list(bodygraph.defined_centers),
            active_channels=[
                (ch.gate_a, ch.gate_b) for ch in bodygraph.active_channels
            ],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Template not found: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Bodygraph calculation failed: {e}"
        )
