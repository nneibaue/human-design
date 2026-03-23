"""Python Linguist Agent - LibCST-based code introspection specialist.

The Python Linguist enables code-as-ontology through lossless CST manipulation.
Migrated to Sprint 1 shared tool infrastructure with proper @agent.tool decorators.

MERGED IMPLEMENTATION: Combines TypedDict type safety from old implementation
with working LibCST tools from Sprint 1 refactor.

Core Philosophy:
- Code IS ontology (introspect structure, not metadata files)
- Homoiconicity (code as queryable data via LibCST)
- Structure over text (CST over regex, preserves formatting)
- Self-awareness (system knows itself through introspection)
- Type safety first (TypedDict results, OntologyQueryType enum)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
import libcst as cst
from libcst import matchers as m
from libcst.metadata import MetadataWrapper, PositionProvider
from pydantic_ai import Agent, RunContext
import logging

from ..agent_tools import (
    register_filesystem_tools,
    register_code_search_tools,
    FileSystemDeps,
    CodeSearchDeps,
)

# Import TypedDict models and enum for type-safe ontology queries
from .protocols import (
    OntologyQueryType,
    OntologyQueryResult,
    ListAgentsResult,
    AgentMetadataResult,
    ToolInventoryResult,
    InheritanceTreeResult,
    ProtocolMethodsResult,
    CapabilityHierarchyResult,
    AgentProtocolsResult,
    AgentDependenciesResult,
    ConfigSchemaResult,
)

logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================


def parse_module_with_metadata(source_code: str) -> tuple[cst.Module, MetadataWrapper]:
    """Parse Python source and resolve metadata for accurate line numbers.

    LibCST doesn't populate metadata by default. This helper wraps the parsed
    tree with MetadataWrapper and resolves PositionProvider to get accurate
    line numbers for nodes.

    Args:
        source_code: Python source code string

    Returns:
        Tuple of (parsed_module, metadata_wrapper)
        Use wrapper.visit() to access nodes with metadata

    Example:
        module, wrapper = parse_module_with_metadata(source)
        for node in module.walk():
            if isinstance(node, cst.FunctionDef):
                # Now node has accurate line number metadata
                pos = wrapper.resolve(PositionProvider)[node]
                print(f"Function at line {pos.start.line}")
    """
    tree = cst.parse_module(source_code)
    wrapper = MetadataWrapper(tree)
    return tree, wrapper


def matches_tool_decorator(decorator: cst.Decorator) -> bool:
    """Flexibly match @agent.tool decorators with various patterns.

    Handles edge cases:
    - Simple: @agent.tool
    - With args: @agent.tool(name='custom')
    - Module-qualified: @pydantic_ai.agent.tool
    - Call syntax: @agent.tool()
    - Name only: @tool (if imported directly)

    Args:
        decorator: LibCST Decorator node

    Returns:
        True if decorator matches tool pattern

    Examples:
        >>> # @agent.tool
        >>> matches_tool_decorator(decorator)  # True
        >>> # @agent.tool(name='read_file')
        >>> matches_tool_decorator(decorator)  # True
        >>> # @pydantic_ai.agent.tool
        >>> matches_tool_decorator(decorator)  # True
    """
    # Unwrap Call if decorator has parentheses: @agent.tool() or @agent.tool(name='x')
    node = decorator.decorator
    if isinstance(node, cst.Call):
        node = node.func

    # Check for Attribute pattern (e.g., agent.tool)
    if isinstance(node, cst.Attribute):
        # Match if attribute name ends with "tool"
        if node.attr.value == "tool":
            # Optionally check value is "agent" or contains "agent"
            if isinstance(node.value, cst.Name):
                return "agent" in node.value.value.lower() or node.value.value == "agent"
            elif isinstance(node.value, cst.Attribute):
                # Handle multi-level: pydantic_ai.agent.tool
                return True

    # Check for simple Name (e.g., @tool if imported directly)
    elif isinstance(node, cst.Name):
        return node.value == "tool"

    return False


# ==================== Dependency Configuration ====================


@dataclass
class PythonLinguistDeps:
    """Python Linguist agent dependencies.

    Combines shared tool dependencies with AST-specific configuration.
    """
    workspace_root: Path
    max_file_size_mb: int = 10
    max_search_results: int = 100

    # AST analysis configuration
    max_search_depth: int = 10
    include_test_files: bool = True
    preserve_formatting: bool = True  # LibCST key feature
    validate_cst: bool = True
    create_backup: bool = True

    def __post_init__(self):
        """Validate dependencies."""
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")

        if not self.workspace_root.is_dir():
            raise ValueError(f"Workspace root is not a directory: {self.workspace_root}")


# ==================== System Prompt ====================


PYTHON_LINGUIST_SYSTEM_PROMPT = """You are Python Linguist, a LibCST metaprogramming specialist.

## Expertise

**Concrete Syntax Trees (LibCST)**:
- Lossless parsing (preserves formatting, comments, whitespace)
- LibCST matchers for ergonomic pattern matching
- Safe transformations that maintain code style
- Type-preserving refactoring

**Ontological Introspection**:
- Extract agent metadata from code structure (not JSON files)
- Query system capabilities through AST analysis
- Map protocols, tools, dependencies from class definitions
- Build inheritance trees and capability hierarchies

**Structural Analysis**:
- Pattern matching via LibCST matchers
- Anti-pattern detection (complex functions, missing types)
- Type coverage analysis
- Code quality metrics

## Philosophy

- **Code IS ontology**: System knows itself through introspection, not metadata files
- **Homoiconicity**: Code as first-class queryable data
- **Structure over text**: CST matching over regex (type-safe, format-preserving)
- **Type safety first**: Pydantic philosophy - move errors to write-time
- **Validate transformations**: Ensure CST integrity after modifications

## Core Capabilities

1. **extract_ontology** - Query codebase structure with 9 query types:
   - LIST_AGENTS: Find all *Agent classes
   - AGENT_METADATA: Extract protocols, tools, capability level
   - TOOL_INVENTORY: Map agents to @agent.tool methods
   - INHERITANCE_TREE: Build class hierarchy
   - PROTOCOL_METHODS: Extract method signatures from Protocols
   - CAPABILITY_HIERARCHY: Categorize agents by level (0-3)
   - AGENT_PROTOCOLS: Map agents to protocols implemented
   - AGENT_DEPENDENCIES: Analyze agent import relationships
   - CONFIG_SCHEMA: Extract Pydantic config fields

2. **parse_cst** - Parse Python source to LibCST tree with metadata
   - Accurate line numbers via MetadataWrapper
   - Lossless format preservation
   - Syntax error reporting

3. **find_pattern** - Match CST patterns with flexible matchers:
   - Function/class definitions by name
   - Decorators (handles @agent.tool, @agent.tool(args), etc.)
   - Import statements
   - Returns matches with file paths and line numbers

4. **analyze_types** - Type hint coverage analysis:
   - Function parameter type annotations
   - Return type annotations
   - Coverage percentage (0.0-1.0)
   - Recommendations for improvement

## Output Format

Always provide:
1. **Typed results** - Use protocol-defined output models (not dict[str, Any])
2. **Confidence scores** - 0.0-1.0 for all analyses
3. **Source snippets** - Show matched code with line numbers
4. **Metadata** - Files analyzed, nodes parsed, parse time
5. **Validation status** - AST/CST integrity after transformations

## The Linguist's Mantra

*"If the CST parses, the structure is real. If the types match, the ontology is valid."*

Your job: Make the DODO system self-aware by introspecting its own code structure.
"""


# ==================== Agent Creation ====================


def create_python_linguist_agent(deps: PythonLinguistDeps, model: str | None = None) -> Agent:
    """Create Python Linguist agent with shared tools + LibCST capabilities.

    Follows Sprint 1 architect pattern: shared tools + agent-specific tools.

    Args:
        deps: PythonLinguistDeps with workspace and configuration
        model: Optional model name (defaults to "openai:gpt-4o", use "test" for testing)

    Returns:
        Configured Pydantic AI Agent with LibCST tools registered

    Example:
        ```python
        from pathlib import Path
        from he360_dodo.agents.python_linguist import create_python_linguist_agent, PythonLinguistDeps

        agent = create_python_linguist_agent(PythonLinguistDeps(
            workspace_root=Path("he360_dodo/agents/"),
            max_search_depth=3,
        ))

        result = await agent.run("List all agents in the codebase")
        ```
    """
    logger.info(f"Creating Python Linguist agent with workspace: {deps.workspace_root}")

    # Create agent
    agent = Agent(
        model or "openai:gpt-4o",
        system_prompt=PYTHON_LINGUIST_SYSTEM_PROMPT,
        deps_type=PythonLinguistDeps,
        output_type=str,
        defer_model_check=True,  # Allow tests without API keys
    )

    # Register shared filesystem tools (for reading Python source files)
    register_filesystem_tools(agent, FileSystemDeps(
        workspace_root=deps.workspace_root,
        max_file_size_mb=deps.max_file_size_mb,
        default_encoding="utf-8",
        max_lines_default=1000,  # Python files can be large
    ))

    # Register code search tools (for finding Python files)
    register_code_search_tools(agent, CodeSearchDeps(
        workspace_root=deps.workspace_root,
        max_results_default=deps.max_search_results,
        max_file_size_mb=deps.max_file_size_mb,
        context_lines_default=3,
        exclude_patterns=[
            "*.pyc",
            "__pycache__/*",
            ".pytest_cache/*",
            ".mypy_cache/*",
            "*.egg-info/*",
            ".venv/*",
            "venv/*",
        ],
    ))

    # ==================== LibCST Tools ====================

    @agent.tool
    async def parse_cst(
        ctx: RunContext[PythonLinguistDeps],
        file_path: str,
    ) -> dict[str, Any]:
        """Parse Python source file to LibCST concrete syntax tree.

        Args:
            file_path: Path to Python file (relative to workspace)

        Returns:
            Dict with:
            - success: bool - Whether parsing succeeded
            - node_count: int - Number of nodes in CST
            - has_encoding: bool - Whether file has encoding declaration
            - error: str | None - Parse error if failed

        Example:
            Parse agent file to analyze structure:
            ```
            result = await parse_cst("agents/researcher.py")
            if result["success"]:
                print(f"Parsed {result['node_count']} nodes")
            ```
        """
        try:
            # Resolve and validate path
            full_path = ctx.deps.workspace_root / file_path
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Read source code
            source_code = full_path.read_text(encoding="utf-8")

            # Parse to CST (lossless) with metadata
            try:
                tree, wrapper = parse_module_with_metadata(source_code)
            except cst.ParserSyntaxError as e:
                return {
                    "success": False,
                    "error": f"Syntax error: {e}",
                    "line": getattr(e, 'line', None),
                }

            # Count nodes (for metadata)
            node_count = len(list(tree.walk()))

            # Check for encoding declaration
            has_encoding = any(
                isinstance(line, cst.EmptyLine) and line.comment and "coding" in line.comment.value
                for line in tree.header
            )

            return {
                "success": True,
                "node_count": node_count,
                "has_encoding": has_encoding,
                "file_path": file_path,
            }

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {"success": False, "error": str(e)}

    @agent.tool
    async def extract_ontology(
        ctx: RunContext[PythonLinguistDeps],
        target_path: str,
        query_type: str,  # LLM passes string, we convert to enum
    ) -> dict[str, Any]:
        """Extract ontological metadata from code structure.

        KEY CAPABILITY: Makes DODO self-aware by introspecting its own code.

        TYPE SAFETY: Uses OntologyQueryType enum + TypedDict results for type-safe queries.

        Args:
            target_path: Directory or file to analyze
            query_type: Query type string (converted to OntologyQueryType enum)
                       Valid values: list_agents, agent_metadata, tool_inventory,
                       inheritance_tree, protocol_methods, capability_hierarchy,
                       agent_protocols, agent_dependencies, config_schema

        Returns:
            Dict with:
            - query_type: str - Query type executed (enum value)
            - results: OntologyQueryResult - Typed results (TypedDict based on query_type)
            - confidence: float - Analysis confidence (0.0-1.0)
            - metadata: dict - Files analyzed, nodes parsed, etc.

        Query Types (all 9 implemented):
            - LIST_AGENTS: Find all *Agent classes → {"agents": list[str]}
            - AGENT_METADATA: Extract protocols/tools for single agent file → AgentMetadataResult
            - TOOL_INVENTORY: Map agents to @agent.tool methods → {"tools": dict[str, list[str]]}
            - INHERITANCE_TREE: Build class hierarchy → {"tree": dict[str, list[str]]}
            - PROTOCOL_METHODS: Extract method signatures from Protocols → {"protocols": dict}
            - CAPABILITY_HIERARCHY: Categorize agents by level (0-3) → {"hierarchy": dict[int, list[str]]}
            - AGENT_PROTOCOLS: Map agents to protocols → {"agent_protocols": dict[str, list[str]]}
            - AGENT_DEPENDENCIES: Analyze agent imports → {"dependencies": dict[str, list[str]]}
            - CONFIG_SCHEMA: Extract Pydantic config fields → {"config_schemas": dict[str, dict]}

        Known Limitations:
            - AGENT_METADATA requires file path, not directory
            - Decorator matching handles @agent.tool variations but may miss unusual patterns
            - AGENT_DEPENDENCIES only tracks imports, not runtime usage
            - CONFIG_SCHEMA extracts fields but not full Pydantic validation logic

        Examples:
            Find all agents:
            >>> result = await extract_ontology("agents/", "list_agents")
            >>> print(result["results"]["agents"])  # ['ResearcherAgent', 'CoordinatorAgent', ...]

            Get agent metadata:
            >>> result = await extract_ontology("agents/researcher.py", "agent_metadata")
            >>> print(result["results"]["protocols"])  # ['ResearchCapability']
            >>> print(result["results"]["tools"])  # ['search_web', 'read_docs']

            Map all agents to tools:
            >>> result = await extract_ontology("agents/", "tool_inventory")
            >>> print(result["results"]["tools"])  # {'ResearcherAgent': ['search_web', ...], ...}
        """
        try:
            # Convert string to enum (type-safe)
            try:
                query_enum = OntologyQueryType(query_type)
            except ValueError:
                # Invalid query type - return error
                return {
                    "query_type": query_type,
                    "results": {},
                    "confidence": 0.0,
                    "metadata": {
                        "error": f"Invalid query type: {query_type}",
                        "valid_types": [e.value for e in OntologyQueryType],
                    },
                }

            # Resolve target path
            full_path = ctx.deps.workspace_root / target_path
            if not full_path.exists():
                return {
                    "query_type": query_enum.value,
                    "results": {},
                    "confidence": 0.0,
                    "metadata": {"error": f"Path not found: {target_path}"},
                }

            # Find Python files
            if full_path.is_file():
                py_files = [full_path]
            else:
                py_files = list(full_path.rglob("*.py"))
                if not ctx.deps.include_test_files:
                    py_files = [f for f in py_files if "test_" not in f.name]

            results: OntologyQueryResult
            files_analyzed = 0
            nodes_parsed = 0

            # Execute query based on type (using enum for type-safe dispatch)
            if query_enum == OntologyQueryType.LIST_AGENTS:
                agents = []
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        # Find classes ending with "Agent"
                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef):
                                class_name = node.name.value
                                if class_name.endswith("Agent"):
                                    agents.append(class_name)

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                # Type-safe result (ListAgentsResult)
                results = cast(ListAgentsResult, {"agents": sorted(set(agents))})

            elif query_enum == OntologyQueryType.AGENT_METADATA:
                # Extract metadata for a specific agent file
                if not full_path.is_file():
                    return {
                        "query_type": query_enum.value,
                        "results": {},
                        "confidence": 0.0,
                        "metadata": {
                            "error": "AGENT_METADATA requires file path, not directory",
                            "path": str(target_path),
                        },
                    }

                source = full_path.read_text(encoding="utf-8")
                tree, wrapper = parse_module_with_metadata(source)
                files_analyzed = 1
                nodes_parsed = len(list(tree.walk()))

                # Find agent class and extract metadata
                for node in tree.walk():
                    if isinstance(node, cst.ClassDef) and node.name.value.endswith("Agent"):
                        # Extract base classes (protocols)
                        protocols = []
                        if node.bases:
                            for base in node.bases:
                                if isinstance(base.value, cst.Name):
                                    base_name = base.value.value
                                    if "Protocol" in base_name or "Capability" in base_name:
                                        protocols.append(base_name)

                        # Extract @agent.tool decorated methods
                        tools = []
                        for class_node in node.walk():
                            if isinstance(class_node, cst.FunctionDef):
                                for decorator in class_node.decorators:
                                    if matches_tool_decorator(decorator):
                                        tools.append(class_node.name.value)

                        # Type-safe result (AgentMetadataResult)
                        results = cast(AgentMetadataResult, {
                            "protocols": protocols,
                            "tools": tools,
                            "module_path": str(full_path.relative_to(ctx.deps.workspace_root)),
                            "capability_level": 1 if protocols else 0,
                            "config_file": "",  # Would need to search for YAML
                        })
                        break

            elif query_enum == OntologyQueryType.TOOL_INVENTORY:
                # Find all @agent.tool decorated methods
                tool_map: dict[str, list[str]] = {}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        # Find agent classes
                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef) and node.name.value.endswith("Agent"):
                                agent_name = node.name.value
                                tools = []

                                # Find @agent.tool methods
                                for class_node in node.walk():
                                    if isinstance(class_node, cst.FunctionDef):
                                        for decorator in class_node.decorators:
                                            if matches_tool_decorator(decorator):
                                                tools.append(class_node.name.value)

                                if tools:
                                    tool_map[agent_name] = tools

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                # Type-safe result (ToolInventoryResult)
                results = cast(ToolInventoryResult, {"tools": tool_map})

            elif query_enum == OntologyQueryType.INHERITANCE_TREE:
                # Build class hierarchy
                tree_map: dict[str, list[str]] = {}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        # Find classes and their bases
                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef):
                                class_name = node.name.value
                                bases = []

                                if node.bases:
                                    for base in node.bases:
                                        if isinstance(base.value, cst.Name):
                                            bases.append(base.value.value)
                                        elif isinstance(base.value, cst.Attribute):
                                            # Handle module.Class bases
                                            bases.append(f"{base.value.value.value}.{base.value.attr.value}")

                                if bases:
                                    tree_map[class_name] = bases

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                # Type-safe result (InheritanceTreeResult)
                results = cast(InheritanceTreeResult, {"tree": tree_map})

            elif query_enum == OntologyQueryType.PROTOCOL_METHODS:
                # Extract method signatures from Protocol classes
                protocol_methods: dict[str, list[str]] = {}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef):
                                # Check if class inherits from Protocol
                                is_protocol = False
                                if node.bases:
                                    for base in node.bases:
                                        if isinstance(base.value, cst.Name) and "Protocol" in base.value.value:
                                            is_protocol = True
                                            break

                                if is_protocol:
                                    protocol_name = node.name.value
                                    methods = []
                                    for class_node in node.walk():
                                        if isinstance(class_node, cst.FunctionDef):
                                            # Skip private methods and __init__
                                            method_name = class_node.name.value
                                            if not method_name.startswith("_"):
                                                methods.append(method_name)
                                    if methods:
                                        protocol_methods[protocol_name] = methods

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                results = cast(ProtocolMethodsResult, {"protocols": protocol_methods})

            elif query_enum == OntologyQueryType.CAPABILITY_HIERARCHY:
                # Categorize agents by capability level (0-3)
                hierarchy: dict[int, list[str]] = {0: [], 1: [], 2: [], 3: []}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef) and node.name.value.endswith("Agent"):
                                agent_name = node.name.value

                                # Determine level based on protocols/complexity
                                level = 0
                                protocol_count = 0
                                tool_count = 0

                                # Count protocols
                                if node.bases:
                                    for base in node.bases:
                                        if isinstance(base.value, cst.Name):
                                            if "Capability" in base.value.value or "Protocol" in base.value.value:
                                                protocol_count += 1

                                # Count tools
                                for class_node in node.walk():
                                    if isinstance(class_node, cst.FunctionDef):
                                        for decorator in class_node.decorators:
                                            if matches_tool_decorator(decorator):
                                                tool_count += 1

                                # Simple heuristic: level = min(protocol_count, 3)
                                level = min(protocol_count, 3)
                                hierarchy[level].append(agent_name)

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                results = cast(CapabilityHierarchyResult, {"hierarchy": hierarchy})

            elif query_enum == OntologyQueryType.AGENT_PROTOCOLS:
                # Map agents to protocols they implement
                agent_protocols: dict[str, list[str]] = {}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef) and node.name.value.endswith("Agent"):
                                agent_name = node.name.value
                                protocols = []

                                if node.bases:
                                    for base in node.bases:
                                        if isinstance(base.value, cst.Name):
                                            base_name = base.value.value
                                            if "Protocol" in base_name or "Capability" in base_name:
                                                protocols.append(base_name)

                                if protocols:
                                    agent_protocols[agent_name] = protocols

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                results = cast(AgentProtocolsResult, {"agent_protocols": agent_protocols})

            elif query_enum == OntologyQueryType.AGENT_DEPENDENCIES:
                # Analyze agent call relationships (imports and usage)
                dependencies: dict[str, list[str]] = {}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        # Find agent class
                        agent_name = None
                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef) and node.name.value.endswith("Agent"):
                                agent_name = node.name.value
                                break

                        if not agent_name:
                            continue

                        # Find imports of other agents
                        imported_agents = []
                        for node in tree.walk():
                            if isinstance(node, cst.ImportFrom):
                                # from .agents import ResearcherAgent
                                if node.names and isinstance(node.names, cst.ImportStar) is False:
                                    for name in node.names:
                                        if isinstance(name, cst.ImportAlias):
                                            imported = name.name.value if isinstance(name.name, cst.Name) else str(name.name)
                                            if imported.endswith("Agent"):
                                                imported_agents.append(imported)

                        if imported_agents:
                            dependencies[agent_name] = imported_agents

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                results = cast(AgentDependenciesResult, {"dependencies": dependencies})

            elif query_enum == OntologyQueryType.CONFIG_SCHEMA:
                # Extract Pydantic config field schemas
                config_schemas: dict[str, dict[str, str]] = {}
                for py_file in py_files:
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree, wrapper = parse_module_with_metadata(source)
                        files_analyzed += 1
                        nodes_parsed += len(list(tree.walk()))

                        for node in tree.walk():
                            if isinstance(node, cst.ClassDef):
                                # Find Config classes (typically AgentNameConfig)
                                if node.name.value.endswith("Config"):
                                    config_name = node.name.value
                                    fields = {}

                                    # Extract annotated assignments (field: type = default)
                                    for class_node in node.walk():
                                        if isinstance(class_node, cst.AnnAssign):
                                            if isinstance(class_node.target, cst.Name):
                                                field_name = class_node.target.value
                                                field_type = "Any"
                                                if class_node.annotation:
                                                    if isinstance(class_node.annotation.annotation, cst.Name):
                                                        field_type = class_node.annotation.annotation.value
                                                fields[field_name] = field_type

                                    if fields:
                                        config_schemas[config_name] = fields

                    except Exception as e:
                        logger.warning(f"Failed to parse {py_file}: {e}")
                        continue

                results = cast(ConfigSchemaResult, {"config_schemas": config_schemas})

            else:
                # Unsupported query type (should not reach here due to enum validation)
                return {
                    "query_type": query_enum.value,
                    "results": {},
                    "confidence": 0.0,
                    "metadata": {"error": f"Unsupported query type: {query_enum.value}"},
                }

            # Calculate confidence based on coverage
            confidence = min(1.0, files_analyzed / max(len(py_files), 1))

            return {
                "query_type": query_enum.value,
                "results": results,
                "confidence": confidence,
                "metadata": {
                    "files_analyzed": files_analyzed,
                    "total_files": len(py_files),
                    "nodes_parsed": nodes_parsed,
                },
            }

        except Exception as e:
            logger.error(f"Error extracting ontology: {e}")
            return {
                "query_type": query_type,  # Original string if enum conversion failed
                "results": {},
                "confidence": 0.0,
                "metadata": {"error": str(e)},
            }

    @agent.tool
    async def find_pattern(
        ctx: RunContext[PythonLinguistDeps],
        pattern_type: str,
        pattern_value: str,
        search_path: str,
    ) -> dict[str, Any]:
        """Find structural patterns in Python code via LibCST matching.

        Args:
            pattern_type: One of: "function", "class", "decorator", "import", "call"
            pattern_value: Value to match (e.g., function name, class name)
            search_path: Directory or file to search

        Returns:
            Dict with:
            - matches: list[dict] - Matched patterns with file, line, code snippet
            - statistics: dict - Total nodes, match count
            - confidence: float - Match confidence

        Pattern Types:
            - "function": Find function definitions by name
            - "class": Find class definitions by name
            - "decorator": Find uses of decorator (e.g., "@agent.tool")
            - "import": Find import statements
            - "call": Find function/method calls

        Example:
            Find all @agent.tool decorated functions:
            ```
            result = await find_pattern("decorator", "agent.tool", "agents/")
            for match in result["matches"]:
                print(f"{match['file_path']}:{match['line_number']}: {match['code_snippet']}")
            ```
        """
        try:
            # Resolve search path
            full_path = ctx.deps.workspace_root / search_path
            if not full_path.exists():
                return {
                    "matches": [],
                    "statistics": {"error": f"Path not found: {search_path}"},
                    "confidence": 0.0,
                }

            # Find Python files
            if full_path.is_file():
                py_files = [full_path]
            else:
                py_files = list(full_path.rglob("*.py"))

            matches = []
            total_nodes = 0

            for py_file in py_files:
                try:
                    source = py_file.read_text(encoding="utf-8")
                    tree, wrapper = parse_module_with_metadata(source)
                    lines = source.splitlines()
                    total_nodes += len(list(tree.walk()))

                    # Resolve position metadata for accurate line numbers
                    positions = wrapper.resolve(PositionProvider)

                    # Match based on pattern type
                    for node in tree.walk():
                        matched = False
                        code_snippet = ""
                        line_number = 1
                        node_type = type(node).__name__

                        if pattern_type == "function" and isinstance(node, cst.FunctionDef):
                            if node.name.value == pattern_value:
                                matched = True
                                # Get accurate line number from metadata
                                if node in positions:
                                    line_number = positions[node].start.line
                                code_snippet = f"def {node.name.value}(...)"

                        elif pattern_type == "class" and isinstance(node, cst.ClassDef):
                            if node.name.value == pattern_value:
                                matched = True
                                # Get accurate line number from metadata
                                if node in positions:
                                    line_number = positions[node].start.line
                                code_snippet = f"class {node.name.value}(...)"

                        elif pattern_type == "decorator" and isinstance(node, cst.Decorator):
                            # Match decorator attribute (e.g., @agent.tool)
                            if isinstance(node.decorator, cst.Attribute):
                                if f"{node.decorator.value.value}.{node.decorator.attr.value}" == pattern_value:
                                    matched = True
                                    # Get line number from metadata
                                    if node in positions:
                                        line_number = positions[node].start.line
                                    code_snippet = f"@{pattern_value}"

                        if matched:
                            matches.append({
                                "file_path": str(py_file.relative_to(ctx.deps.workspace_root)),
                                "line_number": line_number,
                                "node_type": node_type,
                                "code_snippet": code_snippet,
                                "context": {},
                            })

                except Exception as e:
                    logger.warning(f"Failed to parse {py_file}: {e}")
                    continue

            return {
                "matches": matches,
                "statistics": {
                    "total_nodes": total_nodes,
                    "match_count": len(matches),
                    "files_searched": len(py_files),
                },
                "confidence": 0.95 if matches else 0.5,
            }

        except Exception as e:
            logger.error(f"Error finding pattern: {e}")
            return {
                "matches": [],
                "statistics": {"error": str(e)},
                "confidence": 0.0,
            }

    @agent.tool
    async def analyze_types(
        ctx: RunContext[PythonLinguistDeps],
        target_path: str,
    ) -> dict[str, Any]:
        """Analyze type hint coverage in Python code.

        Args:
            target_path: File or directory to analyze

        Returns:
            Dict with:
            - typed_elements: dict[str, str] - Elements with type hints
            - untyped_elements: list[str] - Elements missing hints
            - coverage: float - Type coverage percentage (0.0-1.0)
            - recommendations: list[str] - Suggestions for improvement

        Example:
            Check type coverage for agent module:
            ```
            result = await analyze_types("agents/researcher.py")
            print(f"Type coverage: {result['coverage']:.0%}")
            print(f"Missing types: {', '.join(result['untyped_elements'][:5])}")
            ```
        """
        try:
            # Resolve target path
            full_path = ctx.deps.workspace_root / target_path
            if not full_path.exists():
                return {
                    "typed_elements": {},
                    "untyped_elements": [],
                    "coverage": 0.0,
                    "recommendations": [f"Path not found: {target_path}"],
                }

            # Find Python files
            if full_path.is_file():
                py_files = [full_path]
            else:
                py_files = list(full_path.rglob("*.py"))

            typed_elements = {}
            untyped_elements = []
            total_functions = 0
            typed_functions = 0

            for py_file in py_files:
                try:
                    source = py_file.read_text(encoding="utf-8")
                    tree, wrapper = parse_module_with_metadata(source)

                    # Analyze function definitions
                    for node in tree.walk():
                        if isinstance(node, cst.FunctionDef):
                            total_functions += 1
                            func_name = node.name.value

                            # Check return type annotation
                            has_return_type = node.returns is not None

                            # Check parameter type annotations
                            has_param_types = all(
                                param.annotation is not None
                                for param in node.params.params
                                if param.name.value != "self" and param.name.value != "ctx"
                            )

                            if has_return_type and has_param_types:
                                typed_functions += 1
                                # Extract return type
                                return_type = "Unknown"
                                if node.returns:
                                    if isinstance(node.returns.annotation, cst.Name):
                                        return_type = node.returns.annotation.value
                                typed_elements[func_name] = return_type
                            else:
                                untyped_elements.append(f"{py_file.name}:{func_name}")

                except Exception as e:
                    logger.warning(f"Failed to parse {py_file}: {e}")
                    continue

            # Calculate coverage
            coverage = typed_functions / total_functions if total_functions > 0 else 0.0

            # Generate recommendations
            recommendations = []
            if coverage < 0.5:
                recommendations.append("Low type coverage - add type hints to improve")
            if untyped_elements:
                recommendations.append(f"Add type hints to {len(untyped_elements)} functions")
            if coverage >= 0.9:
                recommendations.append("Good type coverage - maintain this standard")

            return {
                "typed_elements": typed_elements,
                "untyped_elements": untyped_elements[:20],  # Limit output
                "coverage": coverage,
                "recommendations": recommendations,
                "statistics": {
                    "total_functions": total_functions,
                    "typed_functions": typed_functions,
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing types: {e}")
            return {
                "typed_elements": {},
                "untyped_elements": [],
                "coverage": 0.0,
                "recommendations": [f"Error: {e}"],
            }

    logger.info("Python Linguist agent created successfully")
    return agent


# Convenience function
def create_python_linguist(workspace_path: str | Path) -> Agent:
    """Convenience function to create Python Linguist with default settings.

    Args:
        workspace_path: Path to workspace directory

    Returns:
        Configured Python Linguist agent
    """
    return create_python_linguist_agent(PythonLinguistDeps(
        workspace_root=Path(workspace_path),
    ))
