"""Agent Factory - Create agents for strand execution.

Hardcoded agent loading for human-design agents (implementer, test_engineer,
d3_specialist, python_linguist). External DODO agents (researcher, architect,
coordinator, fair_witness) require standalone DODO installation.

DODO: Distributed Ontology-Driven Operations
Inspired by Neal Stephenson's "The Rise and Fall of D.O.D.O."
"""

from pathlib import Path
from typing import Any


class HumanDesignAgentFactory:
    """Factory for creating human-design agents.

    Uses hardcoded if/elif pattern for human-design-specific agents (no dynamic
    imports or ontology lookup). This breaks the bootstrap problem where agents
    need strand executor but strand executor needs agents.
    """

    def __init__(self):
        """Initialize agent factory."""
        self._agent_cache: dict[str, Any] = {}

    def create_agent(self, agent_name: str):
        """Create an agent by name.

        Args:
            agent_name: Name of agent to create

        Returns:
            Agent instance with .run() method

        Raises:
            ValueError: If agent not found
        """
        # Check cache first
        if agent_name in self._agent_cache:
            return self._agent_cache[agent_name]

        # Hardcoded human-design agents
        if agent_name == "implementer":
            from human_design.agents.implementer import (
                create_implementer_agent,
                ImplementerDeps,
            )

            deps = ImplementerDeps(workspace_root=Path.cwd())
            agent = create_implementer_agent(deps, model="claude-opus-4-6")
            self._agent_cache[agent_name] = agent
            return agent

        elif agent_name == "test_engineer":
            from human_design.agents.test_engineer import (
                create_test_engineer_agent,
                TestEngineerConfig,
            )

            config = TestEngineerConfig(workspace_root=Path.cwd())
            agent = create_test_engineer_agent(config)
            self._agent_cache[agent_name] = agent
            return agent

        elif agent_name == "d3_specialist":
            from human_design.agents.d3_specialist import (
                create_d3_specialist_agent,
                D3SpecialistConfig,
            )

            config = D3SpecialistConfig(workspace_root=Path.cwd())
            agent = create_d3_specialist_agent(config)
            self._agent_cache[agent_name] = agent
            return agent

        elif agent_name == "python_linguist":
            from human_design.agents.python_linguist import (
                create_python_linguist_agent,
                PythonLinguistDeps,
            )

            deps = PythonLinguistDeps(workspace_root=Path.cwd())
            agent = create_python_linguist_agent(deps, model="claude-opus-4-6")
            self._agent_cache[agent_name] = agent
            return agent

        # Agent not found in embedded system
        else:
            raise ValueError(
                f"Agent '{agent_name}' not found. "
                f"Available embedded agents: implementer, test_engineer, d3_specialist, python_linguist. "
                f"Additional agents (researcher, architect, coordinator, fair_witness) require "
                f"standalone DODO installation (Distributed Ontology-Driven Operations)."
            )


# Singleton instance
_factory_instance: HumanDesignAgentFactory | None = None


def get_agent_factory() -> HumanDesignAgentFactory:
    """Get singleton agent factory instance.

    Returns:
        HumanDesignAgentFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = HumanDesignAgentFactory()
    return _factory_instance
