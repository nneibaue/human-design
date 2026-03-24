#!/usr/bin/env python
"""Execute D3 visualization test strand.

Tests the d3_specialist agent by creating a standalone HTML bodygraph visualization.
"""

import asyncio
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

from human_design.strands import create_strand
from human_design.strands.agent_factory import get_agent_model

# Load environment
load_dotenv()

async def main():
    """Execute visualization test strand."""

    # Load seed
    seed_path = Path("strand-results/seeds/SEED_d3_test_visualization.yaml")
    with open(seed_path) as f:
        seed_data = yaml.safe_load(f)

    print("🎨 D3 Visualization Test Strand")
    print(f"🤖 Model: {get_agent_model()} ({'$AGENT_MODEL' if 'AGENT_MODEL' in os.environ else 'default'})")
    print(f"📋 Problem: {seed_data['problem_statement'][:80]}...")
    print(f"👥 Agents: {', '.join(seed_data['investigation_agents'].keys())}")
    print()

    # Create and execute strand
    print("🔬 Executing strand...\n")
    strand = create_strand(
        problem=seed_data['problem_statement'],
        agents=list(seed_data['investigation_agents'].keys()),
        context=seed_data.get('context', {}),
        strand_type=seed_data['seed_metadata']['type']
    )

    result = await strand.run()

    # Report results
    print("\n" + "="*60)
    print("📊 Strand Execution Complete")
    print("="*60)
    print(f"\nStatus: {result.status}")

    for agent_name, finding in result.findings.items():
        print(f"\n📋 {agent_name}:")
        output = str(finding)
        print(f"   {output[:300]}..." if len(output) > 300 else f"   {output}")

    if result.error:
        print(f"\n❌ Error: {result.error}")

    print("\n✨ Expected outputs:")
    for output in seed_data.get('expected_outputs', []):
        print(f"   - {output}")

if __name__ == "__main__":
    asyncio.run(main())
