"""Implement skill - Feature implementation with TDD using DODO-Lite."""

import asyncio
from typing import Optional


async def implement(
    feature: str,
    agents: Optional[list[str]] = None,
    tdd: bool = True,
    context: Optional[dict] = None,
) -> dict:
    """Implement feature using multi-agent TDD workflow.

    Args:
        feature: Feature description (natural language)
        agents: Optional agent list (defaults to implementer + test_engineer)
        tdd: Enable strict TDD workflow (tests first)
        context: Optional additional context

    Returns:
        Implementation results with code and tests
    """
    from human_design.strands import create_strand

    # Default agents for implementation
    if agents is None:
        # Check if feature mentions visualization
        if any(word in feature.lower() for word in ["visualize", "d3", "chart", "graph"]):
            agents = ["d3_specialist", "implementer", "test_engineer"]
        else:
            agents = ["implementer", "test_engineer"]

    # Build problem statement
    problem = f"Implement: {feature}. Create working implementation with comprehensive test suite."

    # Add context
    if context is None:
        context = {}
    context["feature"] = feature
    context["tdd"] = tdd
    context["implementation_type"] = "feature"

    # Create strand
    print(f"🚀 Implementing: {feature}")
    print(f"📋 Agents: {', '.join(agents)}")
    print(f"🧪 TDD Mode: {'Enabled' if tdd else 'Disabled'}")

    strand = create_strand(
        problem=problem,
        agents=agents,
        strand_type="implementation",
        context=context,
    )

    # Execute
    result = await strand.run()

    # Present results
    print(f"\n✅ Implementation complete!")
    print(f"📊 Status: {result.status}")

    if result.findings:
        print(f"\n📁 Artifacts:")
        for agent_name, finding in result.findings.items():
            if "files_created" in finding:
                for file in finding["files_created"]:
                    print(f"  • {file}")

    return {
        "feature": feature,
        "agents": agents,
        "tdd": tdd,
        "status": result.status,
        "findings": result.findings,
        "strand_id": result.strand_id,
    }


def main(args: str) -> None:
    """CLI entry point for implement skill.

    Args:
        args: Feature description with optional flags
    """
    # Parse arguments
    parts = args.split()
    if not parts:
        print("Error: Feature description required")
        return

    # Check for flags
    tdd = "--tdd" in parts
    if tdd:
        parts.remove("--tdd")

    # Look for --agents flag
    agents = None
    if "--agents" in parts:
        idx = parts.index("--agents")
        if idx + 1 < len(parts):
            agents = parts[idx + 1].split(",")
            parts = parts[:idx]  # Remove flag from feature description

    # Feature is remaining parts
    feature = " ".join(parts)

    # Execute implementation
    result = asyncio.run(implement(feature, agents, tdd))

    print(f"\n🎯 Implementation ID: {result['strand_id']}")
    print(f"📁 Results saved to: strand-results/active/")
