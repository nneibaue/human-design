"""Visualize skill - D3.js visualization creation using DODO-Lite."""

import asyncio
from typing import Optional


async def visualize(
    description: str,
    features: Optional[list[str]] = None,
    agents: Optional[list[str]] = None,
    context: Optional[dict] = None,
) -> dict:
    """Create D3.js visualization using d3_specialist agent.

    Args:
        description: Visualization description (natural language)
        features: Optional interaction features (hover, click, zoom)
        agents: Optional agent list (defaults to d3_specialist)
        context: Optional additional context

    Returns:
        Visualization results with D3 code and styling
    """
    from human_design.strands import create_strand

    # Default agents for visualization
    if agents is None:
        agents = ["d3_specialist"]

    # Default features
    if features is None:
        features = ["hover"]  # Basic hover by default

    # Build problem statement
    problem = f"Create D3.js visualization: {description}. Use Rebecca Energy aesthetic and modern D3 v7 patterns."

    # Add context
    if context is None:
        context = {}
    context["visualization"] = description
    context["features"] = features
    context["style"] = "rebecca_energy"
    context["d3_version"] = "v7"

    # Create strand
    print(f"🎨 Creating visualization: {description}")
    print(f"📋 Agents: {', '.join(agents)}")
    print(f"✨ Features: {', '.join(features)}")

    strand = create_strand(
        problem=problem,
        agents=agents,
        strand_type="visualization",
        context=context,
    )

    # Execute
    result = await strand.run()

    # Present results
    print(f"\n✅ Visualization complete!")
    print(f"📊 Status: {result.status}")

    if result.findings:
        print(f"\n📁 Artifacts:")
        for agent_name, finding in result.findings.items():
            if "files_created" in finding:
                for file in finding["files_created"]:
                    print(f"  • {file}")

    return {
        "visualization": description,
        "features": features,
        "agents": agents,
        "status": result.status,
        "findings": result.findings,
        "strand_id": result.strand_id,
    }


def main(args: str) -> None:
    """CLI entry point for visualize skill.

    Args:
        args: Visualization description with optional flags
    """
    # Parse arguments
    parts = args.split()
    if not parts:
        print("Error: Visualization description required")
        return

    # Look for --features flag
    features = None
    if "--features" in parts:
        idx = parts.index("--features")
        if idx + 1 < len(parts):
            features = parts[idx + 1].split(",")
            parts = parts[:idx] + parts[idx + 2:]

    # Look for --agents flag
    agents = None
    if "--agents" in parts:
        idx = parts.index("--agents")
        if idx + 1 < len(parts):
            agents = parts[idx + 1].split(",")
            parts = parts[:idx] + parts[idx + 2:]

    # Description is remaining parts
    description = " ".join(parts)

    # Execute visualization
    result = asyncio.run(visualize(description, features, agents))

    print(f"\n🎯 Visualization ID: {result['strand_id']}")
    print(f"📁 Results saved to: strand-results/active/")
    print(f"\n💡 Tip: Check static/js/ and static/css/ for generated files")
