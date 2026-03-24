#!/usr/bin/env python3
"""Strand to fix gate positioning - gates must sit ON channel paths, not around centers.

CRITICAL INSIGHT FROM USER FEEDBACK:
The "channels" (brown lines) are just rectangles floating near gate numbers.
They don't actually connect different centers in a meaningful way.

THE FUNDAMENTAL PROBLEM:
We're positioning gates around center perimeters, then drawing channel lines
between those positions. This is backwards.

CORRECT APPROACH (64keys):
1. Channels are LINES between centers (IDENTITY → EXPRESSION)
2. Gates sit AT SPECIFIC POINTS along those channel lines
3. Gate 1 sits on the line near IDENTITY (30% along the path)
4. Gate 8 sits on the line near EXPRESSION (70% along the path)
5. Gates are colored segments OF the channel path

TEAM COMPOSITION:
- researcher: Deep analysis of bg_example.html to extract gate positions along channels
- d3_specialist: Implement proper channel path positioning
- implementer: Rewrite gate positioning algorithm
- python_linguist: Code review and validation
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from human_design.strands import create_strand


async def main():
    """Execute gate-on-channel-path fix."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found")
        return

    problem = """FIX GATE POSITIONING - GATES MUST SIT ON CHANNEL PATHS

USER FEEDBACK:
"The 'channels' are just rectangles that are on top of the gate number.
They don't connect the different centers."

ROOT CAUSE ANALYSIS:
Current implementation positions gates AROUND center perimeters, then draws
lines between gate positions. This creates disconnected visual elements.

CORRECT ARCHITECTURE (from 64keys):

Channel 1-8 connects IDENTITY center to EXPRESSION center:
- The CHANNEL is a LINE from IDENTITY (400, 505) to EXPRESSION (400, 340)
- Gate 1 sits ON THIS LINE at ~30% from IDENTITY toward EXPRESSION
  Position: IDENTITY + 0.3 * (EXPRESSION - IDENTITY)
  = (400, 505) + 0.3 * (0, -165)
  = (400, 455.5)
- Gate 8 sits ON THIS LINE at ~70% from IDENTITY toward EXPRESSION
  Position: IDENTITY + 0.7 * (EXPRESSION - IDENTITY)
  = (400, 505) + 0.7 * (0, -165)
  = (400, 389.5)

The gate rectangles (3px wide, ~20px tall) are ROTATED to align with the
channel direction and positioned directly on the path.

IMPLEMENTATION REQUIREMENTS:

1. For each channel (gate_a, gate_b):
   - Identify centerA (gate_a's center) and centerB (gate_b's center)
   - Calculate channel vector: V = centerB - centerA
   - Position gate_a at: centerA + t_a * V (where t_a ≈ 0.2-0.4)
   - Position gate_b at: centerA + t_b * V (where t_b ≈ 0.6-0.8)
   - Rotate both gates to align with vector V

2. For gates NOT in channels:
   - Position around center perimeter (current approach is OK)

3. Channel rendering:
   - Draw line from gate_a position to gate_b position
   - NOT from center to center
   - Gates appear as colored segments on the channel

RESEARCH TASKS:

1. Analyze bg_example.html to extract EXACT gate positions
   - Measure distances of gates along channel paths
   - Document the positioning algorithm 64keys uses
   - Extract the t-values (percentage along path) for each gate

2. Identify ALL channels and their gate pairs:
   - Channel 1-8: IDENTITY → EXPRESSION
   - Channel 19-49: DRIVE → EMOTION
   - ... (all 36 channels)

3. Calculate proper positioning for our coordinate system

EXPECTED OUTPUT:
- Gates positioned ON channel lines, not around centers
- Channels connecting gate positions (not center positions)
- Visual flow where gates are PART OF the channel paths
"""

    context = {
        "current_broken_approach": {
            "description": "Positioning gates around center perimeter, then drawing lines",
            "issue": "Gates and channels are visually disconnected",
            "example": "Gate 1 floats near IDENTITY, channel line is separate",
        },
        "correct_approach_64keys": {
            "description": "Gates positioned ALONG channel paths at specific distances",
            "algorithm": "gatePosition = centerA + t * (centerB - centerA)",
            "example": "Gate 1 at 30% along IDENTITY→EXPRESSION line",
        },
        "channels_to_fix": {
            "channel_1_8": {
                "gate_a": 1,
                "gate_b": 8,
                "center_a": "IDENTITY",
                "center_b": "EXPRESSION",
                "coords_a": "(400, 505)",
                "coords_b": "(400, 340)",
                "direction": "vertical",
            },
            "channel_19_49": {
                "gate_a": 19,
                "gate_b": 49,
                "center_a": "DRIVE",
                "center_b": "EMOTION",
                "coords_a": "(400, 850)",
                "coords_b": "(535, 620)",
                "direction": "diagonal",
            },
        },
        "reference_file": "bg_example.html",
        "files_to_modify": [
            "create_sample_visualization.py (Python: calculate positions along paths)",
            "HTML template (JavaScript: render gates on paths)",
        ],
        "key_insight": "Gates are not decorations around centers - they are segments OF the channel paths",
    }

    # Team to completely rewrite gate positioning
    strand = create_strand(
        problem=problem,
        agents=["researcher", "d3_specialist", "implementer", "python_linguist"],
        strand_type="implementation",
        context=context
    )

    print("=" * 80)
    print("🔧 FIX GATE POSITIONING - GATES ON CHANNEL PATHS")
    print("=" * 80)
    print()
    print("🧵 Strand ID:", strand.definition.strand_id)
    print("👥 Team: researcher, d3_specialist, implementer, python_linguist")
    print("🎯 Model: Opus 4.6")
    print()
    print("❌ Current Problem:")
    print("   Gates positioned around center perimeters")
    print("   Channels drawn as separate lines")
    print("   Result: disconnected, non-functional visualization")
    print()
    print("✅ Correct Approach:")
    print("   Gates positioned ALONG channel paths")
    print("   Gate position = centerA + t * (centerB - centerA)")
    print("   Gates are colored segments OF the channels")
    print()
    print("📋 Tasks:")
    print("   1. Analyze bg_example.html for exact gate positioning")
    print("   2. Calculate t-values (percentage along path) for each gate")
    print("   3. Rewrite positioning algorithm")
    print("   4. Render gates as segments on channel paths")
    print()
    print("⏱️  Estimated: 12-15 minutes")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ GATE POSITIONING FIX COMPLETE")
    print("=" * 80)
    print()

    # Display findings
    print("📊 IMPLEMENTATION RESULTS:")
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
                if len(str(findings)) > 3000:
                    print("[Large output - showing first 2000 chars]")
                    print(json.dumps(findings, indent=2)[:2000])
                    print("... [truncated]")
                else:
                    print(json.dumps(findings, indent=2))
        else:
            if len(str(findings)) > 3000:
                print(str(findings)[:2000] + "\n... [truncated]")
            else:
                print(findings)
        print()

    print(f"📁 Full findings: strand-results/active/STRAND_{result.strand_id}.json")
    print()

    return result


if __name__ == "__main__":
    asyncio.run(main())
