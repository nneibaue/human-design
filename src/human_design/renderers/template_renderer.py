"""Template-based bodygraph renderer using 64keys SVG structure.

Instead of calculating geometry, use the working 64keys SVG as a template
and show/hide/color elements based on bodygraph data.
"""

import re
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Any


def render_bodygraph_from_template(
    bodygraph_data: dict[str, Any],
    template_path: Path | None = None,
) -> str:
    """Render bodygraph by modifying 64keys SVG template.

    Args:
        bodygraph_data: Dict with keys:
            - defined_centers: set of center names
            - active_channels: list of (gate_a, gate_b) tuples
            - conscious_gates: list of gate numbers
            - unconscious_gates: list of gate numbers
        template_path: Path to 64keys SVG template (default: bg_example.html)

    Returns:
        Modified SVG string with correct elements shown/hidden/colored
    """
    if template_path is None:
        # Default to bg_example.html in project root
        template_path = Path("bg_example.html")

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Read template
    with open(template_path, 'r') as f:
        content = f.read()

    # Extract SVG element
    svg_start = content.find('<svg enable-background')
    svg_end = content.find('</svg>', svg_start) + 6

    if svg_start < 0 or svg_end <= svg_start:
        raise ValueError("Could not find SVG in template")

    svg_content = content[svg_start:svg_end]

    # Parse SVG
    # Note: ElementTree has issues with some SVG attributes, so we'll do
    # string manipulation for now (safer for preserving exact structure)

    # Extract bodygraph data
    defined_centers = bodygraph_data.get("defined_centers", set())
    active_channels = bodygraph_data.get("active_channels", [])
    conscious_gates = set(bodygraph_data.get("conscious_gates", []))
    unconscious_gates = set(bodygraph_data.get("unconscious_gates", []))
    all_active_gates = conscious_gates | unconscious_gates

    # Build list of gate numbers in active channels
    channel_gates = set()
    for gate_a, gate_b in active_channels:
        channel_gates.add(gate_a)
        channel_gates.add(gate_b)

    # Strategy:
    # 1. Hide all gates not in all_active_gates
    # 2. Show defined centers (colored versions)
    # 3. Hide undefined centers (keep only white versions)

    # Map center names to their numeric IDs in 64keys template
    # From analysis: center_3 = INTUITION, center_4 = EMOTION, center_5 = WILLPOWER,
    # center_6 = LIFEFORCE, center_7 = IDENTITY, center_8 = MIND, center_9 = INSPIRATION
    # center_1 = DRIVE, center_2 = EXPRESSION
    CENTER_MAP = {
        "DRIVE": "center_1",
        "EXPRESSION": "center_2",
        "INTUITION": "center_3",
        "EMOTION": "center_4",
        "WILLPOWER": "center_5",
        "LIFEFORCE": "center_6",
        "IDENTITY": "center_7",
        "MIND": "center_8",
        "INSPIRATION": "center_9",
    }

    modified_svg = svg_content

    # Show/hide gates based on bodygraph data using regex
    for gate_num in range(1, 65):
        # Match <g id="gateN" ... any attributes ... >
        pattern = rf'(<g id="gate{gate_num}"[^>]*)(>)'

        if gate_num in all_active_gates:
            # Show this gate - ensure no opacity="0"
            def show_gate(match):
                tag_start = match.group(1)
                tag_end = match.group(2)
                # Remove opacity="0" if present
                tag_start = re.sub(r'\s*opacity="0"', '', tag_start)
                # Ensure it's visible (opacity="1" or no opacity)
                if 'opacity=' not in tag_start:
                    return tag_start + tag_end
                # Replace opacity with "1"
                tag_start = re.sub(r'opacity="[^"]*"', 'opacity="1"', tag_start)
                return tag_start + tag_end

            modified_svg = re.sub(pattern, show_gate, modified_svg)
        else:
            # Hide this gate - add/set opacity="0"
            def hide_gate(match):
                tag_start = match.group(1)
                tag_end = match.group(2)
                # Remove existing opacity if present
                tag_start = re.sub(r'\s*opacity="[^"]*"', '', tag_start)
                # Add opacity="0"
                return tag_start + ' opacity="0"' + tag_end

            modified_svg = re.sub(pattern, hide_gate, modified_svg)

    # Show/hide center versions based on defined status
    for center_name, center_id in CENTER_MAP.items():
        is_defined = center_name in defined_centers

        # For defined centers: show colored versions (orange/blue), hide white
        # For undefined centers: show white, hide colored versions

        if is_defined:
            # Hide white version
            modified_svg = modified_svg.replace(
                f'<g id="{center_id}_white">',
                f'<g id="{center_id}_white" opacity="0">'
            )
            # Show orange version (if exists)
            modified_svg = modified_svg.replace(
                f'<g id="{center_id}_orange" opacity="0">',
                f'<g id="{center_id}_orange" opacity="1">'
            )
            # Show blue version (if exists)
            modified_svg = modified_svg.replace(
                f'<g id="{center_id}_blue" opacity="1">',
                f'<g id="{center_id}_blue" opacity="1">'
            )
        else:
            # Show white version
            modified_svg = modified_svg.replace(
                f'<g id="{center_id}_white" opacity="0">',
                f'<g id="{center_id}_white" opacity="1">'
            )
            # Hide orange version
            modified_svg = modified_svg.replace(
                f'<g id="{center_id}_orange">',
                f'<g id="{center_id}_orange" opacity="0">'
            )
            # Hide blue version
            modified_svg = modified_svg.replace(
                f'<g id="{center_id}_blue" opacity="1">',
                f'<g id="{center_id}_blue" opacity="0">'
            )

    return modified_svg


def extract_bodygraph_data_from_model(bodygraph) -> dict[str, Any]:
    """Extract template-compatible data from RawBodyGraph model.

    Args:
        bodygraph: RawBodyGraph instance

    Returns:
        Dict compatible with render_bodygraph_from_template
    """
    return {
        "defined_centers": bodygraph.defined_centers,
        "active_channels": [
            (ch.gate_a, ch.gate_b) for ch in bodygraph.active_channels
        ],
        "conscious_gates": [act.gate for act in bodygraph.conscious_activations],
        "unconscious_gates": [act.gate for act in bodygraph.unconscious_activations],
    }
