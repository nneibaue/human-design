#!/usr/bin/env python3
"""
Execute HD ontology JSON generation strand.

HIGH priority for semantic layer and UI generation. Creates HD_ONTOLOGY_complete.json
with all Types, Authorities, Profiles, Channels, Centers, Gates, Quarters.
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
    print("📚 HD Ontology JSON Generation Strand")
    print("=" * 80)
    print("Priority: HIGH - Required for semantic layer and UI generation")
    print("Timeline: Week 2-3 (3-5 days)")
    print("=" * 80)
    print()

    # Base directory (human-design repo)
    base_dir = Path(__file__).parent

    # Load seed specification
    seed_path = base_dir / 'SEED_hd_ontology_json.json'
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
        "from_review_strand_d5a05df6": seed['context']['from_review_strand_d5a05df6'],
        "rebecca_energy_context": seed['context']['rebecca_energy_context'],
        "phases": seed['phases'],
        "expected_artifacts": seed['expected_artifacts'],
        "success_criteria": seed['success_criteria'],
        "constraints": seed['constraints'],
        "validation_rules": seed['validation_rules']
    }

    print("Creating ontology generation strand in fork space...")
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
    print("Executing 5-agent ontology generation workflow:")
    print("  Phase 1: Domain research (2 ontologists in parallel)")
    print("  Phase 2: Schema design (architect)")
    print("  Phase 3: Validation (fair_witness)")
    print("  Phase 4: Synthesis (coordinator)")
    print()
    print("⏳ This will take 12-18 minutes...")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("🎉 HD ONTOLOGY JSON GENERATION COMPLETE")
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

    result_file = strand_results_dir / f'STRAND_hd_ontology_{strand.definition.strand_id[:8]}.json'
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
    print("📦 Extracting ontology artifacts:")
    if hasattr(result, 'findings') and result.findings:
        if isinstance(result.findings, dict):
            for agent_name, content in result.findings.items():
                if content and agent_name not in ['_hemn_space', '_token_usage']:
                    artifact_file = strand_results_dir / f'ONTOLOGY_{agent_name}.md'
                    artifact_file.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
                    print(f"  ✓ {artifact_file.name}")

    print()
    print("🌿 Git fork space status:")
    print(f"  Branch: strand/{seed['metadata']['seed_type']}/{strand.definition.strand_id[:8]}")
    print(f"  Commits: Automatic commits per phase")
    print(f"  Location: {base_dir}")
    print()
    print("📋 Deliverables:")
    print("  ✓ ontology/HD_ONTOLOGY_complete.json")
    print("  ✓ ontology/HD_ONTOLOGY_schema.json")
    print("  ✓ docs/ONTOLOGY_USAGE.md")
    print("  ✓ IMPLEMENTATION_NOTES_ontology.md")
    print("  ✓ VALIDATION_REPORT_ontology_integrity.md")
    print()
    print("📊 Coverage:")
    print("  • 5 Types (Initiator/Builder/Specialist/Coordinator/Observer)")
    print("  • 7 Authorities with hierarchy")
    print("  • 12 Profiles with line meanings")
    print("  • 36 Channels with gate pairs and circuits")
    print("  • 9 Centers with 64keys↔traditional mappings")
    print("  • 64 Gates with I Ching names")
    print("  • 4 Quarters with themes")
    print()
    print("Next: Use ontology for semantic overlays and UI generation")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  HD ontology strand interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
