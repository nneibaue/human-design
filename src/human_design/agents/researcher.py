"""
Researcher Agent - Code pattern extraction for training other agents.

This agent specializes in extracting reusable code patterns from repositories
to train other agents. Focuses on:
- Best practice pattern recognition
- Anti-pattern identification with explanations
- Before/after refactoring examples
- Structured training material generation
"""

from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from pathlib import Path
import logging
from typing import Literal

logger = logging.getLogger(__name__)


RESEARCHER_SYSTEM_PROMPT = r"""You are a Researcher agent specializing in code pattern extraction for agent training.

## CORE RESPONSIBILITIES

1. **Pattern Extraction**: Find reusable code patterns across repositories
   - Best practices (clean code, type safety, validation)
   - Architectural patterns (separation of concerns, layering)
   - Testing patterns (parametrized tests, fixtures, mocking)
   - Anti-patterns (violations of principles)
   - Evolution patterns (refactoring trajectories)

2. **Pattern Analysis**: Extract principles from concrete examples
   - WHY patterns work (design rationale)
   - WHEN to apply (context and constraints)
   - HOW to implement (concrete steps)
   - WHAT to avoid (common pitfalls)
   - CONFIDENCE scoring (0.0-1.0 based on evidence)

3. **Training Material Generation**: Organize findings for agent consumption
   - Structured documentation (Markdown with code blocks)
   - Pattern catalogs (categorized by domain)
   - Anti-pattern registries (with remediation steps)
   - Refactoring guides (before/after examples with explanation)
   - Example libraries (real code from repository)

## RESEARCH METHODOLOGIES

**Inductive Pattern Recognition**:
```
Concrete Examples → Abstract Pattern → Reusable Principle
```

Process:
1. Search for code matching criteria (e.g., all Pydantic models)
2. Analyze commonalities (field validators, ConfigDict usage)
3. Extract pattern (Pydantic v2 best practices)
4. Document principle with examples

## THE RESEARCHER'S MANTRA

*"Show me the code. Explain the principle. Capture the evolution."*

Your job: Extract patterns from real code to train other agents. Every finding must be backed by concrete examples from the repository.
"""


class ResearcherConfig(BaseModel):
    """Configuration for Researcher agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    workspace_root: Path = Field(..., description="Root directory of the project")
    model: str = Field(default="claude-opus-4-6", description="LLM model to use")


@dataclass
class ResearcherDeps:
    """Researcher agent dependencies."""
    workspace_root: Path

    def __post_init__(self):
        """Validate researcher dependencies."""
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")

        if not self.workspace_root.is_dir():
            raise ValueError(f"Workspace root is not a directory: {self.workspace_root}")


def create_researcher_agent(deps: ResearcherDeps, model: str | None = None) -> Agent:
    """Create researcher agent with tools.

    Args:
        deps: Agent dependencies (workspace root, search limits)
        model: Optional LLM model override

    Returns:
        Configured pydantic-ai Agent instance
    """
    agent = Agent(
        model=model or "claude-opus-4-6",
        system_prompt=RESEARCHER_SYSTEM_PROMPT,
        deps_type=ResearcherDeps,
    )

    # Register tools (filesystem, git, code search) when available
    # TODO: Import from he360_dodo.agent_tools when available

    return agent


class ResearcherAgent:
    """High-level researcher agent interface."""

    def __init__(self, config: ResearcherConfig):
        """Initialize researcher agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.deps = ResearcherDeps(workspace_root=config.workspace_root)
        self.agent = create_researcher_agent(self.deps, config.model)

    async def research(
        self,
        query: str,
        query_type: Literal[
            "best_practices",
            "anti_patterns",
            "refactoring_examples",
            "architecture_patterns",
            "testing_patterns",
            "evolution_analysis",
        ],
        context: dict,
    ) -> dict:
        """Execute research query.

        Args:
            query: Research query (e.g., "Find Pydantic v2 field validator patterns")
            query_type: Type of research to perform
            context: Additional context (domain, file_filter, time_range, etc.)

        Returns:
            Research result with patterns, examples, and training documentation
        """
        prompt = f"""Research Query: {query}
Query Type: {query_type}
Context: {context}

Please analyze the codebase and extract patterns according to the query type.
Return structured training documentation with:
- Extracted patterns with examples
- Anti-patterns (if applicable)
- Design principles
- Confidence scores
- Source attributions

Focus on concrete examples from the repository. Show the code, explain the principle, capture the evolution."""

        result = await self.agent.run(prompt, deps=self.deps)

        # Extract output from pydantic-ai AgentRunResult
        if hasattr(result, 'output'):
            findings = result.output
        elif hasattr(result, 'data'):
            findings = result.data
        else:
            findings = str(result)

        return {
            "findings": findings,
            "query": query,
            "query_type": query_type,
            "status": "completed",
            "agent": "researcher",
        }
