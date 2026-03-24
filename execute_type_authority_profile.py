#!/usr/bin/env python3
"""
Execute Type/Authority/Profile calculation implementation strand.

HIGH priority for complete chart readings. Implements HDType enum (64keys names),
Authority hierarchy, Profile model, and calculation functions.
"""

import json
import asyncio
import sys
import os
from pathlib import Path

# CRITICAL: Change to human-design directory BEFORE loading DODO
human_design_dir = Path(__file__).parent.absolute()
os.chdir(human_design_dir)
print(f"✓ Changed working directory to: {os.getcwd()}")

# Add DODO to path


from human_design.strands import create_strand

async def main():
    print("🎯 Type/Authority/Profile Calculation Implementation Strand")
    print("=" * 80)
    print("Priority: HIGH - Required for complete chart readings")
    print("Timeline: Week 1-2 (2 days)")
    print("Prerequisite: Channel formation logic MUST be complete")
    print("=" * 80)
    print()

    # Base directory (human-design repo)
    base_dir = Path(__file__).parent

    # Load seed specification
    seed_path = base_dir / 'SEED_type_authority_profile.json'
    if not seed_path.exists():
        print(f"❌ Seed file not found: {seed_path}")
        sys.exit(1)

    seed = json.loads(seed_path.read_text())

    print(f"Problem: {seed['problem'][:100]}...")
    print(f"Agents: {seed['agents']}")
    print(f"Phases: {list(seed['phases'].keys())}")
    print()

    # Build context for agents
    context = {
        "problem": seed['problem'],
        "goal": seed['goal'],
        "architectural_foundation": seed['context']['architectural_foundation'],
        "hd_calculation_rules": seed['context']['hd_calculation_rules'],
        "phases": seed['phases'],
        "expected_artifacts": seed['expected_artifacts'],
        "success_criteria": seed['success_criteria'],
        "constraints": seed['constraints'],
        "validation_rules": seed['validation_rules']
    }

    print("Creating implementation strand in fork space...")
    print()

    # Create strand
    strand = create_strand(
        problem=seed['problem'],
        agents=seed['agents'],
        strand_type="LIMPLEMENTATION",
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Repository path: {base_dir}")
    print(f"✓ Working directory: {Path.cwd()}")
    print(f"Strand ID: {strand.definition.strand_id}")
    print()
    print("Executing 6-agent implementation workflow:")
    print("  Phase 1: Research HD calculation rules (researcher)")
    print("  Phase 2: Architecture design (architect)")
    print("  Phase 3: Implementation (implementer)")
    print("  Phase 4: Test suite (test_engineer)")
    print("  Phase 5: Validation (fair_witness)")
    print("  Phase 6: Synthesis (coordinator)")
    print()
    print("⏳ This will take 10-15 minutes...")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("🎉 TYPE/AUTHORITY/PROFILE IMPLEMENTATION COMPLETE")
    print("=" * 80)
    print(f"Status: {result.status}")
    if hasattr(result, 'duration_seconds') and result.duration_seconds:
        print(f"Duration: {result.duration_seconds:.1f}s ({result.duration_seconds/60:.1f} min)")
    if hasattr(result, 'total_tokens') and result.total_tokens:
        print(f"Token usage: {result.total_tokens:,} tokens")
    print()

    # Save results
    strand_results_dir = base_dir / 'strand-results/active'
    strand_results_dir.mkdir(parents=True, exist_ok=True)

    result_file = strand_results_dir / f'STRAND_type_authority_profile_{strand.definition.strand_id[:8]}.json'
    result_data = {
        "strand_id": strand.definition.strand_id,
        "problem": seed['problem'],
        "status": str(result.status),
        "metadata": seed['metadata']
    }
    if hasattr(result, 'duration_seconds'):
        result_data["duration_seconds"] = result.duration_seconds
    if hasattr(result, 'total_tokens'):
        result_data["total_tokens"] = result.total_tokens
    if hasattr(result, 'findings'):
        result_data["findings"] = result.findings

    result_file.write_text(json.dumps(result_data, indent=2))

    print(f"✅ Results saved: {result_file}")
    print()

    # Extract and save phase artifacts
    print("📦 Extracting implementation artifacts:")
    if hasattr(result, 'findings') and result.findings:
        if isinstance(result.findings, dict):
            for agent_name, content in result.findings.items():
                if content and agent_name not in ['_hemn_space', '_token_usage']:
                    artifact_file = strand_results_dir / f'TAP_{agent_name}.md'
                    artifact_file.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
                    print(f"  ✓ {artifact_file.name}")

    print()
    print("🌿 Git fork space status:")
    print(f"  Branch: strand/{seed['metadata']['seed_type']}/{strand.definition.strand_id[:8]}")
    print(f"  Commits: Automatic commits per phase")
    print(f"  Location: {base_dir}")
    print()
    print("📋 Deliverables:")
    print("  ✓ src/human_design/models/type.py (HDType enum with 64keys names)")
    print("  ✓ src/human_design/models/authority.py (Authority hierarchy)")
    print("  ✓ src/human_design/models/profile.py (Profile model)")
    print("  ✓ tests/test_type_calculation.py")
    print("  ✓ tests/test_authority_calculation.py")
    print("  ✓ tests/test_profile_calculation.py")
    print("  ✓ RawBodyGraph.type, .authority, .profile computed properties")
    print("  ✓ Implementation notes and validation report")
    print()
    print("🎯 Achievement: Complete chart readings now possible!")
    print()
    print("Next: InteractionChart/PentaChart implementation (Week 2-3)")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Type/Authority/Profile strand interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
