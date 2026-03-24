"""Strand Builder - Create and execute multi-agent investigation workflows.

Minimal extraction from DODO for self-sufficient strand execution.
Removed: metabolization, temporal anchors, signposting, token tracking.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Protocol

from .models import StrandDefinition, StrandResult, StrandStatus


class AgentFactory(Protocol):
    """Protocol defining the interface for agent factories."""

    def create_agent(self, agent_name: str):
        """Create an agent by name.

        Args:
            agent_name: Name of the agent to create

        Returns:
            Agent instance with .run() method
        """
        ...


class Strand:
    """A strand is a problem-specific multi-agent investigation sequence.

    Strands assemble specialist agents for a specific problem, run them in
    parallel, synthesize findings through a coordinator, and return comprehensive
    analysis.
    """

    def __init__(self, definition: StrandDefinition, agent_factory: AgentFactory):
        """Initialize strand from definition.

        Args:
            definition: Strand definition with problem, agents, context
            agent_factory: Factory for creating agents (dependency injection)
        """
        self.definition = definition
        self.factory = agent_factory
        self.findings: Dict[str, Any] = {}
        self.status = StrandStatus.CREATED
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.error: str | None = None

    async def run(self) -> StrandResult:
        """Execute the strand.

        Returns:
            StrandResult with all findings and metadata
        """
        print(f"🧵 Strand: {self.definition.strand_id}")
        print(f"📋 Problem: {self.definition.problem}")
        print(f"👥 Agents: {', '.join(self.definition.agents)}\n")

        self.status = StrandStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

        try:
            # Phase 1: Parallel specialist execution
            await self._run_specialists()

            # Phase 2: Coordinator synthesis (if coordinator in team)
            if 'coordinator' in self.definition.agents:
                await self._run_coordinator()

            self.status = StrandStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            self.status = StrandStatus.FAILED
            self.error = str(e)
            self.completed_at = datetime.now(timezone.utc)
            print(f"❌ Strand failed: {e}")
            raise

        return self._build_result()

    async def _run_specialists(self):
        """Execute all specialist agents in parallel (exclude coordinator)."""
        print("🔬 Phase 1: Specialist Analysis")

        specialist_agents = [a for a in self.definition.agents if a != 'coordinator']
        total_agents = len(specialist_agents)

        tasks = []
        for idx, agent_name in enumerate(specialist_agents, 1):
            task = self._run_agent_with_progress(agent_name, idx, total_agents)
            tasks.append(task)

        specialist_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Store findings
        for agent_name, result in zip(specialist_agents, specialist_results):
            if isinstance(result, Exception):
                self.findings[agent_name] = {
                    "error": str(result),
                    "status": "failed"
                }
                print(f"❌ Agent {agent_name} failed: {result}")
            elif result is not None:
                self.findings[agent_name] = result

    async def _run_agent_with_progress(
        self,
        agent_name: str,
        idx: int,
        total: int
    ) -> Dict[str, Any]:
        """Run agent with progress reporting.

        Args:
            agent_name: Name of agent to run
            idx: Agent index (1-based)
            total: Total number of agents

        Returns:
            Agent findings dict
        """
        print(f"🧵 Agent {idx}/{total}: {agent_name} | Starting...")

        try:
            result = await self._run_agent(agent_name)
            print(f"✅ Agent {idx}/{total}: {agent_name} | Complete")
            return result

        except Exception as e:
            print(f"❌ Agent {idx}/{total}: {agent_name} | Failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }

    async def _run_agent(self, agent_name: str) -> Dict[str, Any]:
        """Run a single agent.

        Args:
            agent_name: Name of agent to run

        Returns:
            Agent findings dict
        """
        agent, deps = self.factory.create_agent(agent_name)

        # Build agent prompt from strand problem and context
        prompt = self.definition.problem

        # Append context as formatted text if present
        if self.definition.context:
            import json
            prompt += "\n\n## CONTEXT PROVIDED:\n"
            prompt += json.dumps(self.definition.context, indent=2)

        # Run agent with deps (pydantic-ai passes deps via RunContext)
        result = await agent.run(prompt, deps=deps)

        # Extract findings from result
        if hasattr(result, 'output'):
            return result.output
        elif hasattr(result, 'data'):
            return result.data
        else:
            return {"result": str(result)}

    async def _run_coordinator(self):
        """Run coordinator agent to synthesize specialist findings."""
        print("\n🎯 Phase 2: Coordinator Synthesis")
        print(f"🧵 Coordinator | Synthesizing findings from {len(self.findings)} specialists...")

        try:
            coordinator, deps = self.factory.create_agent('coordinator')

            # Build coordinator input with all specialist findings
            coordinator_input = {
                "problem": self.definition.problem,
                "context": self.definition.context or {},
                "specialist_findings": self.findings,
            }

            result = await coordinator.run(coordinator_input, deps=deps)

            # Extract synthesis
            if hasattr(result, 'output'):
                synthesis = result.output
            elif hasattr(result, 'data'):
                synthesis = result.data
            else:
                synthesis = {"result": str(result)}

            self.findings['coordinator'] = synthesis
            print("✅ Coordinator | Complete")

        except Exception as e:
            print(f"❌ Coordinator | Failed: {e}")
            self.findings['coordinator'] = {
                "error": str(e),
                "status": "failed"
            }

    def _build_result(self) -> StrandResult:
        """Build strand result from execution state.

        Returns:
            StrandResult with all metadata and findings
        """
        return StrandResult(
            strand_id=self.definition.strand_id,
            problem=self.definition.problem,
            agents=self.definition.agents,
            strand_type=self.definition.strand_type,
            status=self.status,
            findings=self.findings,
            created_at=self.definition.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            error=self.error,
        )
