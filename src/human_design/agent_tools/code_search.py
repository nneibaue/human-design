"""Code search tools for agents.

Provides type-safe code search operations:
- grep: Search for patterns in files
- find_files: Find files by name pattern
- find_in_files: Search pattern with file filtering

All tools support regex patterns and contextual results.
"""

from dataclasses import dataclass
from pathlib import Path
from pydantic import Field
from pydantic_ai import RunContext
import re
import logging
from typing import Pattern

from .types import (
    SearchMatch,
    SearchResult,
    SearchPattern,
    FilePath,
)
from .base import (
    BaseToolDeps,
    validate_directory_path,
    log_tool_call,
    log_tool_result,
)

logger = logging.getLogger(__name__)


@dataclass
class CodeSearchDeps(BaseToolDeps):
    """Dependencies for code search operations.
    
    Inherits workspace_root from BaseToolDeps.
    """
    max_results_default: int = 50
    max_file_size_mb: int = 10
    context_lines_default: int = 2
    default_file_patterns: list[str] = None  # e.g., ["*.py", "*.md"]
    exclude_patterns: list[str] = None  # e.g., ["*.pyc", ".git/*", "node_modules/*"]
    
    def __post_init__(self):
        """Validate code search dependencies."""
        super().__post_init__()
        
        if self.max_results_default <= 0:
            raise ValueError("max_results_default must be positive")
        
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.context_lines_default < 0:
            raise ValueError("context_lines_default must be non-negative")
        
        # Set default exclude patterns if not provided
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                ".git/*",
                "*.pyc",
                "__pycache__/*",
                "*.so",
                "*.dylib",
                "*.egg-info/*",
                ".pytest_cache/*",
                ".mypy_cache/*",
                "node_modules/*",
                ".venv/*",
                "venv/*",
            ]
        
        # Set default file patterns if not provided
        if self.default_file_patterns is None:
            self.default_file_patterns = ["*"]


def _should_exclude_path(path: Path, exclude_patterns: list[str]) -> bool:
    """Check if path matches any exclude pattern.
    
    Args:
        path: Path to check
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        True if path should be excluded
    """
    path_str = str(path)
    
    for pattern in exclude_patterns:
        # Convert glob to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        if re.search(regex_pattern, path_str):
            return True
    
    return False


def _matches_file_pattern(path: Path, file_patterns: list[str]) -> bool:
    """Check if path matches any file pattern.
    
    Args:
        path: Path to check
        file_patterns: List of glob patterns to match
        
    Returns:
        True if path matches any pattern
    """
    if "*" in file_patterns or "**/*" in file_patterns:
        return True
    
    path_str = str(path)
    
    for pattern in file_patterns:
        # Convert glob to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        if re.search(regex_pattern, path_str):
            return True
    
    return False


def _find_files_recursive(
    root: Path,
    file_patterns: list[str],
    exclude_patterns: list[str],
    max_results: int,
) -> list[Path]:
    """Recursively find files matching patterns.
    
    Args:
        root: Root directory to search
        file_patterns: List of glob patterns to match
        exclude_patterns: List of glob patterns to exclude
        max_results: Maximum files to return
        
    Returns:
        List of matching file paths
    """
    found_files = []
    
    def walk_dir(directory: Path):
        if len(found_files) >= max_results:
            return
        
        try:
            for item in directory.iterdir():
                if len(found_files) >= max_results:
                    return
                
                # Check exclude patterns
                if _should_exclude_path(item, exclude_patterns):
                    continue
                
                if item.is_file():
                    if _matches_file_pattern(item, file_patterns):
                        found_files.append(item)
                elif item.is_dir():
                    walk_dir(item)
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")
    
    walk_dir(root)
    return found_files


def register_code_search_tools(agent, deps: CodeSearchDeps) -> None:
    """Register code search tools with an agent.
    
    Args:
        agent: Pydantic AI Agent instance
        deps: CodeSearchDeps configuration
        
    Registers:
        - grep: Search for pattern in files
        - find_files: Find files by name pattern
        - find_in_files: Combined search with file filtering
    """
    
    @agent.tool
    async def grep(
        ctx: RunContext[CodeSearchDeps],
        pattern: SearchPattern,
        directory: str = ".",
        file_pattern: str = "*",
        ignore_case: bool = False,
        max_results: int | None = None,
        context_lines: int | None = None,
    ) -> SearchResult:
        """Search for pattern in files.
        
        Recursively searches files for regex pattern, returning matches with context.
        
        Args:
            pattern: Search pattern (regex or plain text)
            directory: Directory to search (default: workspace root)
            file_pattern: Filter to files matching glob pattern (default: "*")
            ignore_case: Case-insensitive search (default: False)
            max_results: Maximum matches to return (default: 50)
            context_lines: Lines of context before/after match (default: 2)
            
        Returns:
            SearchResult with matches, total_matches, truncated flag
            
        Raises:
            ValueError: If pattern invalid or directory not found
        """
        log_tool_call(
            "grep",
            pattern=pattern,
            directory=directory,
            file_pattern=file_pattern,
        )
        
        max_results = max_results or ctx.deps.max_results_default
        context_lines = context_lines if context_lines is not None else ctx.deps.context_lines_default
        
        # Validate directory
        search_root = validate_directory_path(ctx.deps.workspace_root, directory)
        
        if not search_root.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        # Compile regex pattern
        try:
            flags = re.IGNORECASE if ignore_case else 0
            regex: Pattern = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {pattern} - {e}")
        
        # Find files to search
        file_patterns = [file_pattern] if file_pattern != "*" else ctx.deps.default_file_patterns
        files_to_search = _find_files_recursive(
            search_root,
            file_patterns,
            ctx.deps.exclude_patterns,
            max_results=1000,  # Search more files than result limit
        )
        
        # Search files
        matches = []
        searched_paths = []
        
        for file_path in files_to_search:
            if len(matches) >= max_results:
                break
            
            # Check file size
            if file_path.stat().st_size > ctx.deps.max_file_size_mb * 1024 * 1024:
                logger.warning(f"Skipping large file: {file_path}")
                continue
            
            # Read and search file
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                continue
            
            lines = content.splitlines()
            searched_paths.append(str(file_path.relative_to(ctx.deps.workspace_root)))
            
            for line_idx, line in enumerate(lines):
                if len(matches) >= max_results:
                    break
                
                if regex.search(line):
                    # Get context lines
                    context_before = []
                    context_after = []
                    
                    if context_lines > 0:
                        start_idx = max(0, line_idx - context_lines)
                        context_before = lines[start_idx:line_idx]
                        
                        end_idx = min(len(lines), line_idx + context_lines + 1)
                        context_after = lines[line_idx + 1:end_idx]
                    
                    matches.append(
                        SearchMatch(
                            file_path=str(file_path.relative_to(ctx.deps.workspace_root)),
                            line_number=line_idx + 1,  # 1-indexed
                            line_content=line,
                            context_before=context_before,
                            context_after=context_after,
                        )
                    )
        
        truncated = len(matches) == max_results
        result = SearchResult(
            pattern=pattern,
            matches=matches,
            total_matches=len(matches),
            truncated=truncated,
            search_paths=searched_paths,
        )
        
        log_tool_result("grep", success=True, matches=len(matches))
        return result
    
    @agent.tool
    async def find_files(
        ctx: RunContext[CodeSearchDeps],
        name_pattern: str,
        directory: str = ".",
        max_results: int | None = None,
    ) -> list[FilePath]:
        """Find files by name pattern.
        
        Recursively searches for files matching name pattern (glob or regex).
        
        Args:
            name_pattern: File name pattern (e.g., "*.py", "test_*")
            directory: Directory to search (default: workspace root)
            max_results: Maximum files to return (default: 50)
            
        Returns:
            List of file paths matching pattern
            
        Raises:
            ValueError: If directory not found
        """
        log_tool_call("find_files", name_pattern=name_pattern, directory=directory)
        
        max_results = max_results or ctx.deps.max_results_default
        
        # Validate directory
        search_root = validate_directory_path(ctx.deps.workspace_root, directory)
        
        if not search_root.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        # Find matching files
        found_files = _find_files_recursive(
            search_root,
            [name_pattern],
            ctx.deps.exclude_patterns,
            max_results,
        )
        
        # Convert to relative paths
        result = [
            str(f.relative_to(ctx.deps.workspace_root))
            for f in found_files
        ]
        
        log_tool_result("find_files", success=True, files=len(result))
        return result
    
    @agent.tool
    async def find_in_files(
        ctx: RunContext[CodeSearchDeps],
        pattern: SearchPattern,
        name_pattern: str = "*",
        directory: str = ".",
        ignore_case: bool = False,
        max_results: int | None = None,
    ) -> SearchResult:
        """Search for pattern in files matching name pattern.
        
        Combines grep and find_files - searches only in files matching name pattern.
        
        Args:
            pattern: Search pattern (regex or plain text)
            name_pattern: File name pattern to search (default: "*")
            directory: Directory to search (default: workspace root)
            ignore_case: Case-insensitive search (default: False)
            max_results: Maximum matches to return (default: 50)
            
        Returns:
            SearchResult with matches from files matching name pattern
            
        Raises:
            ValueError: If pattern invalid or directory not found
        """
        log_tool_call(
            "find_in_files",
            pattern=pattern,
            name_pattern=name_pattern,
            directory=directory,
        )
        
        # Delegate to grep with file_pattern
        return await grep(
            ctx,
            pattern=pattern,
            directory=directory,
            file_pattern=name_pattern,
            ignore_case=ignore_case,
            max_results=max_results,
            context_lines=0,  # No context for combined search
        )
