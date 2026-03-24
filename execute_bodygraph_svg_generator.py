#!/usr/bin/env python3
"""Execute DODO strand to build bodygraph SVG generator."""

import sys
sys.path.insert(0, '/Users/nathan.neibauer/code/claude/he360-dodo')

from he360_dodo import create_strand
import asyncio

async def main():
    """Create and execute strand for SVG generator."""

    problem = """
Extract 64keys bodygraph geometry from bg_example.html and create a reusable bodygraph rendering function.

Current situation:
- We have bg_example.html (Rebecca's chart) as a reference for geometry
- Template modification approach failed (trying to hide/show elements)
- Need to BUILD fresh SVGs from scratch for each person

Goal:
Build generate_bodygraph_svg() function that:
1. Takes bodygraph data (defined_centers, active_channels, conscious_gates, unconscious_gates)
2. Extracts geometry from bg_example.html (center positions, channel paths, gate coordinates)
3. Generates complete SVG from scratch using 64keys coordinate system
4. Returns SVG string that visually matches 64keys structure

Success criteria:
- Function generates SVG for Nate's chart with his specific activations
- Nate's gates: [2, 4, 10, 13, 15, 17, 23, 27, 31, 35, 38, 40, 43, 47, 49, 54, 57, 59]
- Nate's defined centers: MIND, EXPRESSION, INTUITION, IDENTITY (colored #8B4513)
- Undefined centers: white with stroke
- Channels connect defined centers correctly
- ViewBox matches 64keys: "0 0 355 480"

Files:
- Input: bg_example.html (reference geometry)
- Output: src/human_design/renderers/svg_generator.py (new)
- Integration: src/human_design/api/bodygraph_endpoint.py (update to use svg_generator)

Scope: Individual bodygraphs only (not composite/interaction charts yet)
"""

    context = {
        "codebase": {
            "template": "bg_example.html",
            "current_renderer": "src/human_design/renderers/template_renderer.py",
            "endpoint": "src/human_design/api/bodygraph_endpoint.py",
            "models": "src/human_design/models/bodygraph.py",
        },
        "test_case": {
            "name": "Nate",
            "birth_date": "1992-08-13",
            "birth_time": "09:13",
            "location": "Albuquerque, NM",
            "expected_type": "Coordinator",
            "expected_authority": "Splenic",
            "expected_profile": "3/5",
            "defined_centers": ["MIND", "EXPRESSION", "INTUITION", "IDENTITY"],
            "active_channels": [[10, 57], [23, 43]],
            "all_gates": [2, 4, 10, 13, 15, 17, 23, 27, 31, 35, 38, 40, 43, 47, 49, 54, 57, 59],
        },
        "geometry_requirements": {
            "viewBox": "0 0 355 480",
            "centers": 9,
            "center_shapes": {
                "DRIVE": "rect",
                "EXPRESSION": "rect",
                "INTUITION": "triangle_right",
                "EMOTION": "triangle_left",
                "WILLPOWER": "triangle_up",
                "LIFEFORCE": "diamond",
                "IDENTITY": "rect",
                "MIND": "triangle_up",
                "INSPIRATION": "triangle_down",
            },
            "colors": {
                "defined": "#8B4513",
                "undefined": "#FFFFFF",
                "stroke": "#8B4513",
            }
        }
    }

    from pathlib import Path

    strand = create_strand(
        problem=problem,
        agents=["researcher", "python_linguist", "implementer"],
        strand_type="implementation",
        context=context,
        repo_path=Path("/Users/nathan.neibauer/code/human-design")
    )

    print("🚀 Executing DODO strand for bodygraph SVG generator...")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ STRAND COMPLETE")
    print("=" * 80)
    print()
    print(f"Status: {result.status}")
    print(f"Findings: {result.findings[:500]}..." if len(result.findings) > 500 else f"Findings: {result.findings}")

    return result

if __name__ == "__main__":
    asyncio.run(main())
