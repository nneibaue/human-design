#!/usr/bin/env python3
"""Example: Render bodygraph using the new renderer."""

from pathlib import Path

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.renderers import render_bodygraph
from datetime import datetime


def main():
    """Generate bodygraph visualization using the renderer."""
    # Calculate bodygraph from birth info
    birth_info = BirthInfo(
        date="1992-11-10",
        localtime=LocalTime(datetime(1992, 11, 10, 18, 20)),
        city="Austin",
        country="TX"
    )

    bodygraph = RawBodyGraph(birth_info=birth_info)

    # Prepare data for renderer
    centers = []
    for center_name in ["INSPIRATION", "MIND", "EXPRESSION", "IDENTITY", "WILLPOWER",
                        "EMOTION", "LIFEFORCE", "INTUITION", "DRIVE"]:
        centers.append({
            "name": center_name,
            "defined": center_name in bodygraph.defined_centers,
        })

    channels = []
    for channel in bodygraph.active_channels:
        channels.append({
            "gate_a": channel.gate_a,
            "gate_b": channel.gate_b,
            "from_center": channel.center_a,
            "to_center": channel.center_b,
        })

    gates = []
    for activation in bodygraph.conscious_activations:
        gates.append({
            "number": activation.gate,
            "activation": "conscious",
        })
    for activation in bodygraph.unconscious_activations:
        gates.append({
            "number": activation.gate,
            "activation": "unconscious",
        })

    # Render SVG
    svg_content = render_bodygraph(
        centers=centers,
        channels=channels,
        gates=gates,
    )

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
            max-width: 800px;
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Human Design Bodygraph</h1>
        <div class="info">
            <strong>Type:</strong> {bodygraph.type.value} |
            <strong>Authority:</strong> {bodygraph.authority.value} |
            <strong>Profile:</strong> {bodygraph.profile}
        </div>
        <div class="info">
            <strong>Birth:</strong> {birth_info.date} in {birth_info.city}, {birth_info.country}
        </div>
        {svg_content}
    </div>
</body>
</html>"""

    # Write output
    output_path = Path("bodygraph_rendered.html")
    output_path.write_text(html_content)

    print("=" * 80)
    print("✅ BODYGRAPH RENDERED")
    print("=" * 80)
    print()
    print(f"📁 Output: {output_path.absolute()}")
    print()
    print(f"Type: {bodygraph.type.value}")
    print(f"Authority: {bodygraph.authority.value}")
    print(f"Profile: {bodygraph.profile}")
    print(f"Defined Centers: {len(bodygraph.defined_centers)}")
    print(f"Active Channels: {len(bodygraph.active_channels)}")
    print()
    print("🎨 Using 64keys-compatible coordinate system")
    print("📐 ViewBox: 0 0 355 480")
    print()


if __name__ == "__main__":
    main()
