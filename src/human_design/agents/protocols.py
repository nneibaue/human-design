"""Agent protocols for type-safe communication.

Protocols define interfaces that agents must implement for team coordination.
This enables static type checking and ensures agents can communicate effectively.

Uses modern Pydantic v2 Annotated syntax for all field definitions.
Type safety is paramount - TypedDict and unions preferred over dict[str, Any].
"""

from typing import Annotated, Any, Protocol, runtime_checkable, TypedDict
from enum import Enum
from pydantic import BaseModel, Field


class ResearchOutput(BaseModel):
    """Structured output from research agents."""
    findings: Annotated[str, Field(description="Research findings and analysis")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in findings")]
    sources: Annotated[list[str], Field(description="List of source citations")]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional metadata about the research")
    ]


class ValidationOutput(BaseModel):
    """Structured output from validation agents."""
    validated: Annotated[bool, Field(description="Whether validation passed")]
    concerns: Annotated[list[str], Field(description="List of validation concerns found")]
    recommendations: Annotated[list[str], Field(description="Recommendations for addressing concerns")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in validation")]


class SynthesisOutput(BaseModel):
    """Structured output from synthesis agents."""
    synthesis: Annotated[str, Field(description="Synthesized narrative from all findings")]
    key_insights: Annotated[list[str], Field(description="Key insights extracted")]
    action_items: Annotated[list[str], Field(description="Actionable next steps")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in synthesis")]


@runtime_checkable
class ResearchCapability(Protocol):
    """Protocol for agents that can perform research."""

    async def research(self, topic: str, context: dict[str, str]) -> ResearchOutput:
        """Research a topic and return structured findings.

        Args:
            topic: Topic to research
            context: Additional context for the research

        Returns:
            ResearchOutput with findings, confidence, and sources
        """
        ...

    async def validate_sources(self, sources: list[str]) -> bool:
        """Validate that sources are credible and relevant.

        Args:
            sources: List of source references to validate

        Returns:
            True if sources are valid, False otherwise
        """
        ...


@runtime_checkable
class ValidationCapability(Protocol):
    """Protocol for agents that can validate findings."""

    async def validate(self, findings: dict[str, str], evidence: list[str]) -> ValidationOutput:
        """Validate findings against evidence.

        Args:
            findings: Findings to validate
            evidence: Supporting evidence

        Returns:
            ValidationOutput with validation status and concerns
        """
        ...


@runtime_checkable
class SynthesisCapability(Protocol):
    """Protocol for agents that can synthesize findings."""

    async def synthesize(self, findings: dict[str, dict]) -> SynthesisOutput:
        """Synthesize findings from multiple sources.

        Args:
            findings: Dict of agent_name -> agent_findings

        Returns:
            SynthesisOutput with synthesis and action items
        """
        ...


@runtime_checkable
class CodeAnalysisCapability(Protocol):
    """Protocol for agents that can analyze code."""

    async def analyze_code(self, code: str, language: str) -> dict[str, str]:
        """Analyze code for issues and patterns.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Dict with analysis results
        """
        ...


@runtime_checkable
class OntologyCapability(Protocol):
    """Protocol for agents that work with ontologies."""

    async def validate_ontology(self, ontology: dict) -> ValidationOutput:
        """Validate ontology structure and semantics.

        Args:
            ontology: Ontology data structure

        Returns:
            ValidationOutput with validation status
        """
        ...


class ArchitectureOutput(BaseModel):
    """Structured output from architecture agents."""
    design_decision: Annotated[str, Field(description="Core architectural decision with rationale")]
    type_definitions: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Type-safe schema definitions")
    ]
    validation_strategy: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Validation approach and rules")
    ]
    ergonomic_considerations: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Developer experience considerations")
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in design")]
    adr_required: Annotated[bool, Field(default=False, description="Whether an ADR should be created")]


class DiagnosticOutput(BaseModel):
    """Structured output from diagnostic agents."""
    diagnosis: Annotated[str, Field(description="Detailed diagnostic analysis of the failure")]
    failure_type: Annotated[str, Field(description="Classification of failure type (transient, permanent, configuration, systemic)")]
    fingerprint: Annotated[str, Field(description="Unique identifier for this failure pattern")]
    remediation_steps: Annotated[list[str], Field(description="Recommended steps to fix the issue")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in diagnosis")]
    context: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional diagnostic context")
    ]


@runtime_checkable
class DiagnosticCapability(Protocol):
    """Protocol for agents that can diagnose failures."""

    async def diagnose_failure(
        self,
        exception: Exception,
        context: dict[str, str]
    ) -> DiagnosticOutput:
        """Diagnose a failure and provide remediation guidance.

        Args:
            exception: The exception that was raised
            context: Execution context (strand_id, agent, inputs, etc.)

        Returns:
            DiagnosticOutput with diagnosis and remediation steps
        """
        ...

    async def fingerprint_error(self, exception: Exception) -> str:
        """Generate a unique fingerprint for an error pattern.

        Args:
            exception: The exception to fingerprint

        Returns:
            Unique fingerprint string for pattern matching
        """
        ...


@runtime_checkable
class ArchitectureCapability(Protocol):
    """Protocol for agents that can design systems and architectures."""

    async def design_system(
        self,
        design_problem: str,
        context: dict[str, str]
    ) -> ArchitectureOutput:
        """Design a system or architecture solution.

        Args:
            design_problem: System design problem to solve
            context: Additional context (design_type, constraints, existing_system)

        Returns:
            ArchitectureOutput with design decision, schemas, and validation strategy
        """
        ...

    async def create_adr(
        self,
        decision: str,
        context: dict[str, str]
    ) -> str:
        """Create an Architectural Decision Record.

        Args:
            decision: The architectural decision made
            context: Context about the decision (alternatives, consequences, etc.)

        Returns:
            ADR markdown content
        """
        ...

    async def validate_architecture(
        self,
        architecture: dict[str, str],
        principles: list[str]
    ) -> bool:
        """Validate architecture against design principles.

        Args:
            architecture: Architecture specification to validate
            principles: Design principles to validate against

        Returns:
            True if architecture is valid, False otherwise
        """
        ...


class ExecutionHistoryOutput(BaseModel):
    """Structured output from execution history analysis."""
    recommendations: Annotated[
        list[dict[str, Any]],
        Field(description="Agent composition recommendations with confidence scores")
    ]
    query_metadata: Annotated[
        dict[str, int],
        Field(default_factory=dict, description="Metadata about the query execution")
    ]
    discovered_patterns: Annotated[
        list[dict[str, Any]],
        Field(default_factory=list, description="Patterns discovered from execution history")
    ]
    spell_candidates: Annotated[
        list[str],
        Field(default_factory=list, description="Patterns that could become spells")
    ]


class GitHistoryOutput(BaseModel):
    """Structured output from git history analysis."""
    agent_name: Annotated[str, Field(description="Name of agent analyzed")]
    usage_count: Annotated[int, Field(ge=0, description="Number of times agent was used")]
    last_updated: Annotated[str, Field(description="Last update date (ISO format)")]
    typical_contexts: Annotated[
        list[str],
        Field(default_factory=list, description="Typical usage contexts")
    ]
    knowledge_gaps: Annotated[
        list[str],
        Field(default_factory=list, description="Identified knowledge gaps")
    ]
    summary: Annotated[str, Field(description="Summary of analysis findings")]
    temporal_anchors: Annotated[
        list[dict[str, str]],
        Field(default_factory=list, description="Temporal anchor tags discovered")
    ]
    design_decisions: Annotated[
        list[dict[str, Any]],
        Field(default_factory=list, description="Design decisions reconstructed from git blame")
    ]


@runtime_checkable
class ExecutionArchaeologyCapability(Protocol):
    """Protocol for agents that can query execution history."""

    async def recommend_composition(
        self,
        problem_description: str,
        constraints: dict[str, Any]
    ) -> ExecutionHistoryOutput:
        """Recommend agent compositions based on execution history.

        Args:
            problem_description: Natural language description of the problem
            constraints: Constraints like required_agents, max_agents, strand_type

        Returns:
            ExecutionHistoryOutput with recommendations and confidence scores
        """
        ...

    async def extract_patterns(
        self,
        min_occurrences: int
    ) -> list[dict[str, Any]]:
        """Extract recurring patterns from execution history.

        Args:
            min_occurrences: Minimum number of times pattern must appear

        Returns:
            List of patterns with metadata
        """
        ...


@runtime_checkable
class GitHistoryCapability(Protocol):
    """Protocol for agents that can analyze git history."""

    async def analyze_agent_usage(
        self,
        agent_name: str,
        time_range: str | None
    ) -> GitHistoryOutput:
        """Analyze agent usage patterns in git history.

        Args:
            agent_name: Name of agent to analyze
            time_range: Time range for analysis (e.g., '30 days', '6 months')

        Returns:
            GitHistoryOutput with usage patterns and insights
        """
        ...

    async def reconstruct_design_decision(
        self,
        file_path: str,
        line_range: str
    ) -> list[dict[str, str]]:
        """Reconstruct design decisions using git blame.

        Args:
            file_path: File path to analyze
            line_range: Line range (e.g., '10,20')

        Returns:
            List of design decisions with author, date, and rationale
        """
        ...


class DataAnalysisOutput(BaseModel):
    """Structured output from data analysis agents."""
    statistics: Annotated[
        dict[str, float],
        Field(default_factory=dict, description="Computed statistical metrics")
    ]
    charts: Annotated[
        list[dict[str, str]],
        Field(default_factory=list, description="Generated chart specifications")
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in analysis")]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional analysis metadata")
    ]


class VisualizationOutput(BaseModel):
    """Structured output from visualization refinement agents."""
    refined_file: Annotated[str, Field(description="Path to refined visualization file")]
    improvements: Annotated[
        list[dict[str, str]],
        Field(
            default_factory=list,
            description="List of improvements made (area, before, after, principle_applied)"
        )
    ]
    design_rationale: Annotated[str, Field(description="Design rationale for refinements")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in refinements")]


@runtime_checkable
class DataAnalysisCapability(Protocol):
    """Protocol for agents that can perform data analysis."""

    async def analyze_data(
        self,
        analysis_type: str,
        data_source: dict[str, Any]
    ) -> DataAnalysisOutput:
        """Analyze data and return structured findings.

        Args:
            analysis_type: Type of analysis (parse_logs, compute_metrics, etc.)
            data_source: Data source specification (file_path, inline_data, etc.)

        Returns:
            DataAnalysisOutput with statistics, charts, and confidence
        """
        ...

    async def compute_metrics(
        self,
        data: list[float],
        metrics: list[str]
    ) -> dict[str, float]:
        """Compute statistical metrics on numeric data.

        Args:
            data: List of numeric values
            metrics: List of metrics to compute (mean, median, std_dev, etc.)

        Returns:
            Dict of metric_name -> computed_value
        """
        ...


@runtime_checkable
class VisualizationCapability(Protocol):
    """Protocol for agents that can refine visualizations."""

    async def refine_visualization(
        self,
        visualization_file: str,
        refinement_goals: list[str]
    ) -> VisualizationOutput:
        """Refine a D3.js visualization with expert design principles.

        Args:
            visualization_file: Path to HTML file with D3.js visualizations
            refinement_goals: List of specific improvements needed

        Returns:
            VisualizationOutput with refined file path, improvements, and rationale
        """
        ...

    async def validate_accessibility(
        self,
        html_content: str
    ) -> dict[str, Any]:
        """Validate visualization accessibility against WCAG guidelines.

        Args:
            html_content: HTML content with D3.js visualization

        Returns:
            Dict with accessibility validation results
        """
        ...


class SpellCompositionOutput(BaseModel):
    """Structured output from spell composition agents."""
    spell_template: Annotated[
        dict[str, Any],
        Field(description="Spell template structure with agent composition")
    ]
    parameters: Annotated[
        list[str],
        Field(description="Parameters that vary across executions")
    ]
    validation_results: Annotated[
        dict[str, Any],
        Field(description="Validation results (conflicts, ontology alignment)")
    ]
    usage_examples: Annotated[
        list[str],
        Field(description="Usage examples and documentation")
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in spell quality")]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional metadata")
    ]


class SpellInterpretationOutput(BaseModel):
    """Structured output from spell interpretation agents."""
    strand_definition: Annotated[
        dict[str, Any],
        Field(description="Complete strand definition with agents")
    ]
    agent_instructions: Annotated[
        dict[str, str],
        Field(description="Explicit instructions for each agent")
    ]
    artifact_requirements: Annotated[
        dict[str, Any],
        Field(description="Artifact requirements (inputs, outputs, formats)")
    ]
    execution_sequence: Annotated[
        list[str],
        Field(description="Execution order with dependencies")
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in interpretation")]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional metadata")
    ]


class SpellSelectionOutput(BaseModel):
    """Structured output from spell selection agents."""
    selection_type: Annotated[
        str,
        Field(description="Selection type: 'spell' or 'adhoc'")
    ]
    selected_spell: Annotated[
        dict[str, Any] | None,
        Field(default=None, description="Selected spell (if selection_type == 'spell')")
    ]
    match_score: Annotated[
        float,
        Field(ge=0.0, le=1.0, description="Similarity score between request and spell")
    ]
    rationale: Annotated[str, Field(description="Selection rationale")]
    alternatives: Annotated[
        list[dict[str, Any]],
        Field(default_factory=list, description="Alternative options considered")
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in selection")]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional metadata")
    ]


class TestExecutionOutput(BaseModel):
    """Structured output from test execution agents."""
    passed: Annotated[int, Field(ge=0, description="Number of tests passed")]
    failed: Annotated[int, Field(ge=0, description="Number of tests failed")]
    skipped: Annotated[int, Field(ge=0, description="Number of tests skipped")]
    total: Annotated[int, Field(ge=0, description="Total number of tests")]
    duration_seconds: Annotated[float, Field(ge=0.0, description="Total execution time")]
    stdout: Annotated[str, Field(description="Captured stdout")]
    stderr: Annotated[str, Field(description="Captured stderr")]
    exit_code: Annotated[int, Field(description="Process exit code")]
    failure_analysis: Annotated[
        list[dict[str, Any]],
        Field(default_factory=list, description="Detailed failure analysis")
    ]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional metadata")
    ]


@runtime_checkable
class SpellCompositionCapability(Protocol):
    """Protocol for agents that can compose spells from patterns."""

    async def compose_spell(
        self,
        pattern_cluster: dict[str, Any],
        extraction_config: dict[str, Any]
    ) -> SpellCompositionOutput:
        """Extract a spell template from a pattern cluster.

        Args:
            pattern_cluster: Pattern recognition event from pattern_recognizer
            extraction_config: Configuration for spell extraction

        Returns:
            SpellCompositionOutput with spell template and validation results
        """
        ...

    async def validate_spell(
        self,
        spell_template: dict[str, Any],
        ontology: dict[str, Any]
    ) -> bool:
        """Validate a spell template against ontology.

        Args:
            spell_template: Spell template to validate
            ontology: Ontology to validate against

        Returns:
            True if valid, False otherwise
        """
        ...


@runtime_checkable
class SpellInterpretationCapability(Protocol):
    """Protocol for agents that can interpret spell templates."""

    async def interpret_spell(
        self,
        spell_template: dict[str, Any],
        problem_context: dict[str, Any]
    ) -> SpellInterpretationOutput:
        """Translate spell template into executable strand definition.

        Args:
            spell_template: Spell template to interpret
            problem_context: Specific problem context for this execution

        Returns:
            SpellInterpretationOutput with strand definition and execution plan
        """
        ...

    async def validate_interpretation(
        self,
        strand_definition: dict[str, Any],
        ontology: dict[str, Any]
    ) -> bool:
        """Validate strand definition against ontology.

        Args:
            strand_definition: Strand definition to validate
            ontology: Ontology to validate against

        Returns:
            True if valid, False otherwise
        """
        ...


@runtime_checkable
class SpellSelectionCapability(Protocol):
    """Protocol for agents that can select spells."""

    async def select_spell(
        self,
        request: dict[str, Any],
        spell_library: dict[str, Any]
    ) -> SpellSelectionOutput:
        """Select appropriate spell or recommend ad-hoc strand.

        Args:
            request: Incoming request with goal and context
            spell_library: Available spells to match against

        Returns:
            SpellSelectionOutput with selection type and rationale
        """
        ...

    async def calculate_similarity(
        self,
        request: dict[str, Any],
        spell: dict[str, Any]
    ) -> float:
        """Calculate similarity between request and spell.

        Args:
            request: Incoming request
            spell: Spell to compare against

        Returns:
            Similarity score (0.0-1.0)
        """
        ...


@runtime_checkable
class TestExecutionCapability(Protocol):
    """Protocol for agents that can execute tests."""

    async def run_tests(
        self,
        test_path: str,
        config: dict[str, Any]
    ) -> TestExecutionOutput:
        """Execute tests and return results.

        Args:
            test_path: Path to tests (file, directory, or test ID)
            config: Test execution configuration

        Returns:
            TestExecutionOutput with results and failure analysis
        """
        ...

    async def analyze_test_failure(
        self,
        failure_output: str,
        test_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze test failure and provide diagnostics.

        Args:
            failure_output: Test failure output (stack trace, assertion message)
            test_context: Context about the test (name, file, framework)

        Returns:
            Dict with failure analysis and suggested fixes
        """
        ...


# =============================================================================
# Python Metaprogramming Protocols (Python Linguist Agent)
# =============================================================================


class OntologyQueryType(str, Enum):
    """Valid ontology query types for extract_ontology method.

    Enum prevents typos and enables IDE autocomplete. Each query type
    returns a specific result structure (see typed result models below).
    """
    LIST_AGENTS = "list_agents"
    AGENT_METADATA = "agent_metadata"
    PROTOCOL_METHODS = "protocol_methods"
    CAPABILITY_HIERARCHY = "capability_hierarchy"
    AGENT_PROTOCOLS = "agent_protocols"
    TOOL_INVENTORY = "tool_inventory"
    AGENT_DEPENDENCIES = "agent_dependencies"
    INHERITANCE_TREE = "inheritance_tree"
    CONFIG_SCHEMA = "config_schema"


# Typed result models for each query type (preserves ontological context)


class ListAgentsResult(TypedDict):
    """Result structure for LIST_AGENTS query."""
    agents: list[str]  # List of agent class names


class AgentMetadataResult(TypedDict):
    """Result structure for AGENT_METADATA query."""
    protocols: list[str]  # Protocols implemented by agent
    tools: list[str]  # Tools available to agent
    capability_level: int  # Agent's capability level (0-3)
    config_file: str  # Path to YAML config
    module_path: str  # Python module path


class ProtocolMethodsResult(TypedDict):
    """Result structure for PROTOCOL_METHODS query."""
    protocols: dict[str, list[str]]  # protocol_name -> [method_name, ...]


class CapabilityHierarchyResult(TypedDict):
    """Result structure for CAPABILITY_HIERARCHY query."""
    hierarchy: dict[int, list[str]]  # level (0-3) -> [agent_name, ...]


class AgentProtocolsResult(TypedDict):
    """Result structure for AGENT_PROTOCOLS query."""
    agent_protocols: dict[str, list[str]]  # agent_name -> [protocol_name, ...]


class ToolInventoryResult(TypedDict):
    """Result structure for TOOL_INVENTORY query."""
    tools: dict[str, list[str]]  # agent_name -> [tool_name, ...]


class AgentDependenciesResult(TypedDict):
    """Result structure for AGENT_DEPENDENCIES query."""
    dependencies: dict[str, list[str]]  # agent_name -> [imported_agent, ...]


class InheritanceTreeResult(TypedDict):
    """Result structure for INHERITANCE_TREE query."""
    tree: dict[str, list[str]]  # class_name -> [parent_class, ...]


class ConfigSchemaResult(TypedDict):
    """Result structure for CONFIG_SCHEMA query."""
    config_schemas: dict[str, dict[str, str]]  # config_name -> {field_name: field_type}


# Union of all possible result types (preserves type safety)
OntologyQueryResult = (
    ListAgentsResult
    | AgentMetadataResult
    | ProtocolMethodsResult
    | CapabilityHierarchyResult
    | AgentProtocolsResult
    | ToolInventoryResult
    | AgentDependenciesResult
    | InheritanceTreeResult
    | ConfigSchemaResult
)


class ASTPatternMatch(BaseModel):
    """Single AST pattern match result."""
    file_path: Annotated[str, Field(description="File where match was found")]
    line_number: Annotated[int, Field(description="Line number of match")]
    node_type: Annotated[str, Field(description="AST node type (e.g., 'FunctionDef', 'Call')")]
    code_snippet: Annotated[str, Field(description="Source code of matched node")]
    context: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Additional context (parent node, scope, etc.)")
    ]


class StructuralAnalysisOutput(BaseModel):
    """Structured output from AST analysis."""
    matches: Annotated[
        list[ASTPatternMatch],
        Field(default_factory=list, description="Matched AST patterns")
    ]
    statistics: Annotated[
        dict[str, int],
        Field(default_factory=dict, description="Statistics (total_nodes, match_count, etc.)")
    ]
    anti_patterns: Annotated[
        list[dict[str, str]],
        Field(default_factory=list, description="Detected anti-patterns with severity")
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in analysis")]
    metadata: Annotated[
        dict[str, Any],
        Field(default_factory=dict, description="Additional metadata")
    ]


class RefactoringOutput(BaseModel):
    """Structured output from AST refactoring."""
    modified_files: Annotated[
        list[str],
        Field(default_factory=list, description="Files modified during refactoring")
    ]
    changes: Annotated[
        list[dict[str, str]],
        Field(default_factory=list, description="List of changes (file, before, after)")
    ]
    ast_valid: Annotated[bool, Field(description="Whether resulting AST is valid")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in refactoring")]
    backup_path: Annotated[
        str | None,
        Field(default=None, description="Path to backup files (if created)")
    ]


class TypeAnalysisOutput(BaseModel):
    """Structured output from type system analysis."""
    typed_elements: Annotated[
        dict[str, str],
        Field(default_factory=dict, description="Elements with type hints (name -> type)")
    ]
    untyped_elements: Annotated[
        list[str],
        Field(default_factory=list, description="Elements missing type hints")
    ]
    type_errors: Annotated[
        list[dict[str, str]],
        Field(default_factory=list, description="Type inconsistencies detected")
    ]
    coverage: Annotated[float, Field(ge=0.0, le=1.0, description="Type hint coverage (0-1)")]
    recommendations: Annotated[
        list[str],
        Field(default_factory=list, description="Recommendations for improving type safety")
    ]


class OntologyExtractionOutput(BaseModel):
    """Structured output from ontological introspection.

    This is the KEY OUTPUT that enables code-as-ontology - the mechanism
    that makes the DODO system self-aware through AST/CST introspection.

    Type Safety: Uses OntologyQueryResult union (not dict[str, Any]) to preserve
    ontological context. Each query type has a specific typed result structure.
    This prevents hallucination and enables static type checking.
    """
    query_type: Annotated[OntologyQueryType, Field(description="Type of ontology query performed")]
    results: Annotated[
        OntologyQueryResult,
        Field(description="Query results with type-safe structure based on query_type")
    ]
    metadata: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="Extraction metadata (files_analyzed, nodes_parsed, parse_time, etc.)"
        )
    ]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Confidence in extraction accuracy")]


@runtime_checkable
class PythonMetaprogrammingCapability(Protocol):
    """Protocol for agents that can perform Python metaprogramming.

    The Python Linguist agent implements this protocol to enable:
    1. Code-as-ontology (system self-awareness through AST)
    2. Structural pattern matching (AST-level search/replace)
    3. Code quality analysis (anti-pattern detection)
    4. Type system analysis (coverage, errors)
    5. Safe refactoring (AST transformation with validation)
    """

    async def extract_ontology(
        self,
        target_path: str,
        ontology_query: OntologyQueryType
    ) -> OntologyExtractionOutput:
        """Extract ontological metadata from code structure.

        This is the KEY METHOD that enables code-as-ontology - making the
        DODO system self-aware by querying its own code structure.

        Replaces static JSON ontology files with dynamic CST introspection (via LibCST).

        Args:
            target_path: Directory/file to analyze
            ontology_query: Query type enum (type-safe, prevents typos)

        Returns:
            OntologyExtractionOutput with typed results based on query_type

        Query Types (OntologyQueryType enum):
            - LIST_AGENTS: Find all *Agent classes → ListAgentsResult
            - AGENT_METADATA: Extract agent info → AgentMetadataResult
            - PROTOCOL_METHODS: Extract protocol signatures → ProtocolMethodsResult
            - CAPABILITY_HIERARCHY: Build hierarchy tree → CapabilityHierarchyResult
            - AGENT_PROTOCOLS: Map agents to protocols → AgentProtocolsResult
            - TOOL_INVENTORY: List all agent tools → ToolInventoryResult
            - AGENT_DEPENDENCIES: Extract can_call relationships → AgentDependenciesResult
            - INHERITANCE_TREE: Build class hierarchy → InheritanceTreeResult
            - CONFIG_SCHEMA: Extract config fields → ConfigSchemaResult

        Examples:
            >>> # Query all agents (type-safe)
            >>> result = await linguist.extract_ontology(
            ...     "agents/",
            ...     OntologyQueryType.LIST_AGENTS
            ... )
            >>> # result.results: ListAgentsResult with 'agents' key

            >>> # Query agent capabilities
            >>> result = await linguist.extract_ontology(
            ...     "agents/researcher.py",
            ...     OntologyQueryType.AGENT_METADATA
            ... )
            >>> # result.results: AgentMetadataResult with typed fields
        """
        ...

    async def find_pattern(
        self,
        pattern: str,
        search_path: str,
        context: dict[str, str]
    ) -> StructuralAnalysisOutput:
        """Find AST patterns in codebase.

        Args:
            pattern: AST pattern to search for (e.g., 'FunctionDef[name=test_*]')
            search_path: Directory/file to search
            context: Additional context (file_filter, depth, etc.)

        Returns:
            StructuralAnalysisOutput with matches and statistics
        """
        ...

    async def refactor_pattern(
        self,
        pattern: str,
        replacement: str,
        search_path: str,
        dry_run: bool
    ) -> RefactoringOutput:
        """Refactor code by replacing AST patterns.

        Args:
            pattern: AST pattern to find
            replacement: AST pattern to replace with
            search_path: Directory/file to refactor
            dry_run: If True, don't modify files (preview only)

        Returns:
            RefactoringOutput with changes and validation status
        """
        ...

    async def analyze_types(
        self,
        target_path: str
    ) -> TypeAnalysisOutput:
        """Analyze type hint coverage and correctness.

        Args:
            target_path: File or directory to analyze

        Returns:
            TypeAnalysisOutput with coverage metrics and recommendations
        """
        ...

    async def detect_anti_patterns(
        self,
        target_path: str,
        anti_pattern_rules: list[str]
    ) -> StructuralAnalysisOutput:
        """Detect code anti-patterns via AST inspection.

        Args:
            target_path: File or directory to analyze
            anti_pattern_rules: List of anti-pattern rules to check

        Returns:
            StructuralAnalysisOutput with detected anti-patterns
        """
        ...

    async def generate_code(
        self,
        spec: dict[str, Any],
        template: str
    ) -> str:
        """Generate Python code from specification.

        Args:
            spec: Code specification (schema, requirements, etc.)
            template: Template to use for generation

        Returns:
            Generated Python code as string
        """
        ...
