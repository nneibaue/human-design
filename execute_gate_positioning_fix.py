#!/usr/bin/env python3
"""Strand to implement directional gate positioning in bodygraph visualization.

Multi-agent implementation:
- implementer: Implement gate positioning algorithm that places gates toward their channel partners
- d3_specialist: Update D3.js code to use directional positioning
- python_linguist: Review code quality and suggest improvements
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from human_design.strands import create_strand


async def main():
    """Execute gate positioning fix strand with Opus."""

    # Verify API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return

    problem = """IMPLEMENT DIRECTIONAL GATE POSITIONING IN BODYGRAPH VISUALIZATION

CURRENT ISSUE:
Gates are distributed evenly around their center's perimeter, but this ignores the
DIRECTION each gate should face - toward the other center it connects to via its channel.

EXAMPLE OF THE PROBLEM:
- Channel 1-8 connects gate 1 (IDENTITY center) to gate 8 (EXPRESSION center)
- Currently: Gate 1 could be anywhere around IDENTITY perimeter
- Should be: Gate 1 positioned on IDENTITY perimeter FACING EXPRESSION center
- Same for gate 8: positioned on EXPRESSION perimeter FACING IDENTITY center

This makes channels connect gates that are pointing toward each other, creating
proper visual flow.

IMPLEMENTATION REQUIREMENTS:

1. For each gate, determine its channel partner(s)
2. Calculate the direction vector from gate's center to partner's center
3. Position gate on center perimeter at the correct angle (facing partner)
4. Handle gates with multiple channels (position toward primary partner)
5. Handle gates with no channels (distribute around perimeter as fallback)

FILES TO MODIFY:
- create_sample_visualization.py (Python gate positioning logic, lines 469-494)
- Generated bodygraph_visualization.html (JavaScript gate positioning)

CONTEXT FROM PREVIOUS INVESTIGATION:
The Opus researcher and implementer both identified this as the key fix:
"Each gate should be positioned ON THE EDGE of its center, on the side
FACING the partner center it connects to via channels."

EXPECTED OUTPUT:
1. Updated Python code in create_sample_visualization.py
2. Working JavaScript implementation in the HTML template
3. Regenerated bodygraph_visualization.html showing correct gate placement
4. Clear comments explaining the directional algorithm
"""

    context = {
        "current_implementation": {
            "file": "create_sample_visualization.py",
            "gate_positioning_code": """
// Current implementation (lines 469-494)
const gatePositions = {};
data.gates.forEach(g => {
    const centerName = data.gate_to_center[g.number];
    const center = data.centers.find(c => c.name === centerName);

    // Get all gates for this center
    const centerGates = data.gates
        .filter(gate => data.gate_to_center[gate.number] === centerName)
        .map(gate => gate.number)
        .sort((a, b) => a - b);

    // Current: distribute evenly around perimeter (WRONG)
    const index = centerGates.indexOf(g.number);
    const total = centerGates.length;
    const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
    const radius = 45;

    gatePositions[g.number] = {
        x: center.x + Math.cos(angle) * radius,
        y: center.y + Math.sin(angle) * radius
    };
});
""",
            "channels_data": "data.channels contains gate_a, gate_b pairs",
        },
        "required_algorithm": {
            "description": "Directional gate positioning toward channel partners",
            "steps": [
                "1. Build gate->channel lookup (which channels use this gate)",
                "2. For each gate, find channel partner gate(s)",
                "3. Get partner gate's center position",
                "4. Calculate angle from gate's center toward partner's center",
                "5. Position gate at that angle on center perimeter",
                "6. Fallback: gates without channels use even distribution",
            ],
            "pseudocode": """
for each gate:
    if gate has channel:
        partner_gate = channel.other_gate
        partner_center = get_center(partner_gate)
        direction = atan2(partner_center.y - my_center.y,
                         partner_center.x - my_center.x)
        gate.position = {
            x: my_center.x + radius * cos(direction),
            y: my_center.y + radius * sin(direction)
        }
    else:
        # Fallback: distribute evenly
        gate.position = even_distribution(gate, center)
""",
        },
        "test_data": {
            "channels": [
                {"gate_a": 1, "gate_b": 8, "from_center": "IDENTITY", "to_center": "EXPRESSION"},
                {"gate_a": 19, "gate_b": 49, "from_center": "DRIVE", "to_center": "EMOTION"},
            ],
            "expected_behavior": "Gate 1 should point from IDENTITY toward EXPRESSION",
        },
        "reference_files": [
            "create_sample_visualization.py",
            "bodygraph_visualization.html (generated)",
            "strand-results/active/STRAND_eae53549-f8dc-4ac8-81aa-271c53fa4bd4.json (previous Opus investigation)",
        ],
    }

    # Create strand with implementation team
    strand = create_strand(
        problem=problem,
        agents=["implementer", "d3_specialist", "python_linguist"],
        strand_type="implementation",
        context=context
    )

    print("=" * 80)
    print("🔧 DIRECTIONAL GATE POSITIONING IMPLEMENTATION")
    print("=" * 80)
    print()
    print("🧵 Strand ID:", strand.definition.strand_id)
    print("👥 Team: implementer, d3_specialist, python_linguist")
    print("🎯 Model: Opus 4.6 (via AGENT_MODEL env var)")
    print()
    print("📋 Implementation Goals:")
    print("   1. Position gates toward their channel partners")
    print("   2. Update both Python and JavaScript code")
    print("   3. Regenerate visualization with correct geometry")
    print()
    print("⏱️  Estimated: 8-12 minutes")
    print()

    # Execute strand with Opus
    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ IMPLEMENTATION COMPLETE")
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
                print(json.dumps(findings, indent=2))
        else:
            print(findings)
        print()

    print(f"📁 Full findings: strand-results/active/STRAND_{result.strand_id}.json")
    print()

    return result


if __name__ == "__main__":
    asyncio.run(main())
