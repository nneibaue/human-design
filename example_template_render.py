#!/usr/bin/env python3
"""Example: Render bodygraph using 64keys SVG template."""

from datetime import datetime
from pathlib import Path

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.renderers.template_renderer import (
    extract_bodygraph_data_from_model,
    render_bodygraph_from_template,
)


def main():
    """Generate bodygraph using template approach."""
    # Calculate bodygraph
    birth_info = BirthInfo(
        date="1992-11-10",
        localtime=LocalTime(datetime(1992, 11, 10, 18, 20)),
        city="Austin",
        country="TX"
    )

    bodygraph = RawBodyGraph(birth_info=birth_info)

    print("=" * 80)
    print("🎨 BODYGRAPH TEMPLATE RENDERING")
    print("=" * 80)
    print()
    print(f"Type: {bodygraph.type.value}")
    print(f"Authority: {bodygraph.authority.value}")
    print(f"Profile: {bodygraph.profile}")
    print(f"Defined Centers: {bodygraph.defined_centers}")
    print(f"Active Channels: {len(bodygraph.active_channels)}")
    print()

    # Extract data for template
    bodygraph_data = extract_bodygraph_data_from_model(bodygraph)

    print("📋 Bodygraph Data:")
    print(f"   Defined Centers: {bodygraph_data['defined_centers']}")
    print(f"   Active Channels: {bodygraph_data['active_channels']}")
    print(f"   Conscious Gates: {len(bodygraph_data['conscious_gates'])}")
    print(f"   Unconscious Gates: {len(bodygraph_data['unconscious_gates'])}")
    print()

    # Render using template
    svg_content = render_bodygraph_from_template(bodygraph_data)

    # Wrap in HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bodygraph - {bodygraph.type.value}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #8B4513;
        }}
        .info {{
            text-align: center;
            margin: 20px 0;
        }}
        svg {{
            display: block;
            margin: 0 auto;
            border: 1px solid #ccc;
            background: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Human Design Bodygraph (Template-Based)</h1>
        <div class="info">
            <strong>Type:</strong> {bodygraph.type.value} |
            <strong>Authority:</strong> {bodygraph.authority.value} |
            <strong>Profile:</strong> {bodygraph.profile}
        </div>
        <div class="info">
            <strong>Birth:</strong> {birth_info.date} in {birth_info.city}, {birth_info.country}
        </div>
        <div class="info" style="font-size: 0.9em; color: #666;">
            Using 64keys SVG template (pure SVG, no D3)
        </div>
        {svg_content}
    </div>
</body>
</html>"""

    # Write output
    output_path = Path("bodygraph_template_rendered.html")
    output_path.write_text(html_content)

    print(f"✅ Rendered to: {output_path.absolute()}")
    print()
    print("📐 Using 64keys SVG template structure")
    print("🎨 Pure SVG (no D3, no JavaScript)")
    print()
    print("⚠️  Note: Currently showing full template")
    print("   TODO: Implement show/hide/color logic based on bodygraph data")
    print()


if __name__ == "__main__":
    main()
