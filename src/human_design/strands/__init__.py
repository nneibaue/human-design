"""Human Design Strands - Embedded multi-agent investigation system.

Self-contained strand execution inspired by Neal Stephenson's "The Rise and Fall of D.O.D.O."
DODO: Distributed Ontology-Driven Operations.

Quick Start:
    >>> from human_design.strands import create_strand
    >>> strand = create_strand(
    ...     problem="Implement feature X",
    ...     agents=["implementer", "test_engineer"],
    ...     strand_type="implementation"
    ... )
    >>> result = await strand.run()
    >>> print(result.findings)

Architecture:
    - models.py: Core data structures (StrandDefinition, StrandResult, StrandStatus)
    - builder.py: Strand execution orchestration
    - agent_factory.py: Hardcoded agent loading (no ontology dependency)
    - convenience.py: create_strand() convenience function

Available Agents:
    - implementer: Feature implementation
    - test_engineer: Test suite creation
    - d3_specialist: D3.js visualization implementation
    - python_linguist: Code quality and Python best practices

Legacy DODO agents (require DODO installation):
    - researcher: Codebase analysis
    - architect: Architecture design
    - coordinator: Multi-agent synthesis
    - fair_witness: Validation and correctness checking
"""

from .models import StrandDefinition, StrandResult, StrandStatus
from .builder import Strand, AgentFactory
from .agent_factory import get_agent_factory
from .convenience import create_strand

__all__ = [
    # Models
    "StrandDefinition",
    "StrandResult",
    "StrandStatus",
    # Builder
    "Strand",
    "AgentFactory",
    # Factory
    "get_agent_factory",
    # Convenience
    "create_strand",
]

__version__ = "0.1.0"  # Embedded DODO-lite version
