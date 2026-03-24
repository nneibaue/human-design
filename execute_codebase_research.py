#!/usr/bin/env python3
"""Use researcher to extract additional patterns from the human-design codebase.

This complements the initial training by finding real examples of:
1. Composite chart patterns (bodygraph + bodygraph = composite)
2. Type-safe API operations
3. Test patterns and fixtures
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from human_design.agents.researcher import ResearcherAgent, ResearcherConfig


async def research_codebase_patterns():
    """Extract patterns from the human-design codebase."""

    print("=" * 80)
    print("🔬 CODEBASE PATTERN RESEARCH: Human Design Repository")
    print("=" * 80)
    print()

    # Create researcher
    config = ResearcherConfig(workspace_root=Path.cwd())
    researcher = ResearcherAgent(config)

    # Research queries for patterns in the current codebase
    queries = [
        {
            "query": "Find composite chart patterns (__add__ operator for bodygraph composition)",
            "query_type": "best_practices",
            "context": {
                "domain": "composite_charts",
                "focus": ["__add__ magic methods", "bodygraph composition", "channel merging"],
                "file_patterns": ["**/models/composite.py", "**/models/bodygraph.py"],
            }
        },
        {
            "query": "Find type-safe repository patterns for Person and Relationship storage",
            "query_type": "best_practices",
            "context": {
                "domain": "storage_patterns",
                "focus": ["type-safe CRUD", "UUID handling", "JSON serialization"],
                "file_patterns": ["**/storage/**/*.py", "**/api/operations.py"],
            }
        },
        {
            "query": "Find pytest patterns (parametrized tests, fixtures, test organization)",
            "query_type": "best_practices",
            "context": {
                "domain": "testing",
                "focus": ["@pytest.mark.parametrize", "fixture factories", "conftest.py"],
                "file_patterns": ["tests/**/*.py", "**/conftest.py"],
            }
        },
        {
            "query": "Find evolution of RawBodyGraph model (git history of refactorings)",
            "query_type": "evolution_analysis",
            "context": {
                "file_path": "src/human_design/models/bodygraph.py",
                "focus": "Pydantic v2 migration, computed_field additions, type annotations",
            }
        },
    ]

    all_findings = []

    for idx, query_spec in enumerate(queries, 1):
        print(f"📚 Research Query {idx}/{len(queries)}: {query_spec['query']}")
        print(f"   Type: {query_spec['query_type']}")
        print()

        result = await researcher.research(
            query=query_spec["query"],
            query_type=query_spec["query_type"],
            context=query_spec["context"]
        )

        all_findings.append(result)
        print(f"✅ Research complete: {result['status']}")
        print()

    print("=" * 80)
    print("📝 CODEBASE RESEARCH SUMMARY")
    print("=" * 80)
    print()

    # Save research findings
    research_output = Path("strand-results/active/CODEBASE_RESEARCH.md")
    research_output.parent.mkdir(parents=True, exist_ok=True)

    with open(research_output, "w") as f:
        f.write("# Human Design Codebase Pattern Research\n\n")
        f.write("Extracted patterns from the human-design repository.\n\n")

        for idx, finding in enumerate(all_findings, 1):
            f.write(f"## Research Query {idx}: {finding['query']}\n\n")
            f.write(f"**Type**: {finding['query_type']}\n\n")
            f.write(f"**Findings**:\n\n")
            if 'findings' in finding:
                f.write(f"{finding['findings']}\n\n")
            f.write("---\n\n")

    print(f"💾 Research findings saved to: {research_output}")
    print()
    print("Next step: Review patterns for additional agent training material")


if __name__ == "__main__":
    try:
        asyncio.run(research_codebase_patterns())
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
