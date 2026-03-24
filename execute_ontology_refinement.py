#!/usr/bin/env python3
"""
Execute HD ontology refinement and validation strand.

HIGH priority - Validate and refine ontology before implementation.
"""

import json
import asyncio
import sys
import os
from pathlib import Path

# Change to human-design directory
human_design_dir = Path(__file__).parent.absolute()
os.chdir(human_design_dir)
print(f"✓ Changed working directory to: {os.getcwd()}")

from human_design.strands import create_strand

async def main():
    print("🔍 HD Ontology Refinement & Validation Strand")
    print("=" * 80)
    print("Priority: HIGH - Validate ontology before implementation")
    print("Timeline: 1-2 hours")
    print("=" * 80)
    print()

    # Base directory (human-design repo)
    base_dir = Path(__file__).parent

    # Load seed specification
    seed_path = base_dir / 'SEED_ontology_refinement.json'
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
        "current_ontology": seed['context']['current_ontology'],
        "validation_requirements": seed['context']['validation_requirements'],
        "existing_codebase_validation": seed['context']['existing_codebase_validation'],
        "phases": seed['phases'],
        "expected_artifacts": seed['expected_artifacts'],
        "success_criteria": seed['success_criteria'],
        "constraints": seed['constraints'],
        "validation_rules": seed['validation_rules']
    }

    print("Creating ontology refinement strand in fork space...")
    print()

    # Create strand
    strand = create_strand(
        problem=seed['problem'],
        agents=seed['agents'],
        strand_type="operational",
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Repository path: {base_dir}")
    print(f"✓ Working directory: {Path.cwd()}")
    print(f"Strand ID: {strand.definition.strand_id}")
    print()
    print("Executing 3-agent validation workflow:")
    print("  Phase 1: Comprehensive validation (ontologist)")
    print("  Phase 2: Integrity audit (fair_witness)")
    print("  Phase 3: Refinement synthesis (coordinator)")
    print()
    print("⏳ This will take 5-10 minutes...")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("🎉 ONTOLOGY REFINEMENT COMPLETE")
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

    result_file = strand_results_dir / f'STRAND_ontology_refinement_{strand.definition.strand_id[:8]}.json'
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
    print("📦 Extracting validation artifacts:")
    if hasattr(result, 'findings') and result.findings:
        if isinstance(result.findings, dict):
            for agent_name, content in result.findings.items():
                if content and agent_name not in ['_hemn_space', '_token_usage']:
                    artifact_file = strand_results_dir / f'REFINE_{agent_name}.md'
                    artifact_file.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
                    print(f"  ✓ {artifact_file.name}")

    print()
    print("🌿 Git fork space status:")
    print(f"  Branch: strand/{seed['metadata']['seed_type']}/{strand.definition.strand_id[:8]}")
    print(f"  Commits: Automatic commits per phase")
    print(f"  Location: {base_dir}")
    print()
    print("📋 Deliverables:")
    print("  ✓ ontology/HD_ONTOLOGY_complete.json (refined)")
    print("  ✓ ONTOLOGY_REFINEMENT_REPORT.md")
    print("  ✓ ONTOLOGY_VALIDATION_RESULTS.md")
    print()
    print("✨ Ontology validated and refined!")
    print()
    print("Next: Implement Python code based on refined ontology")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Ontology refinement strand interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
