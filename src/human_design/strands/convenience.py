"""Convenience functions for strand creation.

Matches DODO API for backward compatibility.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import StrandDefinition
from .builder import Strand, AgentFactory
from .agent_factory import get_agent_factory


def create_strand(
    problem: str,
    agents: List[str],
    agent_factory: Optional[AgentFactory] = None,
    strand_type: str = "uncategorized",
    context: Optional[Dict[str, Any]] = None,
    repo_path: Optional[Path] = None,
) -> Strand:
    """Create a strand from simple parameters (convenience function).

    Args:
        problem: Natural language problem description
        agents: List of agent names to execute
        agent_factory: Optional custom agent factory (defaults to get_agent_factory())
        strand_type: Type of investigation
        context: Additional context for agents
        repo_path: Git repository path (ignored - maintained for API compatibility)

    Returns:
        Strand instance ready to execute

    Example:
        >>> strand = create_strand(
        ...     problem="Audit API security",
        ...     agents=["implementer", "test_engineer", "coordinator"],
        ...     strand_type="implementation"
        ... )
        >>> result = await strand.run()
    """
    # Use default agent factory if none provided
    if agent_factory is None:
        agent_factory = get_agent_factory()

    # Create strand definition
    definition = StrandDefinition(
        problem=problem,
        agents=agents,
        strand_type=strand_type,
        context=context,
    )

    # Create and return strand
    return Strand(definition, agent_factory)
