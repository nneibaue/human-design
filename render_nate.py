#!/usr/bin/env python3
"""Render bodygraph for Nate."""

from datetime import datetime
from pathlib import Path

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.renderers.template_renderer import (
    extract_bodygraph_data_from_model,
    render_bodygraph_from_template,
)


def main():
    """Generate Nate's bodygraph using template approach."""
    # Nate's birth info
    # 13.08.1992, 09:13 h, UTC-7 (+1DST), United States, Albuquerque
    birth_info = BirthInfo(
        date="1992-08-13",
        localtime=LocalTime(datetime(1992, 8, 13, 9, 13)),
        city="Albuquerque",
        country="NM"
    )

    bodygraph = RawBodyGraph(birth_info=birth_info)

    print("=" * 80)
    print("🎨 NATE'S BODYGRAPH")
    print("=" * 80)
    print()
    print(f"Birth: August 13, 1992 at 9:13 AM")
    print(f"Location: Albuquerque, NM (UTC-7/DST)")
    print()
    print(f"Type: {bodygraph.type.value}")
    print(f"Authority: {bodygraph.authority.value}")
    print(f"Profile: {bodygraph.profile}")
    print()
    print(f"Defined Centers: {bodygraph.defined_centers}")
    print(f"Active Channels: {len(bodygraph.active_channels)}")
    for channel in bodygraph.active_channels:
        print(f"   Channel {channel.gate_a}-{channel.gate_b}: {channel.center_a} → {channel.center_b}")
    print()

    # Extract data for template
    bodygraph_data = extract_bodygraph_data_from_model(bodygraph)

    print("📋 Gate Activations:")
    print(f"   Conscious Gates ({len(bodygraph_data['conscious_gates'])}): {sorted(bodygraph_data['conscious_gates'])}")
    print(f"   Unconscious Gates ({len(bodygraph_data['unconscious_gates'])}): {sorted(bodygraph_data['unconscious_gates'])}")
    print()

    # Render using template
    svg_content = render_bodygraph_from_template(bodygraph_data)

    # Wrap in HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Nate's Bodygraph - {bodygraph.type.value}</title>
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
            max-width: 600px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Nate's Human Design Bodygraph</h1>
        <div class="info">
            <strong>Type:</strong> {bodygraph.type.value} |
            <strong>Authority:</strong> {bodygraph.authority.value} |
            <strong>Profile:</strong> {bodygraph.profile}
        </div>
        <div class="info">
            <strong>Birth:</strong> August 13, 1992 at 9:13 AM<br>
            <strong>Location:</strong> Albuquerque, NM
        </div>
        <div class="info" style="font-size: 0.9em; color: #666;">
            Using 64keys SVG template with Nate's activations applied
        </div>
        {svg_content}
        <div class="info" style="margin-top: 30px; padding: 20px; background: #e8f4f8; border-radius: 4px;">
            <strong>✅ Nate's Chart:</strong> Gates and centers have been filtered based on calculated bodygraph data.<br>
            <small>Active gates shown, inactive gates hidden. Defined centers colored, undefined centers white.</small>
        </div>
    </div>
</body>
</html>"""

    # Write output
    output_path = Path("nate_bodygraph.html")
    output_path.write_text(html_content)

    print(f"✅ Rendered to: {output_path.absolute()}")
    print()
    print("📐 Using 64keys SVG template structure")
    print("🎨 Pure SVG (no D3, no JavaScript)")
    print("✨ Show/hide logic applied - this is Nate's actual chart")
    print()
    print("🔍 Compare to 64keys.com to verify accuracy")
    print()


if __name__ == "__main__":
    main()
