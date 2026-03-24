"""File system tools for agents.

Provides type-safe file system operations:
- read_file: Read file contents with optional line ranges
- write_file: Write content to files (creates parent dirs)
- list_directory: List directory contents
- file_exists: Check if file exists
- directory_exists: Check if directory exists

All tools validate paths are within workspace for security.
"""

from dataclasses import dataclass
from pathlib import Path
from pydantic import Field
from pydantic_ai import RunContext
import logging

from .types import (
    FileContent,
    WriteFileResult,
    DirectoryListing,
    FilePath,
    DirectoryPath,
)
from .base import (
    BaseToolDeps,
    validate_file_path,
    validate_directory_path,
    log_tool_call,
    log_tool_result,
)

logger = logging.getLogger(__name__)


@dataclass
class FileSystemDeps(BaseToolDeps):
    """Dependencies for file system operations.
    
    Inherits workspace_root and log_level from BaseToolDeps.
    """
    max_file_size_mb: int = 10
    default_encoding: str = "utf-8"
    max_lines_default: int = 500
    
    def __post_init__(self):
        """Validate file system dependencies."""
        super().__post_init__()
        
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.max_lines_default <= 0:
            raise ValueError("max_lines_default must be positive")


def register_filesystem_tools(agent, deps: FileSystemDeps) -> None:
    """Register file system tools with an agent.
    
    Args:
        agent: Pydantic AI Agent instance
        deps: FileSystemDeps configuration
        
    Registers:
        - read_file: Read file contents
        - write_file: Write file contents
        - list_directory: List directory contents
        - file_exists: Check file existence
        - directory_exists: Check directory existence
    """
    
    @agent.tool
    async def read_file(
        ctx: RunContext[FileSystemDeps],
        file_path: FilePath,
        start_line: int | None = None,
        end_line: int | None = None,
        max_lines: int | None = None,
    ) -> FileContent:
        """Read contents of a file with optional line range.
        
        Use this tool to read file contents for analysis or modification.
        Returns file contents with line numbers and metadata.
        
        Args:
            file_path: Path to file relative to workspace root
            start_line: Optional starting line number (1-indexed, inclusive)
            end_line: Optional ending line number (1-indexed, inclusive)
            max_lines: Maximum lines to return (default: 500)
            
        Returns:
            FileContent with path, content, line_count, encoding, size_bytes
            
        Raises:
            ValueError: If file not found, too large, or path invalid
        """
        log_tool_call("read_file", file_path=file_path, start_line=start_line, end_line=end_line)
        
        # Validate and resolve path
        resolved_path = validate_file_path(ctx.deps.workspace_root, file_path)
        
        # Check file exists
        if not resolved_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if not resolved_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check file size
        size_bytes = resolved_path.stat().st_size
        max_size_bytes = ctx.deps.max_file_size_mb * 1024 * 1024
        
        if size_bytes > max_size_bytes:
            raise ValueError(
                f"File exceeds max size: {file_path} "
                f"({size_bytes / (1024*1024):.2f}MB > {ctx.deps.max_file_size_mb}MB)"
            )
        
        # Read file
        try:
            content = resolved_path.read_text(encoding=ctx.deps.default_encoding)
        except UnicodeDecodeError:
            # Try common fallback encodings
            for encoding in ["latin-1", "cp1252"]:
                try:
                    content = resolved_path.read_text(encoding=encoding)
                    logger.warning(
                        f"File {file_path} decoded with fallback encoding: {encoding}"
                    )
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Unable to decode file: {file_path}")
        
        # Apply line filtering
        lines = content.splitlines()
        original_line_count = len(lines)
        
        if start_line is not None or end_line is not None:
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else len(lines)
            lines = lines[start_idx:end_idx]
        
        # Apply max_lines limit
        max_lines = max_lines or ctx.deps.max_lines_default
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            logger.warning(
                f"File {file_path} truncated to {max_lines} lines "
                f"(original: {original_line_count})"
            )
        
        result_content = "\n".join(lines)
        result = FileContent(
            path=file_path,
            content=result_content,
            line_count=len(lines),
            encoding=ctx.deps.default_encoding,
            size_bytes=len(result_content.encode(ctx.deps.default_encoding)),
        )
        
        log_tool_result("read_file", success=True, lines=len(lines), bytes=result.size_bytes)
        return result
    
    @agent.tool
    async def write_file(
        ctx: RunContext[FileSystemDeps],
        file_path: FilePath,
        content: str,
    ) -> WriteFileResult:
        """Write content to a file.
        
        Creates parent directories if needed. Overwrites existing files.
        Use this tool to create or update files.
        
        Args:
            file_path: Path to file relative to workspace root
            content: Content to write
            
        Returns:
            WriteFileResult with status, path, bytes_written, created_directories
            
        Raises:
            ValueError: If path invalid or write fails
        """
        log_tool_call("write_file", file_path=file_path, content_length=len(content))
        
        # Validate and resolve path
        resolved_path = validate_file_path(ctx.deps.workspace_root, file_path)
        
        # Track created directories
        created_dirs = []
        if not resolved_path.parent.exists():
            # Find which directories need to be created
            current = resolved_path.parent
            while not current.exists() and current != ctx.deps.workspace_root:
                created_dirs.append(str(current.relative_to(ctx.deps.workspace_root)))
                current = current.parent
            
            # Create parent directories
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created parent directories for {file_path}")
        
        # Write file
        try:
            resolved_path.write_text(content, encoding=ctx.deps.default_encoding)
        except OSError as e:
            raise ValueError(f"Failed to write file {file_path}: {e}") from e
        
        bytes_written = len(content.encode(ctx.deps.default_encoding))
        result = WriteFileResult(
            path=file_path,
            bytes_written=bytes_written,
            created_directories=list(reversed(created_dirs)),  # Top-down order
        )
        
        log_tool_result("write_file", success=True, bytes=bytes_written)
        return result
    
    @agent.tool
    async def list_directory(
        ctx: RunContext[FileSystemDeps],
        directory_path: DirectoryPath = ".",
        include_hidden: bool = False,
    ) -> DirectoryListing:
        """List contents of a directory.
        
        Returns separate lists of files and subdirectories.
        
        Args:
            directory_path: Path to directory relative to workspace root (default: ".")
            include_hidden: Whether to include hidden files/directories (default: False)
            
        Returns:
            DirectoryListing with path, files, directories, total_items
            
        Raises:
            ValueError: If directory not found or path invalid
        """
        log_tool_call("list_directory", directory_path=directory_path)
        
        # Validate and resolve path
        resolved_path = validate_directory_path(ctx.deps.workspace_root, directory_path)
        
        # Check directory exists
        if not resolved_path.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # List contents
        files = []
        directories = []
        
        for item in resolved_path.iterdir():
            # Skip hidden files unless requested
            if not include_hidden and item.name.startswith("."):
                continue
            
            if item.is_file():
                files.append(item.name)
            elif item.is_dir():
                directories.append(item.name)
        
        # Sort for consistent ordering
        files.sort()
        directories.sort()
        
        result = DirectoryListing(
            path=directory_path,
            files=files,
            directories=directories,
            total_items=len(files) + len(directories),
            hidden_items_included=include_hidden,
        )
        
        log_tool_result(
            "list_directory",
            success=True,
            files=len(files),
            directories=len(directories),
        )
        return result
    
    @agent.tool
    async def file_exists(
        ctx: RunContext[FileSystemDeps],
        file_path: FilePath,
    ) -> bool:
        """Check if a file exists.
        
        Args:
            file_path: Path to file relative to workspace root
            
        Returns:
            True if file exists, False otherwise
        """
        log_tool_call("file_exists", file_path=file_path)
        
        try:
            resolved_path = validate_file_path(ctx.deps.workspace_root, file_path)
            exists = resolved_path.exists() and resolved_path.is_file()
        except ValueError:
            # Invalid path = doesn't exist
            exists = False
        
        log_tool_result("file_exists", success=True, exists=exists)
        return exists
    
    @agent.tool
    async def directory_exists(
        ctx: RunContext[FileSystemDeps],
        directory_path: DirectoryPath,
    ) -> bool:
        """Check if a directory exists.
        
        Args:
            directory_path: Path to directory relative to workspace root
            
        Returns:
            True if directory exists, False otherwise
        """
        log_tool_call("directory_exists", directory_path=directory_path)
        
        try:
            resolved_path = validate_directory_path(ctx.deps.workspace_root, directory_path)
            exists = resolved_path.exists() and resolved_path.is_dir()
        except ValueError:
            # Invalid path = doesn't exist
            exists = False
        
        log_tool_result("directory_exists", success=True, exists=exists)
        return exists
