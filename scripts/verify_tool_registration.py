#!/usr/bin/env python3
"""Verify that all agents have their tools properly registered.

This script checks tool registration without requiring ANTHROPIC_API_KEY.
It verifies:
1. All agents can be created
2. Tools are registered on each agent
3. Tool counts match expectations
"""
import sys
from pathlib import Path

def main():
    """Verify tool registration for all agents."""
    from human_design.strands.agent_factory import get_agent_factory

    print("🔧 Verifying tool registration...")
    print("=" * 60)

    factory = get_agent_factory()

    # Expected tool counts for each agent
    expected_tools = {
        "implementer": {
            "filesystem": ["read_file", "write_file", "list_directory"],
            "code_search": ["find_files", "search_in_files"],
            "git_history": ["get_git_log", "get_git_diff", "get_current_branch"],
        },
        "test_engineer": {
            "filesystem": ["read_file", "write_file", "list_directory"],
            "code_search": ["find_files", "search_in_files"],
            "git_history": ["get_git_log", "get_git_diff", "get_current_branch"],
        },
        "python_linguist": {
            "git_history": ["get_git_log", "get_git_diff", "get_current_branch"],
        },
        "d3_specialist": {
            # D3 specialist doesn't have tool registration yet
        },
    }

    all_passed = True

    for agent_name, tool_categories in expected_tools.items():
        print(f"\n📋 Agent: {agent_name}")

        try:
            # Create agent
            agent, deps = factory.create_agent(agent_name)
            print(f"  ✓ Agent created successfully")

            # Check tools attribute
            if not hasattr(agent, "_function_tools"):
                print(f"  ⚠️  No _function_tools attribute")
                continue

            tools = agent._function_tools
            tool_names = {tool.name for tool in tools.values()}
            print(f"  ✓ Tools registered: {len(tool_names)}")

            # Verify each category
            for category, expected_names in tool_categories.items():
                found = [name for name in expected_names if name in tool_names]
                missing = [name for name in expected_names if name not in tool_names]

                if missing:
                    print(f"  ❌ {category}: Missing {missing}")
                    all_passed = False
                else:
                    print(f"  ✓ {category}: All {len(found)} tools present")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tool registrations verified!")
        return 0
    else:
        print("❌ Some tool registrations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
