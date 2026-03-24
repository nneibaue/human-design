#!/usr/bin/env python3
"""Create a bodygraph visualization for a sample Manifesting Generator (Specialist).

This demonstrates the complete flow:
1. Birth data → RawBodyGraph calculation
2. RawBodyGraph → D3-friendly JSON
3. D3 JSON → HTML visualization
"""

from datetime import datetime
from pathlib import Path

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime


def create_sample_specialist_bodygraph():
    """Create a sample Manifesting Generator (Specialist) bodygraph.

    Using birth data known to produce a Specialist type with defined Sacral.
    """
    # Sample birth data - Manifesting Generator (Specialist) requires:
    # - Defined Sacral center (LIFEFORCE)
    # - Motor connected to Throat (one-step connection)
    birth_info = BirthInfo(
        date="1992-11-10",
        localtime=LocalTime(datetime(1992, 11, 10, 18, 20)),
        city="Austin",
        country="TX"
    )

    # Calculate bodygraph
    bodygraph = RawBodyGraph(birth_info=birth_info)

    return bodygraph


def bodygraph_to_d3_json(bodygraph: RawBodyGraph) -> dict:
    """Transform RawBodyGraph to D3-friendly JSON format.

    This is the renderer that the implementer agent should create.
    """
    from human_design.models.core import CenterName

    # Center coordinates for SVG (viewBox 800x1000)
    # Corrected to match Human Design bodygraph anatomy
    CENTER_COORDINATES = {
        "INSPIRATION": (400, 80),    # Head - top center
        "MIND": (400, 195),          # Ajna - below head
        "EXPRESSION": (400, 340),    # Throat - central hub
        "IDENTITY": (400, 505),      # G-Center - center of body
        "WILLPOWER": (310, 445),     # Heart/Ego - LEFT of center, between Throat and G
        "EMOTION": (535, 620),       # Solar Plexus - RIGHT side
        "LIFEFORCE": (400, 680),     # Sacral - gut
        "DRIVE": (400, 850),         # Root - base
        "INTUITION": (265, 620),     # Spleen - LEFT side, same level as Sacral
    }

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

    # Gate-to-center mapping (from Human Design specification)
    GATE_TO_CENTER = {
        # HEAD (INSPIRATION) - 3 gates
        61: "INSPIRATION", 63: "INSPIRATION", 64: "INSPIRATION",
        # AJNA (MIND) - 6 gates
        4: "MIND", 11: "MIND", 17: "MIND", 24: "MIND", 43: "MIND", 47: "MIND",
        # THROAT (EXPRESSION) - 11 gates
        8: "EXPRESSION", 12: "EXPRESSION", 16: "EXPRESSION", 20: "EXPRESSION",
        23: "EXPRESSION", 31: "EXPRESSION", 33: "EXPRESSION", 35: "EXPRESSION",
        45: "EXPRESSION", 56: "EXPRESSION", 62: "EXPRESSION",
        # G CENTER (IDENTITY) - 8 gates
        1: "IDENTITY", 2: "IDENTITY", 7: "IDENTITY", 10: "IDENTITY",
        13: "IDENTITY", 15: "IDENTITY", 25: "IDENTITY", 46: "IDENTITY",
        # HEART/EGO (WILLPOWER) - 4 gates
        21: "WILLPOWER", 26: "WILLPOWER", 40: "WILLPOWER", 51: "WILLPOWER",
        # SACRAL (LIFEFORCE) - 9 gates
        3: "LIFEFORCE", 5: "LIFEFORCE", 9: "LIFEFORCE", 14: "LIFEFORCE",
        27: "LIFEFORCE", 29: "LIFEFORCE", 34: "LIFEFORCE", 42: "LIFEFORCE",
        59: "LIFEFORCE",
        # SOLAR PLEXUS (EMOTION) - 7 gates
        6: "EMOTION", 22: "EMOTION", 30: "EMOTION", 36: "EMOTION",
        37: "EMOTION", 49: "EMOTION", 55: "EMOTION",
        # SPLEEN (INTUITION) - 7 gates
        18: "INTUITION", 28: "INTUITION", 32: "INTUITION", 44: "INTUITION",
        48: "INTUITION", 50: "INTUITION", 57: "INTUITION",
        # ROOT (DRIVE) - 9 gates
        19: "DRIVE", 38: "DRIVE", 39: "DRIVE", 41: "DRIVE",
        52: "DRIVE", 53: "DRIVE", 54: "DRIVE", 58: "DRIVE", 60: "DRIVE",
    }

    # Build centers array
    centers = []
    for center_name in CenterName.__args__:
        centers.append({
            "name": center_name,
            "defined": center_name in bodygraph.defined_centers,
            "x": CENTER_COORDINATES[center_name][0],
            "y": CENTER_COORDINATES[center_name][1],
            "shape": CENTER_SHAPES[center_name],
        })

    # Build channels array
    channels = []
    for channel in bodygraph.active_channels:
        channels.append({
            "id": f"{channel.gate_a}-{channel.gate_b}",
            "gate_a": channel.gate_a,
            "gate_b": channel.gate_b,
            "defined": True,
            "from_center": channel.center_a,
            "to_center": channel.center_b,
        })

    return {
        "birth_info": {
            "date": bodygraph.birth_info.date,
            "location": f"{bodygraph.birth_info.city}, {bodygraph.birth_info.country}",
            "timezone": bodygraph.birth_info.timezone,
        },
        "bodygraph": {
            "centers": centers,
            "channels": channels,
            "type": bodygraph.type.value,
            "authority": bodygraph.authority.value,
            "profile": str(bodygraph.profile),
        }
    }


def create_html_visualization(bodygraph_json: dict, output_path: Path):
    """Create an HTML file with D3 visualization."""

    import json

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bodygraph Visualization - {bodygraph_json['bodygraph']['type']}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        /* Rebecca Energy Aesthetic */
        :root {{
            --defined-center: #8B4513;      /* Saddle brown */
            --undefined-center: #F5F5DC;    /* Beige */
            --conscious: #4A5D23;           /* Dark olive green */
            --unconscious: #8B0000;         /* Dark red */
            --emergent: #DAA520;            /* Goldenrod */
            --background: #FFFFFF;          /* White background for visibility */
            --text: #333333;                /* Dark gray text */
        }}

        body {{
            margin: 0;
            padding: 20px;
            background: var(--background);
            color: var(--text);
            font-family: Georgia, serif;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            text-align: center;
            color: #8B4513;
        }}

        .info {{
            text-align: center;
            margin: 20px 0;
            font-size: 18px;
        }}

        .bodygraph-container {{
            display: flex;
            justify-content: center;
            margin: 40px 0;
        }}

        svg {{
            background: #FFFFFF;
            border: 2px solid #CCCCCC;
            border-radius: 8px;
        }}

        .center-defined {{
            fill: var(--defined-center);
            stroke: #333333;
            stroke-width: 2;
        }}

        .center-undefined {{
            fill: #FFFFFF;
            stroke: #333333;
            stroke-width: 2;
        }}

        .center-label {{
            fill: #333333;
            font-family: Georgia, serif;
            font-size: 12px;
            text-anchor: middle;
        }}


        .gate-conscious {{
            fill: var(--conscious);
            stroke: var(--text);
            stroke-width: 1.5;
        }}

        .gate-unconscious {{
            fill: var(--unconscious);
            stroke: var(--text);
            stroke-width: 1.5;
        }}

        .gate-label {{
            fill: var(--text);
            font-size: 10px;
            text-anchor: middle;
        }}

        .tooltip {{
            position: absolute;
            background: #333333;
            color: #FFFFFF;
            padding: 8px;
            border-radius: 4px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Human Design Bodygraph</h1>
        <div class="info">
            <strong>Type:</strong> {bodygraph_json['bodygraph']['type']} |
            <strong>Authority:</strong> {bodygraph_json['bodygraph']['authority']} |
            <strong>Profile:</strong> {bodygraph_json['bodygraph']['profile']}
        </div>
        <div class="info">
            <strong>Birth:</strong> {bodygraph_json['birth_info']['date']} in {bodygraph_json['birth_info']['location']}
        </div>

        <div class="bodygraph-container" id="bodygraph"></div>
        <div class="tooltip" id="tooltip"></div>
    </div>

    <script>
        // Bodygraph data
        const data = {json.dumps(bodygraph_json['bodygraph'], indent=8)};

        // D3 v7 Visualization
        const width = 800;
        const height = 1000;

        const svg = d3.select("#bodygraph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", `0 0 ${{width}} ${{height}}`);

        const tooltip = d3.select("#tooltip");

        // Helper functions
        function getCenterShape(shape, size = 60) {{
            switch (shape) {{
                case "square":
                    return `M ${{-size/2}} ${{-size/2}} h ${{size}} v ${{size}} h ${{-size}} Z`;
                case "triangle":
                    return `M 0 ${{-size/2}} L ${{size/2}} ${{size/2}} L ${{-size/2}} ${{size/2}} Z`;
                case "diamond":
                    return `M 0 ${{-size/2}} L ${{size/2}} 0 L 0 ${{size/2}} L ${{-size/2}} 0 Z`;
                default:
                    return "";
            }}
        }}

        // Draw simple lines connecting centers
        svg.selectAll(".channel")
            .data(data.channels)
            .join("line")
            .attr("class", "channel")
            .attr("x1", d => {{
                const fromCenter = data.centers.find(c => c.name === d.from_center);
                return fromCenter ? fromCenter.x : 0;
            }})
            .attr("y1", d => {{
                const fromCenter = data.centers.find(c => c.name === d.from_center);
                return fromCenter ? fromCenter.y : 0;
            }})
            .attr("x2", d => {{
                const toCenter = data.centers.find(c => c.name === d.to_center);
                return toCenter ? toCenter.x : 0;
            }})
            .attr("y2", d => {{
                const toCenter = data.centers.find(c => c.name === d.to_center);
                return toCenter ? toCenter.y : 0;
            }})
            .attr("stroke", "#8B4513")
            .attr("stroke-width", 4);

        // Draw centers
        const centerGroups = svg.selectAll(".center")
            .data(data.centers)
            .join("g")
            .attr("class", "center")
            .attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);

        centerGroups.append("path")
            .attr("d", d => getCenterShape(d.shape))
            .attr("class", d => d.defined ? "center-defined" : "center-undefined")
            .on("mouseover", (event, d) => {{
                tooltip
                    .style("opacity", 1)
                    .html(`<strong>${{d.name}}</strong><br>${{d.defined ? "Defined" : "Undefined"}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 20) + "px");
            }})
            .on("mouseout", () => {{
                tooltip.style("opacity", 0);
            }});

        centerGroups.append("text")
            .attr("class", "center-label")
            .attr("dy", "0.3em")
            .text(d => d.name.substring(0, 4));
    </script>
</body>
</html>
"""

    output_path.write_text(html_content)
    print(f"✅ Visualization created: {output_path}")


def main():
    """Create sample Manifesting Generator visualization."""
    print("=" * 80)
    print("🎨 CREATING MANIFESTING GENERATOR VISUALIZATION")
    print("=" * 80)
    print()

    # Step 1: Create sample bodygraph
    print("1️⃣  Calculating bodygraph...")
    bodygraph = create_sample_specialist_bodygraph()
    print(f"   Type: {bodygraph.type.value}")
    print(f"   Authority: {bodygraph.authority.value}")
    print(f"   Profile: {bodygraph.profile}")
    print(f"   Defined Centers: {len(bodygraph.defined_centers)}")
    print(f"   Active Channels: {len(bodygraph.active_channels)}")
    print()

    # Step 2: Transform to D3 JSON
    print("2️⃣  Transforming to D3 format...")
    d3_json = bodygraph_to_d3_json(bodygraph)
    print(f"   Centers: {len(d3_json['bodygraph']['centers'])}")
    print(f"   Channels: {len(d3_json['bodygraph']['channels'])}")
    print()

    # Step 3: Create HTML visualization
    print("3️⃣  Creating HTML visualization...")
    output_path = Path("bodygraph_visualization.html")
    create_html_visualization(d3_json, output_path)
    print()

    print("=" * 80)
    print("✅ VISUALIZATION COMPLETE")
    print("=" * 80)
    print()
    print(f"📁 Open in browser: {output_path.absolute()}")
    print()
    print("🎨 Plain bodygraph with Rebecca Energy aesthetic:")
    print("   - Warm browns for defined centers")
    print("   - Beige for undefined centers")
    print("   - Channels connecting centers")
    print("   - No gate activations shown yet")
    print()


if __name__ == "__main__":
    main()
