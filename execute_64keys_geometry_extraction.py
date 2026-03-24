#!/usr/bin/env python3
"""Large multi-agent strand to extract and implement 64keys bodygraph geometry.

DISCOVERY: 64keys uses ROTATED RECTANGLES for gates, not circles!
- Each gate is a 3px wide rectangle
- Gates are ROTATED using SVG transform matrices to point along channels
- Uses gradients to show conscious/unconscious/emergent states

TEAM COMPOSITION:
- 2x d3_specialist: One for SVG analysis, one for D3.js implementation
- 2x implementer: One for Python, one for geometry extraction
- 1x researcher: Extract complete gate positioning data from bg_example.html
- 1x python_linguist: Code quality review
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from human_design.strands import create_strand


async def main():
    """Execute 64keys geometry extraction and implementation."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found")
        return

    problem = """EXTRACT AND IMPLEMENT 64KEYS BODYGRAPH GEOMETRY

CRITICAL DISCOVERY FROM bg_example.html:
64keys does NOT use circles for gates. Gates are RECTANGLES (3px wide bars)
that are ROTATED to point along channel directions!

EXAMPLE FROM bg_example.html (lines 241-242):
```xml
<g id="gate34">
  <rect fill="url(#linearGradientOrangeBlue)"
        height="55.88" width="3"
        transform="matrix(.5735,-.8192,.8192,.5735,-226.9276,297.8299)"
        x="171.23" y="338.9"></rect>
</g>
```

This rect is ROTATED using a transform matrix to align with the channel direction.

INVESTIGATION TASKS:

1. SCRAPING TEAM (researcher):
   - Read bg_example.html completely
   - Extract ALL gate positioning data (x, y, transform matrices)
   - Document the SVG structure (viewBox, coordinate system)
   - Find center positions from the SVG
   - Map gate numbers to their rect elements

2. GEOMETRY ANALYSIS (d3_specialist #1):
   - Analyze the SVG transform matrices
   - Understand how gates rotate to point along channels
   - Document the gradient usage (linearGradientOrangeBlue)
   - Extract the color scheme

3. IMPLEMENTATION (implementer #1 + d3_specialist #2):
   - Implement gate rendering as rotated rectangles (not circles)
   - Calculate rotation angles from gate's center toward channel partner
   - Use SVG rect elements with proper transforms
   - Apply gradients for conscious/unconscious states

4. PYTHON DATA LAYER (implementer #2):
   - Update bodygraph_to_d3_json() to include rotation angles
   - Calculate gate positions + rotation for each gate
   - Handle gates with multiple channels (average rotation)

5. CODE REVIEW (python_linguist):
   - Review all implementations
   - Ensure consistency
   - Validate against 64keys reference

FILES TO ANALYZE:
- bg_example.html (177KB, complete 64keys bodygraph example)
- create_sample_visualization.py (our current implementation)

FILES TO UPDATE:
- create_sample_visualization.py (Python: add rotation calculation)
- Generated HTML template (D3.js: use <rect> with transforms)

KEY INSIGHT:
Gates pointing toward their channel partners makes the bodygraph LOOK RIGHT.
This is why our current visualization looks "disfigured" - we use circles
instead of directional bars.
"""

    context = {
        "reference_file": {
            "path": "bg_example.html",
            "size": "177KB",
            "svg_id": "Bodygraph_v1",
            "viewBox": "0 0 355 479.88483",
            "key_discovery": "Gates are 3px wide rotated rectangles, not circles",
        },
        "example_gate_svg": {
            "gate_31": '<rect fill="#FFF" height="15.99" width="3" x="196.5" y="289.453"></rect>',
            "gate_34_rotated": '<rect fill="url(#linearGradientOrangeBlue)" height="55.88" width="3" transform="matrix(.5735,-.8192,.8192,.5735,-226.9276,297.8299)" x="171.23" y="338.9"></rect>',
            "gate_44_rotated": '<rect fill="#dc7221" height="44" width="3" transform="matrix(-.259,-.9659,.9659,-.259,-150.7011,614.5034)" x="159.15" y="343.062"></rect>',
        },
        "gradient_colors": {
            "conscious": "#dc7221 (orange)",
            "unconscious": "#4d6d90 (blue)",
            "emergent": "url(#linearGradientOrangeBlue)",
        },
        "current_issues": [
            "Using circles instead of rectangles for gates",
            "No rotation/directionality for gates",
            "Channels don't align visually with gate orientations",
            "Missing the 'flow' that 64keys visualization has",
        ],
        "implementation_requirements": [
            "Use SVG <rect> for gates (3px wide)",
            "Calculate rotation angle for each gate toward channel partner",
            "Apply SVG transform: rotate(angle, cx, cy) or matrix",
            "Use proper gradients for activation states",
            "Ensure channels connect to the END of rotated rects",
        ],
    }

    # Large team: multiple specialists working in parallel
    strand = create_strand(
        problem=problem,
        agents=[
            "researcher",           # Scrape bg_example.html
            "d3_specialist",       # Analyze SVG structure
            "d3_specialist",       # Implement D3.js visualization
            "implementer",         # Python geometry calculation
            "implementer",         # Update create_sample_visualization.py
            "python_linguist",     # Code review
        ],
        strand_type="implementation",
        context=context
    )

    print("=" * 80)
    print("🔬 64KEYS BODYGRAPH GEOMETRY EXTRACTION & IMPLEMENTATION")
    print("=" * 80)
    print()
    print("🧵 Strand ID:", strand.definition.strand_id)
    print("👥 Large Team: 6 agents")
    print("   - 1 researcher (scraping)")
    print("   - 2 d3_specialists (SVG analysis + D3 implementation)")
    print("   - 2 implementers (Python geometry + integration)")
    print("   - 1 python_linguist (code review)")
    print()
    print("🎯 Model: Opus 4.6")
    print()
    print("🔍 Key Discovery:")
    print("   64keys uses ROTATED RECTANGLES for gates, not circles!")
    print("   Each gate is a 3px wide bar that points along its channel.")
    print()
    print("📋 Tasks:")
    print("   1. Extract all gate SVG data from bg_example.html")
    print("   2. Analyze rotation transform matrices")
    print("   3. Implement rect-based gate rendering")
    print("   4. Calculate rotation angles in Python")
    print("   5. Update D3.js visualization")
    print()
    print("⏱️  Estimated: 15-20 minutes (large team, thorough work)")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ EXTRACTION & IMPLEMENTATION COMPLETE")
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
                # Truncate large findings for readability
                if len(str(findings)) > 5000:
                    print("[Large output - see full findings in JSON]")
                    print(json.dumps(findings, indent=2)[:2000] + "\n... [truncated]")
                else:
                    print(json.dumps(findings, indent=2))
        else:
            if len(str(findings)) > 5000:
                print(str(findings)[:2000] + "\n... [truncated]")
            else:
                print(findings)
        print()

    print(f"📁 Full findings: strand-results/active/STRAND_{result.strand_id}.json")
    print()

    return result


if __name__ == "__main__":
    asyncio.run(main())
