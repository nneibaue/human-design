"""Base classes and utilities for agent tools.

This module provides common infrastructure for all agent tool modules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import logging

logger = logging.getLogger(__name__)


@dataclass
class BaseToolDeps:
    """Base dependencies shared by all tool sets.
    
    Tool-specific dependency classes should inherit from this.
    """
    workspace_root: Path
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate base dependencies."""
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")
        
        if not self.workspace_root.is_dir():
            raise ValueError(f"Workspace root is not a directory: {self.workspace_root}")
        
        # Configure logging
        logging.getLogger("dodo.agent_tools").setLevel(self.log_level)


class ToolRegistrar(Protocol):
    """Protocol for tool registration functions.
    
    Each tool module should provide a registration function matching this signature.
    This enables type-safe tool registration across all agents.
    """
    
    def __call__(self, agent, deps) -> None:
        """Register tools with an agent.
        
        Args:
            agent: Pydantic AI Agent instance
            deps: Tool-specific dependencies (dataclass)
        """
        ...


def validate_file_path(workspace_root: Path, file_path: str) -> Path:
    """Validate and resolve a file path within workspace.
    
    Args:
        workspace_root: Root workspace directory
        file_path: Relative or absolute file path
        
    Returns:
        Resolved absolute Path
        
    Raises:
        ValueError: If path is outside workspace or invalid
    """
    # Handle both relative and absolute paths
    if Path(file_path).is_absolute():
        full_path = Path(file_path)
    else:
        full_path = workspace_root / file_path
    
    # Resolve to eliminate .. and symlinks
    try:
        resolved = full_path.resolve()
    except (RuntimeError, OSError) as e:
        raise ValueError(f"Invalid file path: {file_path}") from e
    
    # Ensure path is within workspace (security check)
    try:
        resolved.relative_to(workspace_root.resolve())
    except ValueError:
        raise ValueError(
            f"File path outside workspace: {file_path} "
            f"(workspace: {workspace_root})"
        )
    
    return resolved


def validate_directory_path(workspace_root: Path, dir_path: str) -> Path:
    """Validate and resolve a directory path within workspace.
    
    Args:
        workspace_root: Root workspace directory
        dir_path: Relative or absolute directory path
        
    Returns:
        Resolved absolute Path
        
    Raises:
        ValueError: If path is outside workspace or invalid
    """
    # Reuse file path validation
    resolved = validate_file_path(workspace_root, dir_path)
    
    # Additional check: must be a directory if it exists
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")
    
    return resolved


def log_tool_call(tool_name: str, **kwargs) -> None:
    """Log a tool invocation for observability.
    
    Args:
        tool_name: Name of the tool being called
        **kwargs: Tool parameters (will be sanitized for logging)
    """
    # Sanitize sensitive parameters
    sanitized = {}
    for key, value in kwargs.items():
        if "password" in key.lower() or "secret" in key.lower() or "token" in key.lower():
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = f"<{type(value).__name__}>"
    
    logger.info(f"Tool call: {tool_name}", extra={"params": sanitized})


def log_tool_result(tool_name: str, success: bool, **kwargs) -> None:
    """Log a tool result for observability.
    
    Args:
        tool_name: Name of the tool
        success: Whether the tool succeeded
        **kwargs: Result metadata (e.g., bytes_written, matches_found)
    """
    logger.info(
        f"Tool result: {tool_name}",
        extra={"success": success, "metadata": kwargs}
    )
