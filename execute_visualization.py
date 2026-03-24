#!/usr/bin/env python3
"""Execute bodygraph visualization strand - custom D3 implementation from scratch."""

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
    """Execute the bodygraph visualization strand."""
    base_dir = Path(__file__).parent
    seed_path = base_dir / "strand-results/seeds/SEED_medium_priority_visualization.yaml"

    print("🎨 BODYGRAPH VISUALIZATION STRAND")
    print("=" * 80)
    print("Philosophy: Custom D3 implementation from scratch")
    print("Goal: Full ontological control over visualization system")
    print("Approach: Learn from 64keys, build something BETTER")
    print("=" * 80)
    print()

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

    # Add visualization context if present
    if 'context' in seed:
        context.update(seed['context'])

    print("Creating visualization strand...")
    strand = create_strand(
        problem=seed['problem']['description'],
        agents=[a['role'] for a in seed['agents']],
        strand_type="LIMPLEMENTATION",
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print()
    print("▶️  Executing visualization design & implementation...")
    print("   1. Study 64keys approach (reference only)")
    print("   2. Design custom D3 architecture (ontological control)")
    print("   3. Implement renderer (Python + D3.js)")
    print("   4. Apply Rebecca Energy aesthetic")
    print("   5. Validate accuracy & beauty")
    print()
    print("   Estimated: 18-22 minutes")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("🎨 VISUALIZATION STRAND COMPLETE")
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
        print("\n\n⚠️  Visualization strand interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
