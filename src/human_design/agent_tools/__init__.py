"""Shared agent tools infrastructure.

This package provides type-safe, reusable tools for all agents in the DODO system.
Tools are organized into three categories:

1. **FileSystemTools** (filesystem.py):
   - read_file, write_file, list_directory
   - file_exists, directory_exists

2. **GitHistoryTools** (git_history.py):
   - git_log, git_show, git_tag
   - git_diff, git_current_branch

3. **CodeSearchTools** (code_search.py):
   - grep, find_files, find_in_files

## Usage Pattern

```python
from pydantic_ai import Agent
from dataclasses import dataclass
from pathlib import Path

from dodo.agent_tools import (
    register_filesystem_tools,
    register_git_history_tools,
    register_code_search_tools,
    FileSystemDeps,
    GitHistoryDeps,
    CodeSearchDeps,
)

# Define agent-specific dependencies
@dataclass
class MyAgentDeps:
    workspace_root: Path
    # ... other agent-specific deps

# Create agent
agent = Agent(
    "openai:gpt-4o",
    deps_type=MyAgentDeps,
)

# Register tool sets
register_filesystem_tools(agent, FileSystemDeps(
    workspace_root=Path("/path/to/workspace"),
    max_file_size_mb=10,
))

register_git_history_tools(agent, GitHistoryDeps(
    workspace_root=Path("/path/to/repo"),
    max_commits_default=50,
))

register_code_search_tools(agent, CodeSearchDeps(
    workspace_root=Path("/path/to/workspace"),
    max_results_default=50,
))
```

## Design Principles

1. **Type Safety**: All inputs/outputs use Pydantic models
2. **Validation at Boundaries**: Tools validate all parameters
3. **Path Security**: All file operations validate paths are within workspace
4. **Observability**: Tools log all operations for debugging
5. **Composability**: Agents register only the tools they need
6. **Error Messages**: Clear, actionable error messages

## Shared Types

All tools use shared Pydantic models from `types.py`:
- FileContent, WriteFileResult, DirectoryListing
- GitCommit, GitLogResult, GitFileContent, GitTagInfo
- SearchMatch, SearchResult

These types provide:
- IDE autocomplete
- Runtime validation
- Self-documenting APIs
- Consistent error handling
"""

# Public API - Tool Registration Functions
from .filesystem import register_filesystem_tools
from .git_history import register_git_history_tools
from .code_search import register_code_search_tools

# Public API - Dependency Classes
from .filesystem import FileSystemDeps
from .git_history import GitHistoryDeps
from .code_search import CodeSearchDeps

# Public API - Shared Types
from .types import (
    FileContent,
    WriteFileResult,
    DirectoryListing,
    SearchMatch,
    SearchResult,
    GitCommit,
    GitLogResult,
    GitFileContent,
    GitTagInfo,
    FilePath,
    DirectoryPath,
    GitRef,
    SearchPattern,
)

# Public API - Base Classes
from .base import BaseToolDeps, ToolRegistrar

__all__ = [
    # Registration functions
    "register_filesystem_tools",
    "register_git_history_tools",
    "register_code_search_tools",
    
    # Dependency classes
    "FileSystemDeps",
    "GitHistoryDeps",
    "CodeSearchDeps",
    "BaseToolDeps",
    
    # Shared types
    "FileContent",
    "WriteFileResult",
    "DirectoryListing",
    "SearchMatch",
    "SearchResult",
    "GitCommit",
    "GitLogResult",
    "GitFileContent",
    "GitTagInfo",
    "FilePath",
    "DirectoryPath",
    "GitRef",
    "SearchPattern",
    
    # Protocols
    "ToolRegistrar",
]
