"""Bodygraph SVG renderer with parameterized geometry.

Based on analysis of 64keys bodygraph structure from bg_example.html:
- ViewBox: 0 0 355 480
- Centers positioned in fixed locations
- Gates are 3px wide rectangles
- Gates positioned along channel paths between centers
- No separate channel lines (gates ARE the visual channels)
"""

import math
from typing import Any


# Default 64keys-compatible viewBox
DEFAULT_VIEWBOX = "0 0 355 480"

# Center coordinates in 64keys coordinate system (after transforms)
# These are approximate positions extracted from bg_example.html
CENTER_POSITIONS_64KEYS = {
    "INSPIRATION": (177, 60),    # Head
    "MIND": (177, 105),           # Ajna
    "EXPRESSION": (177, 150),     # Throat
    "IDENTITY": (177, 240),       # G-Center
    "WILLPOWER": (130, 210),      # Ego/Heart (left of center)
    "EMOTION": (230, 290),        # Solar Plexus (right side)
    "LIFEFORCE": (177, 290),      # Sacral
    "INTUITION": (120, 290),      # Spleen (left side)
    "DRIVE": (177, 370),          # Root
}

# Center shapes (simplified - can be enhanced)
CENTER_SHAPES = {
    "LIFEFORCE": "square",
    "EMOTION": "triangle",
    "INTUITION": "triangle",
    "IDENTITY": "diamond",
    "WILLPOWER": "triangle",
    "DRIVE": "square",
    "EXPRESSION": "square",
    "MIND": "triangle",
    "INSPIRATION": "triangle",
}

# Default colors matching Rebecca Energy aesthetic
DEFAULT_COLORS = {
    "defined_center": "#8B4513",      # Saddle brown
    "undefined_center": "#FFFFFF",    # White
    "conscious_gate": "#4A5D23",      # Dark olive green
    "unconscious_gate": "#8B0000",    # Dark red
    "background": "#FFFFFF",          # White
    "stroke": "#333333",              # Dark gray
}


def render_center_shape(shape: str, size: int = 30) -> str:
    """Generate SVG path for center shape.

    Args:
        shape: Shape name (square, triangle, diamond)
        size: Size in pixels

    Returns:
        SVG path data string
    """
    half = size / 2

    if shape == "square":
        return f"M {-half} {-half} h {size} v {size} h {-size} Z"
    elif shape == "triangle":
        return f"M 0 {-half} L {half} {half} L {-half} {half} Z"
    elif shape == "diamond":
        return f"M 0 {-half} L {half} 0 L 0 {half} L {-half} 0 Z"
    else:
        return ""


def calculate_gate_position(
    from_center: tuple[float, float],
    to_center: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    """Calculate gate position along channel path.

    Args:
        from_center: (x, y) of source center
        to_center: (x, y) of target center
        t: Position along path (0.0 = from, 1.0 = to)

    Returns:
        (x, y) position for gate
    """
    x = from_center[0] + t * (to_center[0] - from_center[0])
    y = from_center[1] + t * (to_center[1] - from_center[1])
    return (x, y)


def calculate_gate_rotation(
    from_center: tuple[float, float],
    to_center: tuple[float, float],
) -> float:
    """Calculate rotation angle for gate to align with channel.

    Args:
        from_center: (x, y) of source center
        to_center: (x, y) of target center

    Returns:
        Rotation angle in degrees
    """
    dx = to_center[0] - from_center[0]
    dy = to_center[1] - from_center[1]
    angle_rad = math.atan2(dy, dx)
    return math.degrees(angle_rad)


def render_bodygraph(
    centers: list[dict[str, Any]],
    channels: list[dict[str, Any]],
    gates: list[dict[str, Any]],
    *,
    viewBox: str = DEFAULT_VIEWBOX,
    colors: dict[str, str] | None = None,
    center_size: int = 30,
    gate_width: int = 3,
    gate_height: int = 20,
    center_positions: dict[str, tuple[float, float]] | None = None,
) -> str:
    """Render bodygraph as SVG string.

    Args:
        centers: List of center dicts with keys: name, defined
        channels: List of channel dicts with keys: gate_a, gate_b, from_center, to_center
        gates: List of gate dicts with keys: number, activation
        viewBox: SVG viewBox attribute (default: 64keys compatible)
        colors: Color scheme dict (default: Rebecca Energy)
        center_size: Size of center shapes in pixels
        gate_width: Width of gate rectangles
        gate_height: Height of gate rectangles
        center_positions: Custom center positions (default: 64keys layout)

    Returns:
        Complete SVG string
    """
    # Use defaults if not provided
    if colors is None:
        colors = DEFAULT_COLORS
    if center_positions is None:
        center_positions = CENTER_POSITIONS_64KEYS

    # Build SVG parts
    svg_parts = []

    # SVG header
    svg_parts.append(f'<svg viewBox="{viewBox}" xmlns="http://www.w3.org/2000/svg">')

    # Background
    svg_parts.append(f'<rect width="100%" height="100%" fill="{colors["background"]}"/>')

    # Draw centers
    for center in centers:
        name = center["name"]
        defined = center.get("defined", False)

        if name not in center_positions:
            continue

        x, y = center_positions[name]
        shape = CENTER_SHAPES.get(name, "square")
        fill_color = colors["defined_center"] if defined else colors["undefined_center"]

        svg_parts.append(f'<g transform="translate({x}, {y})">')
        svg_parts.append(
            f'<path d="{render_center_shape(shape, center_size)}" '
            f'fill="{fill_color}" stroke="{colors["stroke"]}" stroke-width="2"/>'
        )
        svg_parts.append('</g>')

    # Draw gates (positioned along channels)
    # Build channel info lookup
    channel_info = {}
    for channel in channels:
        gate_a = channel["gate_a"]
        gate_b = channel["gate_b"]
        from_center = channel["from_center"]
        to_center = channel["to_center"]

        channel_info[gate_a] = {
            "partner": gate_b,
            "from_center": from_center,
            "to_center": to_center,
            "is_gate_a": True,
        }
        channel_info[gate_b] = {
            "partner": gate_a,
            "from_center": from_center,
            "to_center": to_center,
            "is_gate_a": False,
        }

    # Render gates
    for gate in gates:
        gate_num = gate["number"]
        activation = gate.get("activation", "conscious")

        if gate_num not in channel_info:
            continue  # Skip gates not in active channels for now

        info = channel_info[gate_num]
        from_pos = center_positions.get(info["from_center"])
        to_pos = center_positions.get(info["to_center"])

        if not from_pos or not to_pos:
            continue

        # Position gate along channel path
        # gate_a at 30% from source, gate_b at 70%
        t = 0.3 if info["is_gate_a"] else 0.7
        gate_x, gate_y = calculate_gate_position(from_pos, to_pos, t)

        # Rotate gate to align with channel
        rotation = calculate_gate_rotation(from_pos, to_pos)

        # Gate color
        gate_color = (
            colors["conscious_gate"]
            if activation == "conscious"
            else colors["unconscious_gate"]
        )

        svg_parts.append(
            f'<rect x="{gate_x - gate_width/2}" y="{gate_y - gate_height/2}" '
            f'width="{gate_width}" height="{gate_height}" '
            f'fill="{gate_color}" '
            f'transform="rotate({rotation}, {gate_x}, {gate_y})"/>'
        )

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)
