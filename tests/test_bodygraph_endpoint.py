"""Tests for bodygraph rendering endpoint."""

import pytest

from human_design.api.bodygraph_endpoint import calculate_and_render_bodygraph


def test_calculate_and_render_bodygraph():
    """Test bodygraph calculation and rendering."""
    # Nate's birth info
    result = calculate_and_render_bodygraph(
        date="1992-08-13",
        time="09:13",
        city="Albuquerque",
        country="NM",
    )

    # Check response structure
    assert result.type == "Coordinator"
    assert result.authority == "Splenic"
    assert "3/5" in result.profile

    # Check defined centers
    assert "INTUITION" in result.defined_centers
    assert "MIND" in result.defined_centers
    assert "EXPRESSION" in result.defined_centers
    assert "IDENTITY" in result.defined_centers

    # Check active channels
    assert len(result.active_channels) == 2
    channel_gates = {tuple(sorted([ch[0], ch[1]])) for ch in result.active_channels}
    assert (10, 57) in channel_gates or (57, 10) in channel_gates
    assert (23, 43) in channel_gates or (43, 23) in channel_gates

    # Check SVG content
    assert result.svg.startswith("<svg")
    assert "viewBox" in result.svg
    assert len(result.svg) > 1000  # Should be substantial SVG


def test_invalid_date_format():
    """Test with invalid date format."""
    with pytest.raises(Exception):  # Will be HTTPException in FastAPI context
        calculate_and_render_bodygraph(
            date="invalid",
            time="09:13",
            city="Albuquerque",
            country="NM",
        )


def test_invalid_time_format():
    """Test with invalid time format."""
    with pytest.raises(Exception):
        calculate_and_render_bodygraph(
            date="1992-08-13",
            time="invalid",
            city="Albuquerque",
            country="NM",
        )
