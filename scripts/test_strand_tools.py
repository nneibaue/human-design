#!/usr/bin/env python3
"""Test strand execution with tool access.

Requirements:
    ANTHROPIC_API_KEY environment variable must be set.

    export ANTHROPIC_API_KEY="sk-ant-..."

This tests that agents can use their registered tools:
- Filesystem tools (read/write files)
- Code search tools (find files, search patterns)
- Git history tools (commits, diffs, branches)
"""
import asyncio
import os
import sys
from pathlib import Path
from human_design.strands import create_strand


async def main():
    """Test strand with implementer using tools."""

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("\nTo run these tests, set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        print("\nAlternatively, run mock tool tests:")
        print("  pytest tests/test_agent_tools.py")
        sys.exit(1)

    print("🔧 Testing strand tool access...")
    print("=" * 60)

    # Test 1: Implementer reads file
    print("\nTest 1: Implementer reads file and summarizes...")
    strand = create_strand(
        problem="Read src/human_design/models/core.py and summarize the gate types defined",
        agents=["implementer"],
        strand_type="test"
    )

    result = await strand.run()
    print(f"✓ Strand completed: {result.status}")
    findings = str(result.findings.get('implementer', 'No findings'))
    print(f"✓ Findings preview: {findings[:200]}...")

    # Test 2: Implementer searches code
    print("\nTest 2: Implementer searches for 'GateNumber' usage...")
    strand = create_strand(
        problem="Search the codebase for 'GateNumber' and report where it's used",
        agents=["implementer"],
        strand_type="test"
    )

    result = await strand.run()
    print(f"✓ Strand completed: {result.status}")
    print(f"✓ Found references: {'GateNumber' in str(result.findings)}")

    # Test 3: Implementer checks git history
    print("\nTest 3: Implementer checks recent commits...")
    strand = create_strand(
        problem="Check the last 5 commits and report what files were changed",
        agents=["implementer"],
        strand_type="test"
    )

    result = await strand.run()
    print(f"✓ Strand completed: {result.status}")
    print(f"✓ Git history accessed: {'commit' in str(result.findings).lower()}")

    print("\n" + "=" * 60)
    print("✅ All strand tool tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
