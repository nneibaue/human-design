#!/usr/bin/env python3
"""Extract 64keys bodygraph geometry and create reusable rendering function.

PROBLEM:
Our current visualization is completely wrong. We need to work backwards from
the working 64keys example (bg_example.html) to understand:
1. ViewBox coordinate system (355 x 480, not 800 x 1000)
2. Center positions and shapes (with transform matrices)
3. Gate positioning (3px wide rectangles with rotation transforms)
4. How gates connect centers (gates ARE the channels, no separate lines)

GOAL:
Create a Python function: render_bodygraph(data, **options)
- Takes: centers, channels, gates
- Returns: correct SVG string
- Options: viewBox, colors, stroke widths, center coordinates

TEAM:
- researcher: Deep analysis of bg_example.html structure
- d3_specialist: SVG geometry, transforms, coordinate systems
- implementer: Build the Python rendering function
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from human_design.strands import create_strand


async def main():
    """Execute bodygraph geometry extraction strand."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found")
        return

    problem = """EXTRACT 64KEYS BODYGRAPH GEOMETRY AND CREATE REUSABLE RENDERER

CURRENT SITUATION:
We have a working 64keys bodygraph in bg_example.html (177KB) but our
create_sample_visualization.py produces incorrect output. The geometry is
completely wrong - wrong coordinate system, wrong center positions, wrong
channel rendering.

ROOT CAUSE:
We've been guessing at the geometry instead of extracting it from the working example.

TASK:
Work backwards from bg_example.html to build a correct bodygraph renderer.

ANALYSIS REQUIRED:
1. Extract SVG viewBox and coordinate system from bg_example.html
   - Current: viewBox="0 0 355 479.88483" (NOT 800x1000!)
   - Transform matrices applied to groups

2. Document center geometry:
   - Exact positions in the coordinate system
   - Path definitions for each shape (triangle, square, diamond)
   - Transform matrices applied to centers

3. Document gate positioning:
   - Gates are 3px wide rectangles
   - Positioned with transform matrices (rotation + translation)
   - Example: <rect width="3" height="15.99" transform="matrix(...)"/>

4. Understand channel architecture:
   - NO separate channel lines in 64keys
   - Gates themselves ARE the visual channels
   - Gates connect centers by being positioned along the path

IMPLEMENTATION REQUIRED:
Create Python function with this signature:

```python
def render_bodygraph(
    centers: list[dict],  # [{"name": "LIFEFORCE", "defined": True, "x": 204, "y": 377}]
    channels: list[dict],  # [{"gate_a": 34, "gate_b": 57, "from_center": "LIFEFORCE", "to_center": "INTUITION"}]
    gates: list[dict],     # [{"number": 34, "activation": "conscious"}]
    *,
    viewBox: str = "0 0 355 480",
    colors: dict = None,
    center_size: int = 30,
    gate_width: int = 3,
    gate_height: int = 20,
) -> str:
    '''Generate SVG string for bodygraph visualization.

    Returns complete SVG with correct 64keys geometry.
    '''
    pass
```

DELIVERABLES:
1. Documented geometry extraction from bg_example.html
2. Python module: src/human_design/renderers/bodygraph_svg.py
3. Working example that produces correct output
4. Tests validating geometry

SUCCESS CRITERIA:
- Output SVG matches 64keys visual structure
- Centers at correct positions
- Gates properly rotated and positioned
- Parameterized for customization
"""

    context = {
        "reference_file": {
            "path": "bg_example.html",
            "size": "177KB",
            "svg_id": "Bodygraph_v1",
            "viewBox": "0 0 355 479.88483",
            "description": "Working 64keys bodygraph with correct geometry",
        },
        "broken_file": {
            "path": "create_sample_visualization.py",
            "issue": "Wrong coordinate system (800x1000), wrong positions, wrong rendering",
        },
        "key_insights": {
            "coordinate_system": "355x480 viewBox, NOT 800x1000",
            "transforms": "Centers and gates use SVG transform matrices",
            "gates_are_channels": "No separate channel lines - gates connect centers",
            "gate_geometry": "3px wide rectangles with rotation transforms",
        },
        "output_location": {
            "renderer": "src/human_design/renderers/bodygraph_svg.py",
            "example": "examples/bodygraph_rendering_example.py",
            "tests": "tests/test_bodygraph_renderer.py",
        },
        "analysis_approach": [
            "Parse bg_example.html to extract SVG structure",
            "Document center positions (after transform matrices)",
            "Extract gate positioning patterns",
            "Identify coordinate transformations",
            "Build parameterized renderer",
        ],
    }

    # Multi-agent strand for geometry extraction and implementation
    strand = create_strand(
        problem=problem,
        agents=["researcher", "d3_specialist", "implementer"],
        strand_type="implementation",
        context=context
    )

    print("=" * 80)
    print("🔬 64KEYS BODYGRAPH GEOMETRY EXTRACTION")
    print("=" * 80)
    print()
    print("🧵 Strand ID:", strand.definition.strand_id)
    print("👥 Team: researcher, d3_specialist, implementer")
    print("🎯 Model: Opus 4.6")
    print()
    print("📋 Task:")
    print("   Work backwards from bg_example.html to extract correct geometry")
    print("   Build reusable render_bodygraph() function")
    print()
    print("🎯 Deliverables:")
    print("   1. Geometry documentation")
    print("   2. src/human_design/renderers/bodygraph_svg.py")
    print("   3. Working example")
    print("   4. Tests")
    print()
    print("⏱️  Estimated: 15-20 minutes")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ GEOMETRY EXTRACTION COMPLETE")
    print("=" * 80)
    print()

    # Display findings
    print("📊 AGENT FINDINGS:")
    print()

    for agent_name, findings in result.findings.items():
        print(f"{'='*60}")
        print(f"📝 {agent_name.upper()}")
        print(f"{'='*60}")
        print()

        if isinstance(findings, dict):
            if "error" in findings:
                print(f"❌ Error: {findings['error']}")
            else:
                import json
                if len(str(findings)) > 5000:
                    print("[Large output - showing first 3000 chars]")
                    print(json.dumps(findings, indent=2)[:3000])
                    print("... [truncated]")
                else:
                    print(json.dumps(findings, indent=2))
        else:
            if len(str(findings)) > 5000:
                print(str(findings)[:3000] + "\n... [truncated]")
            else:
                print(findings)
        print()

    print(f"📁 Full findings: strand-results/active/STRAND_{result.strand_id}.json")
    print()

    return result


if __name__ == "__main__":
    asyncio.run(main())
