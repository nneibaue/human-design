"""Generate bodygraph SVG from scratch using extracted 64keys geometry."""

from typing import Any


# Center positions and shapes (extracted from bg_example.html scaled coordinates)
CENTERS = {
    "DRIVE": {  # center_1 - square at bottom
        "shape": "rect",
        "x": 191.3, "y": 410.9, "width": 26.4, "height": 26.4,
        "rx": 4.0,
        "label": "DRIVE", "label_offset": (13, 16)
    },
    "EXPRESSION": {  # center_2 - square at throat
        "shape": "rect",
        "x": 191.3, "y": 373.5, "width": 26.4, "height": 26.4,
        "rx": 4.0,
        "label": "THROAT", "label_offset": (13, 16)
    },
    "INTUITION": {  # center_3 - triangle pointing right
        "shape": "path",
        "d": "m132.69,394.44c.50,0,.94,-.11,1.34,-.34l24.06,-13.99c.67,-.49,1.09,-1.26,1.09,-2.16 0,-.93-.47,-1.76,-1.19,-2.25l-23.67,-13.82c-.41,-.26-.92,-.40,-1.45,-.40 -1.47,0,-2.65,1.16,-2.69,2.62v28.22c0,1.49,1.23,2.69,2.72,2.69z",
        "label": "SPLEEN", "label_offset": (15, 15)
    },
    "EMOTION": {  # center_4 - triangle pointing left
        "shape": "path",
        "d": "m275.88,360.85c-.50,0-.94,.11,-1.34,.34l-24.06,13.99c-.67,.49,-1.09,1.26,-1.09,2.16 0,.93,.47,1.76,1.19,2.25l23.67,13.82c.41,.26,.92,.40,1.45,.40 1.47,0,2.65,-1.16,2.69,-2.62v-28.22c0,-1.49,-1.23,-2.69,-2.72,-2.69z",
        "label": "SOLAR PL", "label_offset": (15, 15)
    },
    "WILLPOWER": {  # center_5 - triangle pointing up
        "shape": "path",
        "d": "m234.11,332.54c-.78,0,-1.48,.31,-2,.81l-13.53,13.75c-.28,.31,-.44,.71,-.44,1.16 0,.96,.77,1.73,1.72,1.75h28.66c.95,-.02,1.72,-.79,1.72,-1.75 0,-.45,-.19,-.85,-.47,-1.16l-13.56,-13.78c-.52,-.48,-1.21,-.78,-1.97,-.78z",
        "label": "EGO", "label_offset": (14, 16)
    },
    "LIFEFORCE": {  # center_6 - diamond (rotated square)
        "shape": "rect",
        "x": 362.64, "y": 73.39, "width": 26.4, "height": 26.4,
        "rx": 4.0, "transform": "rotate(45 375.84 86.59)",
        "label": "SACRAL", "label_offset": (13, 16)
    },
    "IDENTITY": {  # center_7 - square at G center
        "shape": "rect",
        "x": 191.3, "y": 271.3, "width": 26.4, "height": 26.4,
        "rx": 4.0,
        "label": "G CENTER", "label_offset": (13, 16)
    },
    "MIND": {  # center_8 - triangle pointing up at head
        "shape": "path",
        "d": "m187.71,226.97c0,.50,.11,.94,.34,1.34l13.99,24.06c.49,.67,1.26,1.09,2.16,1.09 .93,0,1.76,-.47,2.25,-1.19l13.82,-23.67c.26,-.41,.40,-.92,.40,-1.45 0,-1.47,-1.16,-2.65,-2.62,-2.69h-28.22c-1.49,0,-2.69,1.23,-2.69,2.72z",
        "label": "AJNA", "label_offset": (14, 15)
    },
    "INSPIRATION": {  # center_9 - triangle pointing down at crown
        "shape": "path",
        "d": "m221.30,211.03c0,-.50,-.11,-.94,-.34,-1.34l-13.99,-24.06c-.49,-.67,-1.26,-1.09,-2.16,-1.09 -.93,0,-1.76,.47,-2.25,1.19l-13.82,23.67c-.26,.41,-.40,.92,-.40,1.45 0,1.47,1.16,2.65,2.62,2.69h28.22c1.49,0,2.69,-1.23,2.69,-2.72z",
        "label": "HEAD", "label_offset": (14, 15)
    },
}


COLORS = {
    "defined": "#8B4513",  # Saddle brown
    "undefined": "#FFFFFF",  # White
    "conscious": "#4A5D23",  # Dark olive green (future use)
    "unconscious": "#8B0000",  # Dark red (future use)
}


def generate_bodygraph_svg(bodygraph_data: dict[str, Any]) -> str:
    """Generate complete bodygraph SVG from data.

    Args:
        bodygraph_data: Dict with:
            - defined_centers: set of center names
            - active_channels: list of (gate_a, gate_b) tuples
            - conscious_gates: list of gate numbers
            - unconscious_gates: list of gate numbers

    Returns:
        Complete SVG string
    """
    defined_centers = bodygraph_data.get("defined_centers", set())

    svg_parts = []

    # SVG header
    svg_parts.append(
        '<svg viewBox="0 0 355 480" xmlns="http://www.w3.org/2000/svg" '
        'style="background: white;">'
    )

    # Draw centers
    for center_name, center_data in CENTERS.items():
        is_defined = center_name in defined_centers
        fill_color = COLORS["defined"] if is_defined else COLORS["undefined"]
        stroke_color = COLORS["defined"]

        if center_data["shape"] == "rect":
            transform = center_data.get("transform", "")
            svg_parts.append(
                f'<rect x="{center_data["x"]}" y="{center_data["y"]}" '
                f'width="{center_data["width"]}" height="{center_data["height"]}" '
                f'rx="{center_data["rx"]}" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" '
                f'{f"transform=\"{transform}\"" if transform else ""}/>'
            )
        elif center_data["shape"] == "path":
            svg_parts.append(
                f'<path d="{center_data["d"]}" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="2"/>'
            )

        # Add center label
        label_x = center_data.get("x", 200) + center_data.get("label_offset", (0, 0))[0]
        label_y = center_data.get("y", 300) + center_data.get("label_offset", (0, 0))[1]
        svg_parts.append(
            f'<text x="{label_x}" y="{label_y}" '
            f'fill="{stroke_color}" font-family="Arial" font-size="8" '
            f'text-anchor="middle">{center_data["label"]}</text>'
        )

    # TODO: Add channels and gates
    # This requires channel path definitions which we'll extract next

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)
