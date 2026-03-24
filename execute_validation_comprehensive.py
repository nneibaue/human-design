#!/usr/bin/env python3
"""Execute comprehensive agent training validation strand."""

import asyncio
import yaml
import sys
import os
from pathlib import Path

# Change to human-design directory before loading DODO
human_design_dir = Path(__file__).parent.absolute()
os.chdir(human_design_dir)
print(f"✓ Changed working directory to: {os.getcwd()}")

# Add DODO to path


from human_design.strands import create_strand

async def execute_strand():
    """Execute the comprehensive validation strand."""
    base_dir = Path(__file__).parent
    seed_path = base_dir / "strand-results/seeds/SEED_agent_training_validation_comprehensive.yaml"

    print(f"🧵 Loading seed: {seed_path}")
    seed = yaml.safe_load(seed_path.read_text())

    print(f"📋 Problem: {seed['problem']['description'][:150]}...")
    print(f"👥 Agents: {', '.join(a['role'] for a in seed['agents'])}")
    print()

    # Build context
    context = {
        "problem": seed['problem'],
        "agents": seed['agents'],
        "expected_artifacts": seed['expected_artifacts'],
        "timeline": seed['timeline'],
    }

    print("Creating validation strand...")
    strand = create_strand(
        problem=seed['problem']['description'],
        agents=[a['role'] for a in seed['agents']],
        strand_type="LDIAGNOSTIC",
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print()
    print("▶️  Executing comprehensive validation...")
    print("   Zero tolerance for Pydantic v1 patterns")
    print("   Estimated: 15-20 minutes")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Status: {result.status}")
    if hasattr(result, 'duration_seconds') and result.duration_seconds:
        print(f"Duration: {result.duration_seconds/60:.1f} min")
    print()

    return strand

if __name__ == "__main__":
    try:
        strand = asyncio.run(execute_strand())
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation strand interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
