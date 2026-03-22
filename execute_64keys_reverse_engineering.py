#!/usr/bin/env python3
"""
Execute 64keys reverse engineering strand in git fork space.

This strand researches 64keys endpoints, builds HD ontology, and designs
chart combination API for Rebecca's workflow.

Execution creates automatic git isolation branch for safe investigation.
"""

import json
import asyncio
import sys
import os
from pathlib import Path

# CRITICAL: Change to human-design directory BEFORE loading DODO
# This ensures agents load context from the correct repository
human_design_dir = Path(__file__).parent.absolute()
os.chdir(human_design_dir)
print(f"✓ Changed working directory to: {os.getcwd()}")

# Add DODO to path
sys.path.insert(0, str(Path.home() / "code/claude/he360-dodo"))

from he360_dodo import create_strand, StrandType

async def main():
    print("🔬 64keys Reverse Engineering Strand")
    print("=" * 80)
    print("Target: Chart combinations + HD ontology + Visualization patterns")
    print("Fork space: Automatic git isolation branch")
    print("=" * 80)
    print()

    # Base directory (human-design repo)
    base_dir = Path(__file__).parent

    # Load seed specification
    seed_path = base_dir / 'SEED_64keys_reverse_engineering.json'
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
        "current_state": seed['context']['current_state'],
        "rebecca_workflow": seed['context']['rebecca_workflow'],
        "exploration_method": seed['context']['exploration_method'],
        "ontology_scope": seed['context']['ontology_scope'],
        "color_scheme_goal": seed['context']['color_scheme_goal'],
        "chart_visualization_goal": seed['context']['chart_visualization_goal'],
        "phases": seed['phases'],
        "expected_artifacts": seed['expected_artifacts'],
        "success_criteria": seed['success_criteria'],
        "constraints": seed['constraints'],
        "critical_files": [
            "src/human_design/api.py",
            "src/human_design/models/bodygraph.py",
            "src/human_design/models/core.py",
            "src/human_design/models/summaries_64keys.py",
            "src/mcp_server_64keys/",
            "bodygraph.yaml",
            "channels.yaml",
            "docs/conversations/2026-01-30-rebecca-feedback-session.md",
            ".github/copilot-instructions.md"
        ]
    }

    print("Creating strand in fork space...")
    print("(Git will automatically create isolation branch)")
    print()

    # Create strand
    # CRITICAL: repo_path must be human-design project, not he360-dodo!
    strand = create_strand(
        problem=seed['problem'],
        agents=seed['agents'],
        strand_type=StrandType.RESEARCH,
        context=context,
        repo_path=base_dir  # This is /Users/nathan.neibauer/code/human-design
    )

    print(f"✓ Repository path: {base_dir}")
    print(f"✓ Working directory: {Path.cwd()}")

    print(f"Strand ID: {strand.definition.strand_id}")
    print(f"Repository: {base_dir}")
    print()
    print("Executing 9-agent multi-phase investigation:")
    print("  Phase 1: Endpoint discovery (2 researchers, parallel)")
    print("  Phase 2: Chart logic reverse engineering (2 researchers, parallel)")
    print("  Phase 3: Ontology construction (2 ontologists, parallel)")
    print("  Phase 4: Visual design research (1 researcher)")
    print("  Phase 5: API architecture (1 architect)")
    print("  Phase 6: Validation (1 fair_witness)")
    print("  Phase 7: Synthesis (1 coordinator)")
    print()
    print("⏳ This will take 15-25 minutes...")
    print()

    # Execute strand
    result = await strand.run()

    print()
    print("=" * 80)
    print("🎉 STRAND EXECUTION COMPLETE")
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

    result_file = strand_results_dir / f'STRAND_64keys_reverse_engineering_{strand.definition.strand_id[:8]}.json'
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
    if hasattr(result, 'synthesis'):
        result_data["synthesis"] = result.synthesis

    result_file.write_text(json.dumps(result_data, indent=2))

    print(f"✅ Results saved: {result_file}")
    print()

    # Extract and save phase artifacts
    print("📦 Extracting phase artifacts:")
    if hasattr(result, 'findings') and result.findings:
        if isinstance(result.findings, dict):
            # Findings is a dictionary of agent -> content
            for agent_name, content in result.findings.items():
                if content:
                    artifact_file = strand_results_dir / f'AGENT_{agent_name}.md'
                    artifact_file.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
                    print(f"  ✓ {artifact_file.name}")
        elif isinstance(result.findings, list):
            # Findings is a list of items
            for i, finding in enumerate(result.findings):
                if isinstance(finding, dict):
                    agent_type = finding.get('agent_type', finding.get('agent', 'unknown'))
                    phase = finding.get('phase', f'phase_{i}')
                    content = finding.get('content', finding.get('findings', finding.get('result', '')))
                elif isinstance(finding, str):
                    agent_type = 'unknown'
                    phase = f'phase_{i}'
                    content = finding
                else:
                    continue

                if content:
                    artifact_file = strand_results_dir / f'PHASE_{i}_{agent_type}_{phase}.md'
                    artifact_file.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
                    print(f"  ✓ {artifact_file.name}")

    print()

    # Save synthesis
    if hasattr(result, 'synthesis') and result.synthesis:
        synthesis_file = strand_results_dir / f'SYNTHESIS_64keys_reverse_engineering_{strand.definition.strand_id[:8]}.md'
        synthesis_content = result.synthesis if isinstance(result.synthesis, str) else json.dumps(result.synthesis, indent=2)
        synthesis_file.write_text(synthesis_content)
        print(f"✅ Synthesis saved: {synthesis_file}")

    print()
    print("🌿 Git fork space status:")
    print(f"  Branch: strand/{seed['metadata']['seed_type']}/{strand.definition.strand_id[:8]}")
    print(f"  Commits: Automatic commits per phase")
    print(f"  Location: {base_dir}")
    print()
    print("Next steps:")
    print("  1. Review synthesis in strand-results/active/")
    print("  2. Validate findings against success criteria")
    print("  3. Begin implementation (Week 1: Interaction models)")
    print("  4. Synthesize 'chart expert' agent from visualization findings")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Strand interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
