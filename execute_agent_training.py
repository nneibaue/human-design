#!/usr/bin/env python3
"""Train the implementer agent with modern Python/FastAPI/pydantic-ai patterns.

Uses the researcher agent to extract patterns from:
1. FastAPI GitHub repo examples
2. pydantic-ai documentation
3. Modern Python typing patterns

Then updates the implementer agent's system prompt with findings.
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from human_design.agents.researcher import ResearcherAgent, ResearcherConfig


async def train_implementer():
    """Use researcher agent to train implementer with modern patterns."""

    print("=" * 80)
    print("🎓 AGENT TRAINING: Implementer with Modern Python Patterns")
    print("=" * 80)
    print()

    # Create researcher
    config = ResearcherConfig(workspace_root=Path.cwd())
    researcher = ResearcherAgent(config)

    # Research modern Python/FastAPI/pydantic patterns
    queries = [
        {
            "query": "Find modern FastAPI endpoint patterns with async/await, dependency injection, and error handling",
            "query_type": "best_practices",
            "context": {
                "domain": "fastapi",
                "focus": ["async patterns", "dependency injection", "HTTPException usage", "response models"],
                "file_patterns": ["**/web/**/*.py", "**/api/**/*.py"],
            }
        },
        {
            "query": "Find Pydantic v2 field validator and model_config patterns",
            "query_type": "best_practices",
            "context": {
                "domain": "pydantic_v2",
                "focus": ["@field_validator", "model_config", "@computed_field", "Annotated types"],
                "file_patterns": ["**/models/**/*.py"],
            }
        },
        {
            "query": "Find modern Python typing patterns (Annotated, Literal, Protocol)",
            "query_type": "best_practices",
            "context": {
                "domain": "python_typing",
                "focus": ["Annotated with Field", "Literal types", "Protocol", "TypedDict"],
                "file_patterns": ["**/*.py"],
            }
        },
        {
            "query": "Identify Pydantic v1 anti-patterns still in use",
            "query_type": "anti_patterns",
            "context": {
                "pattern": "pydantic_v1_legacy",
                "look_for": ["class Config:", "@validator", ".dict()", "__root__"],
                "severity": "high",
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
    print("📝 TRAINING SUMMARY")
    print("=" * 80)
    print()

    # Aggregate findings
    for idx, finding in enumerate(all_findings, 1):
        print(f"\n{idx}. {finding['query']}")
        print(f"   Type: {finding['query_type']}")
        print(f"   Status: {finding['status']}")
        if 'findings' in finding:
            print(f"\n   Findings:")
            print(f"   {finding['findings']}")
        print()

    # Save training material
    training_output = Path("strand-results/active/IMPLEMENTER_TRAINING.md")
    training_output.parent.mkdir(parents=True, exist_ok=True)

    with open(training_output, "w") as f:
        f.write("# Implementer Agent Training Material\n\n")
        f.write("Extracted modern Python/FastAPI/pydantic patterns for agent training.\n\n")

        for idx, finding in enumerate(all_findings, 1):
            f.write(f"## Research Query {idx}: {finding['query']}\n\n")
            f.write(f"**Type**: {finding['query_type']}\n\n")
            f.write(f"**Findings**:\n\n")
            if 'findings' in finding:
                f.write(f"{finding['findings']}\n\n")
            f.write("---\n\n")

    print(f"💾 Training material saved to: {training_output}")
    print()
    print("Next step: Update src/human_design/agents/implementer.py")
    print("with extracted patterns")


if __name__ == "__main__":
    try:
        asyncio.run(train_implementer())
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
