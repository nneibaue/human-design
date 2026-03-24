"""Strand models - Core data structures for multi-agent investigation workflows.

Minimal extraction from DODO for self-sufficient strand execution.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal
import uuid
from pydantic import BaseModel, Field


class StrandStatus:
    """Strand lifecycle states."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StrandDefinition(BaseModel):
    """Definition of a strand before execution.

    Attributes:
        strand_id: Unique identifier
        problem: Natural language problem description
        agents: Ordered list of agent names to execute
        strand_type: Type of investigation
        context: Additional context for agents
        created_at: Timestamp of creation
    """

    strand_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem: str = Field(..., description="Natural language problem description")
    agents: List[str] = Field(..., description="Ordered list of agent names to execute")
    strand_type: str = Field(default="uncategorized", description="Type of investigation")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for agents")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StrandResult(BaseModel):
    """Result of strand execution.

    Attributes:
        strand_id: Unique identifier
        problem: Problem statement
        agents: List of agents executed
        strand_type: Investigation type
        status: Current status
        findings: Agent findings
        created_at: Creation timestamp
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
        error: Error message if failed
    """

    strand_id: str
    problem: str
    agents: List[str]
    strand_type: str = Field(default="uncategorized")
    status: Literal["created", "running", "completed", "failed"]
    findings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
