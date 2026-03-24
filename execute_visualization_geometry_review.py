#!/usr/bin/env python3
"""Multi-agent investigation strand to review bodygraph visualization geometry.

Team composition:
- researcher: Extract proper bodygraph geometry specs from reference materials
- d3_specialist: Analyze D3.js rendering and identify visualization issues
- implementer: Review code implementation and propose fixes
"""

import asyncio
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from human_design.strands import create_strand


async def main():
    """Execute geometry review strand with collaborative investigation."""

    # Verify API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("   Please set it in .env file or export it")
        return

    problem = """BODYGRAPH VISUALIZATION GEOMETRY INVESTIGATION

The current visualization (bodygraph_visualization.html) is "horribly disfigured"
according to user feedback. The tooltips appear to work, but the geometry is incorrect.

CRITICAL QUESTIONS TO ANSWER:
1. What are the specific geometry issues? (centers, gates, channels, or all three?)
2. What does "correct" bodygraph geometry look like per Human Design specifications?
3. How should gates map to centers? (current algorithm uses d.number % 9)
4. What are the proper center coordinates and shapes?
5. How should channels route between centers?

INVESTIGATION APPROACH:
- researcher: Study bodygraph.yaml, docs, and Human Design references for geometry specs
- d3_specialist: Analyze the D3.js code, SVG output, and visual rendering issues
- implementer: Review create_sample_visualization.py implementation logic

Each agent will independently analyze the problem, then findings will be synthesized.

FILES TO ANALYZE:
- create_sample_visualization.py (lines 46-79, 334-345)
- bodygraph_visualization.html (generated output)
- src/human_design/bodygraph.yaml (gate->center mappings)
- docs/gate-zodiac-mapping.md (reference)
"""

    context = {
        "current_implementation": {
            "file": "create_sample_visualization.py",
            "center_coordinates": {
                "INSPIRATION": "(400, 100)",   # Head - top triangle
                "MIND": "(400, 200)",          # Ajna - forehead triangle
                "EXPRESSION": "(400, 350)",    # Throat - neck square
                "IDENTITY": "(400, 500)",      # G-Center - heart diamond
                "WILLPOWER": "(300, 500)",     # Ego/Will - left triangle
                "EMOTION": "(500, 650)",       # Solar Plexus - right triangle
                "LIFEFORCE": "(400, 700)",     # Sacral - belly square
                "DRIVE": "(400, 850)",         # Root - bottom square
                "INTUITION": "(300, 650)",     # Spleen - left triangle
            },
            "center_shapes": {
                "LIFEFORCE": "square",
                "EMOTION": "triangle",
                "INTUITION": "triangle",
                "IDENTITY": "diamond",
                "WILLPOWER": "triangle",
                "DRIVE": "square",
                "EXPRESSION": "square",
                "MIND": "triangle",
                "INSPIRATION": "triangle",
            },
            "gate_positioning_code": """
// CURRENT IMPLEMENTATION (LIKELY INCORRECT)
gateGroups.each(function(d) {
    // Find which center this gate belongs to (simplified)
    const center = data.centers[d.number % 9];
    const angle = (d.number * 30) * Math.PI / 180;
    const radius = 40;
    const x = center.x + Math.cos(angle) * radius;
    const y = center.y + Math.sin(angle) * radius;

    d3.select(this)
        .attr("transform", `translate(${x}, ${y})`);
});
""",
            "known_issues": [
                "Gate-to-center mapping uses d.number % 9 (wrong)",
                "Gates arranged in circle around centers (wrong?)",
                "No gate-to-center lookup from bodygraph.yaml",
                "Channel paths may be incorrect",
            ]
        },
        "reference_files": {
            "bodygraph_yaml": "src/human_design/bodygraph.yaml",
            "gate_zodiac_mapping": "docs/gate-zodiac-mapping.md",
            "visualization_demo": "VISUALIZATION_DEMO.md",
            "current_visualization": "bodygraph_visualization.html",
        },
        "specifications": {
            "centers": 9,
            "gates": 64,
            "channels": 36,
            "d3_version": "v7",
            "svg_viewbox": "800x1000",
            "rebecca_energy_aesthetic": True,
        },
        "investigation_goals": [
            "Identify all geometry errors (centers, gates, channels)",
            "Extract correct geometry specs from authoritative sources",
            "Propose specific code fixes with correct coordinates/algorithms",
            "Validate fixes match Human Design system specifications",
        ]
    }

    # Create collaborative investigation strand (embedded agents only)
    strand = create_strand(
        problem=problem,
        agents=["researcher", "d3_specialist", "implementer"],
        strand_type="investigation",
        context=context
    )

    print("=" * 80)
    print("🔍 BODYGRAPH VISUALIZATION GEOMETRY REVIEW")
    print("=" * 80)
    print()
    print("🧵 Strand ID:", strand.definition.strand_id)
    print("👥 Team: researcher, d3_specialist, implementer")
    print()
    print("📋 Investigation Questions:")
    print("   1. What specific geometry issues exist?")
    print("   2. What are the correct bodygraph specifications?")
    print("   3. How should gates map to centers?")
    print("   4. How should we fix the implementation?")
    print()
    print("⏱️  Estimated: 10-15 minutes")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ INVESTIGATION COMPLETE")
    print("=" * 80)
    print()

    # Display all findings
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
                print(json.dumps(findings, indent=2))
        else:
            print(findings)
        print()

    print(f"📁 Full findings: strand-results/active/STRAND_{result.strand_id}.json")
    print()

    return result


if __name__ == "__main__":
    asyncio.run(main())
