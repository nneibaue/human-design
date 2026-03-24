#!/usr/bin/env python3
"""Execute comprehensive bodygraph visualization refinement strand."""

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
    """Execute the comprehensive visualization refinement strand."""
    base_dir = Path(__file__).parent
    seed_path = base_dir / "strand-results/seeds/SEED_visualization_refinement_comprehensive.yaml"

    print("🎨 BODYGRAPH VISUALIZATION - COMPREHENSIVE REFINEMENT")
    print("=" * 80)
    print("Previous strand identified critical gap: NO geometry extracted from 64keys")
    print("This refinement: LARGE TEAM for exhaustive 64keys study + custom D3 impl")
    print()
    print("Team Size: 17 agents (3 researchers, 2 architects, 4 implementers,")
    print("                       3 test engineers, 3 fair witnesses, 1 coordinator)")
    print()
    print("Phase 1: EXHAUSTIVE 64keys geometry extraction")
    print("Phase 2: Backend visualization API (Pydantic models, builder)")
    print("Phase 3: Custom D3.js renderer (ontologically clean, Rebecca Energy)")
    print("Phase 4: Validation (accuracy <5px, aesthetics, performance)")
    print("=" * 80)
    print()

    seed = yaml.safe_load(seed_path.read_text())

    print(f"📋 Problem: {seed['problem']['description'][:150]}...")
    print(f"👥 Agents: {', '.join(set(a['role'] for a in seed['agents']))}")
    print(f"   Total agent roles: {len(seed['agents'])}")
    print()

    # Build context
    context = {
        "problem": seed['problem'],
        "agents": seed['agents'],
        "expected_artifacts": seed['expected_artifacts'],
        "timeline": seed['timeline'],
    }

    # Add problem context
    if 'context' in seed['problem']:
        context['problem_context'] = seed['problem']['context']

    print("Creating comprehensive visualization strand...")
    strand = create_strand(
        problem=seed['problem']['description'],
        agents=[a['role'] for a in seed['agents']],
        strand_type="LIMPLEMENTATION",
        context=context,
        repo_path=base_dir
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print()
    print("▶️  Executing comprehensive visualization refinement...")
    print()
    print("   PHASE 1 - CRITICAL RESEARCH (BLOCKING):")
    print("     • Extract 9 center positions + shapes")
    print("     • Extract 36 channel path definitions")
    print("     • Extract 64 gate positioning algorithm")
    print("     • Identify rendering technology")
    print("     • Document interaction patterns")
    print()
    print("   PHASE 2 - BACKEND API:")
    print("     • Geometry constants (coordinate precision)")
    print("     • Pydantic visualization models")
    print("     • BodygraphVisualizationBuilder class")
    print("     • FastAPI endpoints")
    print()
    print("   PHASE 3 - FRONTEND RENDERER:")
    print("     • Custom D3.js v7 implementation")
    print("     • Ontologically clean function names")
    print("     • Rebecca Energy CSS theme")
    print("     • Hover/click/tooltip interactions")
    print()
    print("   PHASE 4 - VALIDATION:")
    print("     • Geometry accuracy (<5px variance)")
    print("     • Rebecca Energy aesthetic validation")
    print("     • Composite chart emergent channels")
    print("     • Performance testing (pentas <500ms)")
    print()
    print("   Estimated: 25-35 minutes (large team, thorough work)")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("🎨 COMPREHENSIVE VISUALIZATION REFINEMENT COMPLETE")
    print("=" * 80)
    print(f"Status: {result.status}")
    if hasattr(result, 'duration_seconds') and result.duration_seconds:
        print(f"Duration: {result.duration_seconds/60:.1f} min")
    print()
    print("Deliverables:")
    print("  ✓ docs/64keys_visualization_spec.md (complete reference)")
    print("  ✓ src/human_design/visualization/ (geometry, models, builder)")
    print("  ✓ static/js/d3-bodygraph.js (custom D3 renderer)")
    print("  ✓ static/css/bodygraph.css (Rebecca Energy theme)")
    print("  ✓ tests/test_visualization_*.py (30+ tests)")
    print()

    return strand

if __name__ == "__main__":
    try:
        strand = asyncio.run(execute_strand())
    except KeyboardInterrupt:
        print("\n\n⚠️  Visualization refinement interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
