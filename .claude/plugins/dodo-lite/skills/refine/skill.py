"""Refine skill - Multi-agent code refinement using DODO-Lite."""

import asyncio
from pathlib import Path
from typing import Optional


async def refine(target: str, agents: Optional[list[str]] = None, context: Optional[dict] = None) -> dict:
    """Refine code/agents using multi-agent investigation.

    Args:
        target: What to refine (file, agent, module, etc.)
        agents: Optional agent list (defaults to python_linguist + implementer)
        context: Optional additional context

    Returns:
        Refinement results with findings and recommendations
    """
    from human_design.strands import create_strand

    # Default agents for refinement
    if agents is None:
        agents = ["python_linguist", "implementer"]

    # Build problem statement
    problem = f"Refine {target}. Analyze current implementation, identify gaps, and provide actionable recommendations."

    # Add context
    if context is None:
        context = {}
    context["target"] = target
    context["refinement_type"] = "code_quality"

    # Create strand
    print(f"🔍 Refining: {target}")
    print(f"📋 Agents: {', '.join(agents)}")

    strand = create_strand(
        problem=problem,
        agents=agents,
        strand_type="refinement",
        context=context,
    )

    # Execute
    result = await strand.run()

    # Present results
    print(f"\n✅ Refinement complete!")
    print(f"📊 Status: {result.status}")

    if result.findings:
        print(f"\n📁 Findings:")
        for agent_name, finding in result.findings.items():
            print(f"  • {agent_name}: {finding.get('summary', 'N/A')}")

    return {
        "target": target,
        "agents": agents,
        "status": result.status,
        "findings": result.findings,
        "strand_id": result.strand_id,
    }


def main(args: str) -> None:
    """CLI entry point for refine skill.

    Args:
        args: Space-separated arguments (target, --agents, --context)
    """
    # Parse arguments
    parts = args.split()
    target = parts[0] if parts else "unknown"

    # Look for --agents flag
    agents = None
    if "--agents" in parts:
        idx = parts.index("--agents")
        if idx + 1 < len(parts):
            agents = parts[idx + 1].split(",")

    # Execute refinement
    result = asyncio.run(refine(target, agents))

    print(f"\n🎯 Refinement ID: {result['strand_id']}")
    print(f"📁 Results saved to: strand-results/active/")
