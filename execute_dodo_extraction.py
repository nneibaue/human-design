#!/usr/bin/env python3
"""Execute DODO extraction strand - embed minimal strand executor in human-design."""

import asyncio
import yaml
import sys
import os
from pathlib import Path

# Change to human-design directory before loading DODO
human_design_dir = Path(__file__).parent.absolute()
os.chdir(human_design_dir)
print(f"✓ Changed working directory to: {os.getcwd()}")

# Add DODO to path (last time we'll need to do this!)


from human_design.strands import create_strand

async def execute_strand():
    """Execute the DODO extraction strand."""
    base_dir = Path(__file__).parent
    seed_path = base_dir / "strand-results/seeds/SEED_dodo_extraction.yaml"

    print("🌱 DODO EXTRACTION STRAND - Planting DODO's Seed")
    print("=" * 80)
    print("Goal: Make human-design self-sufficient for multi-agent strands")
    print("Method: Extract minimal executor (~200 lines) into src/human_design/strands/")
    print("Team: 10 agents (2 researchers, 1 architect, 4 implementers, 1 test, 1 witness, 1 coordinator)")
    print("=" * 80)
    print()

    seed = yaml.safe_load(seed_path.read_text())

    print(f"📋 Problem: {seed['problem']['description'][:150]}...")
    print(f"👥 Agents: {', '.join(a['role'] for a in seed['agents'])}")
    print(f"   Total: {len(seed['agents'])} agents")
    print()

    # Build context
    context = {
        "problem": seed['problem'],
        "agents": seed['agents'],
        "critical_files": seed['context']['critical_files'],
        "components_to_extract": seed['context']['components_to_extract'],
        "target_structure": seed['context']['target_structure'],
        "expected_artifacts": seed['expected_artifacts'],
        "success_criteria": seed['success_criteria'],
        "constraints": seed['constraints'],
        "validation_rules": seed['validation_rules'],
    }

    print("Creating DODO extraction strand...")
    strand = create_strand(
        problem=seed['problem']['description'],
        agents=[a['role'] for a in seed['agents']],
        strand_type="implementation",
        context=context,
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print()
    print("▶️  Executing DODO extraction...")
    print()
    print("   PHASE 1 - RESEARCH:")
    print("     • Analyze DODO architecture (builder, models, factory)")
    print("     • Study human-design patterns (execute_*.py, agents)")
    print()
    print("   PHASE 2 - DESIGN:")
    print("     • Design simplified executor (remove metabolization, anchors, signposting)")
    print("     • Plan hardcoded agent factory")
    print()
    print("   PHASE 3 - IMPLEMENTATION:")
    print("     • Extract models.py (~50 lines)")
    print("     • Extract builder.py (~200 lines)")
    print("     • Create agent_factory.py (hardcoded if/elif)")
    print("     • Create convenience.py and __init__.py")
    print("     • Update pyproject.toml (add 3 dependencies)")
    print("     • Update 12 execute_*.py scripts (import changes)")
    print()
    print("   PHASE 4 - VALIDATION:")
    print("     • Create tests/test_strands.py")
    print("     • Verify no DODO imports remain")
    print("     • Validate executor maintains correctness")
    print()
    print("   Estimated: 25-35 minutes (10 agents, high complexity)")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("🌱 DODO EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Status: {result.status}")
    if hasattr(result, 'duration_seconds') and result.duration_seconds:
        print(f"Duration: {result.duration_seconds/60:.1f} min")
    print()
    print("Deliverables:")
    print("  ✓ src/human_design/strands/ (5 files)")
    print("  ✓ tests/test_strands.py")
    print("  ✓ pyproject.toml (updated dependencies)")
    print("  ✓ execute_*.py scripts (12 files, imports changed)")
    print()
    print("Next: Test with `python execute_validation_comprehensive.py`")
    print()

    return strand

if __name__ == "__main__":
    try:
        strand = asyncio.run(execute_strand())
    except KeyboardInterrupt:
        print("\n\n⚠️  DODO extraction interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
