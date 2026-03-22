#!/usr/bin/env python3
"""
Execute review strand to synthesize 64keys findings into actionable specs.

This strand transforms the research findings from strand 3f0f38f7 into
production-ready implementation specifications.
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
sys.path.insert(0, str(Path.home() / "code/claude/he360-dodo"))

from he360_dodo import create_strand, StrandType

async def main():
    print("📋 64keys Findings Review Strand")
    print("=" * 80)
    print("Input: Strand 3f0f38f7 findings")
    print("Output: Actionable implementation specifications")
    print("=" * 80)
    print()

    # Base directory (human-design repo)
    base_dir = Path(__file__).parent

    # Load seed specification
    seed_path = base_dir / 'SEED_64keys_findings_review.json'
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
        "parent_strand": seed['context']['parent_strand'],
        "key_discoveries": seed['context']['key_discoveries'],
        "review_tasks": seed['context']['review_tasks'],
        "output_requirements": seed['context']['output_requirements'],
        "phases": seed['phases'],
        "expected_artifacts": seed['expected_artifacts'],
        "success_criteria": seed['success_criteria'],
        "constraints": seed['constraints']
    }

    print("Creating review strand in fork space...")
    print()

    # Create strand
    # Using SYNAPSE type for inter-strand transformation/synthesis
    strand = create_strand(
        problem=seed['problem'],
        agents=seed['agents'],
        strand_type=StrandType.SYNAPSE,
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Repository path: {base_dir}")
    print(f"✓ Working directory: {Path.cwd()}")
    print(f"Strand ID: {strand.definition.strand_id}")
    print()
    print("Executing 5-agent synthesis workflow:")
    print("  Phase 1: API architecture design (architect)")
    print("  Phase 2: HD ontology construction (ontologist)")
    print("  Phase 3: Channel logic specification (architect)")
    print("  Phase 4: Visual design (color palette + SVG architecture)")
    print("  Phase 5: Validation (fair_witness)")
    print("  Phase 6: Implementation roadmap synthesis (coordinator)")
    print()
    print("⏳ This will take 8-15 minutes...")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("🎉 REVIEW STRAND COMPLETE")
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

    result_file = strand_results_dir / f'STRAND_review_{strand.definition.strand_id[:8]}.json'
    result_data = {
        "strand_id": strand.definition.strand_id,
        "problem": seed['problem'],
        "status": str(result.status),
        "parent_strand": seed['context']['parent_strand']['strand_id'],
        "metadata": seed['metadata']
    }
    if hasattr(result, 'duration_seconds'):
        result_data["duration_seconds"] = result.duration_seconds
    if hasattr(result, 'total_tokens'):
        result_data["total_tokens"] = result.total_tokens
    if hasattr(result, 'findings'):
        result_data["findings"] = result.findings
    if hasattr(result, 'synthesis'):
        result_data["synthesis"] = result.synthesis

    result_file.write_text(json.dumps(result_data, indent=2))

    print(f"✅ Results saved: {result_file}")
    print()

    # Extract and save phase artifacts
    print("📦 Extracting specification artifacts:")
    if hasattr(result, 'findings') and result.findings:
        if isinstance(result.findings, dict):
            for agent_name, content in result.findings.items():
                if content and agent_name not in ['_hemn_space', '_token_usage']:
                    artifact_file = strand_results_dir / f'SPEC_{agent_name}.md'
                    artifact_file.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
                    print(f"  ✓ {artifact_file.name}")

    print()

    # Save synthesis
    if hasattr(result, 'synthesis') and result.synthesis:
        synthesis_file = strand_results_dir / f'IMPLEMENTATION_ROADMAP_{strand.definition.strand_id[:8]}.md'
        synthesis_content = result.synthesis if isinstance(result.synthesis, str) else json.dumps(result.synthesis, indent=2)
        synthesis_file.write_text(synthesis_content)
        print(f"✅ Implementation roadmap: {synthesis_file}")

    print()
    print("🌿 Git fork space status:")
    print(f"  Branch: strand/{seed['metadata']['seed_type']}/{strand.definition.strand_id[:8]}")
    print(f"  Commits: Automatic commits per phase")
    print(f"  Location: {base_dir}")
    print()
    print("📋 Deliverables:")
    print("  ✓ API design for chart combinations (InteractionChart, PentaChart, TransitOverlay)")
    print("  ✓ Complete HD ontology JSON (Types, Authorities, Profiles, Channels)")
    print("  ✓ Channel formation logic specification")
    print("  ✓ Rebecca Energy color palette")
    print("  ✓ SVG chart visualization architecture")
    print("  ✓ 5-week implementation roadmap")
    print()
    print("Next: Review specifications and begin implementation!")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Review strand interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
