#!/usr/bin/env python3
"""Execute 64keys data backup strand - SQLite archive for decoupling."""

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
    """Execute the 64keys backup strand."""
    base_dir = Path(__file__).parent
    seed_path = base_dir / "strand-results/seeds/SEED_64keys_data_backup.yaml"

    print("🗄️  64KEYS DATA BACKUP STRAND")
    print("=" * 80)
    print("Goal: Decouple from 64keys.com by archiving data locally")
    print("Method: SQLModel ORM + SQLite database")
    print("Output: CLI command `hd backup-64keys`")
    print("Philosophy: Preserve their data while building independence")
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

    # Add problem context if present
    if 'context' in seed['problem']:
        context['problem_context'] = seed['problem']['context']

    print("Creating backup implementation strand...")
    strand = create_strand(
        problem=seed['problem']['description'],
        agents=[a['role'] for a in seed['agents']],
        strand_type="LIMPLEMENTATION",
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print()
    print("▶️  Executing 64keys backup implementation...")
    print("   1. Analyze current 64keys integration")
    print("   2. Design SQLModel schema")
    print("   3. Implement backup script")
    print("   4. Add CLI command")
    print("   5. Comprehensive tests")
    print("   6. Validate completeness")
    print()
    print("   Data to backup:")
    print("     • 64 gates × 6 lines = 384 line entries")
    print("     • 5 types, 7 authorities, 9 centers, 12 profiles")
    print("     • All 64keys-specific metadata")
    print()
    print("   Estimated: 15-20 minutes")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("🗄️  64KEYS BACKUP STRAND COMPLETE")
    print("=" * 80)
    print(f"Status: {result.status}")
    if hasattr(result, 'duration_seconds') and result.duration_seconds:
        print(f"Duration: {result.duration_seconds/60:.1f} min")
    print()
    print("Next steps:")
    print("  1. Run `hd backup-64keys` to create initial backup")
    print("  2. Update semantic loader to use local database")
    print("  3. Implement fallback (backup → API if missing)")
    print("  4. Eventually replace with custom semantic system")
    print()

    return strand

if __name__ == "__main__":
    try:
        strand = asyncio.run(execute_strand())
    except KeyboardInterrupt:
        print("\n\n⚠️  64keys backup strand interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
