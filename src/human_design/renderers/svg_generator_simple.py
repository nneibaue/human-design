"""Simple bodygraph SVG generator - minimal working version."""

from typing import Any


def generate_bodygraph_svg(bodygraph_data: dict[str, Any]) -> str:
    """Generate basic bodygraph SVG.

    This is a minimal version that shows centers and basic structure.
    Gate positioning and channels are placeholders for now.

    Args:
        bodygraph_data: Dict with defined_centers, active_channels, conscious_gates, unconscious_gates

    Returns:
        SVG string
    """
    defined_centers = bodygraph_data.get("defined_centers", set())

    # Simple center positions (approximate)
    centers = {
        "INSPIRATION": {"x": 177.5, "y": 200, "label": "HEAD"},
        "MIND": {"x": 177.5, "y": 240, "label": "AJNA"},
        "EXPRESSION": {"x": 177.5, "y": 320, "label": "THROAT"},
        "IDENTITY": {"x": 177.5, "y": 400, "label": "G"},
        "LIFEFORCE": {"x": 240, "y": 400, "label": "SACRAL"},
        "INTUITION": {"x": 115, "y": 400, "label": "SPLEEN"},
        "WILLPOWER": {"x": 177.5, "y": 340, "label": "EGO"},
        "EMOTION": {"x": 240, "y": 450, "label": "SOLAR PL"},
        "DRIVE": {"x": 177.5, "y": 480, "label": "ROOT"},
    }

    svg_parts = [
        '<svg viewBox="0 0 355 550" xmlns="http://www.w3.org/2000/svg" style="background: white;">',
        '<g id="centers">',
    ]

    # Draw centers
    for center_name, pos in centers.items():
        is_defined = center_name in defined_centers
        fill = "#8B4513" if is_defined else "#FFFFFF"
        stroke = "#8B4513"

        svg_parts.append(
            f'<rect x="{pos["x"]-15}" y="{pos["y"]-15}" width="30" height="30" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" rx="4"/>'
        )
        svg_parts.append(
            f'<text x="{pos["x"]}" y="{pos["y"]+5}" text-anchor="middle" '
            f'font-family="Arial" font-size="10" fill="{stroke}">{pos["label"]}</text>'
        )

    svg_parts.append('</g>')
    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)
